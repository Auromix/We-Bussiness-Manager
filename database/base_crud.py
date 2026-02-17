"""通用 CRUD 操作基类。

提供与具体业务无关的通用数据库操作，所有业务仓库均可继承此基类，
获得标准的增删改查能力。

设计原则：
- 所有方法支持外部传入 session（用于事务组合）
- 未传入 session 时自动创建并管理会话生命周期
- 返回 ORM 对象，供上层按需转换为字典
"""
from typing import Optional, List, Dict, Any, Type, TypeVar, Union
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from .connection import DatabaseConnection

# 泛型类型变量，表示任意 SQLAlchemy 模型
T = TypeVar("T")


class BaseCRUD:
    """通用 CRUD 操作基类。

    提供标准的增删改查操作，适用于任意 SQLAlchemy ORM 模型。
    所有业务仓库应继承此类以获得基础数据操作能力。

    Attributes:
        conn: 数据库连接管理器实例。

    Example:
        ```python
        class StaffRepository(BaseCRUD):
            def get_active_staff(self):
                return self.get_all(Employee, filters={"is_active": True})
        ```
    """

    def __init__(self, conn: DatabaseConnection) -> None:
        """初始化 CRUD 基类。

        Args:
            conn: DatabaseConnection 实例。
        """
        self.conn = conn

    def _get_session(self) -> Union[Session, AsyncSession]:
        """获取数据库会话（内部使用）。"""
        return self.conn.get_session()

    # ========== 查询操作 ==========

    def get_by_id(self, model_class: Type[T], record_id: int,
                  session: Optional[Session] = None) -> Optional[T]:
        """根据ID查询单条记录。

        Args:
            model_class: ORM 模型类。
            record_id: 记录ID。
            session: 外部会话（可选）。

        Returns:
            模型实例，不存在则返回 None。
        """
        if session:
            return session.query(model_class).filter(
                model_class.id == record_id
            ).first()

        with self._get_session() as sess:
            return sess.query(model_class).filter(
                model_class.id == record_id
            ).first()

    def get_all(self, model_class: Type[T],
                filters: Optional[Dict[str, Any]] = None,
                order_by: Optional[str] = None,
                limit: Optional[int] = None,
                offset: Optional[int] = None,
                session: Optional[Session] = None) -> List[T]:
        """查询多条记录，支持过滤、排序、分页。

        Args:
            model_class: ORM 模型类。
            filters: 过滤条件字典，键为字段名，值为期望值。
            order_by: 排序字段名（前缀 '-' 表示降序，如 '-created_at'）。
            limit: 返回条数限制。
            offset: 跳过条数（配合 limit 实现分页）。
            session: 外部会话（可选）。

        Returns:
            模型实例列表。
        """
        def _query(sess):
            query = sess.query(model_class)
            if filters:
                for key, value in filters.items():
                    if hasattr(model_class, key):
                        query = query.filter(
                            getattr(model_class, key) == value
                        )
            if order_by:
                if order_by.startswith("-"):
                    field = getattr(model_class, order_by[1:], None)
                    if field is not None:
                        query = query.order_by(field.desc())
                else:
                    field = getattr(model_class, order_by, None)
                    if field is not None:
                        query = query.order_by(field.asc())
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            return query.all()

        if session:
            return _query(session)

        with self._get_session() as sess:
            return _query(sess)

    def count(self, model_class: Type[T],
              filters: Optional[Dict[str, Any]] = None,
              session: Optional[Session] = None) -> int:
        """统计记录数。

        Args:
            model_class: ORM 模型类。
            filters: 过滤条件字典。
            session: 外部会话（可选）。

        Returns:
            满足条件的记录数。
        """
        def _query(sess):
            query = sess.query(model_class)
            if filters:
                for key, value in filters.items():
                    if hasattr(model_class, key):
                        query = query.filter(
                            getattr(model_class, key) == value
                        )
            return query.count()

        if session:
            return _query(session)

        with self._get_session() as sess:
            return _query(sess)

    # ========== 创建操作 ==========

    def create(self, model_class: Type[T],
               session: Optional[Session] = None,
               **kwargs) -> T:
        """创建单条记录。

        Args:
            model_class: ORM 模型类。
            session: 外部会话（可选）。如果传入，不会自动提交。
            **kwargs: 模型字段的键值对。

        Returns:
            新创建的模型实例。
        """
        instance = model_class(**kwargs)

        if session:
            session.add(instance)
            session.flush()
            session.refresh(instance)
            return instance

        with self._get_session() as sess:
            sess.add(instance)
            sess.commit()
            sess.refresh(instance)
            # 重新查询以避免 detached instance 问题
            record_id = instance.id
        with self._get_session() as sess:
            return sess.query(model_class).filter(
                model_class.id == record_id
            ).first()

    def get_or_create(self, model_class: Type[T],
                      lookup: Dict[str, Any],
                      defaults: Optional[Dict[str, Any]] = None,
                      session: Optional[Session] = None) -> T:
        """查找或创建记录（幂等操作）。

        根据 lookup 条件查找记录，若不存在则使用 lookup + defaults 创建。

        Args:
            model_class: ORM 模型类。
            lookup: 查找条件字典（用于查找和创建时的必填字段）。
            defaults: 创建时的附加默认值字典（可选）。
            session: 外部会话（可选）。

        Returns:
            已存在或新创建的模型实例。
        """
        def _do(sess):
            query = sess.query(model_class)
            for key, value in lookup.items():
                if hasattr(model_class, key):
                    query = query.filter(
                        getattr(model_class, key) == value
                    )
            instance = query.first()
            if not instance:
                create_kwargs = {**lookup, **(defaults or {})}
                instance = model_class(**create_kwargs)
                sess.add(instance)
                sess.flush()
                sess.refresh(instance)
            return instance

        if session:
            return _do(session)

        with self._get_session() as sess:
            instance = _do(sess)
            sess.commit()
            record_id = instance.id
        with self._get_session() as sess:
            return sess.query(model_class).filter(
                model_class.id == record_id
            ).first()

    # ========== 更新操作 ==========

    def update_by_id(self, model_class: Type[T], record_id: int,
                     session: Optional[Session] = None,
                     **kwargs) -> Optional[T]:
        """根据ID更新记录。

        Args:
            model_class: ORM 模型类。
            record_id: 记录ID。
            session: 外部会话（可选）。
            **kwargs: 要更新的字段键值对。

        Returns:
            更新后的模型实例，不存在则返回 None。
        """
        def _do(sess):
            instance = sess.query(model_class).filter(
                model_class.id == record_id
            ).first()
            if instance:
                for key, value in kwargs.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
            return instance

        if session:
            instance = _do(session)
            if instance:
                session.flush()
                session.refresh(instance)
            return instance

        with self._get_session() as sess:
            instance = _do(sess)
            if instance:
                sess.commit()
                sess.refresh(instance)
                final_id = instance.id
            else:
                return None
        with self._get_session() as sess:
            return sess.query(model_class).filter(
                model_class.id == final_id
            ).first()

    # ========== 删除操作 ==========

    def delete_by_id(self, model_class: Type[T], record_id: int,
                     session: Optional[Session] = None) -> bool:
        """根据ID删除记录。

        Args:
            model_class: ORM 模型类。
            record_id: 记录ID。
            session: 外部会话（可选）。

        Returns:
            是否成功删除。
        """
        def _do(sess):
            instance = sess.query(model_class).filter(
                model_class.id == record_id
            ).first()
            if instance:
                sess.delete(instance)
                return True
            return False

        if session:
            return _do(session)

        with self._get_session() as sess:
            result = _do(sess)
            if result:
                sess.commit()
            return result

