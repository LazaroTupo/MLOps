import os


DB_HOST = os.getenv(
    "DB_HOST",
    "postgres"
)

DB_PORT = int(
    os.getenv(
        "DB_PORT",
        "5432"
    )
)

DB_NAME = os.getenv(
    "DB_NAME",
    "softint"
)

DB_USER = os.getenv(
    "DB_USER",
    "admin"
)

DB_PASSWORD = os.getenv(
    "DB_PASSWORD",
    "adminpassword"
)

DEFAULT_EVENTS_PER_SECOND = int(
    os.getenv(
        "DEFAULT_EVENTS_PER_SECOND",
        "5"
    )
)