from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.database.session import get_db
from app.models.models import Admin
from app.schemas.schemas import (
    AdminCreate,
    AdminResponse,
    AdminLogin,
    TokenResponse,
    AdminUpdate,
)
from app.services.auth import (
    get_password_hash,
    verify_password,
    create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/admins", tags=["admins"])


async def _check_admin_unique(
        db: AsyncSession,
        name: str,
        telegram_id: int | None,
        exclude_id: int | None = None,
):
    """Проверяет уникальность логина и telegram_id."""
    # Проверка имени (без учета регистра)
    normalized_name = name.strip().lower()
    query_name = select(Admin).where(func.lower(func.trim(Admin.name)) == normalized_name)
    if exclude_id:
        query_name = query_name.where(Admin.id != exclude_id)

    if (await db.execute(query_name)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Админ с таким логином уже существует")

    # Проверка telegram_id
    if telegram_id is not None:
        query_tg = select(Admin).where(Admin.telegram_id == telegram_id)
        if exclude_id:
            query_tg = query_tg.where(Admin.id != exclude_id)
        if (await db.execute(query_tg)).scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Админ с таким Telegram ID уже существует")


@router.get("/", response_model=list[AdminResponse])
async def list_admins(db: AsyncSession = Depends(get_db)):
    """Получить список всех администраторов."""
    result = await db.execute(select(Admin).order_by(Admin.created_at.desc()))
    return result.scalars().all()


@router.get("/{admin_id}", response_model=AdminResponse)
async def get_admin(admin_id: int, db: AsyncSession = Depends(get_db)):
    """Получить одного администратора по ID."""
    admin = await db.get(Admin, admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Администратор не найден")
    return admin


@router.post("/register", response_model=AdminResponse, status_code=201)
async def register_admin(payload: AdminCreate, db: AsyncSession = Depends(get_db)):
    """Регистрация нового администратора."""
    await _check_admin_unique(db, payload.name, payload.telegram_id)

    admin = Admin(
        name=payload.name.strip(),
        phone=payload.phone,
        telegram_id=payload.telegram_id,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(admin)

    try:
        await db.commit()
        await db.refresh(admin)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Ошибка создания: конфликт данных")

    return admin


@router.post("/login", response_model=TokenResponse)
async def login_admin(payload: AdminLogin, db: AsyncSession = Depends(get_db)):
    """Авторизация администратора (возвращает JWT)."""
    result = await db.execute(select(Admin).where(Admin.name == payload.name))
    admin = result.scalar_one_or_none()

    if not admin or not verify_password(payload.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Неверное имя или пароль")

    token = create_access_token(data={"sub": admin.id, "name": admin.name})

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Конвертируем минуты в секунды
    }


@router.put("/{admin_id}", response_model=AdminResponse)
async def update_admin(
        admin_id: int,
        payload: AdminCreate,
        db: AsyncSession = Depends(get_db)
):
    """Полное обновление администратора."""
    admin = await db.get(Admin, admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Администратор не найден")

    await _check_admin_unique(db, payload.name, payload.telegram_id, exclude_id=admin_id)

    admin.name = payload.name.strip()
    admin.phone = payload.phone
    admin.telegram_id = payload.telegram_id
    admin.hashed_password = get_password_hash(payload.password)

    await db.commit()
    await db.refresh(admin)
    return admin


@router.patch("/{admin_id}", response_model=AdminResponse)
async def patch_admin(
        admin_id: int,
        payload: AdminUpdate,
        db: AsyncSession = Depends(get_db)
):
    """Частичное обновление администратора."""
    admin = await db.get(Admin, admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Администратор не найден")

    # Проверка уникальности при изменении
    await _check_admin_unique(
        db,
        name=payload.name if payload.name is not None else admin.name,
        telegram_id=payload.telegram_id if payload.telegram_id is not None else admin.telegram_id,
        exclude_id=admin_id,
    )

    if payload.name is not None:
        admin.name = payload.name.strip()
    if payload.phone is not None:
        admin.phone = payload.phone
    if payload.telegram_id is not None:
        admin.telegram_id = payload.telegram_id
    if payload.password is not None:
        admin.hashed_password = get_password_hash(payload.password)

    await db.commit()
    await db.refresh(admin)
    return admin


@router.delete("/{admin_id}", status_code=204)
async def delete_admin(admin_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить администратора."""
    admin = await db.get(Admin, admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Администратор не найден")

    # Защита: нельзя удалить, если это последний админ
    count_result = await db.execute(select(func.count(Admin.id)))
    admins_count = count_result.scalar()
    if admins_count <= 1:
        raise HTTPException(
            status_code=409,
            detail="Нельзя удалить последнего администратора в системе"
        )

    await db.delete(admin)
    await db.commit()