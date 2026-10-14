from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    falkordb_host: str = "localhost"
    falkordb_port: int = 6379
    embedding_dim: int = 768
    github_token: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""
    default_tenant_graph: str = "repo_falkordb_py"

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")


settings = Settings()
