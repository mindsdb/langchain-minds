import secrets
import inspect
import json
import sys
from typing import Any, Dict, List, Literal, Optional, Text, Union

from pydantic import BaseModel, Field, SecretStr
from langchain_core.utils import convert_to_secret_str, get_from_dict_or_env


class AIMindDataSource(BaseModel):
    """
    The configuration for data sources used by the AIMindTool.
    """
    name: Optional[Text] = Field(default=None, description="Name of the data source")
    engine: Text = Field(description="Engine (type) of the data source")
    description: Text = Field(description="Description of the data contained in the data source")
    connection_data: Dict[Text, Any] = Field(description="Connection parameters to establish a connection to the data source")
    tables: Optional[List[Text]] = Field(default=[], description="List of tables from the data source to be accessible by the Mind")

    def __init__(self, **data: Any) -> None:
        """
        Initializes the configuration for data sources to be used by the Mind.
        Sets the name if not provided.
        """
        super().__init__(**data)

        # If a name is not provided, generate a random one.
        if not self.name:
            self.name = f"lc_datasource_{secrets.token_hex(5)}"

        # Validate that the engine is supported.
        supported_data_sources = self._get_supported_datasources()
        if self.engine not in supported_data_sources.keys():
            raise ValueError(
                f"Data source engine '{self.engine}' is not supported. "
                f"Supported data source engines are: {supported_data_sources.keys()}."
            )

        # Validate the connection data provided using the respective data source model.
        model_cls = supported_data_sources[self.engine]
        model_obj = model_cls(**self.connection_data)
        self.connection_data = model_obj.dict()

    def _get_supported_datasources(self) -> Dict:
        """
        Returns a dictionary of supported data source engines and their corresponding classes.
        """
        return {
            name.lower().replace("datasource", ""): cls
            for name, cls in inspect.getmembers(sys.modules[__name__], inspect.isclass)
            if issubclass(cls, BaseModel) and cls not in [BaseModel, AIMindDataSource]
        }


class AmazonDynamoDBDataSource(BaseModel):
    """
    The configuration (connection parameters) for an Amazon DynamoDB data source.
    """
    aws_access_key_id: SecretStr = Field(default=None)
    aws_secret_access_key: SecretStr = Field(default=None)
    region_name: Text = Field(default=None)
    aws_session_token: SecretStr = Field(default=None)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.aws_access_key_id = convert_to_secret_str(
            get_from_dict_or_env(
                data,
                "aws_access_key_id",
                "AWS_ACCESS_KEY_ID",
            )
        )
        self.aws_secret_access_key = convert_to_secret_str(
            get_from_dict_or_env(
                data,
                "aws_secret_access_key",
                "AWS_SECRET_ACCESS_KEY",
            )
        )
        self.region_name = get_from_dict_or_env(
            data,
            "region_name",
            "AWS_REGION_NAME",
        )
        self.aws_session_token = (
            convert_to_secret_str(
                get_from_dict_or_env(
                    data,
                    "aws_session_token",
                    "AWS_SESSION_TOKEN",
                    default="",
                ) or None
            )
        )

    def dict(self, **kwargs: Any) -> Dict:
        base_dict = super().dict(**kwargs)

        # Convert the secret access key and session token to a string.
        base_dict["aws_access_key_id"] = base_dict["aws_access_key_id"].get_secret_value()
        base_dict["aws_secret_access_key"] = base_dict["aws_secret_access_key"].get_secret_value()
        if base_dict["aws_session_token"]:
            base_dict["aws_session_token"] = base_dict["aws_session_token"].get_secret_value()

        return base_dict


class PostgresDataSource(BaseModel):
    """
    The configuration (connection parameters) for a PostgreSQL data source.
    """
    user: Text = Field(default=None)
    password: SecretStr = Field(default=None)
    host: Text = Field(default=None)
    port: int = Field(default=5432)
    database: Text = Field(default=None)
    database_schema: Text = Field(alias="schema", default=None)
    sslmode: Text = Field(default=None)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.user = get_from_dict_or_env(
            data,
            "user",
            "POSTGRES_USER",
        )
        self.password = convert_to_secret_str(
            get_from_dict_or_env(
                data,
                "password",
                "POSTGRES_PASSWORD",
            )
        )
        self.host = get_from_dict_or_env(
            data,
            "host",
            "POSTGRES_HOST",
        )
        self.port = get_from_dict_or_env(
            data,
            "port",
            "POSTGRES_PORT",
            default=5432,
        )
        self.database = get_from_dict_or_env(
            data,
            "database",
            "POSTGRES_DATABASE",
        )
        self.database_schema = (
            get_from_dict_or_env(
                data,
                "schema",
                "POSTGRES_SCHEMA",
                default="",
            )
            or None
        )
        self.sslmode = (
            get_from_dict_or_env(
                data,
                "sslmode",
                "POSTGRES_SSLMODE",
                default="",
            )
            or None
        )

    def dict(self, **kwargs: Any) -> Dict:
        base_dict = super().dict(**kwargs, exclude_none=True)

        # Convert the secret password to a string.
        base_dict["password"] = base_dict["password"].get_secret_value()

        # Convert database_schema to schema and remove database_schema.
        if "database_schema" in base_dict:
            base_dict["schema"] = base_dict["database_schema"]
            del base_dict["database_schema"]

        return base_dict


class AmazonRedshiftDataSource(PostgresDataSource):
    """
    The configuration (connection parameters) for an Amazon Redshift data source.
    """
    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.user = get_from_dict_or_env(
            data,
            "user",
            "REDSHIFT_USER",
        )
        self.password = convert_to_secret_str(
            get_from_dict_or_env(
                data,
                "password",
                "REDSHIFT_PASSWORD",
            )
        )
        self.host = get_from_dict_or_env(
            data,
            "host",
            "REDSHIFT_HOST",
        )
        self.port = get_from_dict_or_env(
            data,
            "port",
            "REDSHIFT_PORT",
            default=5439,
        )
        self.database = get_from_dict_or_env(
            data,
            "database",
            "REDSHIFT_DATABASE",
        )
        self.database_schema = (
            get_from_dict_or_env(
                data,
                "schema",
                "REDSHIFT_SCHEMA",
                default="",
            )
            or None
        )
        self.sslmode = (
            get_from_dict_or_env(
                data,
                "sslmode",
                "REDSHIFT_SSLMODE",
                default="",
            )
            or None
        )


class AmazonS3DataSource(BaseModel):
    """
    The configuration (connection parameters) for an Amazon S3 data source.
    """
    aws_access_key_id: SecretStr = Field(default=None)
    aws_secret_access_key: SecretStr = Field(default=None)
    bucket: Text = Field(default=None)
    aws_session_token: SecretStr = Field(default=None)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.aws_access_key_id = convert_to_secret_str(
            get_from_dict_or_env(
                data,
                "aws_access_key_id",
                "AWS_ACCESS_KEY_ID",
            )
        )
        self.aws_secret_access_key = convert_to_secret_str(
            get_from_dict_or_env(
                data,
                "aws_secret_access_key",
                "AWS_SECRET_ACCESS_KEY",
            )
        )
        self.bucket = (
            get_from_dict_or_env(
                data,
                "bucket",
                "AWS_S3_BUCKET",
                default="",
            ) or None
        )
        self.aws_session_token = (
            convert_to_secret_str(
                get_from_dict_or_env(
                    data,
                    "aws_session_token",
                    "AWS_SESSION_TOKEN",
                    default="",
                ) or None
            )
        )

    def dict(self, **kwargs: Any) -> Dict:
        base_dict = super().dict(**kwargs)

        # Convert the secret access key and session token to a string.
        base_dict["aws_access_key_id"] = base_dict["aws_access_key_id"].get_secret_value()
        base_dict["aws_secret_access_key"] = base_dict["aws_secret_access_key"].get_secret_value()
        if base_dict["aws_session_token"]:
            base_dict["aws_session_token"] = base_dict["aws_session_token"].get_secret_value()

        return base_dict
    

class DatabricksDataSource(BaseModel):
    """
    The configuration (connection parameters) for a Databricks data source.
    """
    server_hostname: Text = Field(default=None)
    http_path: Text = Field(default=None)
    access_token: SecretStr = Field(default=None)
    session_confirguration: Dict[Text, Any] = Field(default=None)
    http_headers: Dict[Text, Any] = Field(default=None)
    catalog: Text = Field(default=None)
    schema: Text = Field(default=None)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.server_hostname = get_from_dict_or_env(
            data,
            "server_hostname",
            "DATABRICKS_SERVER_HOSTNAME",
        )
        self.http_path = get_from_dict_or_env(
            data,
            "http_path",
            "DATABRICKS_HTTP_PATH",
        )
        self.access_token = convert_to_secret_str(
            get_from_dict_or_env(
                data,
                "access_token",
                "DATABRICKS_ACCESS_TOKEN",
            )
        )
        self.session_confirguration = (
            get_from_dict_or_env(
                data,
                "session_confirguration",
                "DATABRICKS_SESSION_CONFIGURATION",
                default={},
            ) or None
        )
        self.http_headers = (
            get_from_dict_or_env(
                data,
                "http_headers",
                "DATABRICKS_HTTP_HEADERS",
                default={},
            ) or None
        )
        self.catalog = (
            get_from_dict_or_env(
                data,
                "catalog",
                "DATABRICKS_CATALOG",
                default="",
            ) or None
        )
        self.schema = (
            get_from_dict_or_env(
                data,
                "schema",
                "DATABRICKS_SCHEMA",
                default="",
            )
            or None
        )


class ElasticsearchDataSource(BaseModel):
    """
    The configuration (connection parameters) for an Elasticsearch data source.
    """
    cloud_id: Text = Field(default=None)
    hosts: Text = Field(default=None)
    api_key: SecretStr = Field(default=None)
    user: Text = Field(default=None)
    password: SecretStr = Field(default=None)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.cloud_id = (
            get_from_dict_or_env(
                data,
                "cloud_id",
                "ELASTICSEARCH_CLOUD_ID",
                default="",
            ) or None
        )
        self.hosts = (
            get_from_dict_or_env(
                data,
                "hosts",
                "ELASTICSEARCH_HOSTS",
                default="",
            ) or None
        )
        self.api_key = (
            get_from_dict_or_env(
                data,
                "api_key",
                "ELASTICSEARCH_API_KEY",
                default="",
            ) or None
        )
        if self.api_key:
            self.api_key = convert_to_secret_str(self.api_key)
        self.user = (
            get_from_dict_or_env(
                data,
                "user",
                "ELASTICSEARCH_USER",
                default="",
            ) or None
        )
        self.password = (
            get_from_dict_or_env(
                data,
                "password",
                "ELASTICSEARCH_PASSWORD",
                default="",
            ) or None
        )
        if self.password:
            self.password = convert_to_secret_str(self.password)

        if not self.cloud_id and not self.hosts:
            raise ValueError(
                "Either a valid cloud_id or hosts must be provided."
            )
        
        if self.api_key and not (self.user and self.password):
            raise ValueError(
                "Either a valid api_key or user and password must be provided."
            )


class MySQLDataSource(BaseModel):
    """
    The configuration (connection parameters) for a MySQL data source
    """
    user: Text = Field(default=None)
    password: SecretStr = Field(default=None)
    host: Text = Field(default=None)
    port: int = Field(default=3306)
    database: Text = Field(default=None)
    url: Text = Field(default=None)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.user = (
            get_from_dict_or_env(
                data,
                "user",
                "MYSQL_USER",
                default="",
            )
            or None
        )
        self.password = (
            convert_to_secret_str(
                get_from_dict_or_env(
                    data,
                    "password",
                    "MYSQL_PASSWORD",
                    default="",
                )
            )
            or None
        )
        self.host = (
            get_from_dict_or_env(
                data,
                "host",
                "MYSQL_HOST",
                default="",
            )
            or None
        )
        self.port = get_from_dict_or_env(
            data,
            "port",
            "MYSQL_PORT",
            default=3306,
        )
        self.database = (
            get_from_dict_or_env(
                data,
                "database",
                "MYSQL_DATABASE",
                default="",
            )
            or None
        )
        self.url = (
            get_from_dict_or_env(
                data,
                "url",
                "MYSQL_URL",
                default="",
            )
            or None
        )

        if not self.url and not (
            self.host and self.user and self.password and self.database
        ):
            raise ValueError(
                "Either a valid URL or required parameters (host, user, password, "
                "database) must be provided."
            )

    def dict(self, **kwargs: Any) -> Dict:
        base_dict = super().dict(**kwargs, exclude_none=True)

        # Convert the secret password to a string.
        base_dict["password"] = base_dict["password"].get_secret_value()
        return base_dict


class MariaDBDataSource(MySQLDataSource):
    """
    The configuration (connection parameters) for a MariaDB data source.
    """
    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.user = (
            get_from_dict_or_env(
                data,
                "user",
                "MARIADB_USER",
                default="",
            )
            or None
        )
        self.password = convert_to_secret_str(
            get_from_dict_or_env(
                data,
                "password",
                "MARIADB_PASSWORD",
                default="",
            )
            or None
        )
        self.host = (
            get_from_dict_or_env(
                data,
                "host",
                "MARIADB_HOST",
                default="",
            )
            or None
        )
        self.port = get_from_dict_or_env(
            data,
            "port",
            "MARIADB_PORT",
            default=3306,
        )
        self.database = (
            get_from_dict_or_env(
                data,
                "database",
                "MARIADB_DATABASE",
                default="",
            )
            or None
        )
        self.url = (
            get_from_dict_or_env(
                data,
                "url",
                "MARIADB_URL",
                default="",
            )
            or None
        )


class ClickHouseDataSource(BaseModel):
    """
    The configuration (connection parameters) for a ClickHouse data source.
    """
    user: Text = Field(default=None)
    password: SecretStr = Field(default=None)
    host: Text = Field(default=None)
    port: int = Field(default=8443)
    database: Text = Field(default=None)
    protocol: Literal["native", "http", "https"] = Field(default="native")

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.user = get_from_dict_or_env(
            data,
            "user",
            "CLICKHOUSE_USER",
        )
        self.password = convert_to_secret_str(
            get_from_dict_or_env(
                data,
                "password",
                "CLICKHOUSE_PASSWORD",
            )
        )
        self.host = get_from_dict_or_env(
            data,
            "host",
            "CLICKHOUSE_HOST",
        )
        self.port = get_from_dict_or_env(
            data,
            "port",
            "CLICKHOUSE_PORT",
            default=8443,
        )
        self.database = get_from_dict_or_env(
            data,
            "database",
            "CLICKHOUSE_DATABASE",
        )
        self.protocol = get_from_dict_or_env(
            data,
            "protocol",
            "CLICKHOUSE_PROTOCOL",
            default="native",
        )

    def dict(self, **kwargs: Any) -> Dict:
        base_dict = super().dict(**kwargs)

        # Convert the secret password to a string.
        base_dict["password"] = base_dict["password"].get_secret_value()
        return base_dict


class SnowflakeDataSource(BaseModel):
    """
    The configuration (connection parameters) for a Snowflake data source.
    """
    account: Text = Field(default=None)
    user: Text = Field(default=None)
    password: SecretStr = Field(default=None)
    warehouse: Text = Field(default=None)
    database: Text = Field(default=None)
    database_schema: Text = Field(alias="schema", default=None)
    role: Text = Field(default=None)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.account = get_from_dict_or_env(
            data,
            "account",
            "SNOWFLAKE_ACCOUNT",
        )
        self.user = get_from_dict_or_env(
            data,
            "user",
            "SNOWFLAKE_USER",
        )
        self.password = convert_to_secret_str(
            get_from_dict_or_env(
                data,
                "password",
                "SNOWFLAKE_PASSWORD",
            )
        )
        self.warehouse = (
            get_from_dict_or_env(
                data,
                "warehouse",
                "SNOWFLAKE_WAREHOUSE",
                default="",
            )
            or None
        )
        self.database = get_from_dict_or_env(
            data,
            "database",
            "SNOWFLAKE_DATABASE",
        )
        self.database_schema = (
            get_from_dict_or_env(
                data,
                "schema",
                "SNOWFLAKE_SCHEMA",
                default="",
            )
            or None
        )
        self.role = (
            get_from_dict_or_env(
                data,
                "role",
                "SNOWFLAKE_ROLE",
                default="",
            )
            or None
        )

    def dict(self, **kwargs: Any) -> Dict:
        base_dict = super().dict(**kwargs, exclude_none=True)

        # Convert the secret password to a string.
        base_dict["password"] = base_dict["password"].get_secret_value()

        # Convert database_schema to schema and remove database_schema.
        if "database_schema" in base_dict:
            base_dict["schema"] = base_dict["database_schema"]
            del base_dict["database_schema"]

        return base_dict


class BigQueryDataSource(BaseModel):
    """
    The configuration (connection parameters) for a BigQuery data source.
    """
    project_id: Text = Field(default=None)
    dataset: Text = Field(default=None)
    service_account_json: Union[SecretStr, Dict] = Field(default=None)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.project_id = get_from_dict_or_env(
            data,
            "project_id",
            "BIGQUERY_PROJECT_ID",
        )
        self.dataset = get_from_dict_or_env(
            data,
            "dataset",
            "BIGQUERY_DATASET",
        )
        service_account_json = get_from_dict_or_env(
            data,
            "service_account_json",
            "BIGQUERY_SERVICE_ACCOUNT_JSON",
        )
        if isinstance(service_account_json, Dict):
            service_account_json = json.dumps(service_account_json)

        self.service_account_json = convert_to_secret_str(service_account_json)

    def dict(self, **kwargs: Any) -> Dict:
        base_dict = super().dict(**kwargs)

        # Convert the secret service account json to a dict.
        base_dict["service_account_json"] = json.loads(
            base_dict["service_account_json"].get_secret_value()
        )
        return base_dict


class TeradataDataSource(BaseModel):
    """
    The configuration (connection parameters) for a Teradata data source.
    """
    host: Text = Field(default=None)
    user: Text = Field(default=None)
    password: SecretStr = Field(default=None)
    database: Text = Field(default=None)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.host = get_from_dict_or_env(
            data,
            "host",
            "TERADATA_HOST",
        )
        self.user = get_from_dict_or_env(
            data,
            "user",
            "TERADATA_USER",
        )
        self.password = convert_to_secret_str(
            get_from_dict_or_env(
                data,
                "password",
                "TERADATA_PASSWORD",
            )
        )
        self.database = (
            get_from_dict_or_env(
                data,
                "database",
                "TERADATA_DATABASE",
            )
            or None
        )