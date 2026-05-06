"""
send_poll.py — Runs at 9:00 AM on weekdays.
Sends a native Telegram poll and saves state to state.json.
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
    return datetime.datetime.now(datetime.UTC).weekday() < 5


def send_poll():
    today = datetime.datetime.now(datetime.UTC).strftime("%A, %d %B")

    resp = requests.post(
        f"{BASE_URL}/sendPoll",
        json={
            "chat_id": CHAT_ID,
            "question": f"🍽️ Lunch today — {today}?",
            "options": ["✅ I'm in!", "❌ Not today"],
            "is_anonymous": False,   # so we can see who voted
            "allows_multiple_answers": False,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    message_id = data["result"]["message_id"]
    poll_id = data["result"]["poll"]["id"]

    # Get current offset so later scripts only read NEW updates
    updates_resp = requests.get(f"{BASE_URL}/getUpdates", params={"limit": 1, "offset": -1})
    updates_resp.raise_for_status()
    updates = updates_resp.json().get("result", [])
    offset = (updates[-1]["update_id"] + 1) if updates else 0

    state = {
        "message_id": message_id,
        "poll_id": poll_id,
        "offset": offset,
        "date": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d"),
        "voters_in": [],
        "voters_out": [],
    }

    with open("state.json", "w") as f:
        json.dump(state, f, indent=2)

    # Show persistent reply keyboard
    requests.post(
        f"{BASE_URL}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": "🔔 Tap the button below when lunch is ready!",
            "reply_markup": {
                "keyboard": [[{"text": "🍽️ Lunch is ready!"}]],
                "resize_keyboard": True,
                "persistent": True,
            },
        },
    )

    print(f"✅ Poll sent (message_id={message_id}, poll_id={poll_id}, offset={offset})")

if __name__ == "__main__":
    if not is_weekday():
        print("📅 Weekend — skipping.")
        sys.exit(0)
    send_poll()
