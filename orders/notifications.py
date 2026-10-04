"""Telegram notification for new orders.

Works as soon as TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set in the
environment. Without them it only logs, and the order is still saved and
visible in the Wagtail admin under "Заявки".

To get a chat id: create a bot with @BotFather, send it any message,
then open https://api.telegram.org/bot<TOKEN>/getUpdates and read chat.id.
"""
import json
import logging
import urllib.request
from html import escape

from django.conf import settings

logger = logging.getLogger(__name__)


def format_order(order):
    lines = [
        f"<b>Новая заявка #{order.pk}</b>",
        f"{escape(order.product_title)} — {order.price:,} ₽".replace(",", " "),
    ]
    if order.size:
        lines.append(f"Размер: {escape(order.size)}")
    lines.append(f"Имя: {escape(order.name)}")
    lines.append(f"Контакт: {escape(order.contact)}")
    if order.comment:
        lines.append(f"Комментарий: {escape(order.comment)}")
    return "\n".join(lines)


def notify_new_order(order):
    token, chat_id = settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID
    text = format_order(order)
    if not (token and chat_id):
        logger.info("Telegram not configured. Order:\n%s", text)
        return
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload, headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        # Never break the customer's request because Telegram is down.
        logger.exception("Could not send Telegram notification for order %s", order.pk)
