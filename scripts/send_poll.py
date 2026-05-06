"""
send_poll.py — Runs at 9:00 AM on weekdays.
Sends the lunch poll with inline keyboard and saves state to state.json.
"""

import os
import json
import datetime
import requests
import sys

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def is_weekday():
    return datetime.datetime.utcnow().weekday() < 5  # 0=Mon, 4=Fri


def send_poll():
    today = datetime.datetime.utcnow().strftime("%A, %d %B")
    text = (
        f"🍽️ *Lunch today — {today}*\n\n"
        "Who's eating lunch with the team?\n"
        "Vote below 👇 (closes at 12:30)"
    )
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ I'm in!", "callback_data": "in"},
                {"text": "❌ Not today", "callback_data": "out"},
            ]
        ]
    }
    resp = requests.post(
        f"{BASE_URL}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": keyboard,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    message_id = data["result"]["message_id"]

    # Get current update_id offset so later scripts only read NEW updates
    updates_resp = requests.get(f"{BASE_URL}/getUpdates", params={"limit": 1, "offset": -1})
    updates_resp.raise_for_status()
    updates = updates_resp.json().get("result", [])
    offset = (updates[-1]["update_id"] + 1) if updates else 0

    state = {
        "message_id": message_id,
        "offset": offset,
        "date": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
        "voters_in": [],   # list of {"id": ..., "name": ...}
        "voters_out": [],
    }

    with open("state.json", "w") as f:
        json.dump(state, f, indent=2)

    print(f"✅ Poll sent (message_id={message_id}, offset={offset})")


if __name__ == "__main__":
    if not is_weekday():
        print("📅 Weekend — skipping.")
        sys.exit(0)
    send_poll()
