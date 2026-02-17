"""Business repository tests.

Tests for:
- ServiceRecordRepository: save, get_by_date, confirm, auto-entity creation
- ProductSaleRepository: save, get_by_date, auto-entity creation
- MembershipRepository: save, get_active_by_customer,
  deduct_balance, deduct_session, add_points
"""
from datetime import date, datetime

import pytest

from database.models import (
    ServiceRecord, ProductSale, Membership, Customer,
    Employee, ServiceType, ReferralChannel,
)
from tests.database.conftest import make_raw_message


# ============================================================
# ServiceRecordRepository Tests
# ============================================================
class TestServiceRecordRepository:
    """Tests for ServiceRecordRepository."""

    def test_save_basic_record(self, temp_db):
        msg_id = make_raw_message(temp_db, "sr-basic")
        record_id = temp_db.service_records.save(
            {
                "customer_name": "张三",
                "service_or_product": "头疗",
                "date": "2024-01-28",
                "amount": 198,
            },
            msg_id,
        )
        assert record_id > 0

    def test_save_auto_creates_customer(self, temp_db):
        """save() should auto-create customer if not exists."""
        msg_id = make_raw_message(temp_db, "sr-auto-cust")
        temp_db.service_records.save(
            {
                "customer_name": "NewAutoCustomer",
                "service_or_product": "理疗",
                "date": "2024-01-28",
                "amount": 100,
            },
            msg_id,
        )
        cust = temp_db.customers.search("NewAutoCustomer")
        assert len(cust) == 1

    def test_save_auto_creates_service_type(self, temp_db):
        """save() should auto-create service type if not exists."""
        msg_id = make_raw_message(temp_db, "sr-auto-st")
        temp_db.service_records.save(
            {
                "customer_name": "Cust",
                "service_or_product": "新服务类型",
                "date": "2024-01-28",
                "amount": 50,
            },
            msg_id,
        )
        st = temp_db.service_types.get_by_category(None)  # all without category
        # Use get_all to check
        all_st = temp_db.service_types.get_all(ServiceType)
        assert any(s.name == "新服务类型" for s in all_st)

    def test_save_auto_creates_recorder(self, temp_db):
        """save() should auto-create recorder employee."""
        msg_id = make_raw_message(temp_db, "sr-auto-rec")
        temp_db.service_records.save(
            {
                "customer_name": "Cust",
                "service_or_product": "Therapy",
                "date": "2024-01-28",
                "amount": 100,
                "recorder_nickname": "RecorderNick",
            },
            msg_id,
        )
        found = temp_db.staff.search("RecorderNick")
        assert len(found) >= 1

    def test_save_with_commission(self, temp_db):
        msg_id = make_raw_message(temp_db, "sr-comm")
        record_id = temp_db.service_records.save(
            {
                "customer_name": "Alice",
                "service_or_product": "头疗",
                "date": "2024-01-28",
                "amount": 198,
                "commission": 20,
                "commission_to": "李哥",
                "net_amount": 178,
            },
            msg_id,
        )

        with temp_db.get_session() as session:
            record = session.query(ServiceRecord).filter_by(id=record_id).first()
            assert float(record.commission_amount) == 20
            assert record.commission_to == "李哥"
            assert float(record.net_amount) == 178

    def test_save_commission_to_creates_channel(self, temp_db):
        """commission_to should auto-create a referral channel."""
        msg_id = make_raw_message(temp_db, "sr-ch-auto")
        temp_db.service_records.save(
            {
                "customer_name": "Cust",
                "service_or_product": "Therapy",
                "date": "2024-01-28",
                "amount": 100,
                "commission": 10,
                "commission_to": "AutoChannel",
            },
            msg_id,
        )
        channels = temp_db.channels.get_active_channels("external")
        assert any(c.name == "AutoChannel" for c in channels)

    def test_save_with_referral_channel_id(self, temp_db):
        """Explicit referral_channel_id should be used."""
        ch = temp_db.channels.get_or_create("美团", "platform", commission_rate=15)
        msg_id = make_raw_message(temp_db, "sr-ch-id")
        record_id = temp_db.service_records.save(
            {
                "customer_name": "Cust",
                "service_or_product": "Therapy",
                "date": "2024-01-28",
                "amount": 100,
                "referral_channel_id": ch.id,
            },
            msg_id,
        )

        with temp_db.get_session() as session:
            record = session.query(ServiceRecord).filter_by(id=record_id).first()
            assert record.referral_channel_id == ch.id

    def test_save_with_membership_id(self, temp_db):
        msg_id1 = make_raw_message(temp_db, "sr-mem-setup")
        mid = temp_db.memberships.save(
            {"customer_name": "MemCust", "date": "2024-01-01", "amount": 1000},
            msg_id1,
        )

        msg_id2 = make_raw_message(temp_db, "sr-mem-use")
        record_id = temp_db.service_records.save(
            {
                "customer_name": "MemCust",
                "service_or_product": "Therapy",
                "date": "2024-01-28",
                "amount": 100,
                "membership_id": mid,
            },
            msg_id2,
        )

        with temp_db.get_session() as session:
            record = session.query(ServiceRecord).filter_by(id=record_id).first()
            assert record.membership_id == mid

    def test_save_with_extra_data(self, temp_db):
        msg_id = make_raw_message(temp_db, "sr-extra")
        record_id = temp_db.service_records.save(
            {
                "customer_name": "Cust",
                "service_or_product": "Therapy",
                "date": "2024-01-28",
                "amount": 100,
                "extra_data": {"duration": 60, "room": "VIP1"},
            },
            msg_id,
        )
        with temp_db.get_session() as session:
            record = session.query(ServiceRecord).filter_by(id=record_id).first()
            assert record.extra_data["duration"] == 60

    def test_save_with_date_object(self, temp_db):
        """date parameter can be a date object instead of string."""
        msg_id = make_raw_message(temp_db, "sr-date-obj")
        record_id = temp_db.service_records.save(
            {
                "customer_name": "Cust",
                "service_or_product": "Therapy",
                "date": date(2024, 1, 28),
                "amount": 100,
            },
            msg_id,
        )
        assert record_id > 0

    def test_save_invalid_date_raises(self, temp_db):
        msg_id = make_raw_message(temp_db, "sr-bad-date")
        with pytest.raises(ValueError, match="Invalid date format"):
            temp_db.service_records.save(
                {
                    "customer_name": "Cust",
                    "service_or_product": "Therapy",
                    "date": "2024/01/28",
                    "amount": 100,
                },
                msg_id,
            )

    def test_save_missing_date_raises(self, temp_db):
        msg_id = make_raw_message(temp_db, "sr-no-date")
        with pytest.raises(ValueError, match="Service date is required"):
            temp_db.service_records.save(
                {
                    "customer_name": "Cust",
                    "service_or_product": "Therapy",
                    "amount": 100,
                },
                msg_id,
            )

    def test_save_zero_amount(self, temp_db):
        """Zero amount should be accepted (e.g. free trial)."""
        msg_id = make_raw_message(temp_db, "sr-zero")
        record_id = temp_db.service_records.save(
            {
                "customer_name": "FreeTrial",
                "service_or_product": "Trial",
                "date": "2024-01-28",
                "amount": 0,
            },
            msg_id,
        )
        assert record_id > 0

    def test_save_negative_amount(self, temp_db):
        """Negative amount should be accepted (e.g. refund)."""
        msg_id = make_raw_message(temp_db, "sr-negative")
        record_id = temp_db.service_records.save(
            {
                "customer_name": "Refund",
                "service_or_product": "Refund",
                "date": "2024-01-28",
                "amount": -50,
            },
            msg_id,
        )
        assert record_id > 0

    def test_save_default_confidence(self, temp_db):
        msg_id = make_raw_message(temp_db, "sr-conf")
        record_id = temp_db.service_records.save(
            {
                "customer_name": "Cust",
                "service_or_product": "Therapy",
                "date": "2024-01-28",
                "amount": 100,
            },
            msg_id,
        )
        with temp_db.get_session() as session:
            record = session.query(ServiceRecord).filter_by(id=record_id).first()
            assert float(record.parse_confidence) == 0.5

    def test_get_by_date(self, temp_db):
        msg_id = make_raw_message(temp_db, "sr-bydate")
        temp_db.service_records.save(
            {
                "customer_name": "Alice",
                "service_or_product": "Haircut",
                "date": "2024-01-28",
                "amount": 80,
            },
            msg_id,
        )
        records = temp_db.service_records.get_by_date(date(2024, 1, 28))
        assert len(records) >= 1
        assert records[0]["type"] == "service"
        assert records[0]["customer_name"] == "Alice"
        assert records[0]["service_type"] == "Haircut"
        assert records[0]["amount"] == 80.0

    def test_get_by_date_empty(self, temp_db):
        records = temp_db.service_records.get_by_date(date(2099, 1, 1))
        assert records == []

    def test_get_by_date_returns_dict_format(self, temp_db):
        """Verify all expected keys are present in returned dicts."""
        msg_id = make_raw_message(temp_db, "sr-dict-fmt")
        temp_db.service_records.save(
            {
                "customer_name": "DictTest",
                "service_or_product": "Service",
                "date": "2024-01-28",
                "amount": 100,
                "commission": 10,
                "commission_to": "Ref",
            },
            msg_id,
        )
        records = temp_db.service_records.get_by_date(date(2024, 1, 28))
        r = records[0]
        expected_keys = {
            "type", "id", "customer_name", "service_type",
            "amount", "commission", "commission_to",
            "net_amount", "confirmed",
        }
        assert expected_keys.issubset(set(r.keys()))

    def test_confirm_record(self, temp_db):
        msg_id = make_raw_message(temp_db, "sr-confirm")
        record_id = temp_db.service_records.save(
            {
                "customer_name": "Cust",
                "service_or_product": "Therapy",
                "date": "2024-01-28",
                "amount": 100,
            },
            msg_id,
        )
        result = temp_db.service_records.confirm(record_id)
        assert result is True

        with temp_db.get_session() as session:
            record = session.query(ServiceRecord).filter_by(id=record_id).first()
            assert record.confirmed is True
            assert record.confirmed_at is not None

    def test_confirm_nonexistent_returns_false(self, temp_db):
        result = temp_db.service_records.confirm(99999)
        assert result is False


# ============================================================
# ProductSaleRepository Tests
# ============================================================
class TestProductSaleRepository:
    """Tests for ProductSaleRepository."""

    def test_save_basic_sale(self, temp_db):
        msg_id = make_raw_message(temp_db, "ps-basic")
        sale_id = temp_db.product_sales.save(
            {
                "service_or_product": "蛋白粉",
                "date": "2024-01-28",
                "amount": 200,
                "quantity": 1,
            },
            msg_id,
        )
        assert sale_id > 0

    def test_save_auto_creates_product(self, temp_db):
        msg_id = make_raw_message(temp_db, "ps-auto-prod")
        temp_db.product_sales.save(
            {
                "service_or_product": "NewAutoProduct",
                "date": "2024-01-28",
                "amount": 50,
            },
            msg_id,
        )
        from database.models import Product
        all_products = temp_db.products.get_all(Product)
        assert any(p.name == "NewAutoProduct" for p in all_products)

    def test_save_auto_creates_customer(self, temp_db):
        msg_id = make_raw_message(temp_db, "ps-auto-cust")
        temp_db.product_sales.save(
            {
                "service_or_product": "Product1",
                "date": "2024-01-28",
                "amount": 50,
                "customer_name": "SaleCustomer",
            },
            msg_id,
        )
        cust = temp_db.customers.search("SaleCustomer")
        assert len(cust) == 1

    def test_save_auto_creates_recorder(self, temp_db):
        msg_id = make_raw_message(temp_db, "ps-auto-rec")
        temp_db.product_sales.save(
            {
                "service_or_product": "Product1",
                "date": "2024-01-28",
                "amount": 50,
                "recorder_nickname": "SaleRecorder",
            },
            msg_id,
        )
        found = temp_db.staff.search("SaleRecorder")
        assert len(found) >= 1

    def test_save_without_customer(self, temp_db):
        """Sale without customer_name should still work."""
        msg_id = make_raw_message(temp_db, "ps-no-cust")
        sale_id = temp_db.product_sales.save(
            {
                "service_or_product": "WalkIn",
                "date": "2024-01-28",
                "amount": 30,
            },
            msg_id,
        )
        assert sale_id > 0

    def test_save_with_all_fields(self, temp_db):
        msg_id = make_raw_message(temp_db, "ps-all")
        sale_id = temp_db.product_sales.save(
            {
                "service_or_product": "洗发水",
                "date": "2024-01-28",
                "amount": 136,
                "quantity": 2,
                "unit_price": 68,
                "category": "retail",
                "customer_name": "FullCust",
                "recorder_nickname": "FullRec",
                "notes": "Two bottles",
                "confidence": 0.9,
                "confirmed": True,
            },
            msg_id,
        )

        with temp_db.get_session() as session:
            sale = session.query(ProductSale).filter_by(id=sale_id).first()
            assert sale.quantity == 2
            assert sale.notes == "Two bottles"
            assert sale.confirmed is True

    def test_get_by_date(self, temp_db):
        msg_id = make_raw_message(temp_db, "ps-bydate")
        temp_db.product_sales.save(
            {
                "service_or_product": "Product",
                "date": "2024-01-28",
                "amount": 100,
                "customer_name": "Buyer",
            },
            msg_id,
        )
        records = temp_db.product_sales.get_by_date(date(2024, 1, 28))
        assert len(records) >= 1
        assert records[0]["type"] == "product_sale"
        assert records[0]["product_name"] == "Product"
        assert records[0]["total_amount"] == 100.0

    def test_get_by_date_empty(self, temp_db):
        records = temp_db.product_sales.get_by_date(date(2099, 1, 1))
        assert records == []


# ============================================================
# MembershipRepository Tests
# ============================================================
class TestMembershipRepository:
    """Tests for MembershipRepository."""

    def test_save_basic_membership(self, temp_db):
        msg_id = make_raw_message(temp_db, "mem-basic")
        mid = temp_db.memberships.save(
            {
                "customer_name": "MemberUser",
                "date": "2024-01-01",
                "amount": 1000,
            },
            msg_id,
        )
        assert mid > 0

    def test_save_auto_creates_customer(self, temp_db):
        msg_id = make_raw_message(temp_db, "mem-auto-cust")
        temp_db.memberships.save(
            {
                "customer_name": "NewMemCustomer",
                "date": "2024-01-01",
                "amount": 500,
            },
            msg_id,
        )
        cust = temp_db.customers.search("NewMemCustomer")
        assert len(cust) == 1

    def test_save_default_card_type(self, temp_db):
        msg_id = make_raw_message(temp_db, "mem-default-type")
        mid = temp_db.memberships.save(
            {
                "customer_name": "DefaultType",
                "date": "2024-01-01",
                "amount": 500,
            },
            msg_id,
        )
        with temp_db.get_session() as session:
            m = session.query(Membership).filter_by(id=mid).first()
            assert m.card_type == "储值卡"

    def test_save_with_all_fields(self, temp_db):
        msg_id = make_raw_message(temp_db, "mem-all")
        mid = temp_db.memberships.save(
            {
                "customer_name": "FullMember",
                "date": "2024-01-01",
                "amount": 3000,
                "card_type": "年卡",
                "remaining_sessions": 50,
                "expires_at": "2025-01-01",
            },
            msg_id,
        )

        with temp_db.get_session() as session:
            m = session.query(Membership).filter_by(id=mid).first()
            assert m.card_type == "年卡"
            assert float(m.total_amount) == 3000
            assert float(m.balance) == 3000
            assert m.remaining_sessions == 50
            assert m.expires_at == date(2025, 1, 1)

    def test_save_balance_equals_amount(self, temp_db):
        """Initial balance should equal the deposit amount."""
        msg_id = make_raw_message(temp_db, "mem-balance")
        mid = temp_db.memberships.save(
            {
                "customer_name": "BalanceCheck",
                "date": "2024-01-01",
                "amount": 2000,
            },
            msg_id,
        )
        with temp_db.get_session() as session:
            m = session.query(Membership).filter_by(id=mid).first()
            assert float(m.balance) == float(m.total_amount) == 2000

    def test_get_active_by_customer(self, temp_db):
        msg_id = make_raw_message(temp_db, "mem-active")
        mid = temp_db.memberships.save(
            {
                "customer_name": "ActiveMem",
                "date": "2024-01-01",
                "amount": 1000,
            },
            msg_id,
        )
        cust = temp_db.customers.search("ActiveMem")[0]
        active = temp_db.memberships.get_active_by_customer(cust.id)
        assert len(active) == 1
        assert active[0].id == mid

    def test_get_active_by_customer_excludes_inactive(self, temp_db):
        msg_id = make_raw_message(temp_db, "mem-inactive")
        mid = temp_db.memberships.save(
            {
                "customer_name": "InactiveMem",
                "date": "2024-01-01",
                "amount": 500,
            },
            msg_id,
        )
        # Manually deactivate
        with temp_db.get_session() as session:
            m = session.query(Membership).filter_by(id=mid).first()
            m.is_active = False
            session.commit()

        cust = temp_db.customers.search("InactiveMem")[0]
        active = temp_db.memberships.get_active_by_customer(cust.id)
        assert len(active) == 0

    def test_deduct_balance_success(self, temp_db):
        msg_id = make_raw_message(temp_db, "mem-deduct-ok")
        mid = temp_db.memberships.save(
            {"customer_name": "DeductOK", "date": "2024-01-01", "amount": 1000},
            msg_id,
        )
        updated = temp_db.memberships.deduct_balance(mid, 200)
        assert updated is not None
        assert float(updated.balance) == 800.0

    def test_deduct_balance_exact_amount(self, temp_db):
        msg_id = make_raw_message(temp_db, "mem-deduct-exact")
        mid = temp_db.memberships.save(
            {"customer_name": "DeductExact", "date": "2024-01-01", "amount": 500},
            msg_id,
        )
        updated = temp_db.memberships.deduct_balance(mid, 500)
        assert updated is not None
        assert float(updated.balance) == 0.0

    def test_deduct_balance_insufficient(self, temp_db):
        msg_id = make_raw_message(temp_db, "mem-deduct-fail")
        mid = temp_db.memberships.save(
            {"customer_name": "DeductFail", "date": "2024-01-01", "amount": 100},
            msg_id,
        )
        result = temp_db.memberships.deduct_balance(mid, 200)
        assert result is None

    def test_deduct_balance_nonexistent(self, temp_db):
        result = temp_db.memberships.deduct_balance(99999, 100)
        assert result is None

    def test_deduct_session_success(self, temp_db):
        msg_id = make_raw_message(temp_db, "mem-sess-ok")
        mid = temp_db.memberships.save(
            {
                "customer_name": "SessOK",
                "date": "2024-01-01",
                "amount": 1000,
                "remaining_sessions": 10,
            },
            msg_id,
        )
        updated = temp_db.memberships.deduct_session(mid, 2)
        assert updated is not None
        assert updated.remaining_sessions == 8

    def test_deduct_session_to_zero(self, temp_db):
        msg_id = make_raw_message(temp_db, "mem-sess-zero")
        mid = temp_db.memberships.save(
            {
                "customer_name": "SessZero",
                "date": "2024-01-01",
                "amount": 1000,
                "remaining_sessions": 3,
            },
            msg_id,
        )
        updated = temp_db.memberships.deduct_session(mid, 3)
        assert updated is not None
        assert updated.remaining_sessions == 0

    def test_deduct_session_insufficient(self, temp_db):
        msg_id = make_raw_message(temp_db, "mem-sess-fail")
        mid = temp_db.memberships.save(
            {
                "customer_name": "SessFail",
                "date": "2024-01-01",
                "amount": 1000,
                "remaining_sessions": 2,
            },
            msg_id,
        )
        result = temp_db.memberships.deduct_session(mid, 5)
        assert result is None

    def test_deduct_session_without_sessions(self, temp_db):
        """If remaining_sessions is None, deduct_session returns None."""
        msg_id = make_raw_message(temp_db, "mem-sess-none")
        mid = temp_db.memberships.save(
            {"customer_name": "NoSess", "date": "2024-01-01", "amount": 1000},
            msg_id,
        )
        result = temp_db.memberships.deduct_session(mid, 1)
        assert result is None

    def test_add_points(self, temp_db):
        msg_id = make_raw_message(temp_db, "mem-points")
        mid = temp_db.memberships.save(
            {"customer_name": "PointsUser", "date": "2024-01-01", "amount": 1000},
            msg_id,
        )
        updated = temp_db.memberships.add_points(mid, 50)
        assert updated is not None
        assert updated.points == 50

    def test_add_points_cumulative(self, temp_db):
        msg_id = make_raw_message(temp_db, "mem-points-cum")
        mid = temp_db.memberships.save(
            {"customer_name": "CumPoints", "date": "2024-01-01", "amount": 1000},
            msg_id,
        )
        temp_db.memberships.add_points(mid, 30)
        updated = temp_db.memberships.add_points(mid, 20)
        assert updated is not None
        assert updated.points == 50

    def test_add_points_nonexistent(self, temp_db):
        result = temp_db.memberships.add_points(99999, 10)
        assert result is None

    def test_full_membership_lifecycle(self, temp_db):
        """End-to-end: create → deduct balance → deduct session → add points."""
        msg_id = make_raw_message(temp_db, "mem-lifecycle")
        mid = temp_db.memberships.save(
            {
                "customer_name": "LifecycleUser",
                "date": "2024-01-01",
                "amount": 1000,
                "card_type": "VIP",
                "remaining_sessions": 10,
            },
            msg_id,
        )

        # Deduct balance
        m = temp_db.memberships.deduct_balance(mid, 200)
        assert float(m.balance) == 800

        # Deduct sessions
        m = temp_db.memberships.deduct_session(mid, 3)
        assert m.remaining_sessions == 7

        # Add points
        m = temp_db.memberships.add_points(mid, 100)
        assert m.points == 100

        # Verify final state
        active = temp_db.memberships.get_active_by_customer(m.customer_id)
        assert len(active) == 1

