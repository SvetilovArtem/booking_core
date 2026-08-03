import enum
from datetime import date, time, datetime
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Enum, Date, Time, Table, Column, \
    UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database.session import Base

admin_business_association = Table(
    "admin_business_association",
    Base.metadata,
    Column("admin_id", Integer, ForeignKey("admins.id"), primary_key=True),
    Column("business_id", Integer, ForeignKey("businesses.id"), primary_key=True),
)

master_business_association = Table(
    "master_business_association",
    Base.metadata,
    Column("master_id", Integer, ForeignKey("masters.id"), primary_key=True),
    Column("business_id", Integer, ForeignKey("businesses.id"), primary_key=True),
)


class SlotStatus(str, enum.Enum):
    available = "available"
    booked = "booked"
    cancelled = "cancelled"
    blocked = "blocked"


class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"
    no_show = "no_show"


class UserRole(str, enum.Enum):
    client = "client"
    master = "master"
    admin = "admin"


class Business(Base):
    __tablename__ = "businesses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Minsk")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    admins = relationship("Admin", secondary=admin_business_association, back_populates="businesses")
    masters = relationship("Master", secondary=master_business_association, back_populates="businesses")
    slots = relationship("Slot", back_populates="business")
    orders = relationship("Order", back_populates="business")


class Admin(Base):
    __tablename__ = "admins"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    telegram_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    businesses = relationship("Business", secondary=admin_business_association, back_populates="admins")


class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    orders = relationship("Order", back_populates="client")


class Master(Base):
    __tablename__ = "masters"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    telegram_id: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True, index=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    businesses = relationship("Business", secondary=master_business_association, back_populates="masters")
    services = relationship("ServiceMaster", back_populates="master")
    slots = relationship("Slot", back_populates="master")


class Service(Base):
    __tablename__ = "services"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    masters = relationship("ServiceMaster", back_populates="service")
    orders = relationship("Order", back_populates="service")


class ServiceMaster(Base):
    __tablename__ = "service_masters"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    master_id: Mapped[int] = mapped_column(Integer, ForeignKey("masters.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("master_id", "service_id", name="uq_master_service"),)

    master = relationship("Master", back_populates="services")
    service = relationship("Service", back_populates="masters")


class Slot(Base):
    __tablename__ = "slots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    master_id: Mapped[int] = mapped_column(Integer, ForeignKey("masters.id"), nullable=False)
    business_id: Mapped[int] = mapped_column(Integer, ForeignKey("businesses.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[SlotStatus] = mapped_column(Enum(SlotStatus), default=SlotStatus.available)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    master = relationship("Master", back_populates="slots")
    business = relationship("Business", back_populates="slots")
    order = relationship("Order", back_populates="slot", uselist=False)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    slot_id: Mapped[int] = mapped_column(Integer, ForeignKey("slots.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    business_id: Mapped[int] = mapped_column(Integer, ForeignKey("businesses.id"), nullable=False)

    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.pending)
    number: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True, index=True)
    cancel_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    client = relationship("Client", back_populates="orders")
    slot = relationship("Slot", back_populates="order")
    service = relationship("Service", back_populates="orders")
    business = relationship("Business", back_populates="orders")
    # Убрали прямую связь master, так как мастера можно получить через order.slot.master


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)