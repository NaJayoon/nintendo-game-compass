# Nintendo Game Compass

[Open the live app](https://nintendo-game-compass.streamlit.app)

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Languages](https://img.shields.io/badge/Languages-English%20%7C%20Korean%20%7C%20Chinese-F59E0B?style=for-the-badge)
![Kaggle](https://img.shields.io/badge/Kaggle-Starter_Datasets-20BEFF?style=for-the-badge&logo=kaggle&logoColor=white)

Nintendo Game Compass is a multilingual Streamlit site for one practical question:

**What should I play next on Nintendo Switch, and what actually fits my mood, time, group size, and budget?**

Instead of trying to be a huge game encyclopedia, this project focuses on helping players decide faster. It combines Nintendo game metadata, hand-picked recommendation tags, multilingual titles, and official regional Nintendo links in one place.

## What the app does

- **Game Finder**  
  Filter by platform, genre, mood, player type, difficulty, multiplayer needs, and review score.
- **Dashboard Snapshot**  
  Show quick charts for platform mix, genre mix, mood tags, and release-year distribution.
- **Beginner Roadmap**  
  Give new players a simpler entry route instead of dropping them into a huge library.
- **Tonight's Pick**  
  Recommend games for the current situation, like solo play, friends, short sessions, or a relaxed mood.
- **Data Table**  
  Show the curated dataset directly, including localized names and official Nintendo page links.

## Core idea

The project is built as a **decision tool**, not just a database.

It separates the work into three parts:

- **Base game metadata**: titles, platforms, dates, genres, developers, and scores
- **Curated recommendation tags**: mood, play situation, beginner friendliness, multiplayer fit, and budget tier
- **Official presentation layer**: verified Nintendo images, localized names, and regional Nintendo detail pages

## Data sources

The first version started from two Kaggle-style starter datasets and was then refined into a curated Nintendo-focused dataset:

- **Nintendo Games Dataset**  
  Used as the historical Nintendo metadata base
- **Nintendo Switch review / Metacritic-style starter dataset**  
  Used to cross-check newer Switch-era releases and score fields

After that, the project added:

- manual recommendation tags
- English, Korean, and Chinese localized titles
- official Nintendo regional links
- cached official Nintendo media

## Tech stack

- Python
- Streamlit
- Pandas
- NumPy
- CSV-based curated datasets

## Project structure

```text
nintendo-game-compass/
├── app.py
├── requirements.txt
├── README.md
├── data/
└── scripts/
```

## Run locally

```bash
pip install -r requirements.txt
python scripts/clean_data.py
python scripts/merge_data.py
python scripts/fetch_official_media.py
streamlit run app.py
```
