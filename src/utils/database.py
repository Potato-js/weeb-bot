import psycopg
from dotenv import load_dotenv
from os import getenv
from contextlib import contextmanager
from src.utils.logger import setup_logger

logger = setup_logger()
load_dotenv()

# Database configuration
DB_CONFIG = {
    "dbname": getenv("DB_NAME"),
    "user": getenv("DB_USER"),
    "password": getenv("DB_PASSWORD"),
    "host": getenv("DB_HOST"),
    "port": getenv("DB_PORT"),
}


class DatabaseUtils:
    """Universal PostgreSQL database utility class."""

    @staticmethod
    def get_connection():
        """
        Get a new database connection.
        Returns a psycopg connection object.
        """
        try:
            return psycopg.connect(**DB_CONFIG)
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    @staticmethod
    @contextmanager
    def get_connection_context():
        """
        Context manager for database connections.
        Automatically handles connection closing and error handling.

        Usage:
            with DatabaseUtils.get_connection_context() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
                result = cursor.fetchall()
        """
        conn = None
        try:
            conn = DatabaseUtils.get_connection()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                conn.close()

    @staticmethod
    @contextmanager
    def get_cursor_context():
        """
        Context manager for database cursor operations.
        Automatically handles connection, cursor, commit, and cleanup.

        Usage:
            with DatabaseUtils.get_cursor_context() as cursor:
                cursor.execute("SELECT * FROM table")
                result = cursor.fetchall()
        """
        conn = None
        cursor = None
        try:
            conn = DatabaseUtils.get_connection()
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database cursor operation failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def execute_query(query, params=None, fetch=None):
        """
        Execute a query with automatic connection management.

        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            fetch (str, optional): 'one', 'all', or None for fetchone(), fetchall(), or no fetch

        Returns:
            Query result if fetch is specified, None otherwise
        """
        with DatabaseUtils.get_cursor_context() as cursor:
            cursor.execute(query, params)

            if fetch == "one":
                return cursor.fetchone()
            elif fetch == "all":
                return cursor.fetchall()
            return None

    @staticmethod
    def setup_tables():
        """
        Set up all required database tables.
        This can be called during bot initialization.
        """
        tables = [
            # Games table (if needed)
            """
            CREATE TABLE IF NOT EXISTS games (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                game_type VARCHAR(50) NOT NULL,
                score INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # Role permissions table
            """
            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id BIGINT PRIMARY KEY,
                permissions INTEGER NOT NULL
            )
            """,
            # Economy/Bank table
            """
            CREATE TABLE IF NOT EXISTS bank (
                user_id BIGINT PRIMARY KEY,
                wallet BIGINT DEFAULT 0,
                bank BIGINT DEFAULT 100,
                maxbank BIGINT DEFAULT 25000
            )
            """,
        ]

        try:
            with DatabaseUtils.get_cursor_context() as cursor:
                for table_sql in tables:
                    cursor.execute(table_sql)
            logger.info("Database tables setup completed successfully")
        except Exception as e:
            logger.error(f"Failed to setup database tables: {e}")
            raise
