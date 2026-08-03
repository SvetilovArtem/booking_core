from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.models.models import Client
from app.schemas.schemas import ClientCreate, ClientResponse, ClientUpdate

router = APIRouter(prefix="/clients", tags=["clients"])


async def _check_telegram_unique(db: AsyncSession, telegram_id: int | None, exclude_id: int | None = None):
    if telegram_id is None:
        return
    query = select(Client).where(Client.telegram_id == telegram_id)
    if exclude_id:
        query = query.where(Client.id != exclude_id)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Клиент с таким telegram_id уже существует")


@router.get("/", response_model=list[ClientResponse])
async def list_clients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Client).order_by(Client.created_at.desc()))
    return result.scalars().all()


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.post("/", response_model=ClientResponse, status_code=201)
async def create_client(payload: ClientCreate, db: AsyncSession = Depends(get_db)):
    await _check_telegram_unique(db, payload.telegram_id)
    client = Client(name=payload.name, telegram_id=payload.telegram_id, phone=payload.phone)
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(client_id: int, payload: ClientCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    await _check_telegram_unique(db, payload.telegram_id, exclude_id=client_id)

    client.name = payload.name
    client.telegram_id = payload.telegram_id
    client.phone = payload.phone
    await db.commit()
    await db.refresh(client)
    return client


@router.patch("/{client_id}", response_model=ClientResponse)
async def patch_client(client_id: int, payload: ClientUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if payload.name is not None:
        client.name = payload.name
    if payload.phone is not None:
        client.phone = payload.phone
    if payload.is_blocked is not None:
        client.is_blocked = payload.is_blocked

    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
async def delete_client(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    await db.delete(client)
    await db.commit()