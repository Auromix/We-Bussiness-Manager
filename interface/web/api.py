"""Web API 接口 - 用于 Web 端操作数据库

提供 RESTful API 接口，用于：
- Web 端操作数据库（CRUD 操作）
- 管理后台
- 数据查询和统计
- 配置管理

注意：这是预留实现，目前提供基础框架和接口定义
"""
from typing import Any, Dict, List, Optional
from datetime import date, datetime
from fastapi import FastAPI, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from loguru import logger

from interface.base import Interface
from db.repository import DatabaseRepository


# ========== Pydantic 模型定义 ==========

class ServiceRecordCreate(BaseModel):
    """创建服务记录的请求模型"""
    customer_id: Optional[int] = None
    employee_id: Optional[int] = None
    recorder_id: Optional[int] = None
    service_type_id: Optional[int] = None
    service_date: date
    amount: float = Field(..., gt=0, description="服务金额")
    commission_amount: Optional[float] = 0
    referral_channel_id: Optional[int] = None
    membership_id: Optional[int] = None
    notes: Optional[str] = None


class ProductSaleCreate(BaseModel):
    """创建商品销售记录的请求模型"""
    product_id: Optional[int] = None
    customer_id: Optional[int] = None
    recorder_id: Optional[int] = None
    quantity: int = Field(..., gt=0, description="销售数量")
    unit_price: Optional[float] = None
    total_amount: float = Field(..., gt=0, description="总金额")
    sale_date: date
    notes: Optional[str] = None


class CustomerCreate(BaseModel):
    """创建顾客的请求模型"""
    name: str = Field(..., min_length=1, max_length=50)
    phone: Optional[str] = None
    notes: Optional[str] = None


class EmployeeCreate(BaseModel):
    """创建员工的请求模型"""
    name: str = Field(..., min_length=1, max_length=50)
    wechat_nickname: Optional[str] = None
    role: str = "staff"
    commission_rate: Optional[float] = 0


class QueryParams(BaseModel):
    """通用查询参数"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


# ========== Web API 接口类 ==========

class WebAPI(Interface):
    """Web API 接口
    
    提供 RESTful API 用于 Web 端操作数据库
    实现 Interface 接口，可以统一管理
    """
    
    def __init__(self, db_repo: DatabaseRepository, host: str = "0.0.0.0", port: int = 8080):
        """
        Args:
            db_repo: 数据库仓库实例
            host: 监听地址
            port: 监听端口
        """
        super().__init__("web")
        self.db = db_repo
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="Business Manager Web API",
            description="Web API for database operations",
            version="1.0.0"
        )
        self._setup_routes()
    
    def _setup_routes(self):
        """设置 API 路由"""
        
        # ========== 健康检查 ==========
        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            return {"status": "ok", "service": "web_api"}
        
        # ========== 服务记录 ==========
        @self.app.post("/api/service_records")
        async def create_service_record(record: ServiceRecordCreate):
            """创建服务记录"""
            try:
                data = record.dict()
                record_id = self.db.save_service_record(data, None)
                return {"status": "success", "id": record_id}
            except Exception as e:
                logger.error(f"Error creating service record: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/service_records")
        async def list_service_records(
            start_date: Optional[date] = Query(None),
            end_date: Optional[date] = Query(None),
            limit: int = Query(100, ge=1, le=1000),
            offset: int = Query(0, ge=0)
        ):
            """查询服务记录列表"""
            try:
                records = self.db.get_service_records(
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                    offset=offset
                )
                return {"status": "success", "data": records, "count": len(records)}
            except Exception as e:
                logger.error(f"Error listing service records: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/service_records/{record_id}")
        async def get_service_record(record_id: int = Path(..., ge=1)):
            """获取单个服务记录"""
            try:
                # 这里需要实现 get_service_record_by_id 方法
                # 暂时返回占位符
                return {"status": "success", "message": "Not implemented yet"}
            except Exception as e:
                logger.error(f"Error getting service record: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ========== 商品销售 ==========
        @self.app.post("/api/product_sales")
        async def create_product_sale(sale: ProductSaleCreate):
            """创建商品销售记录"""
            try:
                data = sale.dict()
                sale_id = self.db.save_product_sale(data, None)
                return {"status": "success", "id": sale_id}
            except Exception as e:
                logger.error(f"Error creating product sale: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/product_sales")
        async def list_product_sales(
            start_date: Optional[date] = Query(None),
            end_date: Optional[date] = Query(None),
            limit: int = Query(100, ge=1, le=1000),
            offset: int = Query(0, ge=0)
        ):
            """查询商品销售记录列表"""
            try:
                sales = self.db.get_product_sales(
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                    offset=offset
                )
                return {"status": "success", "data": sales, "count": len(sales)}
            except Exception as e:
                logger.error(f"Error listing product sales: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ========== 顾客管理 ==========
        @self.app.post("/api/customers")
        async def create_customer(customer: CustomerCreate):
            """创建顾客"""
            try:
                data = customer.dict()
                customer_id = self.db.create_customer(data)
                return {"status": "success", "id": customer_id}
            except Exception as e:
                logger.error(f"Error creating customer: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/customers")
        async def list_customers(
            limit: int = Query(100, ge=1, le=1000),
            offset: int = Query(0, ge=0)
        ):
            """查询顾客列表"""
            try:
                # 这里需要实现 get_customers 方法
                # 暂时返回占位符
                return {"status": "success", "message": "Not implemented yet", "data": []}
            except Exception as e:
                logger.error(f"Error listing customers: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ========== 员工管理 ==========
        @self.app.post("/api/employees")
        async def create_employee(employee: EmployeeCreate):
            """创建员工"""
            try:
                data = employee.dict()
                employee_id = self.db.create_employee(data)
                return {"status": "success", "id": employee_id}
            except Exception as e:
                logger.error(f"Error creating employee: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/employees")
        async def list_employees():
            """查询员工列表"""
            try:
                # 这里需要实现 get_employees 方法
                # 暂时返回占位符
                return {"status": "success", "message": "Not implemented yet", "data": []}
            except Exception as e:
                logger.error(f"Error listing employees: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ========== 统计查询 ==========
        @self.app.get("/api/statistics/daily")
        async def get_daily_statistics(
            target_date: date = Query(..., description="查询日期")
        ):
            """获取指定日期的统计数据"""
            try:
                # 这里需要实现统计查询方法
                # 暂时返回占位符
                return {
                    "status": "success",
                    "message": "Not implemented yet",
                    "date": target_date.isoformat(),
                    "data": {}
                }
            except Exception as e:
                logger.error(f"Error getting daily statistics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ========== 根路径 ==========
        @self.app.get("/")
        async def root():
            """API 根路径"""
            return {
                "service": "Business Manager Web API",
                "version": "1.0.0",
                "endpoints": {
                    "GET /health": "健康检查",
                    "POST /api/service_records": "创建服务记录",
                    "GET /api/service_records": "查询服务记录列表",
                    "POST /api/product_sales": "创建商品销售记录",
                    "GET /api/product_sales": "查询商品销售记录列表",
                    "POST /api/customers": "创建顾客",
                    "GET /api/customers": "查询顾客列表",
                    "POST /api/employees": "创建员工",
                    "GET /api/employees": "查询员工列表",
                    "GET /api/statistics/daily": "获取每日统计数据"
                }
            }
    
    def start(self):
        """启动 Web API 服务器"""
        import uvicorn
        import threading
        
        logger.info(f"Starting Web API server on {self.host}:{self.port}")
        self.running = True
        
        # 在后台线程中启动服务器
        def run_server():
            uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        logger.info(f"Web API server started in background thread")
    
    def stop(self):
        """停止 Web API 服务器"""
        self.running = False
        logger.info("Web API server stopped")
    
    async def handle_message(self, raw_msg: Dict[str, Any]) -> Optional[str]:
        """处理消息（Web API 通常不处理消息，但实现接口以保持一致性）
        
        Args:
            raw_msg: 消息字典
            
        Returns:
            None（Web API 不处理消息）
        """
        # Web API 不处理消息，返回 None
        return None
    
    def send_message(self, target: str, content: str):
        """发送消息（Web API 通常不发送消息，但实现接口以保持一致性）
        
        Args:
            target: 目标标识
            content: 消息内容
        """
        # Web API 不发送消息，记录日志即可
        logger.info(f"Web API send_message called: target={target}, content={content}")

