from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database.session import get_db
from app.models.models import Master, Admin, Business, master_business_association, admin_business_association
from app.schemas.schemas import BusinessRelation

router = APIRouter(prefix="/relations", tags=["relations"])

# --- MASTER <-> BUSINESS ---
@router.post("/masters/{master_id}/businesses")
async def assign_master_to_business(
    master_id: int,
    payload: BusinessRelation,
    db: AsyncSession = Depends(get_db)
):
    # Проверка существования
    master = await db.get(Master, master_id)
    business = await db.get(Business, payload.business_id)
    if not master or not business:
        raise HTTPException(status_code=404, detail="Master or Business not found")

    # Проверяем, нет ли уже связи
    stmt = select(master_business_association).where(
        master_business_association.c.master_id == master_id,
        master_business_association.c.business_id == payload.business_id
    )
    result = await db.execute(stmt)
    if result.first():
        raise HTTPException(status_code=409, detail="Master already assigned to this business")

    await db.execute(master_business_association.insert().values(master_id=master_id, business_id=payload.business_id))
    await db.commit()
    return {"message": "Master assigned"}

@router.delete("/masters/{master_id}/businesses/{business_id}")
async def remove_master_from_business(
    master_id: int, business_id: int, db: AsyncSession = Depends(get_db)
):
    stmt = delete(master_business_association).where(
        master_business_association.c.master_id == master_id,
        master_business_association.c.business_id == business_id
    )
    await db.execute(stmt)
    await db.commit()
    return {"message": "Master removed from business"}


# --- ADMIN <-> BUSINESS ---
@router.post("/admins/{admin_id}/businesses")
async def assign_admin_to_business(
    admin_id: int,
    payload: BusinessRelation,
    db: AsyncSession = Depends(get_db)
):
    admin = await db.get(Admin, admin_id)
    business = await db.get(Business, payload.business_id)
    if not admin or not business:
        raise HTTPException(status_code=404, detail="Admin or Business not found")

    stmt = select(admin_business_association).where(
        admin_business_association.c.admin_id == admin_id,
        admin_business_association.c.business_id == payload.business_id
    )
    result = await db.execute(stmt)
    if result.first():
        raise HTTPException(status_code=409, detail="Admin already assigned to this business")

    await db.execute(admin_business_association.insert().values(admin_id=admin_id, business_id=payload.business_id))
    await db.commit()
    return {"message": "Admin assigned"}

@router.delete("/admins/{admin_id}/businesses/{business_id}")
async def remove_admin_from_business(
    admin_id: int, business_id: int, db: AsyncSession = Depends(get_db)
):
    stmt = delete(admin_business_association).where(
        admin_business_association.c.admin_id == admin_id,
        admin_business_association.c.business_id == business_id
    )
    await db.execute(stmt)
    await db.commit()
    return {"message": "Admin removed from business"}