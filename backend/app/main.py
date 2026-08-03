"""
Точка входа FastAPI-приложения.
Настраивает lifespan, CORS-middleware и регистрирует все роутеры.
CORS-middleware должен быть добавлен ДО подключения роутеров,
иначе заголовки Access-Control-Allow-Origin не применяются.
"""

import sys
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import engine, Base
from app.routes import admin, business, clients, masters, orders, relations, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения: создание таблиц при старте."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Booking Core API",
    description="Backend для системы онлайн-записи",
    version="1.0.0",
    lifespan=lifespan,
)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router)
app.include_router(business.router)
app.include_router(clients.router)
app.include_router(masters.router)
app.include_router(orders.router)
app.include_router(relations.router)
app.include_router(dashboard.router)


@app.get("/")
async def root():
    """Health-check корневой эндпоинт."""
    return {"message": "Booking Core API is running"}


@app.get("/health")
async def health_check():
    """Эндпоинт проверки работоспособности сервиса."""
    return {"status": "healthy"}