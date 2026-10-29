import os


class Settings:
    PARSER_MODEL: str = os.getenv("PARSER_MODEL", "anthropic.claude-opus-5-5")
    COGNITO_USER_POOL_ID: str = os.getenv("COGNITO_USER_POOL_ID", "eu-north-1_VArufRzST")
    COGNITO_CLIENT_ID: str = os.getenv("COGNITO_CLIENT_ID", "40q78hb988egmd17hs07hci1vh")
    COGNITO_REGION: str = os.getenv("COGNITO_REGION", "eu-north-1")
    MOCK_AI: bool = os.getenv("MOCK_AI", "false").lower() in ("true", "1", "yes")


settings = Settings()
