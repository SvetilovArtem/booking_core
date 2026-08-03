"""Роуты для управления мастерами. Создание с привязкой услуг и салонов в одной транзакции."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError

from app.database.session import get_db
from app.models.models import Master, ServiceMaster, master_business_association
from app.schemas.schemas import MasterCreate, MasterResponse, MasterUpdate

router = APIRouter(prefix="/masters", tags=["masters"])


async def _check_master_unique(
    db: AsyncSession, telegram_id: int, exclude_id: int | None = None
):
    """Проверяет уникальность telegram_id."""
    query = select(Master).where(Master.telegram_id == telegram_id)
    if exclude_id:
        query = query.where(Master.id != exclude_id)
    if (await db.execute(query)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Мастер с таким Telegram ID уже существует")


def _serialize_master(master: Master, service_ids: list[int], business_ids: list[int]) -> dict:
    """Сериализует мастера с добавленными связями."""
    return {
        "id": master.id,
        "name": master.name,
        "phone": master.phone,
        "telegram_id": master.telegram_id,
        "is_blocked": master.is_blocked,
        "created_at": master.created_at,
        "service_ids": service_ids,
        "business_ids": business_ids,
    }


@router.get("/", response_model=list[MasterResponse])
async def list_masters(db: AsyncSession = Depends(get_db)):
    """Получить список всех мастеров с их связями."""
    result = await db.execute(select(Master).order_by(Master.created_at.desc()))
    masters = result.scalars().all()

    if not masters:
        return []

    master_ids = [m.id for m in masters]

    # Загружаем все связи одним запросом
    sm_result = await db.execute(
        select(ServiceMaster.master_id, ServiceMaster.service_id)
        .where(ServiceMaster.master_id.in_(master_ids))
    )
    mb_result = await db.execute(
        select(master_business_association.c.master_id, master_business_association.c.business_id)
        .where(master_business_association.c.master_id.in_(master_ids))
    )

    # Группируем по master_id
    services_map: dict[int, list[int]] = {}
    for mid, sid in sm_result.all():
        services_map.setdefault(mid, []).append(sid)

    businesses_map: dict[int, list[int]] = {}
    for mid, bid in mb_result.all():
        businesses_map.setdefault(mid, []).append(bid)

    return [
        _serialize_master(m, services_map.get(m.id, []), businesses_map.get(m.id, []))
        for m in masters
    ]


@router.post("/", response_model=MasterResponse, status_code=201)
async def create_master(payload: MasterCreate, db: AsyncSession = Depends(get_db)):
    """Создать мастера с привязкой услуг и салонов в одной транзакции."""
    await _check_master_unique(db, payload.telegram_id)

    master = Master(
        name=payload.name.strip(),
        phone=payload.phone,
        telegram_id=payload.telegram_id,
    )
    db.add(master)
    await db.flush()  # Получаем master.id без коммита

    # Создаём связи с услугами
    for service_id in payload.service_ids:
        db.add(ServiceMaster(master_id=master.id, service_id=service_id))

    # Создаём связи с салонами
    for business_id in payload.business_ids:
        await db.execute(
            master_business_association.insert().values(
                master_id=master.id, business_id=business_id
            )
        )

    try:
        await db.commit()
        await db.refresh(master)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Ошибка создания: конфликт данных")

    return _serialize_master(master, payload.service_ids, payload.business_ids)


@router.patch("/{master_id}", response_model=MasterResponse)
async def patch_master(master_id: int, payload: MasterCreate, db: AsyncSession = Depends(get_db)):
    """Частичное обновление мастера с синхронизацией связей."""
    master = await db.get(Master, master_id)
    if not master:
        raise HTTPException(status_code=404, detail="Мастер не найден")

    if payload.telegram_id != master.telegram_id:
        await _check_master_unique(db, payload.telegram_id, exclude_id=master_id)

    # Обновляем базовые поля
    master.name = payload.name.strip()
    master.phone = payload.phone
    master.telegram_id = payload.telegram_id

    # Синхронизируем услуги: удаляем старые, добавляем новые
    await db.execute(
        delete(ServiceMaster).where(ServiceMaster.master_id == master_id)
    )
    for service_id in payload.service_ids:
        db.add(ServiceMaster(master_id=master_id, service_id=service_id))

    # Синхронизируем салоны: удаляем старые, добавляем новые
    await db.execute(
        delete(master_business_association).where(
            master_business_association.c.master_id == master_id
        )
    )
    for business_id in payload.business_ids:
        await db.execute(
            master_business_association.insert().values(
                master_id=master_id, business_id=business_id
            )
        )

    try:
        await db.commit()
        await db.refresh(master)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Ошибка обновления: конфликт данных")

    return _serialize_master(master, payload.service_ids, payload.business_ids)

    master = await db.get(Master, master_id)
    if not master:
        raise HTTPException(status_code=404, detail="Мастер не найден")

    if payload.telegram_id is not None and payload.telegram_id != master.telegram_id:
        await _check_master_unique(db, payload.telegram_id, exclude_id=master_id)

    if payload.name is not None:
        master.name = payload.name.strip()
    if payload.phone is not None:
        master.phone = payload.phone
    if payload.telegram_id is not None:
        master.telegram_id = payload.telegram_id
    if payload.is_blocked is not None:
        master.is_blocked = payload.is_blocked

    await db.commit()
    await db.refresh(master)

    # Загружаем текущие связи для ответа
    sm_result = await db.execute(
        select(ServiceMaster.service_id).where(ServiceMaster.master_id == master_id)
    )
    mb_result = await db.execute(
        select(master_business_association.c.business_id)
        .where(master_business_association.c.master_id == master_id)
    )

    return _serialize_master(
        master,
        [row[0] for row in sm_result.all()],
        [row[0] for row in mb_result.all()],
    )


@router.delete("/{master_id}", status_code=204)
async def delete_master(master_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить мастера и все его связи."""
    master = await db.get(Master, master_id)
    if not master:
        raise HTTPException(status_code=404, detail="Мастер не найден")
    await db.delete(master)
    await db.commit()