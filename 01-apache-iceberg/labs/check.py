"""Run with Spark 3.5.5 and Iceberg runtime 3.5_2.12:1.12.0.

Creates a disposable warehouse, checks results, removes it on exit.
SQL is intentionally visible: the same statements can be run in spark-sql.
"""
from pathlib import Path
import tempfile

from pyspark.sql import SparkSession


def exercise(spark):
    def sql(statement):
        print(f"\nSQL> {statement}", flush=True)
        return spark.sql(statement)

    def check(label, actual, expected):
        assert actual == expected, f"{label}: expected {expected!r}, got {actual!r}"
        print(f"PASS: {label}: {actual!r}", flush=True)

    def rows(table="events"):
        return [tuple(row) for row in sql(
            f"SELECT id, value FROM lab.training.{table} ORDER BY id"
        ).collect()]

    def snapshot():
        return sql("SELECT snapshot_id FROM lab.training.events.refs "
                   "WHERE name = 'main'").first()[0]

    sql("CREATE NAMESPACE lab.training")
    sql("""CREATE TABLE lab.training.events (
        id BIGINT, event_time TIMESTAMP, value STRING
    ) USING iceberg PARTITIONED BY (days(event_time))
    TBLPROPERTIES (
        'format-version'='2',
        'write.delete.mode'='copy-on-write',
        'write.update.mode'='copy-on-write',
        'write.merge.mode'='copy-on-write'
    )""")
    sql("""INSERT INTO lab.training.events VALUES
        (1, TIMESTAMP '2026-01-01 10:00:00', 'a'),
        (2, TIMESTAMP '2026-01-02 10:00:00', 'b')""")
    check("initial rows", rows(), [(1, "a"), (2, "b")])
    first_snapshot = snapshot()

    sql("ALTER TABLE lab.training.events ADD COLUMN source STRING")
    sql("ALTER TABLE lab.training.events RENAME COLUMN source TO origin")
    check("old rows have NULL in added column", sql(
        "SELECT count(*) FROM lab.training.events WHERE origin IS NULL"
    ).first()[0], 2)
    sql("ALTER TABLE lab.training.events REPLACE PARTITION FIELD "
        "days(event_time) WITH months(event_time)")
    sql("""INSERT INTO lab.training.events VALUES
        (3, TIMESTAMP '2026-02-01 10:00:00', 'c', 'batch')""")
    check("old and new partition specs coexist", sql(
        "SELECT count(DISTINCT spec_id) FROM lab.training.events.files"
    ).first()[0], 2)

    sql("""MERGE INTO lab.training.events t
        USING (SELECT 2L AS id, TIMESTAMP '2026-01-02 10:00:00' AS event_time,
                      'updated' AS value, 'merge' AS origin
               UNION ALL
               SELECT 4L, TIMESTAMP '2026-02-02 10:00:00', 'd', 'merge') s
        ON t.id = s.id
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *""")
    check("merge updates and inserts", rows(),
          [(1, "a"), (2, "updated"), (3, "c"), (4, "d")])
    sql("DELETE FROM lab.training.events WHERE id = 1")
    check("delete removes selected row", rows(),
          [(2, "updated"), (3, "c"), (4, "d")])
    history = [tuple(row) for row in sql(
        f"SELECT id, value FROM lab.training.events VERSION AS OF {first_snapshot} "
        "ORDER BY id"
    ).collect()]
    check("time travel preserves original rows", history, [(1, "a"), (2, "b")])
    sql(f"CALL lab.system.rollback_to_snapshot('training.events', {first_snapshot})").show()
    check("rollback restores original data", rows(), [(1, "a"), (2, "b")])
    check("rollback does not undo schema evolution",
          "origin" in spark.table("lab.training.events").columns, True)
    sql("SELECT snapshot_id, parent_id, operation FROM lab.training.events.snapshots").show()
    sql("SELECT made_current_at, snapshot_id, is_current_ancestor "
        "FROM lab.training.events.history").show()
    sql("SELECT * FROM lab.training.events.manifests").show(truncate=False)

    sql("""CREATE TABLE lab.training.compaction_demo (id BIGINT, value STRING)
        USING iceberg TBLPROPERTIES ('format-version'='2')""")
    sql("INSERT INTO lab.training.compaction_demo VALUES (1, 'a'), (2, 'b')")
    sql("INSERT INTO lab.training.compaction_demo VALUES (3, 'c'), (4, 'd')")
    before_rows = rows("compaction_demo")
    before = sql("SELECT count(*) FROM lab.training.compaction_demo.files "
                 "WHERE content = 0").first()[0]
    result = sql("""CALL lab.system.rewrite_data_files(
        table => 'training.compaction_demo',
        options => map('rewrite-all', 'true')
    )""").collect()
    print(f"rewrite_data_files: {result}", flush=True)
    after = sql("SELECT count(*) FROM lab.training.compaction_demo.files "
                "WHERE content = 0").first()[0]
    check("compaction preserves rows", rows("compaction_demo"), before_rows)
    assert after < before, f"compaction did not reduce files: {before} -> {after}"
    print(f"PASS: compaction reduces files: {before} -> {after}", flush=True)
    sql("""CALL lab.system.remove_orphan_files(
        table => 'training.compaction_demo', dry_run => true
    )""").show()
    check("dry run preserves rows", rows("compaction_demo"), before_rows)
    print("\nALL ICEBERG LAB CHECKS PASSED", flush=True)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="iceberg-learning-") as work:
        spark = (SparkSession.builder.appName("iceberg-learning")
                 .config("spark.sql.extensions",
                         "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
                 .config("spark.sql.catalog.lab", "org.apache.iceberg.spark.SparkCatalog")
                 .config("spark.sql.catalog.lab.type", "hadoop")
                 .config("spark.sql.catalog.lab.warehouse", Path(work, "warehouse").as_uri())
                 .config("spark.sql.session.timeZone", "UTC")
                 .config("spark.sql.shuffle.partitions", "2")
                 .config("spark.ui.enabled", "false")
                 .getOrCreate())
        spark.sparkContext.setLogLevel("WARN")
        try:
            exercise(spark)
        finally:
            spark.stop()
