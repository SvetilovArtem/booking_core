"""Роуты для управления услугами. CRUD + проверка уникальности названия."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.database.session import get_db
from app.models.models import Service
from app.schemas.schemas import ServiceCreate, ServiceResponse

router = APIRouter(prefix="/services", tags=["services"])


async def _check_service_name_unique(
    db: AsyncSession, name: str, exclude_id: int | None = None
):
    """Проверяет уникальность названия услуги без учёта регистра."""
    normalized = name.strip().lower()
    query = select(Service).where(func.lower(func.trim(Service.name)) == normalized)
    if exclude_id:
        query = query.where(Service.id != exclude_id)
    if (await db.execute(query)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Услуга с таким названием уже существует")


@router.get("/", response_model=list[ServiceResponse])
async def list_services(db: AsyncSession = Depends(get_db)):
    """Получить список всех услуг."""
    result = await db.execute(select(Service).order_by(Service.name))
    return result.scalars().all()


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: int, db: AsyncSession = Depends(get_db)):
    """Получить одну услугу по ID."""
    service = await db.get(Service, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return service


@router.post("/", response_model=ServiceResponse, status_code=201)
async def create_service(payload: ServiceCreate, db: AsyncSession = Depends(get_db)):
    """Создать новую услугу."""
    await _check_service_name_unique(db, payload.name)
    service = Service(name=payload.name.strip(), price=payload.price)
    db.add(service)
    try:
        await db.commit()
        await db.refresh(service)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Ошибка создания: конфликт данных")
    return service


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: int, payload: ServiceCreate, db: AsyncSession = Depends(get_db)
):
    """Полное обновление услуги."""
    service = await db.get(Service, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    await _check_service_name_unique(db, payload.name, exclude_id=service_id)
    service.name = payload.name.strip()
    service.price = payload.price
    await db.commit()
    await db.refresh(service)
    return service


@router.delete("/{service_id}", status_code=204)
async def delete_service(service_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить услугу."""
    service = await db.get(Service, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    await db.delete(service)
    await db.commit()