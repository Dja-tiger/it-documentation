---
title: "Java Custom Catalog"
tags: [apache-iceberg, catalogs, java, custom]
source_project: apache/iceberg
source_file: docs/docs/custom-catalog.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/custom-catalog.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Custom Catalog

Iceberg table можно читать по HDFS path или через Hive table, но вместо Hive также можно использовать собственный metastore. Для этого реализуются следующие extension points:

- [[#Custom TableOperations implementation|Custom TableOperations]];
- [[#Custom Catalog implementation|Custom Catalog]];
- [[#Custom FileIO implementation|Custom FileIO]];
- [[#Custom LocationProvider implementation|Custom LocationProvider]];
- [[#Custom IcebergSource|Custom IcebergSource]].

> [!important]
> Для encrypted tables custom catalog обязан выполнить security requirements из [[encryption#Требования безопасности к catalog]].

## Custom TableOperations implementation

Расширьте `BaseMetastoreTableOperations`, реализовав чтение и атомарное обновление metadata location.

```java
class CustomTableOperations extends BaseMetastoreTableOperations {
  private String dbName;
  private String tableName;
  private Configuration conf;
  private FileIO fileIO;

  protected CustomTableOperations(Configuration conf, String dbName, String tableName) {
    this.conf = conf;
    this.dbName = dbName;
    this.tableName = tableName;
  }

  @Override
  public void doRefresh() {
    String metadataLocation = CustomService.getMetadataForTable(conf, dbName, tableName);
    refreshFromMetadataLocation(metadataLocation);
  }

  @Override
  public void doCommit(TableMetadata base, TableMetadata metadata) {
    String oldMetadataLocation = base.location();
    String newMetadataLocation = writeNewMetadata(metadata, currentVersion() + 1);
    CustomService.updateMetadataLocation(dbName, tableName, oldMetadataLocation, newMetadataLocation);
  }

  @Override
  public FileIO io() {
    if (fileIO == null) {
      fileIO = new HadoopFileIO(conf);
    }
    return fileIO;
  }
}
```

`TableOperations` обычно создаётся через `Catalog.newTableOps(TableIdentifier)`.

## Custom Catalog implementation

Расширьте `BaseMetastoreCatalog`, определив default warehouse location и создание `CustomTableOperations`.

```java
public class CustomCatalog extends BaseMetastoreCatalog {

  private Configuration configuration;

  // no-arg constructor required for dynamic loading
  public CustomCatalog() {
  }

  public CustomCatalog(Configuration configuration) {
    this.configuration = configuration;
  }

  @Override
  protected TableOperations newTableOps(TableIdentifier tableIdentifier) {
    String dbName = tableIdentifier.namespace().level(0);
    String tableName = tableIdentifier.name();
    return new CustomTableOperations(configuration, dbName, tableName);
  }

  @Override
  protected String defaultWarehouseLocation(TableIdentifier tableIdentifier) {
    String tableLocation = configuration.get("custom.iceberg.warehouse.location");
    if (tableLocation == null) {
      throw new RuntimeException("custom.iceberg.warehouse.location configuration not set!");
    }

    return String.format(
        "%s/%s.db/%s", tableLocation,
        tableIdentifier.namespace().levels()[0],
        tableIdentifier.name());
  }

  @Override
  public boolean dropTable(TableIdentifier identifier, boolean purge) {
    CustomService.deleteTable(identifier.namespace().level(0), identifier.name());
  }

  @Override
  public void renameTable(TableIdentifier from, TableIdentifier to) {
    Preconditions.checkArgument(
        from.namespace().level(0).equals(to.namespace().level(0)),
        "Cannot move table between databases");
    CustomService.renameTable(from.namespace().level(0), from.name(), to.name());
  }

  public void initialize(String name, Map<String, String> properties) {
  }
}
```

Spark/Flink загружают custom catalog через property `catalog-impl`. Для MapReduce реализуйте `org.apache.iceberg.mr.CatalogLoader` и задайте Hadoop property `iceberg.mr.catalog.loader.class`.

Если catalog должен читать Hadoop configuration, реализуйте `org.apache.hadoop.conf.Configurable`.

## Custom FileIO implementation

```java
public class CustomFileIO implements FileIO {

  public CustomFileIO() {
  }

  @Override
  public InputFile newInputFile(String s) {
    return new CustomInputFile(s);
  }

  @Override
  public OutputFile newOutputFile(String s) {
    return new CustomOutputFile(s);
  }

  @Override
  public void deleteFile(String path) {
    Path toDelete = new Path(path);
    FileSystem fs = Util.getFs(toDelete);
    try {
      fs.delete(toDelete, false /* not recursive */);
    } catch (IOException e) {
      throw new RuntimeIOException(e, "Failed to delete file: %s", path);
    }
  }

  public void initialize(Map<String, String> properties) {
  }
}
```

Custom `FileIO` можно вернуть из `TableOperations.io()` либо динамически подключить в `HadoopCatalog`/`HiveCatalog` через `io-impl`.

Для Hadoop configuration реализуйте `Configurable`.

## Custom LocationProvider implementation

`LocationProvider` определяет paths новых data files.

```java
public class CustomLocationProvider implements LocationProvider {

  private String tableLocation;

  public CustomLocationProvider(String tableLocation, Map<String, String> properties) {
    this.tableLocation = tableLocation;
  }

  @Override
  public String newDataLocation(String filename) {
    return String.format(
        "%s/%s/%s", tableLocation, UUID.randomUUID().toString(), filename);
  }

  @Override
  public String newDataLocation(
      PartitionSpec spec, StructLike partitionData, String filename) {
    return newDataLocation(filename);
  }
}
```

Свой implementation можно вернуть из `TableOperations.locationProvider()` или задать per-table property `write.location-provider.impl`:

```sql
create table hive.default.my_table (
  id bigint,
  data string,
  category string
)
using iceberg
options (
  'write.location-provider.impl'='com.my.CustomLocationProvider'
)
partitioned by (category);
```

## Custom IcebergSource

Расширьте `IcebergSource`, реализовав чтение из `CustomCatalog`:

```java
public class CustomIcebergSource extends IcebergSource {

  @Override
  protected Table findTable(DataSourceOptions options, Configuration conf) {
    Optional<String> path = options.get("path");
    Preconditions.checkArgument(path.isPresent(), "Cannot open table: path is not set");

    CustomCatalog catalog = new CustomCatalog(conf);
    TableIdentifier tableIdentifier = TableIdentifier.parse(path.get());
    return catalog.loadTable(tableIdentifier);
  }
}
```

Для регистрации добавьте fully qualified class name в:

```text
META-INF/services/org.apache.spark.sql.sources.DataSourceRegister
```
