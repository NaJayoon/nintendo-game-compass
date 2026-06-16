"""Fetch curated official Nintendo media and cache uniform 16:9 images."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re
import unicodedata

import pandas as pd
import requests
import numpy as np
from PIL import Image, ImageOps


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MANUAL_TAGS_PATH = DATA_DIR / "game_tags_manual.csv"
MEDIA_PATH = DATA_DIR / "game_media_manual.csv"
MEDIA_IMAGE_DIR = DATA_DIR / "media_images"
MERGED_DATA_PATH = DATA_DIR / "nintendo_games_merged.csv"

TARGET_SIZE = (1200, 675)
USER_AGENT = "Mozilla/5.0 (Nintendo Game Compass media fetcher)"
AUTO_PLATFORMS = {"Nintendo Switch", "Nintendo Switch 2"}
WHITE_THRESHOLD = 245

OFFICIAL_URLS_EN = {
    "The Legend of Zelda: Breath of the Wild": "https://www.nintendo.com/us/store/products/the-legend-of-zelda-breath-of-the-wild-us/",
    "Animal Crossing: New Horizons": "https://www.nintendo.com/us/store/products/animal-crossing-new-horizons-switch/",
    "Mario Kart 8 Deluxe": "https://www.nintendo.com/us/store/products/mario-kart-8-deluxe-105275/",
    "Nintendo Switch Sports": "https://www.nintendo.com/us/store/products/nintendo-switch-sports-switch/",
    "Kirby and the Forgotten Land": "https://www.nintendo.com/us/store/products/kirby-and-the-forgotten-land-switch/",
    "Super Mario Odyssey": "https://www.nintendo.com/us/store/products/super-mario-odyssey-switch/",
    "Super Smash Bros. Ultimate": "https://www.nintendo.com/us/store/products/super-smash-bros-ultimate-switch/",
    "Overcooked 2": "https://www.nintendo.com/us/store/products/overcooked-2-switch/",
    "Stardew Valley": "https://www.nintendo.com/us/store/products/stardew-valley-switch/",
    "Metroid Dread": "https://www.nintendo.com/us/store/products/metroid-dread-switch/",
    "The Legend of Zelda: Tears of the Kingdom": "https://www.nintendo.com/us/store/products/the-legend-of-zelda-tears-of-the-kingdom-switch/",
    "Super Mario Bros. Wonder": "https://www.nintendo.com/us/store/products/super-mario-bros-wonder-switch/",
    "Pikmin 4": "https://www.nintendo.com/us/store/products/pikmin-4-switch/",
    "Splatoon 3": "https://www.nintendo.com/us/store/products/splatoon-3-switch/",
    "Pokemon Legends: Arceus": "https://www.nintendo.com/us/store/products/pokemon-legends-arceus-switch/",
    "Pokemon Scarlet": "https://www.nintendo.com/us/store/products/pokemon-scarlet-switch/",
    "Pokemon Violet": "https://www.nintendo.com/us/store/products/pokemon-violet-switch/",
    "Fire Emblem: Three Houses": "https://www.nintendo.com/us/store/products/fire-emblem-three-houses-switch/",
    "Fire Emblem Engage": "https://www.nintendo.com/us/store/products/fire-emblem-engage-switch/",
    "Xenoblade Chronicles 3": "https://www.nintendo.com/us/store/products/xenoblade-chronicles-3-switch/",
    "Xenoblade Chronicles X: Definitive Edition": "https://www.nintendo.com/us/store/products/xenoblade-chronicles-x-definitive-edition-switch/",
    "Paper Mario: The Thousand-Year Door": "https://www.nintendo.com/us/store/products/paper-mario-the-thousand-year-door-switch/",
    "Super Mario RPG": "https://www.nintendo.com/us/store/products/super-mario-rpg-switch/",
    "Princess Peach: Showtime!": "https://www.nintendo.com/us/store/products/princess-peach-showtime-switch/",
    "Mario vs. Donkey Kong": "https://www.nintendo.com/us/store/products/mario-vs-donkey-kong-switch/",
    "The Legend of Zelda: Echoes of Wisdom": "https://www.nintendo.com/us/store/products/the-legend-of-zelda-echoes-of-wisdom-switch/",
    "Super Mario Party Jamboree": "https://www.nintendo.com/us/store/products/super-mario-party-jamboree-switch/",
    "Donkey Kong Country Returns HD": "https://www.nintendo.com/us/store/products/donkey-kong-country-returns-hd-switch/",
    "Mario Kart World": "https://www.nintendo.com/us/store/products/mario-kart-world-switch-2/",
    "Donkey Kong Bananza": "https://www.nintendo.com/us/store/products/donkey-kong-bananza-switch-2/",
    "Kirby and the Forgotten Land + Star-Crossed World": "https://www.nintendo.com/us/store/products/kirby-and-the-forgotten-land-nintendo-switch-2-edition-plus-star-crossed-world-switch-2/",
    "Metroid Prime 4: Beyond": "https://www.nintendo.com/us/store/products/metroid-prime-4-beyond-switch/",
    "Pokemon Legends: Z-A": "https://www.nintendo.com/us/store/products/pokemon-legends-z-a-switch/",
    "Hades": "https://www.nintendo.com/us/store/products/hades-switch/",
    "Hollow Knight": "https://www.nintendo.com/us/store/products/hollow-knight-switch/",
    "Celeste": "https://www.nintendo.com/us/store/products/celeste-switch/",
    "Luigi's Mansion 3": "https://www.nintendo.com/us/store/products/luigi-s-mansion-3-us-109482/",
    "Captain Toad: Treasure Tracker": "https://www.nintendo.com/us/store/products/captain-toad-treasure-tracker-switch/",
    "Clubhouse Games: 51 Worldwide Classics": "https://www.nintendo.com/us/store/products/clubhouse-games-51-worldwide-classics-switch/",
    "Ring Fit Adventure": "https://www.nintendo.com/us/store/products/ring-fit-adventure-switch/",
    "Bayonetta 3": "https://www.nintendo.com/us/store/products/bayonetta-3-switch/",
    "Snipperclips - Cut it out together!": "https://www.nintendo.com/us/store/products/snipperclips-cut-it-out-together-switch/",
    "Super Mario 3D World + Bowser's Fury": "https://www.nintendo.com/us/store/products/super-mario-3d-world-plus-bowsers-fury-switch/",
}


def safe_filename(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title)
    normalized = normalized.encode("ascii", "ignore").decode("ascii").lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return f"{normalized}.jpg"


def product_slug(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title)
    normalized = normalized.encode("ascii", "ignore").decode("ascii").lower()
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return normalized


def candidate_product_urls(title: str, platform: str = "Nintendo Switch") -> list[str]:
    slug = product_slug(title)
    suffixes = ["switch-2", "nintendo-switch-2", "switch", ""]
    if platform == "Nintendo Switch":
        suffixes = ["switch", ""]

    urls = []
    for suffix in suffixes:
        product_slug_with_suffix = f"{slug}-{suffix}" if suffix else slug
        urls.append(f"https://www.nintendo.com/us/store/products/{product_slug_with_suffix}/")
    return list(dict.fromkeys(urls))


def extract_meta_content(html: str, target_name: str) -> str:
    for tag in re.findall(r"<meta\b[^>]*>", html, flags=re.IGNORECASE):
        attrs = dict(re.findall(r'([a-zA-Z_:.-]+)=["\']([^"\']*)["\']', tag))
        name = attrs.get("property") or attrs.get("name")
        if name == target_name:
            return attrs.get("content", "")
    return ""


def fetch_official_image_url(session: requests.Session, official_url: str) -> str:
    response = session.get(official_url, timeout=30)
    response.raise_for_status()
    image_url = extract_meta_content(response.text, "og:image")
    if image_url:
        return image_url
    return extract_meta_content(response.text, "twitter:image")


def white_margin_stats(image: Image.Image) -> tuple[float, float]:
    """Return overall and edge near-white ratios for product images."""
    array = np.asarray(image.convert("RGB"))
    white_pixels = np.all(array >= WHITE_THRESHOLD, axis=2)
    height, width = white_pixels.shape
    band_y = max(1, height // 10)
    band_x = max(1, width // 10)
    edge_pixels = np.concatenate(
        [
            white_pixels[:band_y, :].reshape(-1),
            white_pixels[-band_y:, :].reshape(-1),
            white_pixels[:, :band_x].reshape(-1),
            white_pixels[:, -band_x:].reshape(-1),
        ]
    )
    return float(white_pixels.mean()), float(edge_pixels.mean())


def crop_near_white_border(image: Image.Image) -> Image.Image:
    """Crop official white-padded product art before forcing a 16:9 card."""
    overall_white, edge_white = white_margin_stats(image)
    if overall_white < 0.25 or edge_white < 0.45:
        return image

    array = np.asarray(image.convert("RGB"))
    non_white_mask = np.any(array < WHITE_THRESHOLD, axis=2)
    if float(non_white_mask.mean()) < 0.02:
        return image

    y_values, x_values = np.where(non_white_mask)
    left = int(x_values.min())
    right = int(x_values.max()) + 1
    top = int(y_values.min())
    bottom = int(y_values.max()) + 1

    width, height = image.size
    crop_area = (right - left) * (bottom - top)
    full_area = width * height
    if crop_area / full_area > 0.92:
        return image

    pad_x = int(width * 0.025)
    pad_y = int(height * 0.025)
    left = max(0, left - pad_x)
    top = max(0, top - pad_y)
    right = min(width, right + pad_x)
    bottom = min(height, bottom + pad_y)
    return image.crop((left, top, right, bottom))


def should_refresh_cached_image(image_path: Path) -> bool:
    if not image_path.exists():
        return True
    try:
        with Image.open(image_path) as cached_image:
            image = ImageOps.exif_transpose(cached_image).convert("RGB")
            if image.size != TARGET_SIZE:
                return True
            overall_white, edge_white = white_margin_stats(image)
            return overall_white >= 0.30 and edge_white >= 0.50
    except OSError:
        return True


def find_official_url(session: requests.Session, title: str, platform: str) -> str:
    for candidate_url in candidate_product_urls(title, platform):
        try:
            response = session.head(candidate_url, timeout=10, allow_redirects=True)
            if response.status_code == 200 and "/us/store/products/" in response.url:
                return response.url
        except requests.RequestException:
            continue
    return ""


def save_uniform_image(image_bytes: bytes, output_path: Path) -> None:
    with Image.open(BytesIO(image_bytes)) as original:
        image = ImageOps.exif_transpose(original).convert("RGB")

    image = crop_near_white_border(image)
    source_width, source_height = image.size
    target_width, target_height = TARGET_SIZE
    target_ratio = target_width / target_height
    source_ratio = source_width / source_height

    if source_ratio > target_ratio:
        crop_width = int(source_height * target_ratio)
        left = (source_width - crop_width) // 2
        image = image.crop((left, 0, left + crop_width, source_height))
    elif source_ratio < target_ratio:
        crop_height = int(source_width / target_ratio)
        top = (source_height - crop_height) // 2
        image = image.crop((0, top, source_width, top + crop_height))

    image = image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "JPEG", quality=90, optimize=True)


def load_existing_media() -> pd.DataFrame:
    if not MEDIA_PATH.exists():
        return pd.DataFrame(
            columns=[
                "title",
                "image_url",
                "image_file",
                "official_url_en",
                "official_url_ko",
                "official_url_zh",
                "media_note",
            ]
        )
    return pd.read_csv(MEDIA_PATH).fillna("")


def load_target_games() -> list[dict[str, str]]:
    targets: dict[str, dict[str, str]] = {}

    manual_games = pd.read_csv(MANUAL_TAGS_PATH)["title"].dropna().tolist()
    for title in manual_games:
        targets[product_slug(title)] = {"title": title, "platform": "Nintendo Switch", "priority": "manual"}

    if MERGED_DATA_PATH.exists():
        merged_games = pd.read_csv(MERGED_DATA_PATH)
        if {"title", "platform"}.issubset(merged_games.columns):
            switch_games = merged_games[merged_games["platform"].isin(AUTO_PLATFORMS)]
            for _, game in switch_games.dropna(subset=["title"]).iterrows():
                title = str(game["title"]).strip()
                title_key = product_slug(title)
                if title and title_key not in targets:
                    targets[title_key] = {
                        "title": title,
                        "platform": str(game.get("platform", "Nintendo Switch")),
                        "priority": "auto",
                    }

    return list(targets.values())


def main() -> None:
    existing = load_existing_media().set_index("title", drop=False)
    target_games = load_target_games()
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    rows: list[dict[str, str]] = []
    successes = 0
    auto_found = 0
    auto_missing = 0
    failures: list[str] = []

    for index, target in enumerate(target_games, start=1):
        title = target["title"]
        platform = target["platform"]
        priority = target["priority"]
        current = existing.loc[title].to_dict() if title in existing.index else {}
        official_url = OFFICIAL_URLS_EN.get(title, current.get("official_url_en", ""))
        if official_url and "/us/store/products/" not in official_url:
            official_url = ""
        if not official_url:
            official_url = find_official_url(session, title, platform)
            if official_url:
                auto_found += 1
            elif priority == "auto":
                auto_missing += 1

        image_url = current.get("image_url", "")
        image_file = current.get("image_file", "")
        media_note = current.get("media_note", "")

        if official_url:
            try:
                expected_image_file = f"data/media_images/{safe_filename(title)}"
                existing_image_path = PROJECT_ROOT / expected_image_file
                if (
                    image_file == expected_image_file
                    and existing_image_path.exists()
                    and not should_refresh_cached_image(existing_image_path)
                ):
                    successes += 1
                    media_note = media_note or "Official Nintendo og:image cached locally as 1200x675"
                else:
                    official_image_url = fetch_official_image_url(session, official_url)
                    if not official_image_url:
                        failures.append(f"{title}: no og:image")
                        official_image_url = ""

                    image_url = official_image_url or image_url
                    image_file = expected_image_file
                    image_response = session.get(image_url, timeout=30)
                    image_response.raise_for_status()
                    save_uniform_image(image_response.content, PROJECT_ROOT / image_file)
                    media_note = "Official Nintendo og:image cached locally as 1200x675"
                    successes += 1
            except Exception as error:  # noqa: BLE001
                failures.append(f"{title}: {error}")

        if official_url and image_file:
            rows.append(
                {
                    "title": title,
                    "image_url": image_url,
                    "image_file": image_file,
                    "official_url_en": official_url,
                    "official_url_ko": current.get("official_url_ko", ""),
                    "official_url_zh": current.get("official_url_zh", ""),
                    "media_note": media_note,
                }
            )

        if index % 25 == 0:
            print(f"Processed {index}/{len(target_games)} titles", flush=True)

    media = pd.DataFrame(rows)
    media.to_csv(MEDIA_PATH, index=False)

    print(f"Wrote {len(media)} media rows to {MEDIA_PATH}")
    print(f"Fetched or refreshed {successes} official images")
    print(f"Auto-discovered {auto_found} additional official product pages")
    print(f"Skipped {auto_missing} auto titles without a matching official product page")
    if failures:
        print("Media fetch warnings:")
        for failure in failures:
            print(f"- {failure}")


if __name__ == "__main__":
    main()
