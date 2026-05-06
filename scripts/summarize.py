"""
summarize.py — Runs at 12:30 on weekdays.
Collects final votes and sends the lunch summary.
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


if __name__ == "__main__":
    if not is_weekday():
        print("📅 Weekend — skipping.")
        sys.exit(0)

    sys.path.insert(0, os.path.dirname(__file__))
    from collect_votes import collect_votes

    state = load_state()
    if not state:
        print("⚠️  No state.json found.")
        sys.exit(0)

    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    if state.get("date") != today:
        print("⚠️  State is from a different day — skipping.")
        sys.exit(0)

    state = collect_votes(state)

    voters_in = state["voters_in"]
    count = len(voters_in)

    if count == 0:
        msg = "🍽️ *Lunch today: nobody signed up.* Enjoy your solo meal! 😄"
    elif count == 1:
        name = voters_in[0]["name"]
        msg = f"🍽️ *Lunch today: 1 person* — {name}\nEnjoy! 🥗"
    else:
        names = "\n".join(f"  • {v['name']}" for v in voters_in)
        msg = (
            f"🍽️ *Lunch today: {count} people eating!*\n\n"
            f"{names}\n\n"
            "Bon appétit! 🥘"
        )

    requests.post(
        f"{BASE_URL}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown",
        },
    )

    # Edit the original poll message to show voting is closed
    closed_text = (
        f"🍽️ *Lunch poll — closed*\n\n"
        f"Final count: *{count} eating* today.\n"
        "_Voting has closed._"
    )
    requests.post(
        f"{BASE_URL}/editMessageText",
        json={
            "chat_id": CHAT_ID,
            "message_id": state["message_id"],
            "text": closed_text,
            "parse_mode": "Markdown",
        },
    )

    print(f"✅ Summary sent — {count} people eating.")
