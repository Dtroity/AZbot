from sqlalchemy import BigInteger, String, Boolean, Integer, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

Base = declarative_base()


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    role = Column(String(50), default="supplier")  # supplier, admin
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    filters = relationship("Filter", back_populates="supplier", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="supplier")

    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}', active={self.active})>"


class Filter(Base):
    __tablename__ = "filters"

    id = Column(Integer, primary_key=True)
    keyword = Column(String(255), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher priority = first to get orders
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="filters")

    def __repr__(self):
        return f"<Filter(id={self.id}, keyword='{self.keyword}', supplier_id={self.supplier_id})>"


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(8), primary_key=True)  # Short UUID
    text = Column(Text, nullable=False)
    status = Column(String(50), default="NEW")  # NEW, ACCEPTED, DECLINED, COMPLETED, CANCELLED
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    admin_id = Column(BigInteger, nullable=False)  # Who created the order
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    assigned_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="orders")
    messages = relationship("OrderMessage", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order(id='{self.id}', status='{self.status}', supplier_id={self.supplier_id})>"


class OrderMessage(Base):
    __tablename__ = "order_messages"

    id = Column(Integer, primary_key=True)
    order_id = Column(String(8), ForeignKey("orders.id"), nullable=False)
    sender_id = Column(BigInteger, nullable=False)  # Telegram user ID
    message_text = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # text, system, status_change
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="messages")

    def __repr__(self):
        return f"<OrderMessage(id={self.id}, order_id='{self.order_id}', sender_id={self.sender_id})>"


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    action = Column(String(100), nullable=False)  # order_created, order_accepted, etc.
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<ActivityLog(id={self.id}, user_id={self.user_id}, action='{self.action}')>"
