"""Роуты для управления слотами. Одиночное/массовое создание + статистика по дням."""

from datetime import date, time, timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel, Field

from app.database.session import get_db
from app.models.models import Slot, SlotStatus

router = APIRouter(prefix="/slots", tags=["slots"])


class SlotCreate(BaseModel):
    master_id: int
    business_id: int
    date: date
    start_time: time
    end_time: time


class SlotBulkCreate(BaseModel):
    """Массовое создание слотов: один мастер, один салон, диапазон дат, список времён."""
    master_id: int
    business_id: int
    date_from: date
    date_to: date
    times: list[str] = Field(description="Список времён начала в формате HH:MM")
    duration_minutes: int = Field(default=60, ge=15, le=480)


class DayStats(BaseModel):
    date: str
    available: int
    booked: int
    total: int


@router.get("/stats")
async def get_slots_stats(
    master_id: int | None = None,
    business_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Статистика слотов по дням для календаря."""
    query = (
        select(
            Slot.date,
            Slot.status,
            func.count(Slot.id).label("cnt"),
        )
        .group_by(Slot.date, Slot.status)
        .order_by(Slot.date)
    )

    if master_id:
        query = query.where(Slot.master_id == master_id)
    if business_id:
        query = query.where(Slot.business_id == business_id)
    if date_from:
        query = query.where(Slot.date >= date_from)
    if date_to:
        query = query.where(Slot.date <= date_to)

    result = await db.execute(query)
    rows = result.all()

    stats_map: dict[str, dict] = {}
    for row_date, status, cnt in rows:
        key = str(row_date)
        if key not in stats_map:
            stats_map[key] = {"date": key, "available": 0, "booked": 0, "total": 0}
        stats_map[key]["total"] += cnt
        if status == SlotStatus.available:
            stats_map[key]["available"] += cnt
        elif status in (SlotStatus.booked, SlotStatus.blocked):
            stats_map[key]["booked"] += cnt

    return list(stats_map.values())


@router.post("/bulk", status_code=201)
async def create_slots_bulk(payload: SlotBulkCreate, db: AsyncSession = Depends(get_db)):
    """Массовое создание слотов. Проверяет пересечения только для того же мастера."""
    created_count = 0
    skipped_count = 0
    current_date = payload.date_from

    while current_date <= payload.date_to:
        for start_str in payload.times:
            h, m = map(int, start_str.split(":"))
            start_t = time(h, m)
            end_minutes = h * 60 + m + payload.duration_minutes
            if end_minutes >= 24 * 60:
                skipped_count += 1
                continue
            end_t = time(end_minutes // 60, end_minutes % 60)

            # Пересечение: existing.start < new.end AND existing.end > new.start
            overlap = await db.execute(
                select(Slot).where(
                    and_(
                        Slot.master_id == payload.master_id,
                        Slot.date == current_date,
                        Slot.start_time < end_t,
                        Slot.end_time > start_t,
                    )
                )
            )
            if overlap.scalar_one_or_none():
                skipped_count += 1
                continue

            slot = Slot(
                master_id=payload.master_id,
                business_id=payload.business_id,
                date=current_date,
                start_time=start_t,
                end_time=end_t,
                status=SlotStatus.available,
            )
            db.add(slot)
            created_count += 1

        current_date += timedelta(days=1)

    today = date.today()
    now_time = datetime.now().time()

    while current_date <= payload.date_to:
        if current_date < today:
            current_date += timedelta(days=1)
            continue

        for start_str in payload.times:
            h, m = map(int, start_str.split(":"))
            start_t = time(h, m)
            end_minutes = h * 60 + m + payload.duration_minutes
            if end_minutes >= 24 * 60:
                skipped_count += 1
                continue
            end_t = time(end_minutes // 60, end_minutes % 60)

            # Пропускаем слоты в текущем дне, которые уже начались
            if current_date == today and start_t < now_time:
                skipped_count += 1
                continue
    await db.commit()
    return {"created": created_count, "skipped": skipped_count}


@router.get("/", response_model=list[dict])
async def list_slots(
    master_id: int | None = None,
    business_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Список слотов с фильтрами."""
    query = select(Slot).order_by(Slot.date, Slot.start_time)
    if master_id:
        query = query.where(Slot.master_id == master_id)
    if business_id:
        query = query.where(Slot.business_id == business_id)
    if date_from:
        query = query.where(Slot.date >= date_from)
    if date_to:
        query = query.where(Slot.date <= date_to)

    result = await db.execute(query)
    slots = result.scalars().all()
    return [
        {
            "id": s.id,
            "master_id": s.master_id,
            "business_id": s.business_id,
            "date": str(s.date),
            "start_time": str(s.start_time),
            "end_time": str(s.end_time),
            "status": s.status.value if hasattr(s.status, "value") else s.status,
        }
        for s in slots
    ]

@router.get("/day")
async def get_day_slots(
    date: str,
    master_id: int | None = None,
    business_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Все слоты за конкретный день для модального окна."""
    query = select(Slot).where(Slot.date == date).order_by(Slot.start_time)
    if master_id:
        query = query.where(Slot.master_id == master_id)
    if business_id:
        query = query.where(Slot.business_id == business_id)

    result = await db.execute(query)
    slots = result.scalars().all()
    return [
        {
            "id": s.id,
            "master_id": s.master_id,
            "start_time": str(s.start_time),
            "end_time": str(s.end_time),
            "status": s.status.value if hasattr(s.status, "value") else s.status,
        }
        for s in slots
    ]

@router.delete("/{slot_id}", status_code=204)
async def delete_slot(slot_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить слот."""
    slot = await db.get(Slot, slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Слот не найден")
    await db.delete(slot)
    await db.commit()