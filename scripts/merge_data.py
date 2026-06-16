"""Merge historical and recent Nintendo Switch game data."""

from pathlib import Path
import os
import re
import unicodedata

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CLEAN_DATA_PATH = DATA_DIR / "nintendo_games_clean.csv"
RECENT_DATA_PATH = DATA_DIR / "recent_switch_games.csv"
MANUAL_TAGS_PATH = DATA_DIR / "game_tags_manual.csv"
LOCALIZATIONS_PATH = DATA_DIR / "game_localizations_manual.csv"
MEDIA_PATH = DATA_DIR / "game_media_manual.csv"
MERGED_DATA_PATH = DATA_DIR / "nintendo_games_merged.csv"

TAG_COLUMNS = [
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
    "title_en",
    "title_ko",
    "title_zh",
    "localization_note",
]

MEDIA_COLUMNS = [
    "image_url",
    "image_file",
    "official_url_en",
    "official_url_ko",
    "official_url_zh",
    "media_note",
]

OUTPUT_COLUMNS = [
    "title",
    "platform",
    "date",
    "meta_score",
    "user_score",
    "link",
    "esrb_rating",
    "developers",
    "genres",
    *TAG_COLUMNS,
    *LOCALIZATION_COLUMNS,
    *MEDIA_COLUMNS,
    "normalized_title",
]

PLATFORM_PRIORITY = {
    "Nintendo Switch 2": 0,
    "Nintendo Switch": 1,
}

NON_GAME_PATTERNS = [
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


def normalize_column_name(column_name: str) -> str:
    """Convert source column names into predictable snake_case names."""
    normalized = column_name.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


def normalize_title(title: object) -> str:
    """Create a stable title key for duplicate detection."""
    if pd.isna(title):
        return ""
    normalized = unicodedata.normalize("NFKC", str(title)).casefold()
    normalized = re.sub(r"[^\w]+", " ", normalized, flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized = re.sub(r"^the\s+", "", normalized)
    normalized = re.sub(r"\s+the$", "", normalized)
    return normalized


def is_non_game_row(row: pd.Series) -> bool:
    """Identify service utilities, demos, DLC packs, and subscription app entries."""
    title_text = " ".join(
        str(row.get(column, ""))
        for column in ["title", "title_en", "title_ko", "title_zh", "genres"]
    )
    return any(re.search(pattern, title_text, flags=re.IGNORECASE) for pattern in NON_GAME_PATTERNS)


def standardize_platform(platform: object) -> object:
    """Normalize common Switch platform labels."""
    if pd.isna(platform):
        return pd.NA

    platform_text = str(platform).strip()
    lower_platform = platform_text.lower()

    if lower_platform in {"switch", "nintendo switch"}:
        return "Nintendo Switch"
    if lower_platform in {"switch 2", "nintendo switch 2"}:
        return "Nintendo Switch 2"

    return platform_text


def standardize_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Standardize columns, dates, scores, and duplicate keys."""
    dataframe = dataframe.rename(columns={column: normalize_column_name(column) for column in dataframe.columns})
    dataframe = dataframe.rename(
        columns={
            "metascore": "meta_score",
            "release_date": "date",
            "rating": "esrb_rating",
            "developer": "developers",
            "genre": "genres",
            "url": "link",
        }
    )

    for column in OUTPUT_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = pd.NA

    dataframe["title"] = dataframe["title"].astype("string").str.strip()
    dataframe["platform"] = dataframe["platform"].map(standardize_platform)
    dataframe["normalized_title"] = dataframe["title"].map(normalize_title)
    parsed_dates = dataframe["date"].apply(lambda value: pd.to_datetime(value, errors="coerce"))
    dataframe["date"] = parsed_dates.dt.strftime("%Y-%m-%d")

    for column in ["meta_score", "user_score"]:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    return dataframe[OUTPUT_COLUMNS]


def load_recent_games() -> pd.DataFrame:
    """Load recent game supplement data if present."""
    if not RECENT_DATA_PATH.exists():
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    return pd.read_csv(RECENT_DATA_PATH)


def is_blank(value: object) -> bool:
    """Return whether a dataframe value is empty enough to replace."""
    if value is None or pd.isna(value):
        return True
    return str(value).strip() == ""


def merge_manual_tags(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Apply player-oriented manual tags after old/recent data is deduplicated."""
    if not MANUAL_TAGS_PATH.exists():
        return dataframe

    manual_tags = standardize_dataframe(pd.read_csv(MANUAL_TAGS_PATH))
    tag_columns = ["normalized_title", "title", *TAG_COLUMNS]
    manual_tags = manual_tags[tag_columns].drop_duplicates(subset=["normalized_title"], keep="last")

    tagged = dataframe.merge(
        manual_tags,
        on="normalized_title",
        how="outer",
        suffixes=("", "_manual"),
    )

    if "title_manual" in tagged.columns:
        tagged["title"] = tagged["title"].where(~tagged["title"].map(is_blank), tagged["title_manual"])
        tagged = tagged.drop(columns=["title_manual"])

    for column in TAG_COLUMNS:
        manual_column = f"{column}_manual"
        if manual_column in tagged.columns:
            tagged[column] = tagged[manual_column].where(~tagged[manual_column].map(is_blank), tagged[column])
            tagged = tagged.drop(columns=[manual_column])

    tagged["platform"] = tagged["platform"].where(~tagged["platform"].map(is_blank), "Nintendo Switch")
    return tagged[OUTPUT_COLUMNS]


def merge_localizations(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Apply official or store-localized game titles where manually curated."""
    if not LOCALIZATIONS_PATH.exists():
        dataframe["title_en"] = dataframe["title"]
        return dataframe

    localizations = standardize_dataframe(pd.read_csv(LOCALIZATIONS_PATH))
    localization_columns = ["normalized_title", *LOCALIZATION_COLUMNS]
    localizations = localizations[localization_columns].drop_duplicates(subset=["normalized_title"], keep="last")

    localized = dataframe.merge(
        localizations,
        on="normalized_title",
        how="left",
        suffixes=("", "_localized"),
    )

    for column in LOCALIZATION_COLUMNS:
        localized_column = f"{column}_localized"
        if localized_column in localized.columns:
            localized[column] = localized[localized_column].where(
                ~localized[localized_column].map(is_blank),
                localized[column],
            )
            localized = localized.drop(columns=[localized_column])

    localized["title_en"] = localized["title_en"].where(~localized["title_en"].map(is_blank), localized["title"])
    return localized[OUTPUT_COLUMNS]


def merge_media(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Apply curated official images and regional Nintendo page links."""
    if not MEDIA_PATH.exists():
        return dataframe[OUTPUT_COLUMNS]

    media = standardize_dataframe(pd.read_csv(MEDIA_PATH))
    media_columns = ["normalized_title", *MEDIA_COLUMNS]
    media = media[media_columns].drop_duplicates(subset=["normalized_title"], keep="last")

    with_media = dataframe.merge(
        media,
        on="normalized_title",
        how="left",
        suffixes=("", "_media"),
    )

    for column in MEDIA_COLUMNS:
        media_column = f"{column}_media"
        if media_column in with_media.columns:
            with_media[column] = with_media[media_column].where(
                ~with_media[media_column].map(is_blank),
                with_media[column],
            )
            with_media = with_media.drop(columns=[media_column])

    return with_media[OUTPUT_COLUMNS]


def keep_official_media_games(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Keep only games with verified official page links and cached images."""
    dataframe = dataframe[~dataframe.apply(is_non_game_row, axis=1)].copy()

    has_official_link = (
        dataframe["official_url_en"].map(lambda value: not is_blank(value))
        | dataframe["official_url_ko"].map(lambda value: not is_blank(value))
        | dataframe["official_url_zh"].map(lambda value: not is_blank(value))
    )
    filtered = dataframe[
        dataframe["image_file"].map(lambda value: not is_blank(value))
        & has_official_link
    ].copy()

    filtered["platform_priority"] = filtered["platform"].map(lambda value: PLATFORM_PRIORITY.get(str(value), 9))
    filtered["sort_date"] = pd.to_datetime(filtered["date"], errors="coerce")
    filtered = filtered.sort_values(
        by=["normalized_title", "platform_priority", "sort_date", "meta_score", "title"],
        ascending=[True, True, False, False, True],
        na_position="last",
    )
    filtered = filtered.drop_duplicates(subset=["normalized_title"], keep="first")
    filtered = filtered.sort_values(
        by=["sort_date", "meta_score", "title"],
        ascending=[False, False, True],
        na_position="last",
    )
    return filtered.drop(columns=["platform_priority", "sort_date"])[OUTPUT_COLUMNS]


def write_output_csv(dataframe: pd.DataFrame, path: Path) -> None:
    """Write output atomically so read-only existing files can be replaced."""
    temp_path = path.with_name(f"{path.stem}.tmp{path.suffix}")
    dataframe.to_csv(temp_path, index=False)
    os.replace(temp_path, path)


def merge_data() -> pd.DataFrame:
    """Merge clean historical data with recent Switch supplement data."""
    clean_games = standardize_dataframe(pd.read_csv(CLEAN_DATA_PATH))
    recent_games = standardize_dataframe(load_recent_games())

    clean_games["source_priority"] = 0
    recent_games["source_priority"] = 1

    merged_games = pd.concat([clean_games, recent_games], ignore_index=True)
    merged_games = merged_games.sort_values("source_priority")
    merged_games = merged_games.drop_duplicates(
        subset=["normalized_title", "platform"],
        keep="last",
    )

    merged_games["sort_date"] = pd.to_datetime(merged_games["date"], errors="coerce")
    merged_games = merged_games.sort_values(
        by=["sort_date", "title"],
        ascending=[False, True],
        na_position="last",
    )

    merged_games = merged_games.drop(columns=["source_priority", "sort_date"])
    merged_games = merge_manual_tags(merged_games)
    merged_games = merge_localizations(merged_games)
    merged_games = merge_media(merged_games)
    merged_games = keep_official_media_games(merged_games)
    write_output_csv(merged_games, MERGED_DATA_PATH)
    return merged_games


def main() -> None:
    merged_games = merge_data()
    print(f"Wrote {len(merged_games)} games to {MERGED_DATA_PATH}")


if __name__ == "__main__":
    main()
