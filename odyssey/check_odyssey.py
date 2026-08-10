#!/usr/bin/env python3
"""Watch Cinema City Flora for Odyssey IMAX 70 mm screenings."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
STATE_FILE = BASE_DIR / "known_dates.json"

CINEMA_ID = "1052"
MOVIE_ID = "7268s2r"
START_DATE = date(2026, 8, 20)
END_DATE = date(2026, 9, 15)

SLACK_USER_ID = os.getenv("SLACK_USER_ID", "U027888MD19")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "").strip()
DRY_RUN = os.getenv("ODYSSEY_DRY_RUN", "").lower() in {"1", "true", "yes"}

API_TEMPLATE = (
    "https://www.cinemacity.cz/cz/data-api-service/v1/"
    "quickbook/10101/film-events/in-cinema/"
    f"{CINEMA_ID}/at-date/{{date}}?attr=&lang=en_GB"
)

TARGET_DATES = {
    "2026-09-14": {"priority": 1, "preferred_time": "20:00"},
    "2026-09-11": {"priority": 2, "preferred_time": "20:00"},
}

# Ratios manually verified against the Cinema City seat map. Unknown ratios are
# deliberately reported as unknown rather than guessed.
KNOWN_SEAT_COUNTS = {
    0.0156: 0,
    0.0234: 2,
    0.0286: 2,
}


def log(message: str) -> None:
    timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"[{timestamp}] {message}", flush=True)


def default_state() -> dict[str, Any]:
    return {
        "seen_events": [],
        "seen_dates": [],
        "latest_date": None,
        "target_notifications": [],
    }


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return default_state()
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read {STATE_FILE}: {exc}") from exc


def save_state(state: dict[str, Any]) -> None:
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def slack_api(method: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not SLACK_BOT_TOKEN:
        raise RuntimeError("SLACK_BOT_TOKEN is not configured")

    request = urllib.request.Request(
        f"https://slack.com/api/{method}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        result = json.loads(response.read().decode("utf-8"))

    if not result.get("ok"):
        raise RuntimeError(f"Slack {method} failed: {result.get('error', 'unknown_error')}")
    return result


def notify(title: str, message: str, booking_url: str | None = None) -> None:
    text = f"*{title}*\n{message}"
    if booking_url:
        text += f"\n<{booking_url}|Open Cinema City booking>"

    if DRY_RUN:
        log(f"DRY RUN Slack message:\n{text}")
        return

    slack_api("chat.postMessage", {"channel": SLACK_USER_ID, "text": text})
    log(f"Slack notification sent to {SLACK_USER_ID}.")


def fetch_date(check_date: date) -> dict[str, Any]:
    url = API_TEMPLATE.format(date=check_date.isoformat())
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "Chrome/140 Safari/537.36"
            ),
            "Accept": "application/json",
        },
    )

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == 0:
                time.sleep(1)

    raise RuntimeError(f"Failed to fetch {check_date}: {last_error}")


def is_odyssey_70mm_imax(event: dict[str, Any]) -> bool:
    if event.get("filmId") != MOVIE_ID or "70-mm" not in event.get("attributeIds", []):
        return False
    auditorium = (event.get("auditoriumTinyName") or event.get("auditorium") or "").lower()
    return "imax" in auditorium


def get_events(check_date: date) -> list[dict[str, Any]]:
    events = fetch_date(check_date).get("body", {}).get("events", [])
    return [event for event in events if is_odyssey_70mm_imax(event)]


def event_time(event: dict[str, Any]) -> str:
    return datetime.fromisoformat(event["eventDateTime"]).strftime("%H:%M")


def minutes_difference(time_string: str, preferred: str = "20:00") -> int:
    h1, m1 = map(int, time_string.split(":"))
    h2, m2 = map(int, preferred.split(":"))
    return abs((h1 * 60 + m1) - (h2 * 60 + m2))


def get_seat_count(event: dict[str, Any]) -> int | None:
    ratio = event.get("availabilityRatio")
    if ratio is None:
        return None
    return KNOWN_SEAT_COUNTS.get(round(float(ratio), 4))


def status_text(event: dict[str, Any]) -> str:
    if event.get("soldOut", False):
        return "❌ 0 seats"
    seats = get_seat_count(event)
    if seats == 0:
        return "❌ 0 seats"
    if seats is not None:
        return f"⚠️ {seats} seats available"
    ratio = event.get("availabilityRatio")
    return f"❓ Seats unknown | ratio={float(ratio):.4f}" if ratio is not None else "❓ Seats unknown"


def event_can_be_target(event: dict[str, Any]) -> bool:
    return not event.get("soldOut", False) and get_seat_count(event) != 0


def get_best_event(
    events: list[dict[str, Any]], preferred: str = "20:00"
) -> dict[str, Any] | None:
    candidates = [event for event in events if event_can_be_target(event)]
    if not candidates:
        return None
    return min(candidates, key=lambda event: minutes_difference(event_time(event), preferred))


def target_timing(time_string: str, preferred: str) -> str:
    difference = minutes_difference(time_string, preferred)
    if difference == 0:
        return "🔥 PERFECT — exactly 20:00"
    if difference <= 30:
        return f"⭐ Excellent — {time_string}"
    if difference <= 90:
        return f"✅ Good — {time_string}"
    return f"Screening at {time_string}"


def handle_target_date(
    day_string: str, events: list[dict[str, Any]], state: dict[str, Any]
) -> None:
    target = TARGET_DATES[day_string]
    best = get_best_event(events, target["preferred_time"])
    if not best:
        log(f"Target {day_string} exists, but no usable screening was found.")
        return

    event_id = str(best["id"])
    notification_id = f"{day_string}-{event_id}"
    notified = state.setdefault("target_notifications", [])
    if notification_id in notified:
        return

    time_string = event_time(best)
    priority = "⭐ PRIMARY TARGET" if target["priority"] == 1 else "🥈 SECONDARY TARGET"
    notify(
        f"🎬 ODYSSEY 70MM — {day_string}!",
        "\n".join(
            [
                priority,
                target_timing(time_string, target["preferred_time"]),
                status_text(best),
                f"Event {event_id}",
            ]
        ),
        best.get("bookingLink"),
    )
    notified.append(notification_id)


def print_target_summary(results_by_date: dict[str, list[dict[str, Any]]]) -> None:
    log("=" * 70)
    log("🎯 TARGET DATE SUMMARY")
    log("=" * 70)
    for day_string in ("2026-09-14", "2026-09-11"):
        target = TARGET_DATES[day_string]
        events = results_by_date.get(day_string, [])
        label = "⭐ PRIMARY TARGET" if target["priority"] == 1 else "🥈 SECONDARY TARGET"
        log(f"{label}: {day_string} (preferred ~{target['preferred_time']})")
        if not events:
            log("    ⏳ No IMAX-70mm screenings released yet")
            continue
        for event in sorted(
            events,
            key=lambda item: minutes_difference(event_time(item), target["preferred_time"]),
        ):
            log(f"    {event_time(event)} {status_text(event)} | event={event['id']}")


def main() -> int:
    log("Odyssey IMAX 70mm Cinema City Flora watcher")
    log(f"Checking {START_DATE} → {END_DATE}")

    state = load_state()
    previous_events = set(map(str, state.get("seen_events", [])))
    previous_dates = set(state.get("seen_dates", []))
    found_dates: set[str] = set()
    found_event_ids: set[str] = set()
    results_by_date: dict[str, list[dict[str, Any]]] = {}

    current = START_DATE
    while current <= END_DATE:
        events = get_events(current)
        day_string = current.isoformat()
        if events:
            results_by_date[day_string] = events
            found_dates.add(day_string)
            log(f"🎬 {day_string}: {len(events)} IMAX-70mm screenings")
            for event in events:
                event_id = str(event["id"])
                found_event_ids.add(event_id)
                log(f"    {event_time(event)} {status_text(event)} | event={event_id}")
        else:
            log(f"{day_string}: no IMAX-70mm screenings")
        current += timedelta(days=1)

    print_target_summary(results_by_date)
    if not found_dates:
        log("No Odyssey IMAX-70mm dates currently available.")
        return 0

    latest_date = max(found_dates)
    new_dates = sorted(found_dates - previous_dates)
    log(f"Latest available date: {latest_date}")
    if new_dates:
        notify("🎟️ New Odyssey 70mm dates", "\n".join(new_dates))

    for day_string in TARGET_DATES:
        events = results_by_date.get(day_string)
        if events:
            handle_target_date(day_string, events, state)

    new_event_ids = found_event_ids - previous_events
    if new_event_ids:
        log(f"New screening IDs: {sorted(new_event_ids)}")

    state["seen_events"] = sorted(previous_events | found_event_ids)
    state["seen_dates"] = sorted(previous_dates | found_dates)
    state["latest_date"] = latest_date
    save_state(state)
    log("State saved. Check finished.")
    return 0


if __name__ == "__main__":
    try:
        if "--test-slack" in sys.argv:
            notify(
                "✅ Odyssey watcher connected",
                "GitHub Actions can send alerts to this Slack conversation.",
            )
            raise SystemExit(0)
        raise SystemExit(main())
    except Exception as exc:
        log(f"ERROR: {exc}")
        raise SystemExit(1) from exc
