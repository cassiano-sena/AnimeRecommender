"""Leitura e normalizacao dos dados de animes do CSV."""

import csv
import threading
import urllib.request
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "urlanime1.csv"

# Cache para URLs validadas: {url: bool}
_valid_url_cache = {}
_cache_lock = threading.Lock()


def validate_image_url(url):
    """Verifica se a URL da imagem e valida (retorna HTTP 200 com imagem)."""
    if not url:
        return False
    with _cache_lock:
        if url in _valid_url_cache:
            return _valid_url_cache[url]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                content_type = response.headers.get("Content-Type", "")
                if "image" in content_type:
                    with _cache_lock:
                        _valid_url_cache[url] = True
                    return True
    except Exception:
        pass
    with _cache_lock:
        _valid_url_cache[url] = False
    return False


def prefetch_valid_urls(animes):
    """Pre-valida URLs de imagem em background."""
    def _prefetch():
        for anime in animes:
            url = anime.get("image", "")
            if url:
                validate_image_url(url)
    thread = threading.Thread(target=_prefetch, daemon=True)
    thread.start()


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
