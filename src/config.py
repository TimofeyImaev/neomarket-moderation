import os

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://neomarket:neomarket@db:5432/moderation")

# Входящие запросы от B2B (события)
B2B_TO_MOD_KEY = os.getenv("B2B_TO_MOD_KEY", "")

# Исходящие запросы в B2B
B2B_URL = os.getenv("B2B_URL", "")
MOD_TO_B2B_KEY = os.getenv("MOD_TO_B2B_KEY", "")
