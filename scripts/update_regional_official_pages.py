"""Update Korean and Chinese official game names and regional page links.

This script uses Nintendo Korea and Nintendo Hong Kong's public search API.
It treats the API result card as the source of truth for localized game names
and regional official links. It does not write search-result URLs.
"""

from __future__ import annotations

from pathlib import Path
import csv
import json
import os
import re
import time
import unicodedata
from urllib.parse import quote, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
LOCALIZATIONS_PATH = DATA_DIR / "game_localizations_manual.csv"
MEDIA_PATH = DATA_DIR / "game_media_manual.csv"
REPORT_PATH = DATA_DIR / "regional_official_missing.csv"

API_ROOTS = {
    "ko": "https://www.nintendo.com/kr/",
    "zh": "https://www.nintendo.com/hk/",
}

USER_AGENT = "Mozilla/5.0 (Nintendo Game Compass regional updater)"

BAD_RESULT_TERMS = [
    "upgrade pass",
    "업그레이드",
    "升級",
    "升级",
    "擴充票",
    "追加內容",
    "dlc",
]

TITLE_ALIASES = {
    "zh": {
        "Metroid Prime 4: Beyond": ["密特羅德 究極4 穿越未知", "密特羅德"],
        "Pokémon Legends: Z-A": ["寶可夢傳說 Z-A", "Pokémon LEGENDS Z-A"],
        "Mario Kart World": ["瑪利歐賽車世界"],
        "Donkey Kong Country Returns HD": ["咚奇剛 歸來 HD", "咚奇剛 歸來"],
        "Super Mario Party Jamboree": ["超級瑪利歐派對 空前盛會"],
        "Metroid Prime Remastered": ["密特羅德 究極 復刻版", "密特羅德"],
        "Splatoon 3": ["斯普拉遁 3"],
        "Mario Strikers: Battle League": ["瑪利歐激戰前鋒 戰鬥聯賽", "瑪利歐激戰前鋒"],
        "Nintendo Switch Sports": ["Nintendo Switch 運動"],
        "Pokemon Legends: Arceus": ["寶可夢傳說 阿爾宙斯"],
        "Hyrule Warriors: Age of Calamity": ["ZELDA無雙 災厄啟示錄"],
        "Pikmin 3 Deluxe": ["皮克敏３ 豪華版", "皮克敏3"],
        "Part Time UFO": ["打工UFO"],
        "Kirby Fighters 2": ["卡比鬥士2", "卡比鬥士"],
        "Pokemon Mystery Dungeon: Rescue Team DX": ["寶可夢不可思議迷宮 救助隊DX"],
        "The Stretchers": ["救援擔架隊"],
        "Ring Fit Adventure": ["健身環大冒險"],
        "Little Town Hero": ["小鎮英雄"],
        "Super Kirby Clash": ["超級卡比獵人隊"],
        "Astral Chain": ["ASTRAL CHAIN"],
        "Cadence of Hyrule: Crypt of the NecroDancer Featuring The Legend of Zelda": [
            "節奏海拉魯",
            "Cadence of Hyrule",
        ],
        "Xenoblade Chronicles 2: Torna ~ The Golden Country": ["異度神劍2 黃金之國伊拉"],
        "Captain Toad: Treasure Tracker": ["前進！奇諾比奧隊長", "奇諾比奧隊長"],
        "Mario Tennis Aces": ["瑪利歐網球 王牌", "瑪利歐網球"],
        "Hyrule Warriors: Definitive Edition": ["ZELDA無雙 海拉魯全明星 豪華版"],
        "Fire Emblem Warriors": ["Fire Emblem無雙"],
        "Pokken Tournament DX": ["寶可拳"],
        "Flip Wars": ["翻轉大戰", "翻轉"],
        "Pokemon Scarlet": ["寶可夢 朱"],
        "Pokemon Violet": ["寶可夢 紫"],
        "Pokemon Sword": ["寶可夢 劍"],
        "Pokemon Shield": ["寶可夢 盾"],
        "Super Smash Bros. Ultimate": ["任天堂明星大亂鬥 特別版"],
        "Luigi's Mansion 3": ["路易吉洋樓３"],
        "Animal Crossing: New Horizons": ["集合啦！動物森友會", "Animal Crossing"],
    },
    "ko": {
        "Pokemon Scarlet": ["포켓몬스터스칼렛", "포켓몬스터 스칼렛"],
        "Pokemon Violet": ["포켓몬스터바이올렛", "포켓몬스터 바이올렛"],
        "Pokemon Sword": ["포켓몬스터소드", "포켓몬스터 소드"],
        "Pokemon Shield": ["포켓몬스터실드", "포켓몬스터 실드"],
        "Part Time UFO": ["알바생 UFO"],
        "Clubhouse Games: 51 Worldwide Classics": ["세계 놀이 대전 51", "세계 놀이 대전"],
        "Tokyo Mirage Sessions #FE Encore": ["환영이문록 #FE Encore", "환영이문록"],
        "The Stretchers": ["스트레처즈"],
        "Little Town Hero": ["리틀 타운 히어로"],
        "Overcooked 2": ["오버쿡드 2", "Overcooked! 2"],
        "Arcade Archives: Pinball": ["아케이드 아카이브스 핀볼"],
        "Arcade Archives: Donkey Kong": ["아케이드 아카이브스 동키콩"],
        "Arcade Archives: Punch-Out!": ["아케이드 아카이브스 펀치 아웃"],
        "Arcade Archives: Mario Bros.": ["아케이드 아카이브스 마리오브라더스"],
    },
}

SIMPLIFIED_TO_OFFICIAL_ZH = {
    "超级": "超級",
    "马力欧": "瑪利歐",
    "塞尔达传说": "薩爾達傳說",
    "塞尔达": "薩爾達",
    "传说": "傳說",
    "王国之泪": "王國之淚",
    "旷野之息": "曠野之息",
    "智慧的再现": "智慧的再現",
    "异度神剑": "異度神劍",
    "终极版": "終極版",
    "咚奇刚": "咚奇剛",
    "回归": "歸來",
    "全开": "全開",
    "纸片": "紙片",
    "惊奇": "驚奇",
    "瓦力欧": "瓦利歐",
    "动物森友会": "動物森友會",
    "路易吉洋馆": "路易吉洋樓",
    "健身环": "健身環",
    "任天堂明星大乱斗": "任天堂明星大亂鬥",
    "特别版": "特別版",
    "豪华版": "豪華版",
    "卡丁车": "賽車",
    "奥德赛": "奧德賽",
    "生存恐惧": "生存恐懼",
    "宝可梦": "寶可夢",
    "剑": "劍",
    "运动": "運動",
    "战斗": "戰鬥",
    "联赛": "聯賽",
    "无双": "無雙",
    "灾厄": "災厄",
    "启示录": "啟示錄",
    "海拉鲁": "海拉魯",
    "黄金之国": "黃金之國",
    "寻觅逝去的时光": "尋覓逝去的時光",
    "表演时刻": "表演時刻",
    "阿尔宙斯": "阿爾宙斯",
    "探索发现": "探索發現",
    "星之交错世界": "星耀世界",
    "前进": "前進",
    "奇诺比奥": "奇諾比奧",
    "队长": "隊長",
    "创作家": "創作家",
    "翻转": "翻轉",
    "气球": "氣球",
    "都市冠军": "都市冠軍",
    "弹珠台": "彈珠台",
    "克鲁克鲁": "克魯克魯",
    "随乐拍": "隨樂拍",
    "不可思议": "不可思議",
    "迷宫": "迷宮",
    "救助队": "救助隊",
    "舞动": "舞動",
    "制造": "製造",
    "小镇": "小鎮",
    "节奏": "節奏",
    "死灵": "死靈",
    "猎人队": "獵人隊",
    "担架": "擔架",
}


def to_official_zh(text: str) -> str:
    output = str(text or "")
    for source, target in sorted(SIMPLIFIED_TO_OFFICIAL_ZH.items(), key=lambda item: -len(item[0])):
        output = output.replace(source, target)
    return output


def normalize_text(text: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(text or "")).lower()
    normalized = normalized.replace("pokémon", "pokemon").replace("&", "and")
    normalized = re.sub(
        r"nintendo switch 2 edition|nintendo switch|edition|deluxe|hd|dx|"
        r"the|版|豪華版|豪华版|終極版|终极版|特別版|特别版|重製版|重制版|\(.*?\)",
        " ",
        normalized,
    )
    normalized = re.sub(r"[^0-9a-z가-힣一-龥ぁ-ゟ゠-ヿ]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def compact_text(text: object) -> str:
    return re.sub(r"\s+", "", normalize_text(text))


def query_official_api(region: str, query: str) -> list[dict[str, object]]:
    api_url = (
        f"{API_ROOTS[region]}api/search?"
        f"k={quote(query)}&directory=software&size=20"
    )
    request = Request(api_url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=8) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("items", [])


def build_queries(row: pd.Series, region: str) -> list[str]:
    title = str(row["title"])
    localized_column = "title_ko" if region == "ko" else "title_zh"
    base_queries = [
        *TITLE_ALIASES.get(region, {}).get(title, []),
        str(row.get(localized_column, "")),
        str(row.get("title_en", "")),
        title,
    ]

    queries: list[str] = []
    for query in base_queries:
        query = query.strip()
        if query and query not in queries:
            queries.append(query)
        if region == "zh":
            official_zh = to_official_zh(query).strip()
            if official_zh and official_zh not in queries:
                queries.append(official_zh)

    if not TITLE_ALIASES.get(region, {}).get(title):
        for query in list(queries)[:3]:
            for part in re.split(r"[:：\-–~+]| Nintendo ", query):
                part = part.strip()
                if len(part) >= 3 and part not in queries:
                    queries.append(part)

    return queries[:6]


def atomic_to_csv(dataframe: pd.DataFrame, path: Path) -> None:
    temp_path = path.with_name(f"{path.stem}.tmp{path.suffix}")
    dataframe.to_csv(temp_path, index=False)
    os.replace(temp_path, path)
    path.chmod(0o444)


def regional_url(item: dict[str, object], region: str) -> str:
    link = str(item.get("pageLinkCustom") or item.get("pageLink") or "").strip()
    nsuid = str(item.get("nsuid") or "").strip()
    if "{NSUID}" in link:
        link = link.replace("{NSUID}", nsuid)
    if link.startswith("/"):
        link = urljoin("https://www.nintendo.com", link)
    parsed = urlparse(link)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def is_bad_result(item: dict[str, object], expected_title: str) -> bool:
    title = str(item.get("title") or "")
    lowered = title.lower()
    expected = expected_title.lower()
    if any(term in lowered or term in title for term in BAD_RESULT_TERMS):
        return True
    if expected == "hades" and re.search(r"\bhades\s*(ii|2)\b", lowered):
        return True
    if expected == "hollow knight" and ("silksong" in lowered or "실크송" in title):
        return True
    if "garden of the greek gods" in lowered:
        return True
    return False


def score_item(row: pd.Series, item: dict[str, object], region: str) -> int:
    title = str(item.get("title") or "")
    expected_names = [
        str(row["title"]),
        str(row.get("title_en", "")),
        str(row.get("title_ko" if region == "ko" else "title_zh", "")),
    ]
    if region == "zh":
        expected_names.extend(to_official_zh(name) for name in expected_names)

    candidate = normalize_text(title)
    candidate_compact = compact_text(title)
    best = 0

    for expected_name in expected_names:
        expected = normalize_text(expected_name)
        expected_compact = compact_text(expected_name)
        if not expected or not candidate:
            continue

        if expected == candidate or expected_compact == candidate_compact:
            best = max(best, 100)
        elif expected_compact and (
            expected_compact in candidate_compact or candidate_compact in expected_compact
        ):
            best = max(best, 92)
        else:
            expected_tokens = set(expected.split())
            candidate_tokens = set(candidate.split())
            if expected_tokens and candidate_tokens:
                overlap = len(expected_tokens & candidate_tokens) / max(
                    len(expected_tokens), len(candidate_tokens)
                )
                best = max(best, int(overlap * 100))

    if is_bad_result(item, str(row["title"])):
        best -= 50

    # Prefer normal product pages over update passes and loosely related eShop titles.
    if str(item.get("nintendoSoft") or "") == "['YES']":
        best += 2
    if "Nintendo Switch 2 Edition" in title and "Nintendo Switch 2 Edition" not in str(row["title"]):
        best -= 3

    return best


def choose_best(row: pd.Series, region: str, cache: dict[tuple[str, str], list[dict[str, object]]]) -> dict[str, object] | None:
    seen: set[tuple[str, str, str]] = set()
    candidates: list[tuple[int, dict[str, object]]] = []

    for query in build_queries(row, region):
        cache_key = (region, query)
        if cache_key not in cache:
            try:
                cache[cache_key] = query_official_api(region, query)
                time.sleep(0.05)
            except Exception:
                cache[cache_key] = []
        for item in cache[cache_key]:
            key = (
                str(item.get("title") or ""),
                str(item.get("nsuid") or ""),
                str(item.get("pageLinkCustom") or item.get("pageLink") or ""),
            )
            if key in seen:
                continue
            seen.add(key)
            score = score_item(row, item, region)
            if score >= 65:
                candidates.append((score, item))

    candidates.sort(key=lambda candidate: candidate[0], reverse=True)
    return candidates[0][1] if candidates else None


def main() -> None:
    localizations = pd.read_csv(LOCALIZATIONS_PATH, keep_default_na=False)
    media = pd.read_csv(MEDIA_PATH, keep_default_na=False)
    cache: dict[tuple[str, str], list[dict[str, object]]] = {}
    missing_rows: list[dict[str, str]] = []
    updated_counts = {"ko": 0, "zh": 0}

    media_by_title = media.set_index("title", drop=False)

    for index, row in localizations.iterrows():
        title = str(row["title"])
        for region, title_column, url_column in [
            ("ko", "title_ko", "official_url_ko"),
            ("zh", "title_zh", "official_url_zh"),
        ]:
            best = choose_best(row, region, cache)
            if not best:
                missing_rows.append(
                    {
                        "title": title,
                        "region": region,
                        "queries": " | ".join(build_queries(row, region)[:6]),
                    }
                )
                continue

            official_title = str(best.get("title") or "").strip()
            official_link = regional_url(best, region)
            if not official_title or not official_link:
                continue

            localizations.at[index, title_column] = official_title
            if title in media_by_title.index:
                media_index = media_by_title.index.get_loc(title)
                media.at[media_index, url_column] = official_link
            updated_counts[region] += 1

    localizations["localization_note"] = (
        "Official localized title from Nintendo regional search API where available"
    )
    media["media_note"] = media["media_note"].astype(str).str.replace(
        " | Exact regional game detail pages only; no search-result fallback.",
        "",
        regex=False,
    )
    media["media_note"] = (
        media["media_note"].str.rstrip()
        + " | Regional links come from Nintendo regional search API cards when available; no search-result fallback."
    )

    atomic_to_csv(localizations, LOCALIZATIONS_PATH)
    atomic_to_csv(media, MEDIA_PATH)

    with REPORT_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=["title", "region", "queries"])
        writer.writeheader()
        writer.writerows(missing_rows)

    print(f"Updated Korean official entries: {updated_counts['ko']}")
    print(f"Updated Chinese official entries: {updated_counts['zh']}")
    print(f"Missing regional matches written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
