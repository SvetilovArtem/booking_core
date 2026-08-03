from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.models.models import Order, Slot, Client, Service
from app.schemas.schemas import OrderCreate, OrderUpdate, OrderResponse
from app.services.telegram import notify_master_order_created, notify_master_order_updated

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/", response_model=list[OrderResponse])
async def list_orders(
        business_id: int | None = None,
        master_id: int | None = None,
        client_id: int | None = None,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        db: AsyncSession = Depends(get_db)
):
    query = select(Order)

    if business_id:
        query = query.where(Order.business_id == business_id)
    if client_id:
        query = query.where(Order.client_id == client_id)
    if status:
        query = query.where(Order.status == status)
    if master_id:
        query = query.join(Slot, Order.slot_id == Slot.id).where(Slot.master_id == master_id)
    if date_from:
        query = query.join(Slot, Order.slot_id == Slot.id).where(Slot.date >= date_from)
    if date_to:
        query = query.join(Slot, Order.slot_id == Slot.id).where(Slot.date <= date_to)

    result = await db.execute(query.order_by(Order.created_at.desc()))
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/", response_model=OrderResponse, status_code=201)
async def create_order(payload: OrderCreate, db: AsyncSession = Depends(get_db)):
    slot_result = await db.execute(select(Slot).where(Slot.id == payload.slot_id))
    slot = slot_result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    if slot.status != "available":
        raise HTTPException(status_code=409, detail="Slot is not available")

    order = Order(
        client_id=payload.client_id,
        slot_id=payload.slot_id,
        service_id=payload.service_id,
        business_id=payload.business_id,
        status=payload.status,
        number=payload.number,
    )

    slot.status = "booked"
    db.add(order)
    await db.commit()
    await db.refresh(order)

    client_result = await db.execute(select(Client).where(Client.id == payload.client_id))
    client = client_result.scalar_one_or_none()
    service_result = await db.execute(select(Service).where(Service.id == payload.service_id))
    service = service_result.scalar_one_or_none()

    await notify_master_order_created(
        order.id,
        client.name if client else "Неизвестно",
        service.name if service else "Неизвестно",
        str(slot.date),
        f"{slot.start_time}-{slot.end_time}",
    )

    return order


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(order_id: int, payload: OrderUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    old_status = order.status

    if payload.status is not None:
        if payload.status == "cancelled" and order.slot:
            order.slot.status = "available"
        order.status = payload.status

    if payload.cancel_reason is not None:
        order.cancel_reason = payload.cancel_reason

    await db.commit()
    await db.refresh(order)

    if old_status != order.status or payload.cancel_reason:
        await notify_master_order_updated(order.id, order.status.value, payload.cancel_reason)

    return order


@router.delete("/{order_id}", status_code=204)
async def delete_order(order_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.slot:
        order.slot.status = "available"

    await db.delete(order)
    await db.commit()