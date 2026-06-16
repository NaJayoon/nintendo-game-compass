"""Clean raw Nintendo game metadata for Nintendo Game Compass."""

from pathlib import Path
import re

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_PATH = DATA_DIR / "nintendo_games_raw.csv"
CLEAN_DATA_PATH = DATA_DIR / "nintendo_games_clean.csv"

BASE_COLUMNS = [
    "title",
    "platform",
    "release_date",
    "meta_score",
    "user_score",
    "esrb_rating",
    "developers",
    "genres",
]

NINTENDO_PLATFORM_ALIASES = {
    "switch": "Nintendo Switch",
    "nintendo switch": "Nintendo Switch",
    "switch 2": "Nintendo Switch 2",
    "nintendo switch 2": "Nintendo Switch 2",
    "wii": "Wii",
    "wii u": "Wii U",
    "wiiu": "Wii U",
    "ds": "Nintendo DS",
    "nintendo ds": "Nintendo DS",
    "3ds": "Nintendo 3DS",
    "nintendo 3ds": "Nintendo 3DS",
    "game boy": "Game Boy",
    "gb": "Game Boy",
    "game boy color": "Game Boy",
    "gbc": "Game Boy",
    "game boy advance": "Game Boy Advance",
    "gba": "Game Boy Advance",
    "n64": "Nintendo 64",
    "nintendo 64": "Nintendo 64",
    "gc": "GameCube",
    "gamecube": "GameCube",
}


def normalize_column_name(column_name: str) -> str:
    """Convert source column names into predictable snake_case names."""
    normalized = column_name.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


def standardize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Rename known source columns and add any missing expected columns."""
    dataframe = dataframe.rename(columns={column: normalize_column_name(column) for column in dataframe.columns})
    dataframe = dataframe.rename(
        columns={
            "metascore": "meta_score",
            "date": "release_date",
            "release": "release_date",
            "rating": "esrb_rating",
            "developer": "developers",
            "genre": "genres",
        }
    )

    for column in BASE_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = pd.NA

    return dataframe


def clean_scores(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Convert score columns to numeric values when possible."""
    for column in ["meta_score", "user_score"]:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")
    return dataframe


def clean_dates(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Parse dates into a consistent YYYY-MM-DD format when possible."""
    parsed_dates = dataframe["release_date"].apply(lambda value: pd.to_datetime(value, errors="coerce"))
    dataframe["release_date"] = parsed_dates.dt.strftime("%Y-%m-%d")
    return dataframe


def standardize_platform(platform: object) -> object:
    """Normalize known Nintendo platform labels and discard unsupported platforms."""
    if pd.isna(platform):
        return pd.NA

    platform_text = str(platform).strip()
    normalized = re.sub(r"[^a-z0-9]+", " ", platform_text.lower()).strip()
    normalized = re.sub(r"\s+", " ", normalized)

    return NINTENDO_PLATFORM_ALIASES.get(normalized, pd.NA)


def filter_nintendo_platforms(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Keep rows for Nintendo-related platforms used by this project."""
    dataframe["platform"] = dataframe["platform"].map(standardize_platform)
    return dataframe.dropna(subset=["platform"])


def remove_empty_titles(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Remove rows without a useful game title."""
    dataframe["title"] = dataframe["title"].astype("string").str.strip()
    return dataframe.dropna(subset=["title"]).loc[lambda frame: frame["title"] != ""]


def sort_cleaned_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Sort by review score when available, then title."""
    if "meta_score" in dataframe.columns:
        return dataframe.sort_values(["meta_score", "title"], ascending=[False, True], na_position="last")
    return dataframe.sort_values("title")


def print_summary(original_row_count: int, cleaned_games: pd.DataFrame) -> None:
    """Print a compact data-cleaning summary."""
    print(f"Original row count: {original_row_count}")
    print(f"Cleaned row count: {len(cleaned_games)}")
    print(f"Final column names: {', '.join(cleaned_games.columns)}")


def clean_data() -> pd.DataFrame:
    """Load raw metadata, clean it, and write the objective base dataset."""
    raw_games = pd.read_csv(RAW_DATA_PATH)
    original_row_count = len(raw_games)

    raw_games = standardize_columns(raw_games)
    raw_games = remove_empty_titles(raw_games)
    raw_games = clean_scores(raw_games)
    raw_games = clean_dates(raw_games)
    raw_games = filter_nintendo_platforms(raw_games)

    cleaned_games = (
        raw_games[BASE_COLUMNS]
        .drop_duplicates(subset=["title", "platform"])
    )
    cleaned_games = sort_cleaned_data(cleaned_games)
    cleaned_games.to_csv(CLEAN_DATA_PATH, index=False)
    print_summary(original_row_count, cleaned_games)
    return cleaned_games


def main() -> None:
    clean_data()


if __name__ == "__main__":
    main()
