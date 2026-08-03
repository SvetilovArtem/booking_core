from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.models.models import Master
from app.schemas.schemas import MasterCreate, MasterResponse

router = APIRouter(prefix="/masters", tags=["masters"])


@router.get("/", response_model=list[MasterResponse])
async def list_masters(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Master))
    return result.scalars().all()


@router.get("/{master_id}", response_model=MasterResponse)
async def get_master(master_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Master).where(Master.id == master_id))
    master = result.scalar_one_or_none()
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")
    return master


@router.post("/", response_model=MasterResponse, status_code=201)
async def create_master(payload: MasterCreate, db: AsyncSession = Depends(get_db)):
    master = Master(name=payload.name, phone=payload.phone, telegram_id=payload.telegram_id)
    db.add(master)
    await db.commit()
    await db.refresh(master)
    return master


@router.put("/{master_id}", response_model=MasterResponse)
async def update_master(master_id: int, payload: MasterCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Master).where(Master.id == master_id))
    master = result.scalar_one_or_none()
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")
    master.name = payload.name
    master.phone = payload.phone
    master.telegram_id = payload.telegram_id
    await db.commit()
    await db.refresh(master)
    return master


@router.delete("/{master_id}", status_code=204)
async def delete_master(master_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Master).where(Master.id == master_id))
    master = result.scalar_one_or_none()
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")
    await db.delete(master)
    await db.commit()