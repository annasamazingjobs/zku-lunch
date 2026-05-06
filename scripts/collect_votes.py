"""
collect_votes.py — Shared helper.
Reads callback_query updates since the poll was sent and updates state.json.
"""

import os
import json
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def collect_votes(state: dict) -> dict:
    offset = state.get("offset", 0)
    voters_in = {v["id"]: v for v in state.get("voters_in", [])}
    voters_out = {v["id"]: v for v in state.get("voters_out", [])}

    while True:
        resp = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 0, "limit": 100},
        )
        resp.raise_for_status()
        updates = resp.json().get("result", [])
        if not updates:
            break

        for update in updates:
            offset = update["update_id"] + 1
            cq = update.get("callback_query")
            if not cq:
                continue

            user = cq["from"]
            uid = user["id"]
            first = user.get("first_name", "")
            last = user.get("last_name", "")
            name = f"{first} {last}".strip() or f"User{uid}"
            vote = cq.get("data")

            # Answer the callback so Telegram stops showing the loading spinner
            requests.post(
                f"{BASE_URL}/answerCallbackQuery",
                json={"callback_query_id": cq["id"], "text": "Got it! 👍"},
            )

            if vote == "in":
                voters_in[uid] = {"id": uid, "name": name}
                voters_out.pop(uid, None)
            elif vote == "out":
                voters_out[uid] = {"id": uid, "name": name}
                voters_in.pop(uid, None)

    state["offset"] = offset
    state["voters_in"] = list(voters_in.values())
    state["voters_out"] = list(voters_out.values())
    return state
