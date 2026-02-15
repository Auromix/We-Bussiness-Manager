"""SQLAlchemy ORM 模型定义"""
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime, 
    DECIMAL, ForeignKey, JSON, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, date

Base = declarative_base()


class Employee(Base):
    """员工表"""
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    wechat_nickname = Column(String(100))
    wechat_alias = Column(String(100))
    role = Column(String(20), default="staff")  # staff / manager / bot
    commission_rate = Column(DECIMAL(5, 2), default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    service_records_as_employee = relationship("ServiceRecord", foreign_keys="ServiceRecord.employee_id", back_populates="employee")
    service_records_as_recorder = relationship("ServiceRecord", foreign_keys="ServiceRecord.recorder_id", back_populates="recorder")
    product_sales = relationship("ProductSale", back_populates="recorder")


class Customer(Base):
    """顾客/会员表"""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    phone = Column(String(20))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    memberships = relationship("Membership", back_populates="customer")
    service_records = relationship("ServiceRecord", back_populates="customer")
    product_sales = relationship("ProductSale", back_populates="customer")


class Membership(Base):
    """会员卡表"""
    __tablename__ = "memberships"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    card_type = Column(String(50))
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    balance = Column(DECIMAL(10, 2), nullable=False)
    remaining_sessions = Column(Integer)
    opened_at = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="memberships")
    service_records = relationship("ServiceRecord", back_populates="membership")


class ServiceType(Base):
    """服务类型字典表"""
    __tablename__ = "service_types"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    default_price = Column(DECIMAL(10, 2))
    category = Column(String(50))
    
    # Relationships
    service_records = relationship("ServiceRecord", back_populates="service_type")


class ServiceRecord(Base):
    """服务记录表（核心表）"""
    __tablename__ = "service_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    employee_id = Column(Integer, ForeignKey("employees.id"))
    recorder_id = Column(Integer, ForeignKey("employees.id"))
    service_type_id = Column(Integer, ForeignKey("service_types.id"))
    service_date = Column(Date, nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    commission_amount = Column(DECIMAL(10, 2), default=0)
    commission_to = Column(String(50))
    net_amount = Column(DECIMAL(10, 2))
    membership_id = Column(Integer, ForeignKey("memberships.id"))
    notes = Column(Text)
    raw_message_id = Column(Integer, ForeignKey("raw_messages.id"))
    parse_confidence = Column(DECIMAL(3, 2))
    confirmed = Column(Boolean, default=False)
    confirmed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="service_records")
    employee = relationship("Employee", foreign_keys=[employee_id], back_populates="service_records_as_employee")
    recorder = relationship("Employee", foreign_keys=[recorder_id], back_populates="service_records_as_recorder")
    service_type = relationship("ServiceType", back_populates="service_records")
    membership = relationship("Membership", back_populates="service_records")
    raw_message = relationship("RawMessage", back_populates="service_records")


class Product(Base):
    """商品表"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50))  # supplement / medicine / accessory
    unit_price = Column(DECIMAL(10, 2))
    stock_quantity = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sales = relationship("ProductSale", back_populates="product")
    inventory_logs = relationship("InventoryLog", back_populates="product")


class ProductSale(Base):
    """商品销售记录"""
    __tablename__ = "product_sales"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))
    recorder_id = Column(Integer, ForeignKey("employees.id"))
    quantity = Column(Integer, default=1)
    unit_price = Column(DECIMAL(10, 2))
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    sale_date = Column(Date, nullable=False)
    notes = Column(Text)
    raw_message_id = Column(Integer, ForeignKey("raw_messages.id"))
    parse_confidence = Column(DECIMAL(3, 2))
    confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="sales")
    customer = relationship("Customer", back_populates="product_sales")
    recorder = relationship("Employee", back_populates="product_sales")
    raw_message = relationship("RawMessage", back_populates="product_sales")


class InventoryLog(Base):
    """库存变动记录"""
    __tablename__ = "inventory_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    change_type = Column(String(20), nullable=False)  # sale / restock / adjustment
    quantity_change = Column(Integer, nullable=False)  # 正数入库，负数出库
    quantity_after = Column(Integer, nullable=False)
    reference_id = Column(Integer)  # 关联 product_sales.id 或其他
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="inventory_logs")


class RawMessage(Base):
    """原始消息存档"""
    __tablename__ = "raw_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wechat_msg_id = Column(String(100), unique=True)
    sender_nickname = Column(String(100), nullable=False)
    sender_wechat_id = Column(String(100))
    content = Column(Text, nullable=False)
    msg_type = Column(String(20), default="text")
    group_id = Column(String(100))
    timestamp = Column(DateTime, nullable=False)
    is_at_bot = Column(Boolean, default=False)
    is_business = Column(Boolean)
    parse_status = Column(String(20), default="pending")  # pending / parsed / failed / ignored
    parse_result = Column(JSON)
    parse_error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    service_records = relationship("ServiceRecord", back_populates="raw_message")
    product_sales = relationship("ProductSale", back_populates="raw_message")
    corrections = relationship("Correction", back_populates="raw_message")


class Correction(Base):
    """修正记录"""
    __tablename__ = "corrections"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    original_record_type = Column(String(50))  # service_records / product_sales
    original_record_id = Column(Integer)
    correction_type = Column(String(20))  # date_change / amount_change / delete
    old_value = Column(JSON)
    new_value = Column(JSON)
    reason = Column(Text)
    raw_message_id = Column(Integer, ForeignKey("raw_messages.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    raw_message = relationship("RawMessage", back_populates="corrections")


class DailySummary(Base):
    """每日汇总快照"""
    __tablename__ = "daily_summaries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    summary_date = Column(Date, nullable=False, unique=True)
    total_service_revenue = Column(DECIMAL(10, 2))
    total_product_revenue = Column(DECIMAL(10, 2))
    total_commissions = Column(DECIMAL(10, 2))
    net_revenue = Column(DECIMAL(10, 2))
    service_count = Column(Integer)
    product_sale_count = Column(Integer)
    new_members = Column(Integer)
    membership_revenue = Column(DECIMAL(10, 2))
    summary_text = Column(Text)
    confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

