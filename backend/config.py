"""Backend configuration, loaded from the environment (see .env.example)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # AWS KMS — the operator's master key. Only its key id is needed here;
    # boto3 picks up AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_SESSION_TOKEN
    # from the environment automatically.
    aws_region: str
    kms_key_id: str

    # Postgres
    database_url: str

    # Google Gemini (the agents' LLM)
    google_api_key: str

    # Where the agent (MCP client) reaches the MCP server.
    mcp_server_url: str = "http://localhost:8001/mcp"


settings = Settings()
