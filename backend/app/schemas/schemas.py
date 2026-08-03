from datetime import date, time, datetime
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class SlotStatusEnum(str, Enum):
    available = "available"
    booked = "booked"
    cancelled = "cancelled"
    blocked = "blocked"


class OrderStatusEnum(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"
    no_show = "no_show"


class UserRoleEnum(str, Enum):
    client = "client"
    master = "master"
    admin = "admin"


# --- Business ---
class BusinessCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    timezone: str = "Europe/Minsk"


class BusinessResponse(BaseModel):
    id: int
    name: str
    timezone: str
    is_active: bool

    class Config:
        from_attributes = True


# --- Admin ---
class AdminCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    telegram_id: Optional[int] = None
    password: str = Field(min_length=6)

class AdminUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    telegram_id: Optional[int] = None
    password: Optional[str] = None


class AdminResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    telegram_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class AdminLogin(BaseModel):
    name: str
    password: str


# --- Client ---
class ClientCreate(BaseModel):
    name: Optional[str] = None
    telegram_id: int
    phone: Optional[str] = None


class ClientResponse(BaseModel):
    id: int
    name: Optional[str]
    telegram_id: int
    phone: Optional[str]
    is_blocked: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Master ---
class MasterCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    telegram_id: Optional[int] = None


class MasterResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    telegram_id: Optional[int]
    is_blocked: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Service ---
class ServiceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    price: int = Field(ge=0)


class ServiceResponse(BaseModel):
    id: int
    name: str
    price: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- ServiceMaster ---
class ServiceMasterCreate(BaseModel):
    master_id: int
    service_id: int


class ServiceMasterResponse(BaseModel):
    id: int
    master_id: int
    service_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- Slot ---
class SlotCreate(BaseModel):
    master_id: int
    business_id: int
    date: date
    start_time: time
    end_time: time
    status: SlotStatusEnum = SlotStatusEnum.available


class SlotResponse(BaseModel):
    id: int
    master_id: int
    business_id: int
    date: date
    start_time: time
    end_time: time
    status: SlotStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True


# --- Order ---
class OrderCreate(BaseModel):
    client_id: int
    slot_id: int
    service_id: int
    business_id: int
    status: OrderStatusEnum = OrderStatusEnum.pending
    number: Optional[str] = None


class OrderUpdate(BaseModel):
    status: Optional[OrderStatusEnum] = None
    cancel_reason: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    client_id: int
    slot_id: int
    service_id: int
    business_id: int
    status: OrderStatusEnum
    number: Optional[str]
    cancel_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Notification ---
class NotificationCreate(BaseModel):
    user_id: int
    user_role: UserRoleEnum
    text: str = Field(max_length=500)


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    user_role: UserRoleEnum
    text: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Updates ---
class ClientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    is_blocked: Optional[bool] = None

class MasterUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    telegram_id: Optional[int] = None
    is_blocked: Optional[bool] = None

class BusinessRelation(BaseModel):
    business_id: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Время жизни в секундах