"""Leitura e normalizacao dos dados de animes do CSV."""

import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "urlanime1.csv"


def parse_float(value, default=0.0):
    try:
        if value in (None, ""):
            return default
        return float(value)
    except ValueError:
        return default


def parse_int(value, default=0):
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except ValueError:
        return default


def parse_genres(value):
    return {
        genre.strip().replace('"', "").replace("'", "")
        for genre in (value or "").split(",")
        if genre.strip()
    }


def load_animes():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Arquivo de dados nao encontrado: {DATA_PATH}")

    with DATA_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    animes = []
    for row in rows:
        anime = {
            "id": parse_int(row.get("uid")),
            "title": (row.get("title") or "").strip(),
            "synopsis": (row.get("synopsis") or "").strip(),
            "genre": (row.get("genre") or "").strip(),
            "genres": parse_genres(row.get("genre")),
            "episodes": row.get("episodes") or "",
            "members": parse_int(row.get("members")),
            "popularity": parse_int(row.get("popularity")),
            "ranked": parse_int(row.get("ranked")),
            "score": parse_float(row.get("score")),
            "image": row.get("img_url") or "",
            "link": row.get("link") or "",
            "cluster": parse_int(row.get("cluster"), -1),
        }
        if anime["id"] and anime["title"]:
            animes.append(anime)

    return sorted(animes, key=lambda item: item["title"].lower())
