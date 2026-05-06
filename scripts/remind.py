"""
remind.py — Runs at 12:15 on weekdays.
Collects votes so far; sends a reminder if nobody has voted yet.
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
    return datetime.datetime.utcnow().weekday() < 5


def load_state():
    try:
        with open("state.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def save_state(state):
    with open("state.json", "w") as f:
        json.dump(state, f, indent=2)


if __name__ == "__main__":
    if not is_weekday():
        print("📅 Weekend — skipping.")
        sys.exit(0)

    # Import here so the file is found at runtime
    sys.path.insert(0, os.path.dirname(__file__))
    from collect_votes import collect_votes

    state = load_state()
    if not state:
        print("⚠️  No state.json found — poll may not have been sent today.")
        sys.exit(0)

    # Check it's today's poll
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    if state.get("date") != today:
        print("⚠️  State is from a different day — skipping.")
        sys.exit(0)

    state = collect_votes(state)
    save_state(state)

    count_in = len(state["voters_in"])
    if count_in == 0:
names_in = ", ".join(v["name"] for v in state["voters_in"]) or "nobody yet"
    msg = (
        f"⏰ *Lunch reminder!*\n\n"
        f"{count_in} people eating so far: {names_in}\n\n"
        "Last chance to vote before 12:30! 👆"
    )
    requests.post(
        f"{BASE_URL}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown",
            "reply_to_message_id": state["message_id"],
        },
    )
    print(f"⏰ Reminder sent — {count_in} people in so far.")
