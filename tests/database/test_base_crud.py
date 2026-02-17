"""BaseCRUD generic method tests.

Tests all CRUD operations provided by BaseCRUD:
- get_by_id
- get_all (with filters, order_by, limit, offset)
- count (with filters)
- create
- get_or_create (idempotent)
- update_by_id
- delete_by_id
- External session support (transaction composition)
"""
from datetime import date

import pytest

from database.base_crud import BaseCRUD
from database.models import Customer, Employee, ServiceType, Product


class TestGetById:
    """Test BaseCRUD.get_by_id()."""

    def test_get_existing_record(self, temp_db, base_crud):
        customer = base_crud.create(Customer, name="FindMe")
        found = base_crud.get_by_id(Customer, customer.id)
        assert found is not None
        assert found.name == "FindMe"

    def test_get_nonexistent_record(self, temp_db, base_crud):
        result = base_crud.get_by_id(Customer, 99999)
        assert result is None

    def test_get_by_id_with_external_session(self, temp_db, base_crud):
        customer = base_crud.create(Customer, name="SessionTest")
        with temp_db.get_session() as session:
            found = base_crud.get_by_id(Customer, customer.id, session=session)
            assert found is not None
            assert found.name == "SessionTest"


class TestGetAll:
    """Test BaseCRUD.get_all()."""

    def test_get_all_no_filters(self, temp_db, base_crud):
        base_crud.create(Customer, name="A")
        base_crud.create(Customer, name="B")
        results = base_crud.get_all(Customer)
        assert len(results) >= 2

    def test_get_all_with_filters(self, temp_db, base_crud):
        base_crud.create(Employee, name="ActiveEmp", is_active=True)
        base_crud.create(Employee, name="InactiveEmp", is_active=False)
        active = base_crud.get_all(Employee, filters={"is_active": True})
        assert all(e.is_active for e in active)
        assert any(e.name == "ActiveEmp" for e in active)

    def test_get_all_with_order_by_asc(self, temp_db, base_crud):
        base_crud.create(Customer, name="Zebra")
        base_crud.create(Customer, name="Apple")
        results = base_crud.get_all(Customer, order_by="name")
        names = [r.name for r in results]
        assert names == sorted(names)

    def test_get_all_with_order_by_desc(self, temp_db, base_crud):
        base_crud.create(Customer, name="Zebra2")
        base_crud.create(Customer, name="Apple2")
        results = base_crud.get_all(Customer, order_by="-name")
        names = [r.name for r in results]
        assert names == sorted(names, reverse=True)

    def test_get_all_with_limit(self, temp_db, base_crud):
        for i in range(5):
            base_crud.create(Customer, name=f"Limit{i}")
        results = base_crud.get_all(Customer, limit=3)
        assert len(results) == 3

    def test_get_all_with_offset(self, temp_db, base_crud):
        for i in range(5):
            base_crud.create(Customer, name=f"Offset{i}")
        all_results = base_crud.get_all(Customer)
        offset_results = base_crud.get_all(Customer, offset=2)
        assert len(offset_results) == len(all_results) - 2

    def test_get_all_with_limit_and_offset(self, temp_db, base_crud):
        for i in range(10):
            base_crud.create(Customer, name=f"Page{i}")
        page = base_crud.get_all(Customer, limit=3, offset=2)
        assert len(page) == 3

    def test_get_all_filter_nonexistent_field_ignored(self, temp_db, base_crud):
        """Filters with unknown field names should be silently ignored."""
        base_crud.create(Customer, name="FilterTest")
        results = base_crud.get_all(Customer, filters={"nonexistent_field": "value"})
        assert len(results) >= 1

    def test_get_all_with_external_session(self, temp_db, base_crud):
        base_crud.create(Customer, name="SessAll")
        with temp_db.get_session() as session:
            results = base_crud.get_all(Customer, session=session)
            assert len(results) >= 1


class TestCount:
    """Test BaseCRUD.count()."""

    def test_count_all(self, temp_db, base_crud):
        base_crud.create(Customer, name="Count1")
        base_crud.create(Customer, name="Count2")
        assert base_crud.count(Customer) >= 2

    def test_count_with_filters(self, temp_db, base_crud):
        base_crud.create(Employee, name="CountActive", is_active=True)
        base_crud.create(Employee, name="CountInactive", is_active=False)
        active_count = base_crud.count(Employee, filters={"is_active": True})
        assert active_count >= 1

    def test_count_empty_table(self, temp_db, base_crud):
        """Count on an empty (or nearly empty) table should return 0+."""
        count = base_crud.count(ServiceType)
        assert count >= 0


class TestCreate:
    """Test BaseCRUD.create()."""

    def test_create_returns_instance_with_id(self, temp_db, base_crud):
        customer = base_crud.create(Customer, name="NewCust")
        assert customer is not None
        assert customer.id is not None
        assert customer.name == "NewCust"

    def test_create_with_external_session(self, temp_db, base_crud):
        with temp_db.get_session() as session:
            customer = base_crud.create(Customer, name="SessCreate", session=session)
            assert customer.id is not None
            customer_id = customer.id  # capture id before session closes
            session.commit()

        # Verify persisted
        found = base_crud.get_by_id(Customer, customer_id)
        assert found is not None


class TestGetOrCreate:
    """Test BaseCRUD.get_or_create() - idempotent operation."""

    def test_creates_when_not_exists(self, temp_db, base_crud):
        customer = base_crud.get_or_create(
            Customer, lookup={"name": "NewGetOrCreate"}
        )
        assert customer is not None
        assert customer.name == "NewGetOrCreate"

    def test_returns_existing_when_exists(self, temp_db, base_crud):
        c1 = base_crud.get_or_create(
            Customer, lookup={"name": "Idempotent"}
        )
        c2 = base_crud.get_or_create(
            Customer, lookup={"name": "Idempotent"}
        )
        assert c1.id == c2.id

    def test_get_or_create_with_defaults(self, temp_db, base_crud):
        customer = base_crud.get_or_create(
            Customer,
            lookup={"name": "WithDefaults"},
            defaults={"phone": "13800138000", "notes": "from defaults"},
        )
        assert customer.phone == "13800138000"
        assert customer.notes == "from defaults"

    def test_get_or_create_defaults_not_applied_on_existing(self, temp_db, base_crud):
        """Defaults should NOT overwrite existing record's fields."""
        base_crud.create(Customer, name="ExistingDefaults", phone="111")
        customer = base_crud.get_or_create(
            Customer,
            lookup={"name": "ExistingDefaults"},
            defaults={"phone": "999"},
        )
        assert customer.phone == "111"  # original phone kept

    def test_get_or_create_with_external_session(self, temp_db, base_crud):
        with temp_db.get_session() as session:
            c = base_crud.get_or_create(
                Customer,
                lookup={"name": "SessGetOrCreate"},
                session=session,
            )
            assert c.id is not None
            session.commit()


class TestUpdateById:
    """Test BaseCRUD.update_by_id()."""

    def test_update_existing_record(self, temp_db, base_crud):
        customer = base_crud.create(Customer, name="BeforeUpdate")
        updated = base_crud.update_by_id(
            Customer, customer.id, name="AfterUpdate"
        )
        assert updated is not None
        assert updated.name == "AfterUpdate"

    def test_update_nonexistent_record(self, temp_db, base_crud):
        result = base_crud.update_by_id(Customer, 99999, name="NoRecord")
        assert result is None

    def test_update_multiple_fields(self, temp_db, base_crud):
        customer = base_crud.create(Customer, name="MultiField")
        updated = base_crud.update_by_id(
            Customer, customer.id,
            name="Updated", phone="13800000000", notes="Updated notes",
        )
        assert updated.name == "Updated"
        assert updated.phone == "13800000000"
        assert updated.notes == "Updated notes"

    def test_update_with_external_session(self, temp_db, base_crud):
        customer = base_crud.create(Customer, name="SessUpdate")
        with temp_db.get_session() as session:
            updated = base_crud.update_by_id(
                Customer, customer.id,
                session=session, name="SessUpdated",
            )
            assert updated.name == "SessUpdated"
            session.commit()


class TestDeleteById:
    """Test BaseCRUD.delete_by_id()."""

    def test_delete_existing_record(self, temp_db, base_crud):
        customer = base_crud.create(Customer, name="ToDelete")
        result = base_crud.delete_by_id(Customer, customer.id)
        assert result is True

        found = base_crud.get_by_id(Customer, customer.id)
        assert found is None

    def test_delete_nonexistent_record(self, temp_db, base_crud):
        result = base_crud.delete_by_id(Customer, 99999)
        assert result is False

    def test_delete_with_external_session(self, temp_db, base_crud):
        customer = base_crud.create(Customer, name="SessDelete")
        with temp_db.get_session() as session:
            result = base_crud.delete_by_id(Customer, customer.id, session=session)
            assert result is True
            session.commit()

        found = base_crud.get_by_id(Customer, customer.id)
        assert found is None

