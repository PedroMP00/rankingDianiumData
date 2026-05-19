#!/usr/bin/env python3
"""
Telegram bot notifications for ranking updates.
Sends status updates about pipeline execution.
"""

import os
import sys
import json
from datetime import datetime
import requests


def send_telegram_message(token: str, chat_id: str, message: str) -> bool:
    """
    Send message to Telegram chat.

    Args:
        token: Telegram bot token (from GitHub Secrets)
        chat_id: Telegram chat ID
        message: Message text (supports markdown)

    Returns:
        True if successful, False otherwise
    """
    if not token or not chat_id:
        print("⚠️  Telegram token or chat_id not configured. Skipping notification.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ Telegram notification sent")
        return True
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {str(e)}")
        return False


def notify_success(token: str, chat_id: str, records: int, compiled_records: int):
    """Notify successful pipeline completion."""
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M UTC")
    message = f"""
<b>✅ Atletisme Dianium Rankings Updated</b>

<b>Timestamp:</b> {timestamp}
<b>Records processed:</b> {records}
<b>Total compiled:</b> {compiled_records}

<i>Data is available at GitHub Pages</i>
"""
    return send_telegram_message(token, chat_id, message.strip())


def notify_failure(token: str, chat_id: str, error: str):
    """Notify pipeline failure."""
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M UTC")
    message = f"""
<b>❌ Atletisme Dianium Rankings Update Failed</b>

<b>Timestamp:</b> {timestamp}
<b>Error:</b> <code>{error[:200]}</code>

Check GitHub Actions for details.
"""
    return send_telegram_message(token, chat_id, message.strip())


if __name__ == "__main__":
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if len(sys.argv) > 1 and sys.argv[1] == "success":
        records = sys.argv[2] if len(sys.argv) > 2 else "0"
        compiled = sys.argv[3] if len(sys.argv) > 3 else "0"
        notify_success(token, chat_id, records, compiled)
    elif len(sys.argv) > 1 and sys.argv[1] == "failure":
        error = sys.argv[2] if len(sys.argv) > 2 else "Unknown error"
        notify_failure(token, chat_id, error)
    else:
        print("Usage: telegram_bot.py {success|failure} [args...]")
        sys.exit(1)