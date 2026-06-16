"""Add the official Nintendo Switch 2 lineup to the curated dataset."""

from __future__ import annotations

from pathlib import Path
import os

import pandas as pd
import requests

from fetch_official_media import safe_filename, save_uniform_image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MEDIA_IMAGE_DIR = DATA_DIR / "media_images"

RECENT_PATH = DATA_DIR / "recent_switch_games.csv"
TAGS_PATH = DATA_DIR / "game_tags_manual.csv"
LOCALIZATIONS_PATH = DATA_DIR / "game_localizations_manual.csv"
MEDIA_PATH = DATA_DIR / "game_media_manual.csv"

USER_AGENT = "Mozilla/5.0 (Nintendo Game Compass Switch 2 updater)"

RECENT_COLUMNS = [
    "title",
    "platform",
    "date",
    "meta_score",
    "user_score",
    "esrb_rating",
    "developers",
    "genres",
]

TAG_COLUMNS = [
    "title",
    "platform_group",
    "nintendo_relation",
    "genre_main",
    "player_type",
    "play_situation",
    "difficulty",
    "mood",
    "session_length",
    "beginner_friendly",
    "local_multiplayer",
    "online_multiplayer",
    "budget_tier",
    "buying_advice",
]

LOCALIZATION_COLUMNS = [
    "title",
    "title_en",
    "title_ko",
    "title_zh",
    "localization_note",
]

MEDIA_COLUMNS = [
    "title",
    "image_url",
    "image_file",
    "official_url_en",
    "official_url_ko",
    "official_url_zh",
    "media_note",
]


def nintendo_url(link: str) -> str:
    if link.startswith("http"):
        return link.strip()
    return f"https://www.nintendo.com{link}".strip()


SWITCH2_GAMES = [
    {
        "title": "Nintendo Switch 2 Welcome Tour",
        "date": "2025-06-05",
        "developers": "Nintendo",
        "genres": "['Educational', 'Puzzle']",
        "title_ko": "Nintendo Switch 2 웰컴 투어",
        "title_zh": "Nintendo Switch 2秘密展",
        "official_url_en": "https://www.nintendo.com/us/store/products/nintendo-switch-2-welcome-tour-switch-2/",
        "official_url_ko": nintendo_url("/kr/games/switch2/aahea/"),
        "official_url_zh": nintendo_url("/zh-hans-hk/games/switch2/aahea/index.html"),
        "image_url": "https://images.ctfassets.net/o5v89n4kg6h4/70010000096816db042301894311f0bed16fd20ad41733/21b25e65c23de73389e5eee9de722830/2dda55540a93ada523cc179fcc1a040f3bbd2b30098b204d1af3bbd8eb914303.jpg",
        "tag": {
            "platform_group": "Switch 2",
            "nintendo_relation": "Nintendo Core",
            "genre_main": "Puzzle",
            "player_type": "Beginner",
            "play_situation": "Solo|Short Break",
            "difficulty": "Easy",
            "mood": "Creative",
            "session_length": "Short",
            "beginner_friendly": "Yes",
            "local_multiplayer": "No",
            "online_multiplayer": "No",
            "budget_tier": "Medium",
            "buying_advice": "Best for players who want a guided introduction to Switch 2 hardware features.",
        },
    },
    {
        "title": "Mario Kart World",
        "date": "2025-06-05",
        "developers": "Nintendo",
        "genres": "['Racing', 'Multiplayer']",
        "title_ko": "마리오 카트 월드",
        "title_zh": "瑪利歐賽車世界",
        "official_url_en": "https://www.nintendo.com/us/store/products/mario-kart-world-switch-2/",
        "official_url_ko": nintendo_url("/kr/games/switch2/aaaaa/"),
        "official_url_zh": nintendo_url("/zh-hans-hk/games/switch2/aaaaa/index.html"),
        "image_url": "https://images.ctfassets.net/o5v89n4kg6h4/7001000009680838a0fa12894011f0a6be5dd7946b86e3/29a1b9dc0fd68a22a76580868b6561b1/701576595770f5bf0f2d56a335faa1d9545e499243cb96c4e4a127bb65b7bb9c.jpg",
        "tag": {
            "platform_group": "Switch 2",
            "nintendo_relation": "Nintendo Core",
            "genre_main": "Racing",
            "player_type": "Party Player",
            "play_situation": "Friends|Family|Online|Party|Short Break",
            "difficulty": "Easy",
            "mood": "Fun",
            "session_length": "Short",
            "beginner_friendly": "Yes",
            "local_multiplayer": "Yes",
            "online_multiplayer": "Yes",
            "budget_tier": "High",
            "buying_advice": "A strong first Switch 2 multiplayer pick for families, friends, and online racing.",
        },
    },
    {
        "title": "Nintendo GameCube - Nintendo Classics",
        "date": "2025-06-05",
        "developers": "Nintendo",
        "genres": "['Retro', 'Collection']",
        "title_ko": "Nintendo GameCube - Nintendo Classics",
        "title_zh": "Nintendo GameCube™ – Nintendo Classics",
        "official_url_en": "https://www.nintendo.com/us/store/products/nintendo-gamecube-nintendo-classics-switch-2/",
        "official_url_ko": "",
        "official_url_zh": nintendo_url("https://ec.nintendo.com/HK/zh/titles/70010000096628"),
        "image_url": "https://images.ctfassets.net/o5v89n4kg6h4/70010000096628def5ec26894311f080705b5d4f5e7bb5/ad20dab99cd324c17685366ced4e18f5/88e3dae1d9fffea534a287ab02ff3392e09e6d0d83b11b6157f6310ac265e367.jpg",
        "tag": {
            "platform_group": "Switch 2",
            "nintendo_relation": "Nintendo Core",
            "genre_main": "Adventure",
            "player_type": "Core Player",
            "play_situation": "Solo|Long Session",
            "difficulty": "Medium",
            "mood": "Immersive",
            "session_length": "Medium",
            "beginner_friendly": "Yes",
            "local_multiplayer": "No",
            "online_multiplayer": "Yes",
            "budget_tier": "Medium",
            "buying_advice": "Good for players who want official classic Nintendo library access on Switch 2.",
        },
    },
    {
        "title": "Donkey Kong Bananza",
        "date": "2025-07-17",
        "developers": "Nintendo",
        "genres": "['Action', 'Adventure', 'Platformer']",
        "title_ko": "동키콩 바난자",
        "title_zh": "咚奇剛 蕉力全開",
        "official_url_en": "https://www.nintendo.com/us/store/products/donkey-kong-bananza-switch-2/",
        "official_url_ko": nintendo_url("/kr/games/switch2/aaaca/index.html"),
        "official_url_zh": nintendo_url("/zh-hans-hk/games/switch2/aaaca/index.html"),
        "image_url": "https://images.ctfassets.net/o5v89n4kg6h4/70010000096812e4780925894311f08746ff65488e78ef/867be12b3837baca359965aa8557af2d/3a40edb8fc1354911e0907f1494b5678c2fa37acb8925967e638bd63d06e4580.jpg",
        "tag": {
            "platform_group": "Switch 2",
            "nintendo_relation": "Nintendo Core",
            "genre_main": "Adventure",
            "player_type": "Explorer",
            "play_situation": "Solo|Family|Long Session",
            "difficulty": "Medium",
            "mood": "Exciting",
            "session_length": "Long",
            "beginner_friendly": "Yes",
            "local_multiplayer": "No",
            "online_multiplayer": "No",
            "budget_tier": "High",
            "buying_advice": "Best for players who want a big new Nintendo action adventure on Switch 2.",
        },
    },
    {
        "title": "Drag x Drive",
        "date": "2025-08-14",
        "developers": "Nintendo",
        "genres": "['Sports', 'Action', 'Multiplayer']",
        "title_ko": "Drag x Drive",
        "title_zh": "拖曳＆突破",
        "official_url_en": "https://www.nintendo.com/us/store/products/drag-x-drive-switch-2/",
        "official_url_ko": "https://www.nintendo.com/kr/games/switch2/aaaqa/",
        "official_url_zh": nintendo_url("/zh-hans-hk/games/switch2/aaaqa/index.html"),
        "image_url": "https://images.ctfassets.net/o5v89n4kg6h4/70010000099954dc912537894311f0a5c171ba1e81c7be/7297cf36cce500a02e7e390f7a5380ff/dd051fb7702a2d43a6b4e7f0c12299749ebff278994e03f089c6f12b3f2a0108.jpg",
        "tag": {
            "platform_group": "Switch 2",
            "nintendo_relation": "Nintendo Core",
            "genre_main": "Sports",
            "player_type": "Competitive Player",
            "play_situation": "Friends|Online|Short Break",
            "difficulty": "Medium",
            "mood": "Active",
            "session_length": "Short",
            "beginner_friendly": "Yes",
            "local_multiplayer": "No",
            "online_multiplayer": "Yes",
            "budget_tier": "Medium",
            "buying_advice": "A better fit for players who want short competitive matches built around Joy-Con 2 controls.",
        },
    },
    {
        "title": "Hyrule Warriors: Age of Imprisonment",
        "date": "2025-11-06",
        "developers": "Koei Tecmo Games",
        "genres": "['Action', 'Adventure']",
        "title_ko": "젤다무쌍 봉인 전기",
        "title_zh": "ZELDA無雙 封印戰記",
        "official_url_en": "https://www.nintendo.com/us/store/products/hyrule-warriors-age-of-imprisonment-switch-2/",
        "official_url_ko": nintendo_url("/kr/games/switch2/zelda-fuuin/"),
        "official_url_zh": nintendo_url("/zh-hans-hk/games/switch2/aagab/"),
        "image_url": "https://images.ctfassets.net/o5v89n4kg6h4/70010000103949ddf2b178894311f0a72cff65488e78ef/98677676082f7f2a556aa24bd74d1fbd/9972be610a6afe1c928b148fe1339f6e13f4c0f511ab9437fdcfdc039f9471ce.jpg",
        "tag": {
            "platform_group": "Switch 2",
            "nintendo_relation": "Nintendo Published",
            "genre_main": "Action",
            "player_type": "Core Player",
            "play_situation": "Solo|Friends|Long Session",
            "difficulty": "Medium",
            "mood": "Exciting",
            "session_length": "Long",
            "beginner_friendly": "No",
            "local_multiplayer": "Yes",
            "online_multiplayer": "No",
            "budget_tier": "High",
            "buying_advice": "A story-heavy action pick for Zelda fans who want large-scale battles.",
        },
    },
    {
        "title": "Kirby Air Riders",
        "date": "2025-11-20",
        "developers": "Nintendo",
        "genres": "['Racing', 'Action', 'Multiplayer']",
        "title_ko": "커비의 에어 라이더",
        "title_zh": "卡比的馭天飛行者",
        "official_url_en": "https://www.nintendo.com/us/store/products/kirby-air-riders-switch-2/",
        "official_url_ko": nintendo_url("/kr/games/switch2/aaaba/"),
        "official_url_zh": nintendo_url("https://ec.nintendo.com/HK/zh/titles/70010000103778"),
        "image_url": "https://images.ctfassets.net/o5v89n4kg6h4/70010000103778e98f48dc894311f0bf4fff65488e78ef/351b7631b43f4bddc7eb865001a4c21f/d5a796526b37a5b9b29e0b8ee5974c202ef85295a793b9a5bc1c80b96ee9da63.jpg",
        "tag": {
            "platform_group": "Switch 2",
            "nintendo_relation": "Nintendo Core",
            "genre_main": "Racing",
            "player_type": "Party Player",
            "play_situation": "Friends|Family|Online|Party|Short Break",
            "difficulty": "Easy",
            "mood": "Fun",
            "session_length": "Short",
            "beginner_friendly": "Yes",
            "local_multiplayer": "Yes",
            "online_multiplayer": "Yes",
            "budget_tier": "High",
            "buying_advice": "A playful multiplayer racing pick for Kirby fans and short party sessions.",
        },
    },
    {
        "title": "Mario Tennis Fever",
        "date": "2026-02-12",
        "developers": "Camelot Software Planning",
        "genres": "['Sports', 'Multiplayer']",
        "title_ko": "마리오 테니스 피버",
        "title_zh": "瑪利歐網球 狂熱",
        "official_url_en": "https://www.nintendo.com/us/store/products/mario-tennis-fever-switch-2/",
        "official_url_ko": "https://www.nintendo.com/kr/games/switch2/aaaea/index.html",
        "official_url_zh": nintendo_url("https://ec.nintendo.com/HK/zh/titles/70010000105872"),
        "image_url": "https://images.ctfassets.net/o5v89n4kg6h4/700100001058721dcf6aa3901411f09ebe834f03113de6/8525f6b6d734b81f6b0d2fa3a1a89d75/7db3bbe3483f58683b80c649341e821648ac8bbae434ff668ceaac2bca5bf5ff.jpg",
        "tag": {
            "platform_group": "Switch 2",
            "nintendo_relation": "Nintendo Core",
            "genre_main": "Sports",
            "player_type": "Competitive Player",
            "play_situation": "Friends|Family|Online|Short Break",
            "difficulty": "Medium",
            "mood": "Exciting",
            "session_length": "Short",
            "beginner_friendly": "Yes",
            "local_multiplayer": "Yes",
            "online_multiplayer": "Yes",
            "budget_tier": "High",
            "buying_advice": "Good for players who want easy-to-start competitive sports matches.",
        },
    },
    {
        "title": "Pokemon Pokopia",
        "date": "2026-03-05",
        "developers": "The Pokemon Company",
        "genres": "['Simulation', 'Adventure']",
        "title_ko": "Pokémon Pokopia",
        "title_zh": "Pokémon Pokopia",
        "official_url_en": "https://www.nintendo.com/us/store/products/pokemon-pokopia-switch-2/",
        "official_url_ko": "https://pokemonkorea.co.kr/pokemonpokopia",
        "official_url_zh": "https://www.pocoapokemon.jp/sc/",
        "image_url": "https://images.ctfassets.net/o5v89n4kg6h4/70010000107424f3747daabf3911f09db4b71be4cc4cfa/4d881b425b3f2a10fb9340b367e8a6bc/5fdf92546dc6405f94304388e9f87275993191433feecbeefe4f69544007206d.jpg",
        "tag": {
            "platform_group": "Switch 2",
            "nintendo_relation": "Nintendo Published",
            "genre_main": "Simulation",
            "player_type": "Relaxed Player",
            "play_situation": "Solo|Long Session",
            "difficulty": "Easy",
            "mood": "Healing",
            "session_length": "Long",
            "beginner_friendly": "Yes",
            "local_multiplayer": "No",
            "online_multiplayer": "Yes",
            "budget_tier": "High",
            "buying_advice": "A cozy Pokemon choice for players who prefer gentle building and long-term play.",
        },
    },
    {
        "title": "Yoshi and the Mysterious Book",
        "date": "2026-05-21",
        "developers": "Nintendo",
        "genres": "['Adventure', 'Puzzle']",
        "title_ko": "요시와 신기한 도감",
        "title_zh": "耀西與不可思議的圖鑑",
        "official_url_en": "https://www.nintendo.com/us/store/products/yoshi-and-the-mysterious-book-switch-2/",
        "official_url_ko": nintendo_url("/kr/games/switch2/aakga/"),
        "official_url_zh": nintendo_url("https://ec.nintendo.com/HK/zh/titles/70010000119862"),
        "image_url": "https://images.ctfassets.net/o5v89n4kg6h4/70010000119862c97ae3951cbc11f1a5f0a5038c94390e/07998f8857775362550a5bda06a74dfe/f47acc5561f3830949b62abbfd9c899eb03a0c21d19e25270d336190043607c7.jpg",
        "tag": {
            "platform_group": "Switch 2",
            "nintendo_relation": "Nintendo Core",
            "genre_main": "Puzzle",
            "player_type": "Beginner",
            "play_situation": "Solo|Family",
            "difficulty": "Easy",
            "mood": "Cute",
            "session_length": "Medium",
            "beginner_friendly": "Yes",
            "local_multiplayer": "No",
            "online_multiplayer": "No",
            "budget_tier": "High",
            "buying_advice": "A gentle family-friendly pick for players who like cute worlds and lighter puzzles.",
        },
    },
    {
        "title": "Star Fox",
        "date": "2026-06-25",
        "developers": "Nintendo",
        "genres": "['Shooter', 'Action']",
        "title_ko": "스타폭스",
        "title_zh": "Star Fox (星際火狐)",
        "official_url_en": "https://www.nintendo.com/us/store/products/star-fox-switch-2/",
        "official_url_ko": nintendo_url("/kr/news/article/jqP3XvfoaXCrIz7rrlZ0v"),
        "official_url_zh": nintendo_url("https://ec.nintendo.com/HK/zh/titles/70010000123170"),
        "image_url": "https://images.ctfassets.net/o5v89n4kg6h4/7001000012317005a93d0949a211f19f686f453170fd9f/47612a5e820fcd09cee2f360aa038f87/0e1ce3e25ee3b190df9fc2b9284bd9847672a4cc9bf548103545dc4edfc197a4.jpg",
        "tag": {
            "platform_group": "Switch 2",
            "nintendo_relation": "Nintendo Core",
            "genre_main": "Shooter",
            "player_type": "Core Player",
            "play_situation": "Solo|Short Break",
            "difficulty": "Medium",
            "mood": "Exciting",
            "session_length": "Short",
            "beginner_friendly": "Yes",
            "local_multiplayer": "No",
            "online_multiplayer": "No",
            "budget_tier": "Medium",
            "buying_advice": "A classic action-shooter route for players who want a focused arcade-style Nintendo pick.",
        },
    },
    {
        "title": "Splatoon Raiders",
        "date": "2026-07-23",
        "developers": "Nintendo",
        "genres": "['Shooter', 'Action', 'Online']",
        "title_ko": "스플래툰 레이더스",
        "title_zh": "斯普拉遁 塗擊隊",
        "official_url_en": "https://www.nintendo.com/us/store/products/splatoon-raiders-switch-2/",
        "official_url_ko": "https://store.nintendo.co.kr/70010000122826",
        "official_url_zh": nintendo_url("/hk/games/switch2/aadla/index.html"),
        "image_url": "https://images.ctfassets.net/o5v89n4kg6h4/700100001228270b216ace3dbe11f1981251d357ba780b/8c42325f9e62bb74a17434734d2bd1a0/ac10d398536e75dbd5ab9961c04d8fdaeaa35b531a173adfedf684ec18a8460d.jpg",
        "tag": {
            "platform_group": "Switch 2",
            "nintendo_relation": "Nintendo Core",
            "genre_main": "Shooter",
            "player_type": "Competitive Player",
            "play_situation": "Solo|Online|Long Session",
            "difficulty": "Medium",
            "mood": "Exciting",
            "session_length": "Medium",
            "beginner_friendly": "No",
            "local_multiplayer": "No",
            "online_multiplayer": "Yes",
            "budget_tier": "High",
            "buying_advice": "Best for Splatoon players who want a new Switch 2 entry with a stronger action focus.",
        },
    },
]


def read_csv(path: Path, columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=columns)
    dataframe = pd.read_csv(path, keep_default_na=False)
    for column in columns:
        if column not in dataframe.columns:
            dataframe[column] = ""
    return dataframe[columns]


def write_csv(dataframe: pd.DataFrame, path: Path) -> None:
    temp_path = path.with_name(f"{path.stem}.tmp{path.suffix}")
    dataframe.to_csv(temp_path, index=False)
    os.replace(temp_path, path)


def upsert_row(dataframe: pd.DataFrame, row: dict[str, str], columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column not in dataframe.columns:
            dataframe[column] = ""
        row.setdefault(column, "")

    title = str(row["title"]).casefold()
    mask = dataframe["title"].astype(str).str.casefold() == title
    if mask.any():
        for column in columns:
            dataframe.loc[mask, column] = row[column]
    else:
        dataframe = pd.concat([dataframe, pd.DataFrame([row])], ignore_index=True)
    return dataframe[columns]


def cache_official_image(session: requests.Session, game: dict) -> str:
    output_path = MEDIA_IMAGE_DIR / safe_filename(game["title"])
    response = session.get(game["image_url"], timeout=30)
    response.raise_for_status()
    save_uniform_image(response.content, output_path)
    return str(output_path.relative_to(PROJECT_ROOT))


def build_rows(game: dict, image_file: str) -> tuple[dict[str, str], dict[str, str], dict[str, str], dict[str, str]]:
    recent = {
        "title": game["title"],
        "platform": "Nintendo Switch 2",
        "date": game["date"],
        "meta_score": "",
        "user_score": "",
        "esrb_rating": "",
        "developers": game["developers"],
        "genres": game["genres"],
    }

    tag = {"title": game["title"], **game["tag"]}

    localization = {
        "title": game["title"],
        "title_en": game["title"],
        "title_ko": game["title_ko"],
        "title_zh": game["title_zh"],
        "localization_note": "Official regional names from Nintendo Switch 2 lineup pages where available.",
    }

    media = {
        "title": game["title"],
        "image_url": game["image_url"],
        "image_file": image_file,
        "official_url_en": game["official_url_en"],
        "official_url_ko": game["official_url_ko"],
        "official_url_zh": game["official_url_zh"],
        "media_note": "Official Nintendo Switch 2 lineup image cached locally as 1200x675; links point to official game pages, not search results.",
    }

    return recent, tag, localization, media


def sync_switch2_lineup() -> None:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    recent = read_csv(RECENT_PATH, RECENT_COLUMNS)
    tags = read_csv(TAGS_PATH, TAG_COLUMNS)
    localizations = read_csv(LOCALIZATIONS_PATH, LOCALIZATION_COLUMNS)
    media = read_csv(MEDIA_PATH, MEDIA_COLUMNS)

    for game in SWITCH2_GAMES:
        image_file = cache_official_image(session, game)
        recent_row, tag_row, localization_row, media_row = build_rows(game, image_file)
        recent = upsert_row(recent, recent_row, RECENT_COLUMNS)
        tags = upsert_row(tags, tag_row, TAG_COLUMNS)
        localizations = upsert_row(localizations, localization_row, LOCALIZATION_COLUMNS)
        media = upsert_row(media, media_row, MEDIA_COLUMNS)

    write_csv(recent, RECENT_PATH)
    write_csv(tags, TAGS_PATH)
    write_csv(localizations, LOCALIZATIONS_PATH)
    write_csv(media, MEDIA_PATH)

    print(f"Synced {len(SWITCH2_GAMES)} official Switch 2 lineup games.")


if __name__ == "__main__":
    sync_switch2_lineup()
