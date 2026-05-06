"""
lunch_ready.py — Polls for "🍽️ Lunch is ready!" keyboard button press.
Runs every 5 minutes via GitHub Actions.
"""

import os
import json
import requests
import sys

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
OFFSET_FILE = "lunchready_offset.json"


def load_offset():
    try:
        with open(OFFSET_FILE) as f:
            return json.load(f).get("offset", 0)
    except FileNotFoundError:
        return 0


def save_offset(offset):
    with open(OFFSET_FILE, "w") as f:
        json.dump({"offset": offset}, f)


def check_and_respond():
    offset = load_offset()
    triggered_by = None
    new_offset = offset

    while True:
        resp = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": new_offset, "timeout": 0, "limit": 100},
        )
        resp.raise_for_status()
        updates = resp.json().get("result", [])
        if not updates:
            break

        for update in updates:
            new_offset = update["update_id"] + 1
            msg = update.get("message", {})
            text = msg.get("text", "")
            chat_id = str(msg.get("chat", {}).get("id", ""))

            if text == "🍽️ Lunch is ready!" and chat_id == str(CHAT_ID):
                first = msg.get("from", {}).get("first_name", "Someone")
                triggered_by = first

    save_offset(new_offset)

    if triggered_by:
        requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": f"🔔 *LUNCH IS READY!* 🍽️\n\n_(called by {triggered_by})_\nCome and get it! 🏃",
                "parse_mode": "Markdown",
            },
        )
        print(f"✅ Lunch ready announced by {triggered_by}")
    else:
        print("No lunch ready signal.")


if __name__ == "__main__":
    check_and_respond()
