import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./calculator.db")
BUILD_VERSION = os.getenv("BUILD_VERSION", "1.0.0-dev")
COMMIT_SHA = os.getenv("COMMIT_SHA", "local")
ENVIRONMENT = os.getenv("APP_ENV", "development")
HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "100"))
AI_PROVIDER = os.getenv("AI_PROVIDER", "rules")
