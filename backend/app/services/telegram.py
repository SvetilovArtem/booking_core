import os
import logging
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
logger = logging.getLogger(__name__)


async def send_telegram_message(chat_id: int, text: str) -> bool:
    """Отправляет сообщение в Telegram. Возвращает True при успехе."""
    if not BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN не настроен, уведомление пропущено")
        return False

    import httpx
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Ошибка отправки Telegram: {e}")
        return False


async def notify_master_slots_created(telegram_id: int | None, master_name: str, slots_count: int, date: str):
    """Уведомление мастеру о создании слотов."""
    if not telegram_id:
        return

    text = (
        f" <b>Новые слоты</b>\n\n"
        f"Мастер: {master_name}\n"
        f"Дата: {date}\n"
        f"Количество слотов: {slots_count}"
    )
    await send_telegram_message(telegram_id, text)


async def notify_master_order_created(
    telegram_id: int | None,
    order_id: int,
    client_name: str,
    service_name: str,
    slot_date: str,
    slot_time: str
):
    """Уведомление мастеру о новой заявке."""
    if not telegram_id:
        return

    text = (
        f"🔔 <b>Новая заявка #{order_id}</b>\n\n"
        f"Клиент: {client_name}\n"
        f"Услуга: {service_name}\n"
        f"Дата: {slot_date}\n"
        f"Время: {slot_time}"
    )
    await send_telegram_message(telegram_id, text)


async def notify_master_order_updated(
    telegram_id: int | None,
    order_id: int,
    status: str,
    cancel_reason: str | None = None
):
    """Уведомление мастеру об изменении заявки."""
    if not telegram_id:
        return

    status_map = {
        "pending": "⏳ Ожидает подтверждения",
        "confirmed": "✅ Подтверждена",
        "cancelled": "❌ Отменена",
        "completed": "✔️ Завершена",
        "no_show": " Клиент не пришел",
    }
    status_text = status_map.get(status, status)

    text = f"🔄 <b>Заявка #{order_id} изменена</b>\n\nНовый статус: {status_text}"
    if cancel_reason:
        text += f"\nПричина: {cancel_reason}"

    await send_telegram_message(telegram_id, text)