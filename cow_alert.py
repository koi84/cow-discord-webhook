import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SOURCE_URL = "https://kr-cowstats.com/games_list"
DETAIL_URL = "https://kr-cowstats.com/{game_id}"
STATE_FILE = Path("data/seen_games.json")
CONFIG_FILE = Path("config.json")
FLAGS = {"FR": "🇫🇷", "EN": "🇺🇸🇬🇧", "DE": "🇩🇪", "IT": "🇮🇹"}

GAME_RE = re.compile(
    r"(?P<id>\d{7,})\s*:\s*scrap date:.*?server:\s*"
    r"(?P<language>[A-Z]{2}).*?-\s*game day:\s*(?P<day>\d+),\s*"
    r"Scenario:\s*(?P<scenario>.*?)\.\s*Start Date:\s*"
    r"(?P<start>.*?)\.\s*Opens? Slots:\s*(?P<slots>\d+)",
    re.IGNORECASE,
)


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def fetch_games():
    response = requests.get(
        SOURCE_URL,
        timeout=30,
        headers={"User-Agent": "CoW-Discord-Alerts/1.0 (+GitHub Actions)"},
    )
    response.raise_for_status()
    text = BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True)
    games = []
    for match in GAME_RE.finditer(text):
        game = match.groupdict()
        game["language"] = game["language"].upper()
        game["scenario"] = " ".join(game["scenario"].split())
        game["slots"] = int(game["slots"])
        games.append(game)
    if not games:
        raise RuntimeError("Aucune partie détectée : la structure de CoW Stats a peut-être changé.")
    return games


def wanted(game, config):
    matches_filters = (
        game["scenario"] in config["scenarios"]
        and game["language"] in config["languages"]
        and (not config.get("only_open_games", True) or game["slots"] > 0)
    )
    if not matches_filters:
        return False

    # CoW Stats affiche les dates en UTC sous la forme JJ-MM-AAAA HH:MM:SS.
    # La petite tolérance négative couvre un léger décalage d'horloge.
    try:
        opened_at = datetime.strptime(game["start"], "%d-%m-%Y %H:%M:%S").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return False
    age_minutes = (datetime.now(timezone.utc) - opened_at).total_seconds() / 60
    return -2 <= age_minutes <= config.get("max_start_age_minutes", 10)


def send_to_discord(webhook_url, game):
    flag = FLAGS.get(game["language"], "")
    payload = {
        "username": "CoW Map Watcher",
        "allowed_mentions": {"parse": []},
        "embeds": [{
            "title": "Map Found!",
            "url": DETAIL_URL.format(game_id=game["id"]),
            "color": 0x5865F2,
            "fields": [
                {"name": "Start Date", "value": game["start"], "inline": False},
                {"name": "Game ID", "value": game["id"], "inline": True},
                {"name": "Open Slots", "value": str(game["slots"]), "inline": True},
                {"name": "Scenario", "value": game["scenario"], "inline": False},
                {"name": "Language Server", "value": f"{game['language']} {flag}", "inline": False},
            ],
            "footer": {"text": "Données : kr-cowstats.com"},
        }],
    }
    response = requests.post(webhook_url, json=payload, timeout=30)
    response.raise_for_status()


def main():
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        sys.exit("Le secret DISCORD_WEBHOOK_URL est absent.")

    config = load_json(CONFIG_FILE, {})
    games = [game for game in fetch_games() if wanted(game, config)]
    state = load_json(STATE_FILE, {"initialized": False, "ids": []})
    # Compatibilité avec l’ancien format éventuel, qui était une simple liste.
    if isinstance(state, list):
        state = {"initialized": bool(state), "ids": state}
    first_run = not state.get("initialized", False)
    seen = set(state.get("ids", []))

    if first_run and not config.get("send_existing_on_first_run", False):
        new_games = []
    else:
        new_games = [game for game in games if game["id"] not in seen]

    for game in reversed(new_games):
        send_to_discord(webhook_url, game)
        print(f"Alerte envoyée pour {game['id']} ({game['scenario']}, {game['language']})")

    # Conserve les identifiants actuels et récents, avec une taille bornée.
    updated = list(dict.fromkeys([game["id"] for game in games] + list(seen)))[:2000]
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps({"initialized": True, "ids": updated}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{len(games)} partie(s) correspondante(s), {len(new_games)} nouvelle(s).")


if __name__ == "__main__":
    main()
