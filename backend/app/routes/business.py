from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.models.models import Business
from app.schemas.schemas import BusinessCreate, BusinessResponse

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.get("/", response_model=list[BusinessResponse])
async def list_businesses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Business))
    return result.scalars().all()


@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(business_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Business).where(Business.id == business_id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


@router.post("/", response_model=BusinessResponse, status_code=201)
async def create_business(payload: BusinessCreate, db: AsyncSession = Depends(get_db)):
    business = Business(name=payload.name, timezone=payload.timezone)
    db.add(business)
    await db.commit()
    await db.refresh(business)
    return business


@router.put("/{business_id}", response_model=BusinessResponse)
async def update_business(business_id: int, payload: BusinessCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Business).where(Business.id == business_id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    business.name = payload.name
    business.timezone = payload.timezone
    await db.commit()
    await db.refresh(business)
    return business


@router.delete("/{business_id}", status_code=204)
async def delete_business(business_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Business).where(Business.id == business_id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    await db.delete(business)
    await db.commit()