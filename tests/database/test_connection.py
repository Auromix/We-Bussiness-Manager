"""DatabaseConnection infrastructure tests.

Tests for:
- Engine creation (SQLite sync)
- Table creation (idempotent)
- Session management
- Raw SQL execution
- Database URL handling
"""
import os
import tempfile
import shutil

from sqlalchemy import inspect, text

from database import DatabaseManager, DatabaseConnection


# ============================================================
# Expected tables based on models.py
# ============================================================
EXPECTED_TABLES = {
    "employees",
    "customers",
    "memberships",
    "service_types",
    "referral_channels",
    "service_records",
    "products",
    "product_sales",
    "inventory_logs",
    "raw_messages",
    "corrections",
    "daily_summaries",
    "plugin_data",
}


class TestDatabaseConnectionInit:
    """Test DatabaseConnection initialization."""

    def test_sqlite_creates_sync_engine(self, temp_db):
        """SQLite URL should produce a synchronous engine."""
        assert temp_db.is_async is False

    def test_database_url_is_stored(self, temp_db):
        """database_url property should return the configured URL."""
        assert temp_db.database_url.startswith("sqlite:///")

    def test_engine_is_accessible(self, temp_db):
        """engine property should be accessible."""
        assert temp_db.engine is not None

    def test_custom_sqlite_url(self, tmp_path):
        """Custom SQLite URL should be used as-is."""
        url = f"sqlite:///{tmp_path}/custom.db"
        db = DatabaseManager(url)
        assert db.database_url == url
        assert db.is_async is False


class TestTableCreation:
    """Test table creation via create_tables()."""

    def test_create_tables_creates_all_expected_tables(self, temp_db):
        """All 13 tables from models.py should exist."""
        inspector = inspect(temp_db.engine)
        table_names = set(inspector.get_table_names())
        assert EXPECTED_TABLES.issubset(table_names), (
            f"Missing tables: {EXPECTED_TABLES - table_names}"
        )

    def test_create_tables_is_idempotent(self, temp_db):
        """Calling create_tables() twice should not error."""
        temp_db.create_tables()  # second call
        inspector = inspect(temp_db.engine)
        table_names = set(inspector.get_table_names())
        assert EXPECTED_TABLES.issubset(table_names)


class TestSessionManagement:
    """Test get_session() and session lifecycle."""

    def test_get_session_returns_usable_session(self, temp_db):
        """Session should be able to execute simple queries."""
        with temp_db.get_session() as session:
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_session_context_manager_closes(self, temp_db):
        """Session should be closed after context manager exits."""
        session = temp_db.get_session()
        with session:
            session.execute(text("SELECT 1"))
        # After exit, session is closed — no error expected


class TestRawSQL:
    """Test execute_raw_sql()."""

    def test_execute_raw_sql_select(self, temp_db):
        """Raw SQL SELECT should return results."""
        result = temp_db.execute_raw_sql("SELECT 1 AS val")
        assert result.scalar() == 1

    def test_execute_raw_sql_with_params(self, temp_db):
        """Raw SQL with parameters should work."""
        temp_db.customers.get_or_create("ParamUser")
        result = temp_db.execute_raw_sql(
            "SELECT COUNT(*) FROM customers WHERE name = :name",
            {"name": "ParamUser"},
        )
        assert result.scalar() == 1

    def test_execute_raw_sql_insert_and_read(self, temp_db):
        """Raw SQL INSERT + SELECT should work end-to-end."""
        temp_db.execute_raw_sql(
            "INSERT INTO customers (name) VALUES (:name)",
            {"name": "RawInsert"},
        )
        result = temp_db.execute_raw_sql(
            "SELECT name FROM customers WHERE name = :name",
            {"name": "RawInsert"},
        )
        assert result.scalar() == "RawInsert"


class TestDatabaseIsolation:
    """Test that separate DatabaseManagers use separate databases."""

    def test_separate_managers_use_separate_databases(self, tmp_path):
        """Two managers pointing to different files should be isolated."""
        db1 = DatabaseManager(f"sqlite:///{tmp_path}/a.db")
        db2 = DatabaseManager(f"sqlite:///{tmp_path}/b.db")
        db1.create_tables()
        db2.create_tables()

        db1.customers.get_or_create("Alice")
        db2.customers.get_or_create("Bob")

        with db1.get_session() as s1:
            names1 = [
                row[0]
                for row in s1.execute(
                    text("SELECT name FROM customers")
                ).fetchall()
            ]
        with db2.get_session() as s2:
            names2 = [
                row[0]
                for row in s2.execute(
                    text("SELECT name FROM customers")
                ).fetchall()
            ]

        assert names1 == ["Alice"]
        assert names2 == ["Bob"]

