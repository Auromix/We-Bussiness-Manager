"""数据访问层"""
from sqlalchemy import create_engine, select, func, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from loguru import logger
from db.models import (
    Base, Employee, Customer, Membership, ServiceType, ServiceRecord,
    Product, ProductSale, InventoryLog, RawMessage, Correction, DailySummary
)
from config.settings import settings
import json


class DatabaseRepository:
    """数据库访问层"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        
        # 判断是否为异步数据库URL
        if self.database_url.startswith("sqlite"):
            # SQLite 使用同步引擎
            self.engine = create_engine(
                self.database_url.replace("sqlite:///", "sqlite:///"),
                echo=False,
                connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {}
            )
            self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
            self.is_async = False
        else:
            # PostgreSQL 等使用异步引擎
            async_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
            self.engine = create_async_engine(async_url, echo=False)
            self.SessionLocal = async_sessionmaker(self.engine, class_=AsyncSession)
            self.is_async = True
    
    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()
    
    # ========== RawMessage 相关 ==========
    
    def save_raw_message(self, msg_data: Dict[str, Any]) -> int:
        """保存原始消息"""
        with self.get_session() as session:
            # 检查是否已存在（去重）
            existing = session.query(RawMessage).filter(
                RawMessage.wechat_msg_id == msg_data.get("wechat_msg_id")
            ).first()
            
            if existing:
                return existing.id
            
            msg = RawMessage(
                wechat_msg_id=msg_data.get("wechat_msg_id"),
                sender_nickname=msg_data.get("sender_nickname"),
                sender_wechat_id=msg_data.get("sender_wechat_id"),
                content=msg_data.get("content"),
                msg_type=msg_data.get("msg_type", "text"),
                group_id=msg_data.get("group_id"),
                timestamp=msg_data.get("timestamp"),
                is_at_bot=msg_data.get("is_at_bot", False),
                is_business=msg_data.get("is_business"),
                parse_status=msg_data.get("parse_status", "pending")
            )
            session.add(msg)
            session.commit()
            session.refresh(msg)
            return msg.id
    
    def update_parse_status(self, msg_id: int, status: str, result: Optional[Dict] = None, error: Optional[str] = None):
        """更新消息解析状态"""
        with self.get_session() as session:
            msg = session.query(RawMessage).filter(RawMessage.id == msg_id).first()
            if msg:
                msg.parse_status = status
                if result:
                    msg.parse_result = result
                if error:
                    msg.parse_error = error
                session.commit()
    
    # ========== Employee 相关 ==========
    
    def get_or_create_employee(self, name: str, wechat_nickname: Optional[str] = None, session=None) -> Employee:
        """获取或创建员工"""
        if session is None:
            with self.get_session() as sess:
                return self._get_or_create_employee_in_session(name, wechat_nickname, sess)
        else:
            return self._get_or_create_employee_in_session(name, wechat_nickname, session)
    
    def _get_or_create_employee_in_session(self, name: str, wechat_nickname: Optional[str], session) -> Employee:
        """在指定会话中获取或创建员工"""
        employee = session.query(Employee).filter(
            or_(
                Employee.name == name,
                Employee.wechat_nickname == wechat_nickname
            )
        ).first()
        
        if not employee:
            employee = Employee(name=name, wechat_nickname=wechat_nickname)
            session.add(employee)
            session.flush()  # 使用 flush 而不是 commit，让外层会话控制提交
            session.refresh(employee)
        
        return employee
    
    # ========== Customer 相关 ==========
    
    def get_or_create_customer(self, name: str, session=None) -> Customer:
        """获取或创建顾客"""
        if session is None:
            with self.get_session() as sess:
                return self._get_or_create_customer_in_session(name, sess)
        else:
            return self._get_or_create_customer_in_session(name, session)
    
    def _get_or_create_customer_in_session(self, name: str, session) -> Customer:
        """在指定会话中获取或创建顾客"""
        customer = session.query(Customer).filter(Customer.name == name).first()
        
        if not customer:
            customer = Customer(name=name)
            session.add(customer)
            session.flush()  # 使用 flush 而不是 commit
            session.refresh(customer)
        
        return customer
    
    # ========== ServiceType 相关 ==========
    
    def get_or_create_service_type(self, name: str, default_price: Optional[float] = None, category: Optional[str] = None, session=None) -> ServiceType:
        """获取或创建服务类型"""
        if session is None:
            with self.get_session() as sess:
                return self._get_or_create_service_type_in_session(name, default_price, category, sess)
        else:
            return self._get_or_create_service_type_in_session(name, default_price, category, session)
    
    def _get_or_create_service_type_in_session(self, name: str, default_price: Optional[float], category: Optional[str], session) -> ServiceType:
        """在指定会话中获取或创建服务类型"""
        service_type = session.query(ServiceType).filter(ServiceType.name == name).first()
        
        if not service_type:
            service_type = ServiceType(name=name, default_price=default_price, category=category)
            session.add(service_type)
            session.flush()  # 使用 flush 而不是 commit
            session.refresh(service_type)
        
        return service_type
    
    # ========== ServiceRecord 相关 ==========
    
    def save_service_record(self, record_data: Dict[str, Any], raw_message_id: int) -> int:
        """保存服务记录"""
        with self.get_session() as session:
            # 获取或创建相关实体（使用当前会话）
            customer = self.get_or_create_customer(record_data.get("customer_name", ""), session=session)
            service_type = self.get_or_create_service_type(
                record_data.get("service_or_product", ""),
                record_data.get("default_price"),
                record_data.get("category"),
                session=session
            )
            
            recorder = None
            if record_data.get("recorder_nickname"):
                recorder = self.get_or_create_employee(
                    name=record_data.get("recorder_nickname"),
                    wechat_nickname=record_data.get("recorder_nickname"),
                    session=session
                )
            
            # 解析日期
            service_date = record_data.get("date")
            if isinstance(service_date, str):
                try:
                    service_date = datetime.strptime(service_date, "%Y-%m-%d").date()
                except ValueError:
                    logger.error(f"Invalid date format: {service_date}")
                    raise ValueError(f"Invalid date format: {service_date}, expected YYYY-MM-DD")
            elif service_date is None:
                raise ValueError("Service date is required")
            
            record = ServiceRecord(
                customer_id=customer.id,
                service_type_id=service_type.id,
                service_date=service_date,
                amount=record_data.get("amount", 0),
                commission_amount=record_data.get("commission") or 0,
                commission_to=record_data.get("commission_to"),
                net_amount=record_data.get("net_amount") or record_data.get("amount", 0),
                notes=record_data.get("notes"),
                raw_message_id=raw_message_id,
                parse_confidence=record_data.get("confidence", 0.5),
                confirmed=record_data.get("confirmed", False),
                recorder_id=recorder.id if recorder else None
            )
            
            session.add(record)
            session.commit()
            session.refresh(record)
            return record.id
    
    def get_records_by_date(self, target_date: date) -> List[Dict]:
        """获取指定日期的所有记录"""
        with self.get_session() as session:
            service_records = session.query(ServiceRecord).filter(
                ServiceRecord.service_date == target_date
            ).all()
            
            product_sales = session.query(ProductSale).filter(
                ProductSale.sale_date == target_date
            ).all()
            
            results = []
            for sr in service_records:
                results.append({
                    "type": "service",
                    "id": sr.id,
                    "customer_name": sr.customer.name if sr.customer else "",
                    "service_type": sr.service_type.name if sr.service_type else "",
                    "amount": float(sr.amount),
                    "commission": float(sr.commission_amount) if sr.commission_amount else None,
                    "commission_to": sr.commission_to,
                    "net_amount": float(sr.net_amount) if sr.net_amount else float(sr.amount),
                    "confirmed": sr.confirmed
                })
            
            for ps in product_sales:
                results.append({
                    "type": "product_sale",
                    "id": ps.id,
                    "product_name": ps.product.name if ps.product else "",
                    "customer_name": ps.customer.name if ps.customer else "",
                    "total_amount": float(ps.total_amount),
                    "quantity": ps.quantity,
                    "confirmed": ps.confirmed
                })
            
            return results
    
    # ========== Product 相关 ==========
    
    def get_or_create_product(self, name: str, category: Optional[str] = None, unit_price: Optional[float] = None, session=None) -> Product:
        """获取或创建商品"""
        if session is None:
            with self.get_session() as sess:
                return self._get_or_create_product_in_session(name, category, unit_price, sess)
        else:
            return self._get_or_create_product_in_session(name, category, unit_price, session)
    
    def _get_or_create_product_in_session(self, name: str, category: Optional[str], unit_price: Optional[float], session) -> Product:
        """在指定会话中获取或创建商品"""
        product = session.query(Product).filter(Product.name == name).first()
        
        if not product:
            product = Product(name=name, category=category, unit_price=unit_price)
            session.add(product)
            session.flush()
            session.refresh(product)
        
        return product
    
    def save_product_sale(self, sale_data: Dict[str, Any], raw_message_id: int) -> int:
        """保存商品销售记录"""
        with self.get_session() as session:
            product = self.get_or_create_product(
                sale_data.get("service_or_product", ""),
                sale_data.get("category"),
                sale_data.get("unit_price"),
                session=session
            )
            
            customer = None
            if sale_data.get("customer_name"):
                customer = self.get_or_create_customer(sale_data.get("customer_name"), session=session)
            
            recorder = None
            if sale_data.get("recorder_nickname"):
                recorder = self.get_or_create_employee(
                    name=sale_data.get("recorder_nickname"),
                    wechat_nickname=sale_data.get("recorder_nickname"),
                    session=session
                )
            
            sale_date = sale_data.get("date")
            if isinstance(sale_date, str):
                try:
                    sale_date = datetime.strptime(sale_date, "%Y-%m-%d").date()
                except ValueError:
                    logger.error(f"Invalid date format: {sale_date}")
                    raise ValueError(f"Invalid date format: {sale_date}, expected YYYY-MM-DD")
            elif sale_date is None:
                raise ValueError("Sale date is required")
            
            sale = ProductSale(
                product_id=product.id,
                customer_id=customer.id if customer else None,
                recorder_id=recorder.id if recorder else None,
                quantity=sale_data.get("quantity", 1),
                unit_price=sale_data.get("unit_price"),
                total_amount=sale_data.get("amount", 0),
                sale_date=sale_date,
                notes=sale_data.get("notes"),
                raw_message_id=raw_message_id,
                parse_confidence=sale_data.get("confidence", 0.5),
                confirmed=sale_data.get("confirmed", False)
            )
            
            session.add(sale)
            session.commit()
            session.refresh(sale)
            return sale.id
    
    # ========== Membership 相关 ==========
    
    def save_membership(self, membership_data: Dict[str, Any], raw_message_id: int) -> int:
        """保存会员卡记录"""
        with self.get_session() as session:
            customer = self.get_or_create_customer(membership_data.get("customer_name", ""), session=session)
            
            opened_at = membership_data.get("date")
            if isinstance(opened_at, str):
                try:
                    opened_at = datetime.strptime(opened_at, "%Y-%m-%d").date()
                except ValueError:
                    logger.error(f"Invalid date format: {opened_at}")
                    raise ValueError(f"Invalid date format: {opened_at}, expected YYYY-MM-DD")
            elif opened_at is None:
                raise ValueError("Membership opened_at date is required")
            
            membership = Membership(
                customer_id=customer.id,
                card_type=membership_data.get("card_type", "理疗卡"),
                total_amount=membership_data.get("amount", 0),
                balance=membership_data.get("amount", 0),
                opened_at=opened_at
            )
            
            session.add(membership)
            session.commit()
            session.refresh(membership)
            return membership.id
    
    # ========== DailySummary 相关 ==========
    
    def save_daily_summary(self, summary_date: date, summary_data: Dict[str, Any]) -> int:
        """保存每日汇总"""
        with self.get_session() as session:
            # 检查是否已存在
            existing = session.query(DailySummary).filter(
                DailySummary.summary_date == summary_date
            ).first()
            
            if existing:
                # 更新现有记录
                for key, value in summary_data.items():
                    setattr(existing, key, value)
                session.commit()
                session.refresh(existing)
                return existing.id
            else:
                # 创建新记录
                summary = DailySummary(summary_date=summary_date, **summary_data)
                session.add(summary)
                session.commit()
                session.refresh(summary)
                return summary.id

