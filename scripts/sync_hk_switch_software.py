"""Sync Nintendo-published Switch software from Nintendo Hong Kong."""

from __future__ import annotations

from pathlib import Path
import math
import os
import re
from urllib.parse import urlsplit

import pandas as pd
import requests

from fetch_official_media import save_uniform_image
from merge_data import normalize_title


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MEDIA_IMAGE_DIR = DATA_DIR / "media_images"

RECENT_PATH = DATA_DIR / "recent_switch_games.csv"
TAGS_PATH = DATA_DIR / "game_tags_manual.csv"
LOCALIZATIONS_PATH = DATA_DIR / "game_localizations_manual.csv"
MEDIA_PATH = DATA_DIR / "game_media_manual.csv"
MERGED_PATH = DATA_DIR / "nintendo_games_merged.csv"

HK_API_URL = "https://www.nintendo.com/hk/api/software"
HK_SOFTWARE_URL = "https://www.nintendo.com/hk/software/switch?sftab=nintendo"
USER_AGENT = "Mozilla/5.0 (Nintendo Game Compass HK software updater)"
PAGE_SIZE = 24

NON_GAME_TITLE_PATTERNS = [
    r"全島轉移服務",
    r"轉移服務",
    r"转移服务",
    r"transfer service",
    r"體驗版",
    r"体验版",
    r"\bdemo\b",
    r"試玩版",
    r"试玩版",
    r"更新資料",
    r"更新资料",
    r"update data",
    r"追加內容",
    r"追加内容",
    r"additional content",
    r"battle pack",
    r"gold classics pack",
    r"nintendo classics",
    r"nintendo switch online",
    r"calculator",
    r"clock",
]

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

SPECIAL_TITLE_MAP = {
    normalize_title("ZELDA無雙 封印戰記"): "Hyrule Warriors: Age of Imprisonment",
    normalize_title("ZELDA無雙 災厄啟示錄"): "Hyrule Warriors: Age of Calamity",
    normalize_title("Fire Emblem無雙"): "Fire Emblem Warriors",
    normalize_title("Fire Emblem 風花雪月"): "Fire Emblem: Three Houses",
    normalize_title("異度神劍X 終極版"): "Xenoblade Chronicles X: Definitive Edition",
    normalize_title("異度神劍2"): "Xenoblade Chronicles 2",
    normalize_title("薩爾達傳說 曠野之息"): "The Legend of Zelda: Breath of the Wild",
    normalize_title("瑪利歐vs.咚奇剛"): "Mario vs. Donkey Kong",
    normalize_title("進め！キノピオ隊長"): "Captain Toad: Treasure Tracker",
    normalize_title("Splatoon™ 2 (日文版)"): "Splatoon 2",
    normalize_title("ポッ拳　POKKÉN TOURNAMENT DX"): "Pokken Tournament DX",
}

LOCALIZATION_REPAIRS = {
    "Arcade Archives: Vs. Super Mario Bros.": {
        "title_zh": "Arcade Archives: Vs. Super Mario Bros.",
        "official_url_zh": "",
    },
    "Overcooked 2": {
        "title_zh": "Overcooked! 2",
        "official_url_zh": "https://ec.nintendo.com/HK/zh/titles/70010000033098",
    },
    "Fire Emblem Warriors": {
        "title_zh": "Fire Emblem無雙",
        "official_url_zh": "https://www.nintendo.com/hk/switch/fire_emblem_warriors/store/",
    },
    "Tomodachi Life 朋友收集 夢想生活": {
        "title_zh": "Tomodachi Life 朋友收集 夢想生活",
        "official_url_en": "https://www.nintendo.com/hk/switch/blfga/",
        "official_url_zh": "https://www.nintendo.com/hk/switch/blfga/",
    },
}

SWITCH2_EDITION_TITLE_MAP = {
    normalize_title("星之卡比 探索發現 Nintendo Switch 2 Edition + 星耀世界"): "Kirby and the Forgotten Land + Star-Crossed World",
}

SUPPLEMENTAL_RELEASE_DATES = {
    "Celeste": "2018-01-25",
    "Fire Emblem Warriors": "2017-09-28",
    "Hades": "2020-09-17",
    "Hollow Knight": "2018-06-12",
    "Metroid Dread": "2021-10-08",
    "New Pokemon Snap": "2021-04-30",
    "Overcooked 2": "2018-08-07",
    "Stardew Valley": "2017-10-05",
}


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


def is_blank(value: object) -> bool:
    return value is None or str(value).strip() == "" or str(value).strip().lower() == "nan"


def is_non_game_title(title: str) -> bool:
    return any(re.search(pattern, title, flags=re.IGNORECASE) for pattern in NON_GAME_TITLE_PATTERNS)


def prefer_new(current: object, new_value: object) -> str:
    if not is_blank(new_value):
        return str(new_value).strip()
    if not is_blank(current):
        return str(current).strip()
    return ""


def is_eshop_url(value: object) -> bool:
    return "ec.nintendo.com" in str(value)


def prefer_detail_url(current: object, new_value: object) -> str:
    if is_blank(current):
        return "" if is_blank(new_value) else str(new_value).strip()
    if is_blank(new_value):
        return str(current).strip()
    if is_eshop_url(current) and not is_eshop_url(new_value):
        return str(new_value).strip()
    return str(current).strip()


def upsert_row(dataframe: pd.DataFrame, row: dict[str, str], columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column not in dataframe.columns:
            dataframe[column] = ""
        row.setdefault(column, "")

    title = normalize_title(row["title"])
    mask = dataframe["title"].map(normalize_title) == title
    if mask.any():
        index = dataframe.index[mask][0]
        for column in columns:
            dataframe.at[index, column] = prefer_new(dataframe.at[index, column], row[column])
    else:
        dataframe = pd.concat([dataframe, pd.DataFrame([row])], ignore_index=True)

    return dataframe[columns]


def upsert_media_row(dataframe: pd.DataFrame, row: dict[str, str]) -> pd.DataFrame:
    title = normalize_title(row["title"])
    mask = dataframe["title"].map(normalize_title) == title
    if not mask.any():
        return pd.concat([dataframe, pd.DataFrame([row])], ignore_index=True)[MEDIA_COLUMNS]

    index = dataframe.index[mask][0]
    for column in MEDIA_COLUMNS:
        if column in {"official_url_en", "official_url_ko", "official_url_zh"}:
            dataframe.at[index, column] = prefer_detail_url(dataframe.at[index, column], row[column])
        elif column in {"image_url", "image_file"}:
            dataframe.at[index, column] = prefer_new(row[column], dataframe.at[index, column])
        else:
            dataframe.at[index, column] = prefer_new(dataframe.at[index, column], row[column])
    return dataframe[MEDIA_COLUMNS]


def build_existing_title_map(localizations: pd.DataFrame) -> dict[str, str]:
    title_map: dict[str, str] = {}
    for _, row in localizations.iterrows():
        canonical = str(row.get("title", "")).strip()
        if not canonical:
            continue
        for column in ["title", "title_en", "title_ko", "title_zh"]:
            value = str(row.get(column, "")).strip()
            if value:
                title_map[normalize_title(value)] = canonical
    title_map.update(SPECIAL_TITLE_MAP)
    return title_map


def apply_repairs(localizations: pd.DataFrame, media: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    for title, repair in LOCALIZATION_REPAIRS.items():
        loc_mask = localizations["title"].map(normalize_title) == normalize_title(title)
        if loc_mask.any():
            index = localizations.index[loc_mask][0]
            localizations.at[index, "title_en"] = title
            localizations.at[index, "title_zh"] = repair["title_zh"]
        media_mask = media["title"].map(normalize_title) == normalize_title(title)
        if media_mask.any():
            index = media.index[media_mask][0]
            if "official_url_en" in repair:
                media.at[index, "official_url_en"] = repair["official_url_en"]
            media.at[index, "official_url_zh"] = repair["official_url_zh"]
    return localizations, media


def strip_language_suffix(title: str) -> str:
    return re.sub(r"[（(](日文版|英文版|繁體中文版|中文版)[）)]", "", title).strip()


def canonical_title(item: dict, title_map: dict[str, str]) -> str:
    title = str(item.get("title", "")).strip()
    if re.search(r"Pokémon (FireRed|LeafGreen) Version", title):
        return "Pokémon FireRed / LeafGreen Version"

    if item.get("hardwareCategory") == "Nintendo Switch 2 Edition":
        mapped = SWITCH2_EDITION_TITLE_MAP.get(normalize_title(title))
        return mapped or title

    for candidate in [title, strip_language_suffix(title)]:
        mapped = title_map.get(normalize_title(candidate))
        if mapped:
            return mapped

    return title


def nintendo_url(link: str) -> str:
    if not link:
        return ""
    if link.startswith("http"):
        return link.strip()
    return f"https://www.nintendo.com{link}".strip()


def official_hk_url(item: dict) -> str:
    custom_link = str(item.get("pageLinkCustom") or "").strip()
    if custom_link:
        return nintendo_url(custom_link)

    if item.get("softwarePortal"):
        hardware = item.get("hardwareCategory", "")
        soft_code = item.get("softCode", "")
        if hardware == "Nintendo Switch 2":
            return nintendo_url(f"/hk/switch2/{soft_code}/portal")
        if hardware == "Nintendo Switch 2 Edition":
            return nintendo_url(f"/hk/switch2/edition/{soft_code}/portal")
        if hardware == "Nintendo Switch":
            return nintendo_url(f"/hk/switch/{soft_code}/portal")

    page_link = str(item.get("pageLink") or "")
    if "{NSUID}" in page_link:
        return page_link.replace("{NSUID}", str(item.get("nsuid", "")))
    if page_link == "リンクなし":
        return ""
    return nintendo_url(page_link)


def release_date(item: dict) -> str:
    for field in ["releaseDate", "releaseDateDownload", "releaseDatePackage"]:
        value = item.get(field)
        if value:
            return str(value)[:10]
    return ""


def original_image_url(item: dict) -> str:
    url = (item.get("imageHero") or {}).get("url") or item.get("imageHeroOrg") or ""
    if not url:
        return ""
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}{parts.path}"


def filename_for_item(item: dict, canonical: str) -> str:
    if canonical == "Pokémon FireRed / LeafGreen Version":
        return "data/media_images/hk_pokemon_firered_leafgreen.jpg"
    nsuid = re.sub(r"[^0-9A-Za-z]+", "", str(item.get("nsuid", "")))
    if nsuid:
        return f"data/media_images/hk_{nsuid}.jpg"
    fallback = re.sub(r"[^a-z0-9]+", "_", normalize_title(canonical)).strip("_") or "official_hk_game"
    return f"data/media_images/hk_{fallback}.jpg"


def fetch_hk_items(session: requests.Session) -> tuple[list[dict], int]:
    first = session.get(HK_API_URL, params={"sftab": "nintendo"}, timeout=30).json()
    total = int(first.get("total", 0))
    pages = max(1, math.ceil(total / PAGE_SIZE))
    items: list[dict] = []
    seen_exact: set[tuple[str, str]] = set()
    fire_leaf_item: dict | None = None

    for page in range(1, pages + 1):
        data = session.get(HK_API_URL, params={"sftab": "nintendo", "spage": page}, timeout=30).json()
        for item in data.get("items", []):
            title = str(item.get("title", "")).strip()
            if is_non_game_title(title):
                continue

            key = (str(item.get("nsuid", "")).strip(), title)
            if key in seen_exact:
                continue
            seen_exact.add(key)

            if re.search(r"Pokémon (FireRed|LeafGreen) Version", title):
                if fire_leaf_item is None or "FireRed" in title:
                    fire_leaf_item = item
                continue

            items.append(item)

    if fire_leaf_item is not None:
        fire_leaf_item = {**fire_leaf_item, "title": "Pokémon FireRed / LeafGreen Version"}
        items.append(fire_leaf_item)

    return items, total


def platform_group(hardware: str) -> str:
    if hardware == "Nintendo Switch 2":
        return "Switch 2"
    if hardware == "Nintendo Switch 2 Edition":
        return "Switch 2 Edition"
    return "Switch Compatible"


def relation_for(title: str, publisher: str) -> str:
    if publisher and publisher.lower() != "nintendo":
        return "Third-party"
    core_words = [
        "瑪利歐",
        "Mario",
        "薩爾達",
        "Zelda",
        "Splatoon",
        "斯普拉遁",
        "Metroid",
        "密特羅德",
        "Pikmin",
        "皮克敏",
        "Donkey Kong",
        "咚奇剛",
        "路易吉",
        "Wario",
        "瓦利歐",
        "Yoshi",
        "耀西",
        "Nintendo Labo",
        "Ring Fit",
        "ARMS",
        "1-2-Switch",
    ]
    if any(word in title for word in core_words):
        return "Nintendo Core"
    return "Nintendo Published"


def genre_for(title: str) -> str:
    rules = [
        (["Mario Kart", "瑪利歐賽車", "Air Riders", "馭天飛行者"], "Racing"),
        (["Mario Party", "瑪利歐派對", "WarioWare", "瓦利歐製造", "1-2-Switch"], "Party"),
        (["Fitness", "Ring Fit", "運動", "Sports", "Tennis", "網球"], "Sports"),
        (["Boxing", "Fit"], "Fitness"),
        (["Pokémon", "寶可夢", "異度神劍", "Xenoblade", "Fire Emblem", "瑪利歐RPG", "Paper Mario", "紙片瑪利歐"], "RPG"),
        (["Famicom偵探", "Another Code", "笑臉男"], "Adventure"),
        (["Zelda", "薩爾達", "Pikmin", "皮克敏", "Luigi", "路易吉", "Donkey Kong", "咚奇剛"], "Adventure"),
        (["Metroid", "密特羅德", "Splatoon", "斯普拉遁", "Star Fox"], "Shooter"),
        (["Kirby", "卡比", "耀西", "Yoshi", "Captain Toad", "キノピオ"], "Platformer"),
        (["Puzzle", "Picross", "Dr. Mario", "腦鍛鍊", "Brain", "Snipperclips", "你裁我剪"], "Puzzle"),
        (["Rhythm", "節奏天國"], "Rhythm"),
        (["Smash", "大亂鬥", "Pokkén", "POKKÉN", "蓓優妮塔"], "Fighting"),
        (["Labo", "Welcome Tour", "秘密展"], "Puzzle"),
        (["Tomodachi", "朋友收集", "Animal Crossing", "集合啦！動物森友會"], "Simulation"),
    ]
    for keywords, genre in rules:
        if any(keyword.lower() in title.lower() for keyword in keywords):
            return genre
    return "Adventure"


def tag_profile(title: str, genre: str, hardware: str, categories: list[str]) -> dict[str, str]:
    is_online = "Nintendo Classics" in title or "Online" in title or "斯普拉遁" in title or "Splatoon" in title
    is_local = genre in {"Party", "Racing", "Sports", "Fighting"} or "多人" in title
    beginner = "No" if genre in {"Fighting", "Shooter"} and "Splatoon" not in title else "Yes"
    difficulty = "Hard" if genre in {"Fighting"} else "Medium" if genre in {"RPG", "Shooter", "Strategy"} else "Easy"
    session = "Long" if genre in {"RPG", "Simulation"} else "Short" if genre in {"Party", "Racing", "Sports", "Puzzle", "Rhythm"} else "Medium"
    mood = {
        "Racing": "Fun",
        "Party": "Fun",
        "Sports": "Active",
        "Fitness": "Active",
        "RPG": "Story",
        "Shooter": "Exciting",
        "Platformer": "Cute",
        "Simulation": "Healing",
        "Puzzle": "Creative",
        "Rhythm": "Fun",
        "Fighting": "Exciting",
    }.get(genre, "Immersive")
    player_type = {
        "Racing": "Party Player",
        "Party": "Party Player",
        "Sports": "Family Player",
        "Fitness": "Family Player",
        "RPG": "Story Player",
        "Shooter": "Competitive Player",
        "Platformer": "Beginner",
        "Simulation": "Relaxed Player",
        "Puzzle": "Beginner",
        "Rhythm": "Party Player",
        "Fighting": "Competitive Player",
    }.get(genre, "Explorer")
    situation = "Friends|Family|Party|Short Break" if is_local else "Online|Short Break" if is_online else "Solo|Long Session" if session == "Long" else "Solo|Short Break"
    budget = "High" if "盒裝版" in categories or hardware == "Nintendo Switch 2" else "Medium"
    return {
        "genre_main": genre,
        "player_type": player_type,
        "play_situation": situation,
        "difficulty": difficulty,
        "mood": mood,
        "session_length": session,
        "beginner_friendly": beginner,
        "local_multiplayer": "Yes" if is_local else "No",
        "online_multiplayer": "Yes" if is_online else "No",
        "budget_tier": budget,
        "buying_advice": "Official Nintendo HK listing. Use the filters to decide whether this fits your play situation, budget, and session length.",
    }


def genres_value(genre: str) -> str:
    return f"['{genre}']"


def build_existing_meta() -> dict[str, dict[str, str]]:
    if not MERGED_PATH.exists():
        return {}
    merged = pd.read_csv(MERGED_PATH, keep_default_na=False)
    return {
        normalize_title(row["title"]): row.to_dict()
        for _, row in merged.iterrows()
        if str(row.get("title", "")).strip()
    }


def cache_image(session: requests.Session, item: dict, canonical: str, existing_file: str = "") -> tuple[str, str]:
    if existing_file and (PROJECT_ROOT / existing_file).exists():
        return original_image_url(item), existing_file

    image_url = original_image_url(item)
    if not image_url:
        return "", ""

    image_file = filename_for_item(item, canonical)
    output_path = PROJECT_ROOT / image_file
    response = session.get(image_url, timeout=30)
    response.raise_for_status()
    save_uniform_image(response.content, output_path)
    return image_url, image_file


def sync_hk_switch_software() -> None:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})

    recent = read_csv(RECENT_PATH, RECENT_COLUMNS)
    tags = read_csv(TAGS_PATH, TAG_COLUMNS)
    localizations = read_csv(LOCALIZATIONS_PATH, LOCALIZATION_COLUMNS)
    media = read_csv(MEDIA_PATH, MEDIA_COLUMNS)
    existing_meta = build_existing_meta()
    title_map = build_existing_title_map(localizations)

    items, official_total = fetch_hk_items(session)

    imported = 0
    for item in items:
        official_title = str(item.get("title", "")).strip()
        canonical = canonical_title(item, title_map)
        normalized = normalize_title(canonical)
        existing = existing_meta.get(normalized, {})
        existing_media = media[media["title"].map(normalize_title) == normalized]
        existing_media_row = existing_media.iloc[0].to_dict() if not existing_media.empty else {}
        categories = item.get("category") or []
        hardware = str(item.get("hardwareCategory") or "Nintendo Switch")
        publisher = str(item.get("publisher") or "")
        developer = str(item.get("developer") or publisher or "Nintendo")
        genre = genre_for(f"{canonical} {official_title}")
        image_url, image_file = cache_image(session, item, canonical, str(existing_media_row.get("image_file", "")))
        official_url_zh = official_hk_url(item)

        recent_row = {
            "title": canonical,
            "platform": hardware,
            "date": release_date(item),
            "meta_score": existing.get("meta_score", ""),
            "user_score": existing.get("user_score", ""),
            "esrb_rating": existing.get("esrb_rating", ""),
            "developers": developer,
            "genres": existing.get("genres", "") or genres_value(genre),
        }

        profile = tag_profile(f"{canonical} {official_title}", genre, hardware, categories)
        tag_row = {
            "title": canonical,
            "platform_group": platform_group(hardware),
            "nintendo_relation": relation_for(f"{canonical} {official_title}", publisher),
            **profile,
        }

        localization_row = {
            "title": canonical,
            "title_en": existing.get("title_en", "") or canonical,
            "title_ko": existing.get("title_ko", ""),
            "title_zh": official_title,
            "localization_note": f"Chinese title and release metadata synced from Nintendo HK software list: {HK_SOFTWARE_URL}",
        }

        media_row = {
            "title": canonical,
            "image_url": image_url or existing_media_row.get("image_url", ""),
            "image_file": image_file or existing_media_row.get("image_file", ""),
            "official_url_en": existing_media_row.get("official_url_en", "") or official_url_zh,
            "official_url_ko": existing_media_row.get("official_url_ko", ""),
            "official_url_zh": official_url_zh,
            "media_note": "Official Nintendo HK software listing image cached locally as 1200x675; HK detail page is used when no other regional page is verified.",
        }

        recent = upsert_row(recent, recent_row, RECENT_COLUMNS)
        tags = upsert_row(tags, tag_row, TAG_COLUMNS)
        localizations = upsert_row(localizations, localization_row, LOCALIZATION_COLUMNS)
        media = upsert_media_row(media, media_row)
        imported += 1

    for title, date in SUPPLEMENTAL_RELEASE_DATES.items():
        existing = existing_meta.get(normalize_title(title), {})
        recent = upsert_row(
            recent,
            {
                "title": title,
                "platform": existing.get("platform", "Nintendo Switch"),
                "date": date,
                "meta_score": existing.get("meta_score", ""),
                "user_score": existing.get("user_score", ""),
                "esrb_rating": existing.get("esrb_rating", ""),
                "developers": existing.get("developers", ""),
                "genres": existing.get("genres", ""),
            },
            RECENT_COLUMNS,
        )

    localizations, media = apply_repairs(localizations, media)

    write_csv(recent, RECENT_PATH)
    write_csv(tags, TAGS_PATH)
    write_csv(localizations, LOCALIZATIONS_PATH)
    write_csv(media, MEDIA_PATH)

    print(f"Official HK total: {official_total}")
    print(f"Synced rows after exact/version dedupe: {imported}")


if __name__ == "__main__":
    sync_hk_switch_software()
