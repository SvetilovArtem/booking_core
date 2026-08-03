from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.database.session import get_db
from app.models.models import (
    Order, Client, Master, Service, Slot, Business, OrderStatus
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
        business_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        db: AsyncSession = Depends(get_db)
):
    """Возвращает агрегированную статистику для дашборда."""

    # Базовые запросы с фильтрацией
    order_query = select(Order)
    if business_id:
        order_query = order_query.where(Order.business_id == business_id)

    # Фильтр по датам (через Slot)
    if date_from:
        order_query = order_query.join(Slot).where(Slot.date >= date_from)
    if date_to:
        order_query = order_query.join(Slot).where(Slot.date <= date_to)

    # Общее количество записей
    total_orders_result = await db.execute(
        select(func.count(Order.id)).select_from(Order)
    )
    total_orders = total_orders_result.scalar() or 0

    # Записи сегодня
    today = date.today()
    orders_today_result = await db.execute(
        select(func.count(Order.id))
        .join(Slot)
        .where(Slot.date == today)
    )
    orders_today = orders_today_result.scalar() or 0

    # Записи за неделю
    week_ago = today - timedelta(days=7)
    orders_week_result = await db.execute(
        select(func.count(Order.id))
        .join(Slot)
        .where(Slot.date >= week_ago)
    )
    orders_week = orders_week_result.scalar() or 0

    # Записи за месяц
    month_ago = today - timedelta(days=30)
    orders_month_result = await db.execute(
        select(func.count(Order.id))
        .join(Slot)
        .where(Slot.date >= month_ago)
    )
    orders_month = orders_month_result.scalar() or 0

    # Статусы записей
    status_counts = {}
    for status in OrderStatus:
        result = await db.execute(
            select(func.count(Order.id)).where(Order.status == status)
        )
        status_counts[status.value] = result.scalar() or 0

    # Выручка (только completed заказы)
    revenue_result = await db.execute(
        select(func.coalesce(func.sum(Service.price), 0))
        .join(Order, Order.service_id == Service.id)
        .where(Order.status == OrderStatus.completed)
    )
    total_revenue = revenue_result.scalar() or 0

    # Выручка за месяц
    revenue_month_result = await db.execute(
        select(func.coalesce(func.sum(Service.price), 0))
        .join(Order, Order.service_id == Service.id)
        .join(Slot, Order.slot_id == Slot.id)
        .where(
            and_(
                Order.status == OrderStatus.completed,
                Slot.date >= month_ago
            )
        )
    )
    revenue_month = revenue_month_result.scalar() or 0

    # Общее количество сущностей
    clients_count = (await db.execute(select(func.count(Client.id)))).scalar() or 0
    masters_count = (await db.execute(select(func.count(Master.id)))).scalar() or 0
    services_count = (await db.execute(select(func.count(Service.id)))).scalar() or 0
    businesses_count = (await db.execute(select(func.count(Business.id)))).scalar() or 0

    return {
        "total_orders": total_orders,
        "orders_today": orders_today,
        "orders_week": orders_week,
        "orders_month": orders_month,
        "orders_by_status": status_counts,
        "total_revenue": total_revenue,
        "revenue_month": revenue_month,
        "total_clients": clients_count,
        "total_masters": masters_count,
        "total_services": services_count,
        "total_businesses": businesses_count,
    }


@router.get("/recent-orders")
async def get_recent_orders(
        business_id: int | None = None,
        limit: int = Query(10, ge=1, le=50),
        db: AsyncSession = Depends(get_db)
):
    """Последние записи с деталями."""
    query = (
        select(
            Order.id,
            Order.status,
            Order.number,
            Order.created_at,
            Client.name.label("client_name"),
            Master.name.label("master_name"),
            Service.name.label("service_name"),
            Service.price,
            Slot.date,
            Slot.start_time,
            Slot.end_time,
        )
        .join(Client, Order.client_id == Client.id)
        .join(Slot, Order.slot_id == Slot.id)
        .join(Master, Slot.master_id == Master.id)
        .join(Service, Order.service_id == Service.id)
        .order_by(Order.created_at.desc())
        .limit(limit)
    )

    if business_id:
        query = query.where(Order.business_id == business_id)

    result = await db.execute(query)
    orders = result.mappings().all()

    return [
        {
            "id": o["id"],
            "status": o["status"].value if hasattr(o["status"], 'value') else o["status"],
            "number": o["number"],
            "client_name": o["client_name"],
            "master_name": o["master_name"],
            "service_name": o["service_name"],
            "price": o["price"],
            "date": str(o["date"]),
            "start_time": str(o["start_time"]),
            "end_time": str(o["end_time"]),
            "created_at": o["created_at"].isoformat() if o["created_at"] else None,
        }
        for o in orders
    ]


@router.get("/master-performance")
async def get_master_performance(
        business_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = Query(10, ge=1, le=50),
        db: AsyncSession = Depends(get_db)
):
    """Производительность мастеров: количество записей и выручка."""
    query = (
        select(
            Master.id.label("master_id"),
            Master.name.label("master_name"),
            func.count(Order.id).label("orders_count"),
            func.coalesce(func.sum(Service.price), 0).label("revenue"),
        )
        .join(Slot, Master.id == Slot.master_id)
        .join(Order, Slot.id == Order.slot_id)
        .join(Service, Order.service_id == Service.id)
        .where(Order.status == OrderStatus.completed)
        .group_by(Master.id, Master.name)
        .order_by(func.count(Order.id).desc())
        .limit(limit)
    )

    if business_id:
        query = query.where(Order.business_id == business_id)
    if date_from:
        query = query.where(Slot.date >= date_from)
    if date_to:
        query = query.where(Slot.date <= date_to)

    result = await db.execute(query)
    masters = result.mappings().all()

    return [
        {
            "master_id": m["master_id"],
            "master_name": m["master_name"],
            "orders_count": m["orders_count"],
            "revenue": m["revenue"],
        }
        for m in masters
    ]


@router.get("/businesses")
async def get_businesses(db: AsyncSession = Depends(get_db)):
    """Список салонов для селектора в дашборде."""
    result = await db.execute(select(Business).where(Business.is_active == True))
    businesses = result.scalars().all()
    return [{"id": b.id, "name": b.name} for b in businesses]