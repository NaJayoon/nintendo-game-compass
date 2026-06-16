"""Nintendo Game Compass Streamlit app."""

from __future__ import annotations

import base64
from html import escape
import mimetypes
from pathlib import Path
import re
import unicodedata

import numpy as np
import pandas as pd
import streamlit as st


APP_TITLE = "Nintendo Game Compass"
PROJECT_ROOT = Path(__file__).resolve().parent
MERGED_DATA_PATH = PROJECT_ROOT / "data" / "nintendo_games_merged.csv"
CLEAN_DATA_PATH = PROJECT_ROOT / "data" / "nintendo_games_clean.csv"
MANUAL_TAGS_PATH = PROJECT_ROOT / "data" / "game_tags_manual.csv"
LOCALIZATIONS_PATH = PROJECT_ROOT / "data" / "game_localizations_manual.csv"
MEDIA_PATH = PROJECT_ROOT / "data" / "game_media_manual.csv"

LANGUAGE_OPTIONS = {
    "English": "en",
    "한국어": "ko",
    "中文": "zh",
}

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

DISPLAY_COLUMNS = [
    "title",
    *LOCALIZATION_COLUMNS,
    *MEDIA_COLUMNS,
    "platform",
    "platform_group",
    "nintendo_relation",
    "genre_main",
    "date",
    "genres",
    "meta_score",
    "user_score",
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

TEXT = {
    "en": {
        "sidebar_caption": "Pick a game by mood, people, time, and budget.",
        "filter_panel_title": "Find a game that fits today",
        "filter_panel_desc": "Choose your console first, then add only the details that matter for this session.",
        "filter_group_library": "Start here",
        "filter_group_feel": "What should it feel like?",
        "filter_group_practical": "Must-have details",
        "filter_more_title": "More filters",
        "filter_version_hint": "Pick this only when you want to separate Switch 2-only games from Switch games that also run on Switch 2.",
        "filter_badge": "Start with your console",
        "nav_label": "Sections",
        "language": "Language",
        "hero_kicker": "Choose your next Nintendo game",
        "hero_copy": "Start with the moment you are in: a quiet solo night, a family hangout, a quick party round, or a long weekend adventure. The Compass turns that situation into a shorter, more useful game list.",
        "quick_new": "New Player Route",
        "quick_new_desc": "Start with beginner-friendly picks.",
        "quick_tonight": "Tonight's Pick",
        "quick_tonight_desc": "Choose something for this exact session.",
        "quick_table_desc": "Browse and download the curated library.",
        "quick_games_desc": "have curated decision labels.",
        "finder_main_kicker": "Main compass",
        "finder_main_note": "Use this as the starting shelf: pick your console, mood, people, time, and budget, then let the list shrink naturally.",
        "data_notes": "Data Source & Accuracy Notes",
        "tab_finder": "Game Finder",
        "tab_tonight": "Tonight's Pick",
        "tab_roadmap": "Beginner Roadmap",
        "tab_budget": "Budget Planner",
        "tab_quiz": "Player Type Test",
        "tab_table": "Data Table",
        "finder_desc": "Narrow the shelf by the things you actually care about: who is playing, how hard it feels, what mood you want, and how much you want to spend.",
        "platform": "Your console",
        "search_title": "Search title",
        "platform_group": "Playable version",
        "nintendo_relation": "Game source",
        "genre_main": "Game type",
        "genre": "Genre",
        "minimum_meta": "Minimum Metacritic score",
        "player_type": "Player type",
        "play_situation": "Play situation",
        "difficulty": "Difficulty",
        "mood": "Mood",
        "beginner_friendly": "Beginner friendly",
        "local_multiplayer": "Local multiplayer",
        "online_multiplayer": "Online multiplayer",
        "budget_tier": "Budget tier",
        "matching_games": "Matching games",
        "tagged_picks": "Tagged picks",
        "meta_80": "80+ Metacritic",
        "sort_results": "Sort results",
        "show_count": "Cards to show",
        "recommendation_count": "Recommendations to show",
        "all_results": "All",
        "best_reviewed": "Best reviewed",
        "newest": "Newest",
        "title_az": "Title A-Z",
        "no_matches": "No matching games yet. Try loosening one or two filters.",
        "no_filter_options": "No options available after the filters above.",
        "switch_release_hidden": "Choose Switch 2 above to separate Switch 2-only games, upgrade versions, and Switch games that also work there.",
        "not_tagged": "Not tagged yet",
        "genre_missing": "Genre not listed",
        "release_date": "Release",
        "untitled": "Untitled game",
        "score": "Match score",
        "metacritic": "Metacritic",
        "user": "User",
        "beginner_card": "Beginner friendly",
        "local_multi_card": "Local multiplayer",
        "why": "Why recommend",
        "manual_advice_missing": "Manual buying advice has not been added yet.",
        "original_title": "Original title",
        "official_page": "Official Nintendo page",
        "no_image": "Official image pending",
        "image_click_note": "Image and title open the exact regional game page when one is verified.",
        "tonight_desc": "For the nights when nobody wants to scroll for twenty minutes. Pick the room, mood, and time, then get a short list.",
        "players": "How many people?",
        "session_length": "Session length",
        "any_new": "Any new players?",
        "tonight_recs": "Tonight's recommendations",
        "roadmap_desc": "A first-buy path for new players: start approachable, then branch into bigger worlds or stronger challenges.",
        "preferred_style": "Preferred style",
        "no_roadmap": "No roadmap games match this style yet. Add more manual tags to expand this route.",
        "step": "Step",
        "quiz_desc": "Answer five quick questions and get a game shelf that feels closer to your habits.",
        "play_with": "Who do you usually play with?",
        "pace": "What pace do you like?",
        "difficulty_comfort": "Difficulty comfort",
        "priority": "What matters most?",
        "budget_comfort": "Budget comfort",
        "quiz_submit": "Confirm and update recommendations",
        "quiz_pending": "Choose your answers, then confirm to update the player type and recommendations.",
        "quiz_rule_note": "Recommendations use your confirmed budget, difficulty, and play situation as filters, then rank by pace and preference.",
        "your_type": "Your player type",
        "budget_desc": "Plan a practical pair of games with budget tiers. Real-time sale prices can come later; this version focuses on buying balance.",
        "budget_krw": "Budget in KRW",
        "solo_game": "Solo game",
        "multi_game": "Multiplayer game",
        "no_combo": "No tier-based combo fits this budget yet. Try a higher budget or add more Low tier manual tags.",
        "combo": "Recommended combo",
        "estimated_budget": "estimated tier budget",
        "solo_pick": "Solo pick in this budget combination.",
        "multi_pick": "Multiplayer pick in this budget combination.",
        "buying_note": "Buying advice: first-party games are often worth considering as cartridges or during sales. Lower-cost indie games usually fit digital purchases well.",
        "table_desc": "Browse the full curated library, check regional names and official links, or use the table toolbar to download the CSV.",
        "download": "Download merged CSV",
        "run_clean": "Please run python scripts/clean_data.py first.",
        "no_games": "No games found yet. Add data to the CSV files and rerun the data scripts.",
        "notes_list": [
            "The base dataset covers older Nintendo games and may not include recent releases.",
            "Recent Switch and Switch 2 games are supplemented through recent_switch_games.csv.",
            "Player-oriented labels and classification fields are manually curated for recommendation purposes.",
            "Localized titles are manually curated from official or store-localized names when available.",
            "Rows without an official Nintendo product page and cached official image are excluded from the app dataset.",
            "Price data is not real-time in the MVP version.",
        ],
        "table_notes_list": [
            "Basic game metadata comes from a public Nintendo games CSV dataset.",
            "Review scores are used as reference indicators, not absolute quality judgments.",
            "Player-oriented tags and classification fields such as platform_group, nintendo_relation, genre_main, mood, play_situation, and buying_advice are manually curated for recommendation purposes.",
            "Localized title columns title_en, title_ko, and title_zh are curated separately so the original title remains auditable.",
            "Official image URLs and country/region game detail links are curated in game_media_manual.csv; regional links are left blank when no exact page has been verified.",
            "The recommendation system uses transparent rule-based scoring, not a black-box AI model.",
            "Price data is not real-time in the current MVP version.",
        ],
    },
    "ko": {
        "sidebar_caption": "기분, 인원, 시간, 예산으로 게임을 고릅니다.",
        "filter_panel_title": "오늘에 맞는 게임 찾기",
        "filter_panel_desc": "먼저 가지고 있는 기기를 고르고, 오늘 필요한 조건만 더해보세요.",
        "filter_group_library": "먼저 선택",
        "filter_group_feel": "어떤 느낌으로 할까요?",
        "filter_group_practical": "꼭 필요한 조건",
        "filter_more_title": "추가 필터",
        "filter_version_hint": "Switch 2 전용 게임과 Switch에서도 되고 Switch 2에서도 되는 게임을 구분하고 싶을 때만 고르세요.",
        "filter_badge": "기기부터 선택",
        "nav_label": "메뉴",
        "language": "언어",
        "hero_kicker": "다음 닌텐도 게임 고르기",
        "hero_copy": "혼자 조용히 보내는 밤, 가족 모임, 짧은 파티 라운드, 긴 주말 모험처럼 지금의 상황에서 시작하세요. Compass가 선택지를 더 짧고 유용하게 줄여줍니다.",
        "quick_new": "입문 루트",
        "quick_new_desc": "초보자에게 맞는 게임부터 시작합니다.",
        "quick_tonight": "오늘 밤 추천",
        "quick_tonight_desc": "지금 상황에 맞는 게임을 고릅니다.",
        "quick_table_desc": "큐레이션 목록을 보고 내려받습니다.",
        "quick_games_desc": "개 게임에 큐레이션 라벨이 있습니다.",
        "finder_main_kicker": "메인 선택 도구",
        "finder_main_note": "가장 먼저 쓰는 게임 선반입니다. 기기, 기분, 인원, 시간, 예산을 고르면 목록이 자연스럽게 줄어듭니다.",
        "data_notes": "데이터 출처 및 정확도 메모",
        "tab_finder": "게임 찾기",
        "tab_tonight": "오늘 밤 추천",
        "tab_roadmap": "입문 로드맵",
        "tab_budget": "예산 플래너",
        "tab_quiz": "플레이어 유형 테스트",
        "tab_table": "데이터 표",
        "finder_desc": "누구와 할지, 얼마나 어려운지, 어떤 기분을 원하는지, 예산은 어느 정도인지로 게임 선반을 좁혀봅니다.",
        "platform": "가지고 있는 기기",
        "search_title": "제목 검색",
        "platform_group": "플레이 가능 버전",
        "nintendo_relation": "게임 출처",
        "genre_main": "게임 유형",
        "genre": "장르",
        "minimum_meta": "최소 메타크리틱 점수",
        "player_type": "플레이어 유형",
        "play_situation": "플레이 상황",
        "difficulty": "난이도",
        "mood": "기분",
        "beginner_friendly": "초보자 친화",
        "local_multiplayer": "로컬 멀티플레이",
        "online_multiplayer": "온라인 멀티플레이",
        "budget_tier": "예산 등급",
        "matching_games": "일치하는 게임",
        "tagged_picks": "라벨이 있는 추천",
        "meta_80": "메타크리틱 80+",
        "sort_results": "정렬",
        "show_count": "표시할 카드 수",
        "recommendation_count": "추천 표시 수",
        "all_results": "전체",
        "best_reviewed": "평점 높은 순",
        "newest": "최신순",
        "title_az": "제목순",
        "no_matches": "조건에 맞는 게임이 없습니다. 필터를 조금 줄여보세요.",
        "no_filter_options": "위 필터 조건에서 선택할 수 있는 옵션이 없습니다.",
        "switch_release_hidden": "위에서 Switch 2를 선택하면 Switch 2 전용, 업그레이드판, Switch와 Switch 2 모두 가능한 게임을 나눠 볼 수 있습니다.",
        "not_tagged": "아직 라벨 없음",
        "genre_missing": "장르 정보 없음",
        "release_date": "발매일",
        "untitled": "제목 없음",
        "score": "추천 점수",
        "metacritic": "메타크리틱",
        "user": "유저",
        "beginner_card": "초보자 친화",
        "local_multi_card": "로컬 멀티",
        "why": "추천 이유",
        "manual_advice_missing": "아직 구매 조언이 추가되지 않았습니다.",
        "original_title": "원제",
        "official_page": "공식 닌텐도 페이지",
        "no_image": "공식 이미지 준비 중",
        "image_click_note": "이미지와 제목은 확인된 지역별 게임 상세 페이지가 있을 때만 이동합니다.",
        "tonight_desc": "고르느라 시간을 쓰고 싶지 않은 밤을 위한 추천입니다. 인원, 기분, 시간을 고르면 짧은 목록으로 줄여줍니다.",
        "players": "몇 명이 플레이하나요?",
        "session_length": "플레이 시간",
        "any_new": "초보자가 있나요?",
        "tonight_recs": "오늘 밤 추천 게임",
        "roadmap_desc": "처음 구매할 순서를 제안합니다. 쉬운 게임에서 시작해 더 큰 세계나 도전으로 이어집니다.",
        "preferred_style": "선호 스타일",
        "no_roadmap": "이 스타일에 맞는 로드맵 게임이 아직 없습니다. 수동 라벨을 더 추가해 주세요.",
        "step": "단계",
        "quiz_desc": "다섯 가지 질문으로 평소 취향에 가까운 게임 선반을 만들어봅니다.",
        "play_with": "주로 누구와 플레이하나요?",
        "pace": "어떤 플레이 템포를 좋아하나요?",
        "difficulty_comfort": "난이도 선호",
        "priority": "가장 중요하게 보는 것은?",
        "budget_comfort": "예산 선호",
        "quiz_submit": "확인하고 추천 업데이트",
        "quiz_pending": "답변을 고른 뒤 확인을 눌러 플레이어 유형과 추천을 업데이트하세요.",
        "quiz_rule_note": "추천은 확인한 예산, 난이도, 플레이 상황을 필터로 사용하고, 템포와 선호도로 정렬합니다.",
        "your_type": "당신의 플레이어 유형",
        "budget_desc": "예산 등급으로 실용적인 게임 조합을 계획합니다. 실시간 할인가는 나중에 붙이고, 지금은 구매 균형에 집중합니다.",
        "budget_krw": "예산(KRW)",
        "solo_game": "싱글 플레이 게임",
        "multi_game": "멀티플레이 게임",
        "no_combo": "이 예산에 맞는 조합이 없습니다. 예산을 올리거나 Low 등급 라벨을 더 추가해 보세요.",
        "combo": "추천 조합",
        "estimated_budget": "예상 등급 예산",
        "solo_pick": "이 예산 조합의 싱글 플레이 추천입니다.",
        "multi_pick": "이 예산 조합의 멀티플레이 추천입니다.",
        "buying_note": "구매 조언: 닌텐도 퍼스트파티 게임은 패키지판이나 세일을 고려할 만합니다. 저가 인디 게임은 디지털판 구매가 잘 맞습니다.",
        "table_desc": "전체 큐레이션 목록, 지역별 이름, 공식 링크를 확인하고 표 오른쪽 위 도구로 CSV를 내려받을 수 있습니다.",
        "download": "병합 CSV 다운로드",
        "run_clean": "먼저 python scripts/clean_data.py 를 실행해 주세요.",
        "no_games": "게임 데이터가 없습니다. CSV를 추가하고 데이터 스크립트를 다시 실행해 주세요.",
        "notes_list": [
            "기본 데이터셋은 오래된 닌텐도 게임을 포함하며 최신 출시작이 누락될 수 있습니다.",
            "최근 Switch 및 Switch 2 게임은 recent_switch_games.csv로 보완합니다.",
            "플레이어 중심 라벨과 분류 필드는 추천을 위해 수동으로 큐레이션했습니다.",
            "현지화 제목은 가능한 경우 공식 또는 스토어 현지화명을 기준으로 수동 큐레이션했습니다.",
            "공식 닌텐도 상품 페이지와 캐시된 공식 이미지가 없는 행은 앱 데이터에서 제외합니다.",
            "MVP 버전의 가격 데이터는 실시간이 아닙니다.",
        ],
        "table_notes_list": [
            "기본 게임 메타데이터는 공개 닌텐도 게임 CSV 데이터셋에서 가져옵니다.",
            "리뷰 점수는 참고 지표이며 절대적인 품질 판단이 아닙니다.",
            "platform_group, nintendo_relation, genre_main, mood, play_situation, buying_advice 같은 라벨과 분류 필드는 추천 목적의 수동 큐레이션 데이터입니다.",
            "title_en, title_ko, title_zh 열은 원제를 보존하면서 별도로 큐레이션한 현지화 제목입니다.",
            "공식 이미지 URL과 국가/지역별 게임 상세 페이지 링크는 game_media_manual.csv에서 관리하며, 확인된 정확한 페이지가 없으면 지역 링크를 비워 둡니다.",
            "추천 시스템은 블랙박스 AI가 아니라 투명한 규칙 기반 점수를 사용합니다.",
            "현재 MVP 버전의 가격 데이터는 실시간이 아닙니다.",
        ],
    },
    "zh": {
        "sidebar_caption": "按心情、人数、时间和预算选游戏。",
        "filter_panel_title": "找到今天适合玩的游戏",
        "filter_panel_desc": "先选你手上的主机，再按今天的心情、人数和预算缩小范围。",
        "filter_group_library": "先从这里开始",
        "filter_group_feel": "今天想怎么玩？",
        "filter_group_practical": "必须满足的条件",
        "filter_more_title": "更多筛选",
        "filter_version_hint": "只有想区分 Switch 2 限定游戏、Switch 游戏在 Switch 2 上也能玩、或 Switch 2 升级版时才需要选。",
        "filter_badge": "先选主机",
        "nav_label": "页面",
        "language": "语言",
        "hero_kicker": "选择下一款任天堂游戏",
        "hero_copy": "从你此刻的场景开始：一个人的安静晚上、家庭聚会、朋友快速来一局，或是周末长时间冒险。Compass 会把选择缩成更好判断的一小组。",
        "quick_new": "新手路线",
        "quick_new_desc": "从新手友好的游戏开始。",
        "quick_tonight": "今晚玩什么",
        "quick_tonight_desc": "按今晚的具体场景选游戏。",
        "quick_table_desc": "查看并下载精选游戏库。",
        "quick_games_desc": "款游戏有人工决策标签。",
        "finder_main_kicker": "主选择台",
        "finder_main_note": "这里是最主要的游戏筛选入口。先选主机，再按心情、人数、时长和预算，把候选游戏自然缩小。",
        "data_notes": "数据来源与准确性说明",
        "tab_finder": "游戏筛选",
        "tab_tonight": "今晚推荐",
        "tab_roadmap": "新手路线",
        "tab_budget": "预算规划",
        "tab_quiz": "玩家类型测试",
        "tab_table": "数据表",
        "finder_desc": "按真正会影响购买和开玩的因素缩小范围：和谁玩、想要什么心情、能接受多难、预算到哪一档。",
        "platform": "你的主机",
        "search_title": "搜索标题",
        "platform_group": "可玩版本",
        "nintendo_relation": "游戏来源",
        "genre_main": "游戏类型",
        "genre": "类型",
        "minimum_meta": "最低 Metacritic 评分",
        "player_type": "玩家类型",
        "play_situation": "游玩场景",
        "difficulty": "难度",
        "mood": "心情",
        "beginner_friendly": "新手友好",
        "local_multiplayer": "本地多人",
        "online_multiplayer": "在线多人",
        "budget_tier": "预算档位",
        "matching_games": "匹配游戏",
        "tagged_picks": "已标注推荐",
        "meta_80": "Metacritic 80+",
        "sort_results": "排序",
        "show_count": "显示数量",
        "recommendation_count": "推荐数量",
        "all_results": "全部",
        "best_reviewed": "评分优先",
        "newest": "最新优先",
        "title_az": "标题 A-Z",
        "no_matches": "暂时没有匹配游戏。可以放宽一两个筛选条件。",
        "no_filter_options": "当前上方条件下暂无可选项。",
        "switch_release_hidden": "先在上方选择 Switch 2，才会显示“仅 Switch 2”“Switch 2 升级版”“Switch 和 Switch 2 都能玩”的细分。",
        "not_tagged": "尚未标注",
        "genre_missing": "暂无类型信息",
        "release_date": "发售日",
        "untitled": "未命名游戏",
        "score": "匹配分",
        "metacritic": "Metacritic",
        "user": "用户",
        "beginner_card": "新手友好",
        "local_multi_card": "本地多人",
        "why": "推荐理由",
        "manual_advice_missing": "尚未添加人工购买建议。",
        "original_title": "原始标题",
        "official_page": "任天堂官方页面",
        "no_image": "官方图片待补充",
        "image_click_note": "图片和标题只会在已确认对应地区游戏详情页时打开。",
        "tonight_desc": "不想大家一起翻列表翻二十分钟的时候，用人数、心情和时长快速缩小选择。",
        "players": "几个人玩？",
        "session_length": "游玩时长",
        "any_new": "有没有新手？",
        "tonight_recs": "今晚推荐",
        "roadmap_desc": "给新玩家一个购买顺序：先从容易上手的开始，再慢慢进入更大的世界或更强的挑战。",
        "preferred_style": "偏好风格",
        "no_roadmap": "这个风格暂时没有匹配路线。可以继续补充人工标签。",
        "step": "第",
        "quiz_desc": "回答 5 个问题，生成一个更接近你平时习惯的游戏架。",
        "play_with": "你通常和谁玩？",
        "pace": "你喜欢什么节奏？",
        "difficulty_comfort": "难度接受度",
        "priority": "你最在意什么？",
        "budget_comfort": "预算接受度",
        "quiz_submit": "确认并更新推荐",
        "quiz_pending": "先选择答案，再点击确认更新玩家类型和推荐游戏。",
        "quiz_rule_note": "推荐会把已确认的预算、难度、游玩对象作为筛选条件，再按节奏和偏好排序。",
        "your_type": "你的玩家类型",
        "budget_desc": "用预算档位先规划一个实用组合。实时折扣可以后面再接，这一版先关注买得是否均衡。",
        "budget_krw": "预算（KRW）",
        "solo_game": "单人游戏",
        "multi_game": "多人游戏",
        "no_combo": "这个预算暂时没有匹配组合。可以提高预算或补充更多 Low 档标签。",
        "combo": "推荐组合",
        "estimated_budget": "预估档位预算",
        "solo_pick": "这个组合里的单人游戏推荐。",
        "multi_pick": "这个组合里的多人游戏推荐。",
        "buying_note": "购买建议：任天堂第一方大作可以考虑卡带或等折扣；低价独立游戏通常更适合数字版。",
        "table_desc": "查看完整精选库、地区译名和官方链接，也可以用表格右上角工具下载 CSV。",
        "download": "下载合并 CSV",
        "run_clean": "请先运行 python scripts/clean_data.py。",
        "no_games": "暂时没有游戏数据。请添加 CSV 并重新运行数据脚本。",
        "notes_list": [
            "基础数据集覆盖较早的任天堂游戏，可能不包含最新发行作品。",
            "近年的 Switch 和 Switch 2 游戏通过 recent_switch_games.csv 补充。",
            "面向玩家决策的标签和分类字段由人工整理，用于推荐逻辑。",
            "本地化标题尽量采用官方或商店本地化名称，并单独维护。",
            "没有任天堂官方商品页和本地官方图片缓存的行会从应用数据中排除。",
            "MVP 版本的价格数据不是实时价格。",
        ],
        "table_notes_list": [
            "基础游戏元数据来自公开 Nintendo games CSV 数据集。",
            "评分只作为参考指标，不代表绝对质量判断。",
            "platform_group、nintendo_relation、genre_main、mood、play_situation、buying_advice 等分类和玩家标签是为了推荐目的人工整理的。",
            "title_en、title_ko、title_zh 是单独整理的本地化标题列，保留原始标题以便审计。",
            "官方图片 URL 和国家/地区游戏详情页链接维护在 game_media_manual.csv 中；没有确认到精确详情页时，对应地区链接会留空。",
            "推荐系统使用透明的规则打分，不使用黑箱 AI 模型。",
            "当前 MVP 版本的价格数据不是实时价格。",
        ],
    },
}

STYLE_TO_MOODS = {
    "healing": ["Healing", "Cute"],
    "adventure": ["Immersive", "Exciting"],
    "party": ["Fun", "Chaotic", "Active"],
    "action": ["Exciting", "Tense"],
    "cute": ["Cute", "Healing"],
    "immersive": ["Immersive", "Tense"],
    "story": ["Story", "Immersive"],
    "puzzle": ["Creative", "Fun"],
    "active": ["Active", "Exciting"],
}

STYLE_TO_PLAYER_TYPES = {
    "healing": ["Relaxed Player", "Family Player"],
    "adventure": ["Explorer", "Core Player"],
    "party": ["Party Player", "Family Player"],
    "action": ["Core Player", "Explorer"],
    "cute": ["Beginner", "Relaxed Player", "Family Player"],
    "immersive": ["Explorer", "Core Player"],
    "story": ["Story Player", "Explorer", "Core Player"],
    "puzzle": ["Beginner", "Creative Player", "Relaxed Player"],
    "active": ["Family Player", "Party Player", "Competitive Player"],
}

BUDGET_ESTIMATES_KRW = {
    "Low": 20000,
    "Medium": 50000,
    "High": 75000,
}

PLATFORM_PRIORITY = {
    "Nintendo Switch 2": 0,
    "Nintendo Switch": 1,
}

EN_DETAIL_OVERRIDES = {
    "animal crossing new horizons": "https://animalcrossing.nintendo.com/new-horizons/",
    "legend of zelda breath of the wild": "https://zelda.nintendo.com/breath-of-the-wild/",
    "legend of zelda tears of the kingdom": "https://zelda.nintendo.com/tears-of-the-kingdom/",
    "mario kart 8 deluxe": "https://mariokart8.nintendo.com/",
    "super mario bros wonder": "https://supermariobroswonder.nintendo.com/",
    "super mario odyssey": "https://supermario.nintendo.com/",
    "splatoon 3": "https://splatoon.nintendo.com/",
    "nintendo switch sports": "https://nintendoswitchsports.nintendo.com/",
    "ring fit adventure": "https://ringfitadventure.nintendo.com/",
    "luigis mansion 3": "https://luigismansion.nintendo.com/",
    "luigi s mansion 3": "https://luigismansion.nintendo.com/",
    "mario party superstars": "https://mariopartysuperstars.nintendo.com/",
    "mario partytm superstars 瑪利歐派對 超級巨星": "https://mariopartysuperstars.nintendo.com/",
    "super smash bros ultimate": "https://www.smashbros.com/en_US/",
    "yoshis crafted world": "https://yoshiscraftedworld.nintendo.com/",
    "耀西的手工世界": "https://yoshiscraftedworld.nintendo.com/",
}

SAFE_TITLE_OVERRIDES = {
    "Another Code 回憶錄：兩種記憶／記憶之門": "Another Code: Recollection",
    "FIRE EMBLEM 無雙 風花雪月": "Fire Emblem Warriors: Three Hopes",
    "Famicom偵探俱樂部 消失的繼承人": "Famicom Detective Club: The Missing Heir",
    "Famicom偵探俱樂部 站在身後的少女": "Famicom Detective Club: The Girl Who Stands Behind",
    "Famicom偵探俱樂部 笑臉男ＥＭＩＯ": "Emio - The Smiling Man: Famicom Detective Club",
    "Mario Party™ Superstars（瑪利歐派對 超級巨星）": "Mario Party Superstars",
    "Nintendo Labo Toy-Con 01: 組合套裝": "Nintendo Labo Toy-Con 01: Variety Kit",
    "Nintendo Labo Toy-Con 02: 機器人套裝": "Nintendo Labo Toy-Con 02: Robot Kit",
    "Nintendo Labo Toy-Con 03: 駕駛套裝": "Nintendo Labo Toy-Con 03: Vehicle Kit",
    "Nintendo Labo Toy-Con 04: VR套裝": "Nintendo Labo Toy-Con 04: VR Kit",
    "Nintendo Labo Toy-Con 04: VR套裝 輕量版（僅附火箭筒）": "Nintendo Labo Toy-Con 04: VR Kit Starter Set + Blaster",
    "Nintendo Switch 運動": "Nintendo Switch Sports",
    "Nintendo World Championships Famicom世界大會": "Nintendo World Championships: NES Edition",
    "Splatoon™ 2 (美版)": "Splatoon 2",
    "Tomodachi Life 朋友收集 夢想生活": "Tomodachi Life: Living the Dream",
    "[Pokémon Café Mix]歡迎光臨！寶可夢咖啡店 ～拌拌繽紛趣～": "Pokemon Cafe ReMix",
    "ポケモン不思議のダンジョン 救助隊DX": "Pokemon Mystery Dungeon: Rescue Team DX",
    "你裁我剪！斯尼帕Plus": "Snipperclips Plus: Cut It Out, Together!",
    "凱登絲勇闖海拉魯：死靈舞師地牢 薩爾達傳說 合作鉅獻": "Cadence of Hyrule: Crypt of the NecroDancer Featuring The Legend of Zelda",
    "分享同樂！瓦利歐製造": "WarioWare: Get It Together!",
    "卡比的美食節": "Kirby's Dream Buffet",
    "卡比群星戰2": "Kirby Fighters 2",
    "名偵探皮卡丘 閃電回歸": "Detective Pikachu Returns",
    "咚奇剛 歸來 HD": "Donkey Kong Country Returns HD",
    "密特羅德 究極4 穿越未知 Nintendo Switch 2 Edition": "Metroid Prime 4: Beyond Nintendo Switch 2 Edition",
    "寶可夢 明亮珍珠": "Pokemon Shining Pearl",
    "寶可夢 晶燦鑽石": "Pokemon Brilliant Diamond",
    "寶可夢傳說 Z-A Nintendo Switch 2 Edition": "Pokemon Legends: Z-A Nintendo Switch 2 Edition",
    "搭檔任務 秘密搜查組": "Buddy Mission BOND",
    "擔架拍擋™": "The Stretchers",
    "斯普拉遁 3 擴充票": "Splatoon 3 Expansion Pass",
    "星之卡比 Wii 豪華版": "Kirby's Return to Dream Land Deluxe",
    "永恆蔚藍 流光": "Endless Ocean Luminous",
    "瑪利歐 + 瘋狂兔子 王國之戰 (日中版)": "Mario + Rabbids Kingdom Battle",
    "瑪利歐賽車8 豪華版 新增賽道通行證": "Mario Kart 8 Deluxe Booster Course Pass",
    "瑪利歐高爾夫 超級衝衝衝": "Mario Golf: Super Rush",
    "瑪利歐＆路易吉RPG 兄弟齊航！": "Mario & Luigi: Brothership",
    "異度神劍X 終極版": "Xenoblade Chronicles X: Definitive Edition",
    "異度神劍X 終極版 Nintendo Switch 2 Edition": "Xenoblade Chronicles X: Definitive Edition Nintendo Switch 2 Edition",
    "皮克敏１": "Pikmin 1",
    "皮克敏２": "Pikmin 2",
    "節奏天國 奇蹟之星": "Rhythm Heaven Groove",
    "精靈寶可夢 Let's Go！伊布": "Pokemon: Let's Go, Eevee!",
    "精靈寶可夢 Let's Go！皮卡丘": "Pokemon: Let's Go, Pikachu!",
    "耀西的手工世界": "Yoshi's Crafted World",
    "蓓優妮塔 起源︰瑟蕾莎與迷失的惡魔": "Bayonetta Origins: Cereza and the Lost Demon",
    "薩爾達傳說 曠野之息 Nintendo Switch 2 Edition": "The Legend of Zelda: Breath of the Wild Nintendo Switch 2 Edition",
    "薩爾達傳說 王國之淚 Nintendo Switch 2 Edition": "The Legend of Zelda: Tears of the Kingdom Nintendo Switch 2 Edition",
    "薩爾達傳說 織夢島": "The Legend of Zelda: Link's Awakening",
    "超回転 寿司ストライカー The Way of Sushido (日文版)": "Sushi Striker: The Way of Sushido",
    "超級瑪利歐兄弟 驚奇 Nintendo Switch 2 Edition + 同遊鈴鈴公園": "Super Mario Bros. Wonder Nintendo Switch 2 Edition + Meetup in Bellabel Park",
    "超級瑪利歐派對 空前盛會 Nintendo Switch 2 Edition + 空前盛會TV": "Super Mario Party Jamboree Nintendo Switch 2 Edition + Jamboree TV",
    "超級瑪利歐銀河": "Super Mario Galaxy",
    "超級瑪利歐銀河 ＋ 超級瑪利歐銀河 ２": "Super Mario Galaxy + Super Mario Galaxy 2",
    "路易吉洋樓２ HD": "Luigi's Mansion 2 HD",
    "迷托邦": "Miitopia",
    "附帶導航！一做就上手 第一次的遊戲程式設計": "Game Builder Garage",
    "集合啦！動物森友會 Nintendo Switch 2 Edition": "Animal Crossing: New Horizons Nintendo Switch 2 Edition",
    "靈活腦學校 一起伸展大腦": "Big Brain Academy: Brain vs. Brain",
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

VALUE_LABELS = {
    "en": {
        "Any": "Any",
        "Yes": "Yes",
        "No": "No",
        "Nintendo Switch": "I play on Switch",
        "Nintendo Switch 2": "I play on Switch 2",
        "Nintendo Switch 2 Edition": "Switch 2 upgrade game",
        "Switch": "Switch game",
        "Switch 2": "Only on Switch 2",
        "Switch 2 Edition": "Switch game with Switch 2 upgrade",
        "Switch Compatible": "Works on Switch & Switch 2",
        "Legacy": "Older Nintendo system",
    },
    "ko": {
        "Any": "전체",
        "Yes": "예",
        "No": "아니오",
        "Low": "낮음",
        "Medium": "중간",
        "High": "높음",
        "Easy": "쉬움",
        "Hard": "어려움",
        "Short": "짧게",
        "Long": "길게",
        "Explorer": "탐험형",
        "Relaxed Player": "느긋한 플레이어",
        "Party Player": "파티 플레이어",
        "Family Player": "가족 플레이어",
        "Core Player": "코어 플레이어",
        "Competitive Player": "경쟁형 플레이어",
        "Budget Player": "가성비 플레이어",
        "Beginner": "입문자",
        "Creative Player": "창작형 플레이어",
        "Solo": "혼자",
        "Friends": "친구",
        "Family": "가족",
        "Online": "온라인",
        "Online Multiplayer": "온라인 멀티",
        "Solo or Family": "혼자 또는 가족",
        "Solo or Couple": "혼자 또는 커플",
        "Solo or Friends": "혼자 또는 친구",
        "Couple": "커플",
        "Party": "파티",
        "Travel": "이동 중",
        "Short Break": "짧은 휴식",
        "Long Session": "긴 플레이",
        "Fun": "즐거움",
        "Healing": "힐링",
        "Exciting": "신남",
        "Immersive": "몰입",
        "Competitive": "경쟁",
        "Chaotic": "혼돈",
        "Active": "활동적",
        "Cute": "귀여움",
        "Creative": "창의",
        "Adventure": "모험",
        "Funny": "코미디",
        "Tense": "긴장",
        "Story": "스토리",
        "Action": "액션",
        "Puzzle": "퍼즐",
        "Cozy": "포근함",
        "Emotional": "감성",
        "1 player": "1명",
        "2 players": "2명",
        "3-4 players": "3-4명",
        "Family group": "가족 여러 명",
        "healing": "힐링",
        "adventure": "모험",
        "party": "파티",
        "action": "액션",
        "cute": "귀여움",
        "immersive": "몰입",
        "story": "스토리",
        "puzzle": "퍼즐",
        "active": "활동적",
        "Alone": "혼자",
        "Partner or roommate": "연인 또는 룸메이트",
        "Slow and cozy": "천천히 편하게",
        "Quick round": "짧게 한 판",
        "Long immersion": "오래 몰입",
        "Tense challenge": "긴장감 있는 도전",
        "Cute style": "귀여운 스타일",
        "Story and world": "스토리와 세계관",
        "Action feel": "조작감과 액션",
        "Funny interaction": "웃긴 상호작용",
        "Free exploration": "자유 탐험",
        "One solo game": "싱글 게임 1개",
        "No solo game": "싱글 게임 없음",
        "One multiplayer game": "멀티 게임 1개",
        "No multiplayer game": "멀티 게임 없음",
        "Best reviewed": "평점 높은 순",
        "Newest": "최신순",
        "Title A-Z": "제목순",
        "Nintendo Switch": "Switch로 플레이해요",
        "Nintendo Switch 2": "Switch 2로 플레이해요",
        "Nintendo Switch 2 Edition": "Switch 2 업그레이드판 게임",
        "Switch": "Switch 게임",
        "Switch 2": "Switch 2 전용",
        "Switch 2 Edition": "Switch 게임의 Switch 2 업그레이드판",
        "Switch Compatible": "Switch와 Switch 2 모두 플레이 가능",
        "Legacy": "이전 닌텐도 기기",
        "Nintendo Core": "닌텐도 코어",
        "Nintendo Published": "닌텐도 퍼블리싱",
        "Third-party": "서드파티",
        "Indie": "인디",
        "RPG": "RPG",
        "Platformer": "플랫포머",
        "Racing": "레이싱",
        "Party": "파티",
        "Simulation": "시뮬레이션",
        "Strategy": "전략",
        "Sports": "스포츠",
        "Fitness": "피트니스",
        "Shooter": "슈터",
        "Rhythm": "리듬",
        "Fighting": "격투",
        "Story Player": "스토리 플레이어",
    },
    "zh": {
        "Any": "不限",
        "Yes": "是",
        "No": "否",
        "Low": "低",
        "Medium": "中",
        "High": "高",
        "Easy": "简单",
        "Hard": "困难",
        "Short": "短",
        "Long": "长",
        "Explorer": "探索型玩家",
        "Relaxed Player": "休闲玩家",
        "Party Player": "聚会玩家",
        "Family Player": "家庭玩家",
        "Core Player": "核心玩家",
        "Competitive Player": "竞技玩家",
        "Budget Player": "预算玩家",
        "Beginner": "新手",
        "Creative Player": "创作型玩家",
        "Solo": "单人",
        "Friends": "朋友",
        "Family": "家庭",
        "Online": "在线",
        "Online Multiplayer": "在线多人",
        "Solo or Family": "单人或家庭",
        "Solo or Couple": "单人或情侣",
        "Solo or Friends": "单人或朋友",
        "Couple": "情侣 / 室友",
        "Party": "聚会",
        "Travel": "通勤 / 旅行",
        "Short Break": "碎片时间",
        "Long Session": "长时间游玩",
        "Fun": "好玩",
        "Healing": "治愈",
        "Exciting": "刺激",
        "Immersive": "沉浸",
        "Competitive": "竞技",
        "Chaotic": "混乱欢乐",
        "Active": "运动感",
        "Cute": "可爱",
        "Creative": "创造",
        "Adventure": "冒险",
        "Funny": "搞笑",
        "Tense": "紧张",
        "Story": "剧情",
        "Action": "动作",
        "Puzzle": "解谜",
        "Cozy": "轻松",
        "Emotional": "情绪",
        "1 player": "1 人",
        "2 players": "2 人",
        "3-4 players": "3-4 人",
        "Family group": "家庭多人",
        "healing": "治愈",
        "adventure": "冒险",
        "party": "聚会",
        "action": "动作",
        "cute": "可爱",
        "immersive": "沉浸",
        "story": "剧情",
        "puzzle": "解谜",
        "active": "运动感",
        "Alone": "一个人",
        "Partner or roommate": "情侣 / 室友",
        "Slow and cozy": "慢慢玩",
        "Quick round": "快速来一局",
        "Long immersion": "长时间沉浸",
        "Tense challenge": "紧张挑战",
        "Cute style": "可爱画风",
        "Story and world": "剧情世界观",
        "Action feel": "操作爽感",
        "Funny interaction": "搞笑互动",
        "Free exploration": "自由探索",
        "One solo game": "一个单人游戏",
        "No solo game": "不需要单人游戏",
        "One multiplayer game": "一个多人游戏",
        "No multiplayer game": "不需要多人游戏",
        "Best reviewed": "评分优先",
        "Newest": "最新优先",
        "Title A-Z": "标题 A-Z",
        "Nintendo Switch": "我用 Switch 玩",
        "Nintendo Switch 2": "我用 Switch 2 玩",
        "Nintendo Switch 2 Edition": "Switch 2 升级版游戏",
        "Switch": "Switch 游戏",
        "Switch 2": "仅 Switch 2 可玩",
        "Switch 2 Edition": "Switch 游戏的 Switch 2 升级版",
        "Switch Compatible": "Switch 和 Switch 2 都能玩",
        "Legacy": "旧款任天堂主机",
        "Nintendo Core": "任天堂核心",
        "Nintendo Published": "任天堂发行",
        "Third-party": "第三方",
        "Indie": "独立游戏",
        "RPG": "RPG",
        "Platformer": "平台跳跃",
        "Racing": "竞速",
        "Party": "聚会",
        "Simulation": "模拟",
        "Strategy": "策略",
        "Sports": "体育",
        "Fitness": "健身",
        "Shooter": "射击",
        "Rhythm": "节奏",
        "Fighting": "格斗",
        "Story Player": "剧情玩家",
    },
}


def normalize_column_name(column_name: str) -> str:
    normalized = column_name.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


def normalize_title(title: object) -> str:
    if pd.isna(title):
        return ""
    normalized = unicodedata.normalize("NFKC", str(title)).casefold()
    normalized = re.sub(r"[^\w]+", " ", normalized, flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized = re.sub(r"^the\s+", "", normalized)
    normalized = re.sub(r"\s+the$", "", normalized)
    return normalized


def has_non_korean_east_asian_text(value: object) -> bool:
    if is_blank(value):
        return False
    return bool(re.search(r"[\u3400-\u9fff\u3040-\u30ff]", str(value)))


def has_latin_text(value: object) -> bool:
    if is_blank(value):
        return False
    return bool(re.search(r"[A-Za-z]", str(value)))


def get_safe_title_override(game: pd.Series) -> str:
    title_candidates = [game.get(column) for column in ["title", "title_en", "title_zh", "title_ko"]]
    candidate_keys = {normalize_title(candidate) for candidate in title_candidates if not is_blank(candidate)}
    for source_title, safe_title in SAFE_TITLE_OVERRIDES.items():
        if normalize_title(source_title) in candidate_keys:
            return safe_title
    return ""


def strip_non_korean_east_asian_text(value: object) -> str:
    if is_blank(value):
        return ""

    text = unicodedata.normalize("NFKC", str(value))
    text = re.sub(r"[\(（][^\(\)（）]*[\u3400-\u9fff\u3040-\u30ff][^\(\)（）]*[\)）]", " ", text)
    text = re.sub(r"[\u3400-\u9fff\u3040-\u30ff]", " ", text)
    text = text.replace("™", "").replace("®", "")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*[:：/／+＋|,-]\s*$", "", text)
    text = text.strip(" -_:：/／+＋|,()（）[]【】")
    if has_latin_text(text):
        return text
    return ""


def get_safe_non_chinese_title(game: pd.Series, lang: str) -> str:
    override_title = get_safe_title_override(game)
    if override_title:
        return override_title

    for column in ["title_en", "title"]:
        title = game.get(column)
        if not is_blank(title) and not has_non_korean_east_asian_text(title):
            return str(title)

    for column in ["title_en", "title"]:
        stripped_title = strip_non_korean_east_asian_text(game.get(column))
        if stripped_title:
            return stripped_title

    return ""


def is_non_game_row(row: pd.Series) -> bool:
    title_text = " ".join(
        str(row.get(column, ""))
        for column in ["title", "title_en", "title_ko", "title_zh", "genres"]
    )
    return any(re.search(pattern, title_text, flags=re.IGNORECASE) for pattern in NON_GAME_PATTERNS)


def t(lang: str, key: str) -> str:
    return TEXT.get(lang, TEXT["en"]).get(key, TEXT["en"].get(key, key))


def t_list(lang: str, key: str) -> list[str]:
    value = TEXT.get(lang, TEXT["en"]).get(key, TEXT["en"].get(key, []))
    return value if isinstance(value, list) else []


def localize_value(lang: str, value: object) -> str:
    if is_blank(value):
        return t(lang, "not_tagged")
    text = str(value)
    return VALUE_LABELS.get(lang, {}).get(text, text)


def localize_tags(lang: str, value: object) -> str:
    tags = parse_tags(value)
    if not tags:
        return t(lang, "not_tagged")
    return ", ".join(localize_value(lang, tag) for tag in tags)


def get_display_title(game: pd.Series, lang: str) -> str:
    title_column = {"en": "title_en", "ko": "title_ko", "zh": "title_zh"}.get(lang, "title_en")
    localized_title = game.get(title_column)
    if lang == "zh":
        if not is_blank(localized_title):
            return str(localized_title)
        for column in ["title", "title_en"]:
            fallback_title = game.get(column)
            if not is_blank(fallback_title):
                return str(fallback_title)
        return t(lang, "untitled")

    if lang in {"en", "ko"}:
        if not is_blank(localized_title) and not has_non_korean_east_asian_text(localized_title):
            return str(localized_title)
        return get_safe_non_chinese_title(game, lang)

    fallback_title = game.get("title_en")
    if not is_blank(fallback_title) and not has_non_korean_east_asian_text(fallback_title):
        return str(fallback_title)
    return get_safe_non_chinese_title(game, lang)


def filter_games_for_language(dataframe: pd.DataFrame, lang: str) -> pd.DataFrame:
    if lang == "zh":
        return dataframe

    shaped = ensure_columns(dataframe)
    mask = shaped.apply(
        lambda row: not is_blank(get_display_title(row, lang))
        and not has_non_korean_east_asian_text(get_display_title(row, lang)),
        axis=1,
    )
    return shaped.loc[mask.fillna(False)].copy()


def get_original_title(game: pd.Series) -> str:
    title_en = game.get("title_en")
    if not is_blank(title_en):
        return str(title_en)
    return clean_text(game.get("title"), "Untitled game")


def get_localized_advice(game: pd.Series, lang: str) -> str:
    if lang == "en":
        return clean_text(game.get("buying_advice"), t(lang, "manual_advice_missing"))

    player_type = localize_tags(lang, game.get("player_type"))
    play_situation = localize_tags(lang, game.get("play_situation"))
    difficulty = localize_tags(lang, game.get("difficulty"))
    mood = localize_tags(lang, game.get("mood"))
    session_length = localize_tags(lang, game.get("session_length"))
    budget = localize_value(lang, clean_text(game.get("budget_tier"), ""))

    if lang == "ko":
        return f"{player_type}에게 잘 맞고, {play_situation} 상황에서 {mood} 분위기로 즐기기 좋습니다. 난이도는 {difficulty}, 플레이 시간은 {session_length}, 예산 등급은 {budget}입니다."
    if lang == "zh":
        return f"适合{player_type}，更适合在{play_situation}场景下获得{mood}体验。难度为{difficulty}，游玩时长偏{session_length}，预算档位为{budget}。"

    return clean_text(game.get("buying_advice"), t(lang, "manual_advice_missing"))


def is_blank(value: object) -> bool:
    if value is None or pd.isna(value):
        return True
    return str(value).strip() == ""


def clean_text(value: object, fallback: str = "Not tagged yet") -> str:
    if is_blank(value):
        return fallback
    return str(value).strip()


def parse_tags(value: object) -> list[str]:
    if is_blank(value):
        return []

    text = str(value).strip()
    text = text.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
    parts = re.split(r",|/|;|\|", text)
    return [part.strip() for part in parts if part.strip()]


def contains_choice(value: object, choice: str) -> bool:
    if choice == "Any":
        return True
    return choice.lower() in [item.lower() for item in parse_tags(value)]


def contains_any(value: object, choices: list[str]) -> bool:
    if not choices:
        return True
    value_tags = {item.lower() for item in parse_tags(value)}
    return any(choice.lower() in value_tags for choice in choices)


def match_yes_no(value: object, selected: str) -> bool:
    if selected == "Any":
        return True
    return clean_text(value, "").lower() == selected.lower()


def format_score(value: object) -> str:
    if is_blank(value):
        return "N/A"
    try:
        score = float(value)
    except ValueError:
        return "N/A"
    if np.isnan(score):
        return "N/A"
    if score.is_integer():
        return str(int(score))
    return f"{score:.1f}"


def format_release_date(value: object, lang: str) -> str:
    if is_blank(value):
        return t(lang, "not_tagged")
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return t(lang, "not_tagged")
    return parsed.strftime("%Y-%m-%d")


def numeric_value(value: object, fallback: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    if np.isnan(number):
        return fallback
    return number


def standardize_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = dataframe.rename(columns={column: normalize_column_name(column) for column in dataframe.columns})
    dataframe = dataframe.rename(
        columns={
            "release_date": "date",
            "metascore": "meta_score",
            "rating": "esrb_rating",
            "genre": "genres",
            "developer": "developers",
        }
    )

    if "title" not in dataframe.columns:
        dataframe["title"] = pd.NA

    dataframe["normalized_title"] = dataframe["title"].map(normalize_title)
    return dataframe


def ensure_columns(dataframe: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """Keep empty filtered dataframes shaped like the app dataset."""
    required_columns = columns or [*DISPLAY_COLUMNS, "normalized_title"]
    shaped = dataframe.copy()
    for column in required_columns:
        if column not in shaped.columns:
            shaped[column] = pd.NA
    return shaped


def filter_with_mask(dataframe: pd.DataFrame, column: str, predicate) -> pd.DataFrame:
    """Apply a boolean predicate without letting empty masks drop columns."""
    shaped = ensure_columns(dataframe)
    if column not in shaped.columns:
        return shaped.iloc[0:0].copy()

    mask = shaped[column].map(predicate).fillna(False).astype(bool)
    return shaped.loc[mask].copy()


def filter_by_tag_choices(dataframe: pd.DataFrame, column: str, choices: list[str]) -> pd.DataFrame:
    if not choices:
        return ensure_columns(dataframe)
    return filter_with_mask(dataframe, column, lambda value: contains_any(value, choices))


def get_playable_system_options(dataframe: pd.DataFrame) -> list[str]:
    """Return only real consoles for the user-facing console picker."""
    shaped = ensure_columns(dataframe)
    platforms = set(get_unique_tags(shaped, "platform"))
    platform_groups = set(get_unique_tags(shaped, "platform_group"))
    options: list[str] = []

    if "Nintendo Switch" in platforms:
        options.append("Nintendo Switch")
    if "Nintendo Switch 2" in platforms or "Nintendo Switch 2 Edition" in platforms or {"Switch 2", "Switch 2 Edition"} & platform_groups:
        options.append("Nintendo Switch 2")

    return options


def filter_by_playable_systems(dataframe: pd.DataFrame, systems: list[str]) -> pd.DataFrame:
    """Filter by the console the player owns, including Switch 2 compatibility."""
    shaped = ensure_columns(dataframe)
    if not systems:
        return shaped

    masks: list[pd.Series] = []
    if "Nintendo Switch" in systems:
        masks.append(shaped["platform"].astype(str).eq("Nintendo Switch"))
    if "Nintendo Switch 2" in systems:
        switch_2_groups = ["Switch Compatible", "Switch 2", "Switch 2 Edition"]
        masks.append(
            shaped["platform"].astype(str).eq("Nintendo Switch 2")
            | shaped["platform_group"].map(lambda value: contains_any(value, switch_2_groups))
        )

    if not masks:
        return shaped.iloc[0:0].copy()

    combined_mask = masks[0].copy()
    for mask in masks[1:]:
        combined_mask = combined_mask | mask
    return shaped.loc[combined_mask.fillna(False)].copy()


def sidebar_tag_multiselect(
    label: str,
    options: list[str],
    lang: str,
    key: str,
    default: list[str] | None = None,
) -> list[str]:
    """Render a multiselect whose stored values are pruned when parent filters change."""
    default_values = [value for value in (default or []) if value in options]
    if key in st.session_state and isinstance(st.session_state[key], list):
        st.session_state[key] = [value for value in st.session_state[key] if value in options]

    if not options:
        st.sidebar.caption(f"{label}: {t(lang, 'no_filter_options')}")
        return []

    widget_kwargs = {
        "label": label,
        "options": options,
        "format_func": lambda value: localize_value(lang, value),
        "key": key,
    }
    if key not in st.session_state:
        widget_kwargs["default"] = default_values

    return st.sidebar.multiselect(**widget_kwargs)


def tag_multiselect(
    label: str,
    options: list[str],
    lang: str,
    key: str,
    default: list[str] | None = None,
) -> list[str]:
    """Render a multiselect in the main page and prune stale stored values."""
    default_values = [value for value in (default or []) if value in options]
    if key in st.session_state and isinstance(st.session_state[key], list):
        st.session_state[key] = [value for value in st.session_state[key] if value in options]

    if not options:
        st.caption(f"{label}: {t(lang, 'no_filter_options')}")
        return []

    widget_kwargs = {
        "label": label,
        "options": options,
        "format_func": lambda value: localize_value(lang, value),
        "key": key,
    }
    if key not in st.session_state:
        widget_kwargs["default"] = default_values

    return st.multiselect(**widget_kwargs)


def combine_prefer_manual(dataframe: pd.DataFrame, column: str) -> pd.Series:
    manual_column = f"{column}_manual"
    if manual_column not in dataframe.columns:
        return dataframe[column] if column in dataframe.columns else pd.Series(pd.NA, index=dataframe.index)
    if column not in dataframe.columns:
        return dataframe[manual_column]
    return dataframe[manual_column].where(~dataframe[manual_column].map(is_blank), dataframe[column])


def merge_localizations(dataframe: pd.DataFrame) -> pd.DataFrame:
    if not LOCALIZATIONS_PATH.exists():
        for column in LOCALIZATION_COLUMNS:
            if column not in dataframe.columns:
                dataframe[column] = pd.NA
        dataframe["title_en"] = dataframe["title_en"].where(~dataframe["title_en"].map(is_blank), dataframe["title"])
        return dataframe

    localizations = standardize_dataframe(pd.read_csv(LOCALIZATIONS_PATH))
    localization_columns = ["normalized_title", *LOCALIZATION_COLUMNS]
    localizations = localizations[localization_columns].drop_duplicates(subset=["normalized_title"], keep="last")
    localized = dataframe.merge(localizations, on="normalized_title", how="left", suffixes=("", "_localized"))

    for column in LOCALIZATION_COLUMNS:
        localized_column = f"{column}_localized"
        if localized_column in localized.columns:
            localized[column] = localized[localized_column].where(
                ~localized[localized_column].map(is_blank),
                localized[column],
            )
            localized = localized.drop(columns=[localized_column])

    localized["title_en"] = localized["title_en"].where(~localized["title_en"].map(is_blank), localized["title"])
    return localized


def merge_media(dataframe: pd.DataFrame) -> pd.DataFrame:
    if not MEDIA_PATH.exists():
        for column in MEDIA_COLUMNS:
            if column not in dataframe.columns:
                dataframe[column] = pd.NA
        return dataframe

    media = standardize_dataframe(pd.read_csv(MEDIA_PATH))
    for column in MEDIA_COLUMNS:
        if column not in media.columns:
            media[column] = pd.NA

    media_columns = ["normalized_title", *MEDIA_COLUMNS]
    media = media[media_columns].drop_duplicates(subset=["normalized_title"], keep="last")
    with_media = dataframe.merge(media, on="normalized_title", how="left", suffixes=("", "_media"))

    for column in MEDIA_COLUMNS:
        media_column = f"{column}_media"
        if media_column in with_media.columns:
            with_media[column] = with_media[media_column].where(
                ~with_media[media_column].map(is_blank),
                with_media[column],
            )
            with_media = with_media.drop(columns=[media_column])

    return with_media


def is_store_like_url(value: object) -> bool:
    if is_blank(value):
        return False
    url = str(value).strip().lower()
    store_markers = [
        "/us/store/products/",
        "ec.nintendo.com",
        "/hk/store/",
        "/kr/store/",
    ]
    return any(marker in url for marker in store_markers)


def is_url_for_language(value: object, lang: str) -> bool:
    if is_blank(value):
        return False
    url = str(value).strip().lower()

    if lang == "en":
        wrong_language_markers = [
            "nintendo.com.hk",
            "nintendo.com/zh-hans-hk",
            "nintendo.com/hk/",
            "ec.nintendo.com/hk/",
            "nintendo.com/kr/",
            "ec.nintendo.com/kr/",
        ]
        return not any(marker in url for marker in wrong_language_markers)

    if lang == "zh":
        zh_markers = [
            "nintendo.com.hk",
            "nintendo.com/zh-hans-hk",
            "nintendo.com/hk/",
            "ec.nintendo.com/hk/",
        ]
        return any(marker in url for marker in zh_markers)

    if lang == "ko":
        ko_markers = [
            "nintendo.com/kr/",
            "ec.nintendo.com/kr/",
        ]
        return any(marker in url for marker in ko_markers)

    return True


def get_en_detail_override(game: pd.Series) -> str:
    for column in ["title_en", "title", "title_zh", "title_ko"]:
        title_key = normalize_title(game.get(column))
        if title_key in EN_DETAIL_OVERRIDES:
            return EN_DETAIL_OVERRIDES[title_key]
    return ""


def get_official_url(game: pd.Series, lang: str) -> str:
    url_column = {"en": "official_url_en", "ko": "official_url_ko", "zh": "official_url_zh"}.get(lang, "official_url_en")

    if lang == "en":
        detail_url = get_en_detail_override(game)
        if detail_url:
            return detail_url

    regional_url = game.get(url_column)
    if is_url_for_language(regional_url, lang):
        return str(regional_url).strip()

    return ""


@st.cache_data
def load_local_image_data_uri(image_file: str, modified_ns: int) -> str:
    image_path = (PROJECT_ROOT / image_file).resolve()
    if not image_path.exists() or not image_path.is_file():
        return ""

    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
    encoded_image = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded_image}"


def resolve_project_image(image_file: object) -> Path | None:
    if is_blank(image_file):
        return None

    relative_path = Path(str(image_file).strip())
    if relative_path.is_absolute():
        return None

    image_path = (PROJECT_ROOT / relative_path).resolve()
    try:
        image_path.relative_to(PROJECT_ROOT)
    except ValueError:
        return None

    if not image_path.is_file():
        return None
    return image_path


def get_image_src(game: pd.Series) -> str:
    image_file = clean_text(game.get("image_file"), "")
    image_path = resolve_project_image(image_file)
    if image_path is not None:
        modified_ns = image_path.stat().st_mtime_ns
        local_src = load_local_image_data_uri(image_file, modified_ns)
        if local_src:
            return local_src

    return clean_text(game.get("image_url"), "")


def keep_official_media_games(dataframe: pd.DataFrame) -> pd.DataFrame:
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

    if filtered.empty:
        return filtered

    filtered["platform_priority"] = filtered["platform"].map(lambda value: PLATFORM_PRIORITY.get(str(value), 9))
    filtered["sort_date"] = pd.to_datetime(filtered["date"], errors="coerce")
    filtered = filtered.sort_values(
        by=["normalized_title", "platform_priority", "sort_date", "meta_score", "title"],
        ascending=[True, True, False, False, True],
        na_position="last",
    )
    filtered = filtered.drop_duplicates(subset=["normalized_title"], keep="first")
    filtered = filtered.drop(columns=["platform_priority", "sort_date"])
    return filtered


def get_data_path() -> Path | None:
    """Prefer the full merged dataset, then fall back to the cleaned base dataset."""
    if MERGED_DATA_PATH.exists():
        return MERGED_DATA_PATH
    if CLEAN_DATA_PATH.exists():
        return CLEAN_DATA_PATH
    return None


def get_data_cache_token(data_path: Path) -> tuple[int, ...]:
    watched_paths = [data_path, MANUAL_TAGS_PATH, LOCALIZATIONS_PATH, MEDIA_PATH]
    return tuple(path.stat().st_mtime_ns if path.exists() else 0 for path in watched_paths)


@st.cache_data
def load_games(data_path: str, cache_token: tuple[int, ...]) -> pd.DataFrame:
    """Load public game data and merge player-oriented manual tags."""
    base_games = standardize_dataframe(pd.read_csv(data_path))

    if MANUAL_TAGS_PATH.exists():
        manual_tags = standardize_dataframe(pd.read_csv(MANUAL_TAGS_PATH))
    else:
        manual_tags = pd.DataFrame(columns=["normalized_title", *TAG_COLUMNS])

    merged = base_games.merge(
        manual_tags,
        on="normalized_title",
        how="outer",
        suffixes=("", "_manual"),
    )

    if "title_manual" in merged.columns:
        merged["title"] = merged["title"].where(~merged["title"].map(is_blank), merged["title_manual"])

    for column in TAG_COLUMNS:
        merged[column] = combine_prefer_manual(merged, column)

    merged = merge_localizations(merged)
    merged = merge_media(merged)

    for column in DISPLAY_COLUMNS:
        if column not in merged.columns:
            merged[column] = pd.NA

    for column in ["meta_score", "user_score"]:
        merged[column] = pd.to_numeric(merged[column], errors="coerce")

    if "date" in merged.columns:
        merged["date"] = pd.to_datetime(merged["date"], errors="coerce").dt.strftime("%Y-%m-%d")

    merged["platform"] = merged["platform"].fillna("Nintendo Switch")
    merged = keep_official_media_games(merged)
    merged = merged.drop_duplicates(subset=["normalized_title", "platform"], keep="first")
    merged = merged.sort_values(["meta_score", "user_score", "title"], ascending=[False, False, True], na_position="last")
    return merged[DISPLAY_COLUMNS + ["normalized_title"]]


def get_unique_tags(dataframe: pd.DataFrame, column: str) -> list[str]:
    values: set[str] = set()
    if column not in dataframe.columns:
        return []
    for value in dataframe[column].dropna():
        values.update(parse_tags(value))
    return sorted(values)


def add_page_style() -> None:
    st.markdown(
        """
        <style>
        #MainMenu,
        footer,
        div[data-testid="stDecoration"] {
            display: none;
        }
        div[data-testid="stToolbar"] {
            position: fixed !important;
            top: 0.85rem !important;
            left: 0.85rem !important;
            right: auto !important;
            bottom: auto !important;
            width: auto !important;
            min-width: 0 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            z-index: 1002 !important;
            padding: 0 !important;
        }
        div[data-testid="stToolbar"] a,
        div[data-testid="stToolbar"] button:not([kind="header"]) {
            display: none !important;
        }
        .stApp {
            background:
                linear-gradient(180deg, rgba(226, 246, 255, 0.72) 0%, rgba(248, 251, 255, 0.88) 36%, #f6fbf4 100%);
        }
        .block-container {
            padding-top: 1.5rem;
            max-width: 1240px;
        }
        @keyframes navGlow {
            0%, 100% { box-shadow: 0 10px 24px rgba(239, 68, 68, 0.22); }
            50% { box-shadow: 0 14px 30px rgba(14, 165, 233, 0.22); }
        }
        @keyframes gentleFloat {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-5px); }
        }
        @keyframes softSlide {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        section[data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, #fff7f1 0%, #eef8ff 48%, #f3fff6 100%);
            border-right: 1px solid #dbeafe;
            box-shadow: 10px 0 28px rgba(15, 23, 42, 0.08);
        }
        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"],
        button[kind="header"] {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            visibility: visible !important;
            opacity: 1 !important;
            z-index: 1000 !important;
        }
        [data-testid="collapsedControl"] {
            position: fixed !important;
            top: 0.9rem !important;
            left: 0.9rem !important;
            width: 2.75rem !important;
            height: 2.75rem !important;
            border-radius: 999px !important;
            background: rgba(255, 255, 255, 0.94) !important;
            border: 1px solid rgba(251, 146, 60, 0.35) !important;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.12) !important;
            backdrop-filter: blur(10px);
        }
        button[kind="header"] {
            position: fixed !important;
            top: 0.9rem !important;
            left: 0.9rem !important;
            width: 2.75rem !important;
            height: 2.75rem !important;
            border-radius: 999px !important;
            background: rgba(255, 255, 255, 0.94) !important;
            border: 1px solid rgba(251, 146, 60, 0.35) !important;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.12) !important;
            backdrop-filter: blur(10px);
        }
        [data-testid="stSidebarCollapseButton"] {
            border-radius: 999px !important;
            background: rgba(255, 255, 255, 0.88) !important;
            border: 1px solid rgba(251, 146, 60, 0.28) !important;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08) !important;
            backdrop-filter: blur(8px);
        }
        [data-testid="stSidebarCollapseButton"]:hover,
        [data-testid="collapsedControl"]:hover,
        button[kind="header"]:hover {
            background: rgba(255, 247, 237, 0.98) !important;
            border-color: rgba(239, 68, 68, 0.35) !important;
        }
        section[data-testid="stSidebar"] * {
            color: #1f2937;
            letter-spacing: 0;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
            padding-top: 1.4rem;
        }
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label {
            color: #475569;
        }
        section[data-testid="stSidebar"] h1 {
            color: #172033;
            font-weight: 900;
            line-height: 1.02;
            margin-bottom: 8px;
        }
        section[data-testid="stSidebar"] h1::after {
            content: "";
            display: block;
            width: 74px;
            height: 6px;
            border-radius: 999px;
            margin-top: 12px;
            background: linear-gradient(90deg, #ef4444, #facc15, #22c55e, #38bdf8);
            background-size: 220% 100%;
            animation: softSlide 5s ease infinite;
        }
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background: #ffffff;
            border-color: #d7e2ef;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
        }
        section[data-testid="stSidebar"] div[data-baseweb="select"] * {
            color: #172033;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] {
            display: grid;
            gap: 11px;
            margin-top: 10px;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label {
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid #dbe6f4;
            border-radius: 14px;
            padding: 12px 12px;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
            position: relative;
            overflow: hidden;
            transition: transform 0.18s ease, background 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label::before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 5px;
            background: linear-gradient(180deg, #ef4444, #facc15);
            opacity: 0;
            transition: opacity 0.18s ease;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            transform: translateX(4px);
            background: #ffffff;
            border-color: #fecaca;
            box-shadow: 0 12px 24px rgba(239, 68, 68, 0.14);
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
            background: linear-gradient(135deg, #ff4b4b 0%, #ff6b55 56%, #ffb84d 100%);
            border-color: #f87171;
            animation: navGlow 3.6s ease infinite;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked)::before {
            opacity: 1;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label p {
            color: #172033;
            font-weight: 850;
            font-size: 1rem;
            line-height: 1.18;
            margin: 0;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
            color: #ffffff;
            text-shadow: 0 1px 2px rgba(127, 29, 29, 0.18);
        }
        .sidebar-nav-copy {
            color: #64748b;
            font-size: 0.78rem;
            line-height: 1.35;
            margin: 6px 0 12px;
        }
        div[data-testid="stTabs"] button {
            font-weight: 750;
            color: #475569;
            padding-top: 12px;
            padding-bottom: 12px;
        }
        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: #dc2626;
        }
        div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] {
            background-color: #ef4444;
            height: 3px;
        }
        .compass-hero {
            background:
                linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(240, 249, 255, 0.92) 48%, rgba(240, 253, 244, 0.96) 100%);
            border: 1px solid #dbeafe;
            border-top: 6px solid #ef4444;
            border-radius: 12px;
            padding: 28px;
            margin-bottom: 18px;
            box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
            position: relative;
            overflow: hidden;
        }
        .compass-hero::after {
            content: "";
            position: absolute;
            inset: auto 0 0 0;
            height: 7px;
            background: linear-gradient(90deg, #ef4444, #facc15, #22c55e, #38bdf8, #ef4444);
            background-size: 240% 100%;
            animation: softSlide 7s ease infinite;
        }
        .hero-layout {
            display: grid;
            grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
            gap: 26px;
            align-items: center;
        }
        .hero-kicker {
            color: #be123c;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .hero-title {
            color: #1f2937;
            font-size: 2.25rem;
            line-height: 1.08;
            font-weight: 800;
            margin-bottom: 10px;
        }
        .hero-copy {
            color: #4b5563;
            font-size: 1.05rem;
            line-height: 1.55;
            max-width: 760px;
        }
        .hero-stats {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 18px;
        }
        .hero-stat {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            background: #fafafa;
            padding: 9px 12px;
            min-width: 118px;
        }
        .hero-stat strong {
            display: block;
            color: #111827;
            font-size: 1.05rem;
            line-height: 1.15;
        }
        .hero-stat span {
            color: #6b7280;
            font-size: 0.76rem;
        }
        .hero-visuals {
            display: grid;
            gap: 10px;
        }
        .hero-shot {
            display: block;
            border-radius: 8px;
            border: 1px solid #dbe3ee;
            overflow: hidden;
            background: #eef2f7;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.12);
        }
        .hero-shot:first-child {
            animation: gentleFloat 6s ease-in-out infinite;
        }
        .hero-shot img {
            display: block;
            width: 100%;
            aspect-ratio: 16 / 9;
            object-fit: cover;
        }
        .hero-shot-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .quick-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin: 14px 0 20px;
        }
        .quick-tile {
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 14px;
            background: #ffffff;
            min-height: 100px;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
            position: relative;
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        }
        .quick-tile:hover {
            transform: translateY(-4px);
            border-color: #bfdbfe;
            box-shadow: 0 16px 30px rgba(14, 165, 233, 0.14);
        }
        .quick-tile::before {
            content: attr(data-step);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            border-radius: 999px;
            background: #fee2e2;
            color: #b91c1c;
            font-size: 0.78rem;
            font-weight: 800;
            margin-bottom: 10px;
        }
        .quick-tile strong {
            display: block;
            color: #1f2937;
            font-size: 0.96rem;
            margin-bottom: 5px;
        }
        .quick-tile span {
            color: #64748b;
            font-size: 0.82rem;
            line-height: 1.35;
        }
        .finder-main-header {
            background:
                linear-gradient(135deg, #172033 0%, #243b63 48%, #0f766e 100%);
            border: 1px solid rgba(255, 255, 255, 0.5);
            border-radius: 16px;
            padding: 24px 26px;
            margin: 8px 0 18px;
            color: #ffffff;
            box-shadow: 0 18px 38px rgba(15, 23, 42, 0.16);
            position: relative;
            overflow: hidden;
        }
        .finder-main-header::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                repeating-linear-gradient(135deg, rgba(255, 255, 255, 0.09) 0 1px, transparent 1px 18px);
            opacity: 0.72;
            pointer-events: none;
        }
        .finder-main-header > * {
            position: relative;
            z-index: 1;
        }
        .finder-main-header .finder-kicker {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #172033;
            background: #fef3c7;
            border: 1px solid rgba(254, 243, 199, 0.8);
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 0.78rem;
            font-weight: 900;
            margin-bottom: 12px;
        }
        .finder-main-header h2 {
            color: #ffffff;
            font-size: 2rem;
            line-height: 1.08;
            margin: 0 0 10px;
            letter-spacing: 0;
        }
        .finder-main-header p {
            color: #e0f2fe;
            max-width: 780px;
            line-height: 1.55;
            font-size: 1rem;
            margin: 0;
        }
        .finder-main-stats {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 16px;
        }
        .finder-main-chip {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            color: #ffffff;
            background: rgba(255, 255, 255, 0.14);
            border: 1px solid rgba(255, 255, 255, 0.22);
            border-radius: 999px;
            padding: 7px 11px;
            font-size: 0.82rem;
            font-weight: 760;
            backdrop-filter: blur(6px);
        }
        .finder-main-chip strong {
            color: #fde68a;
            font-size: 0.92rem;
        }
        .filter-heading {
            display: flex;
            justify-content: space-between;
            gap: 18px;
            align-items: center;
            margin-bottom: 16px;
        }
        .filter-heading h3 {
            color: #111827;
            font-size: 1.35rem;
            margin: 0 0 4px;
            letter-spacing: 0;
        }
        .filter-heading p {
            color: #64748b;
            margin: 0;
            font-size: 0.9rem;
            line-height: 1.45;
        }
        .filter-badge {
            flex: 0 0 auto;
            color: #b91c1c;
            background: #fee2e2;
            border: 1px solid #fecaca;
            border-radius: 999px;
            padding: 6px 10px;
            font-size: 0.76rem;
            font-weight: 800;
        }
        .filter-group-title {
            color: #0f172a;
            font-size: 0.95rem;
            font-weight: 850;
            margin: 16px 0 8px;
            letter-spacing: 0;
        }
        .filter-group-title::before {
            content: "";
            display: inline-block;
            width: 7px;
            height: 7px;
            border-radius: 999px;
            background: #ef4444;
            margin-right: 8px;
            vertical-align: 2px;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: #d9e2ec;
            border-radius: 8px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.06);
            background: linear-gradient(180deg, #ffffff 0%, #fbfcfd 100%);
        }
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div {
            border-radius: 8px;
        }
        .section-intro {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px 22px;
            margin: 10px 0 18px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
        }
        .section-intro .section-kicker {
            display: inline-block;
            color: #be123c;
            background: #fff1f2;
            border: 1px solid #fecdd3;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 0.76rem;
            font-weight: 800;
            margin-bottom: 10px;
        }
        .section-intro h2 {
            color: #111827;
            font-size: 1.55rem;
            line-height: 1.2;
            margin: 0 0 7px;
            letter-spacing: 0;
        }
        .section-intro p {
            color: #556174;
            font-size: 0.98rem;
            line-height: 1.55;
            margin: 0;
            max-width: 820px;
        }
        .game-card {
            background: #ffffff;
            border: 1px solid #e3e7ee;
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 14px;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.07);
            min-height: 430px;
            transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
        }
        .game-card:hover {
            border-color: #fecaca;
            box-shadow: 0 16px 34px rgba(15, 23, 42, 0.11);
            transform: translateY(-3px);
        }
        .game-card-body {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .game-cover-link,
        .game-cover-wrap {
            display: block;
            width: 100%;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #dfe5ed;
            background: #f3f5f8;
            text-decoration: none;
        }
        .game-cover-link {
            transition: transform 0.16s ease, box-shadow 0.16s ease;
        }
        .game-cover-link:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.14);
        }
        .game-cover {
            display: block;
            width: 100%;
            aspect-ratio: 16 / 9;
            object-fit: cover;
        }
        .game-cover-placeholder {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            aspect-ratio: 16 / 9;
            color: #7b8797;
            font-size: 0.78rem;
            text-align: center;
            padding: 8px;
            background: linear-gradient(135deg, #f4f6fa, #ffffff);
        }
        .game-content {
            min-width: 0;
            flex: 1;
            width: 100%;
        }
        .game-card h3 {
            color: #172033;
            font-size: 1.08rem;
            line-height: 1.25;
            margin: 0 0 8px 0;
            letter-spacing: 0;
        }
        .game-title-link {
            color: #172033;
            text-decoration: none;
        }
        .game-title-link:hover {
            color: #dc2626;
            text-decoration: underline;
        }
        .meta-row {
            color: #5b677a;
            font-size: 0.85rem;
            margin-bottom: 7px;
        }
        .tag-row {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin: 8px 0;
        }
        .tag-chip {
            display: inline-block;
            color: #334155;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 999px;
            padding: 4px 8px;
            font-size: 0.76rem;
            line-height: 1.2;
        }
        .small-note {
            color: #667085;
            font-size: 0.85rem;
            line-height: 1.45;
            margin-top: 8px;
        }
        .score-pill {
            display: inline-block;
            background: #fff7ed;
            color: #9a3412;
            border: 1px solid #fed7aa;
            border-radius: 999px;
            padding: 3px 8px;
            font-size: 0.78rem;
            margin-right: 5px;
            margin-bottom: 4px;
        }
        @media (max-width: 900px) {
            .hero-layout {
                grid-template-columns: 1fr;
            }
            .quick-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .filter-heading {
                align-items: flex-start;
                flex-direction: column;
            }
            .hero-title {
                font-size: 1.65rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero_image_html(games: pd.DataFrame, lang: str) -> str:
    featured = games[games["image_file"].map(lambda value: not is_blank(value))].head(3)
    image_tags: list[str] = []
    for _, game in featured.iterrows():
        image_src = get_image_src(game)
        if not image_src:
            continue
        title = escape(get_display_title(game, lang))
        image_tags.append(f'<span class="hero-shot"><img src="{escape(image_src)}" alt="{title}"></span>')

    if len(image_tags) < 3:
        return ""

    return (
        '<div class="hero-visuals">'
        f"{image_tags[0]}"
        '<div class="hero-shot-row">'
        f"{image_tags[1]}{image_tags[2]}"
        "</div>"
        "</div>"
    )


def render_section_intro(title: str, description: str, kicker: str) -> None:
    st.markdown(
        f"""
        <section class="section-intro">
            <span class="section-kicker">{escape(kicker)}</span>
            <h2>{escape(title)}</h2>
            <p>{escape(description)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_finder_main_header(games: pd.DataFrame, lang: str) -> None:
    total_games = len(games)
    tagged_games = int(games["buying_advice"].map(lambda value: not is_blank(value)).sum())
    strong_score_games = int((games["meta_score"].fillna(0) >= 80).sum())
    st.markdown(
        f"""
        <section class="finder-main-header">
            <span class="finder-kicker">{escape(t(lang, "finder_main_kicker"))}</span>
            <h2>{escape(t(lang, "tab_finder"))}</h2>
            <p>{escape(t(lang, "finder_main_note"))}</p>
            <div class="finder-main-stats">
                <span class="finder-main-chip"><strong>{total_games}</strong>{escape(t(lang, "matching_games"))}</span>
                <span class="finder-main-chip"><strong>{tagged_games}</strong>{escape(t(lang, "tagged_picks"))}</span>
                <span class="finder-main-chip"><strong>{strong_score_games}</strong>{escape(t(lang, "meta_80"))}</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_hero(games: pd.DataFrame, total_games: int, tagged_games: int, lang: str) -> None:
    visual_html = hero_image_html(games, lang)
    st.markdown(
        f"""
        <section class="compass-hero">
            <div class="hero-layout">
                <div>
                    <div class="hero-kicker">{escape(t(lang, "hero_kicker"))}</div>
                    <div class="hero-title">Nintendo Game Compass</div>
                    <div class="hero-copy">
                        {escape(t(lang, "hero_copy"))}
                    </div>
                    <div class="hero-stats">
                        <div class="hero-stat"><strong>{total_games}</strong><span>Games</span></div>
                        <div class="hero-stat"><strong>{tagged_games}</strong><span>{escape(t(lang, "tagged_picks"))}</span></div>
                        <div class="hero-stat"><strong>3</strong><span>{escape(t(lang, "language"))}</span></div>
                    </div>
                </div>
                {visual_html}
            </div>
        </section>
        <div class="quick-grid">
            <div class="quick-tile" data-step="01"><strong>{escape(t(lang, "quick_new"))}</strong><span>{escape(t(lang, "quick_new_desc"))}</span></div>
            <div class="quick-tile" data-step="02"><strong>{escape(t(lang, "quick_tonight"))}</strong><span>{escape(t(lang, "quick_tonight_desc"))}</span></div>
            <div class="quick-tile" data-step="03"><strong>{escape(t(lang, "tab_table"))}</strong><span>{escape(t(lang, "quick_table_desc"))}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_card(game: pd.Series, lang: str, reason: str | None = None, score: int | None = None) -> None:
    display_title = get_display_title(game, lang)
    title = escape(display_title)
    platform = escape(localize_value(lang, clean_text(game.get("platform"), "Nintendo Switch")))
    release_date = escape(format_release_date(game.get("date"), lang))
    genres = escape(localize_tags(lang, game.get("genres")) if parse_tags(game.get("genres")) else t(lang, "genre_missing"))
    genre_main = localize_tags(lang, game.get("genre_main"))
    player_type = localize_tags(lang, game.get("player_type"))
    play_situation = localize_tags(lang, game.get("play_situation"))
    mood = localize_tags(lang, game.get("mood"))
    difficulty = localize_tags(lang, game.get("difficulty"))
    budget = localize_tags(lang, game.get("budget_tier"))
    beginner = localize_value(lang, clean_text(game.get("beginner_friendly"), ""))
    local_multi = localize_value(lang, clean_text(game.get("local_multiplayer"), ""))
    online_multi = localize_value(lang, clean_text(game.get("online_multiplayer"), ""))

    score_html = ""
    if score is not None:
        score_html = f'<span class="score-pill">{escape(t(lang, "score"))} {score}</span>'

    image_url = get_image_src(game)
    official_url = get_official_url(game, lang)
    if image_url and official_url:
        image_html = (
            f'<a class="game-cover-link" href="{escape(official_url)}" target="_blank" rel="noopener noreferrer" '
            f'aria-label="{escape(t(lang, "official_page"))}: {title}">'
            f'<img class="game-cover" src="{escape(image_url)}" alt="{title}"></a>'
        )
    elif image_url:
        image_html = f'<span class="game-cover-wrap"><img class="game-cover" src="{escape(image_url)}" alt="{title}"></span>'
    else:
        image_html = f'<span class="game-cover-wrap"><span class="game-cover-placeholder">{escape(t(lang, "no_image"))}</span></span>'

    title_html = title
    if official_url:
        title_html = (
            f'<a class="game-title-link" href="{escape(official_url)}" '
            f'target="_blank" rel="noopener noreferrer">{title}</a>'
        )

    tag_values = [genre_main, player_type, play_situation, mood, difficulty, budget]
    tag_html = "".join(
        f'<span class="tag-chip">{escape(value)}</span>'
        for value in tag_values
        if value and value != t(lang, "not_tagged")
    )

    card_html = (
        '<article class="game-card">'
        '<div class="game-card-body">'
        f"{image_html}"
        '<div class="game-content">'
        f"<h3>{title_html}</h3>"
        f'<div class="meta-row">{platform} | {escape(t(lang, "release_date"))}: {release_date}</div>'
        f'<div class="meta-row">{genres}</div>'
        f'<div class="tag-row">{tag_html}</div>'
        f'<div class="meta-row">{score_html}'
        f'<span class="score-pill">{escape(t(lang, "metacritic"))} {format_score(game.get("meta_score"))}</span>'
        f'<span class="score-pill">{escape(t(lang, "user"))} {format_score(game.get("user_score"))}</span></div>'
        f'<div class="small-note">{escape(t(lang, "beginner_card"))}: {escape(beginner)} | {escape(t(lang, "local_multi_card"))}: {escape(local_multi)} | {escape(t(lang, "online_multiplayer"))}: {escape(online_multi)}</div>'
        "</div>"
        "</div>"
        "</article>"
    )
    st.markdown(card_html, unsafe_allow_html=True)


def render_card_grid(dataframe: pd.DataFrame, lang: str, max_cards: int = 12, with_score: bool = False) -> None:
    if dataframe.empty:
        st.info(t(lang, "no_matches"))
        return

    cards = dataframe.head(max_cards)
    cards_per_row = 3
    for start in range(0, len(cards), cards_per_row):
        columns = st.columns(cards_per_row)
        for column, (_, row) in zip(columns, cards.iloc[start : start + cards_per_row].iterrows()):
            with column:
                reason = row.get("recommendation_reason") if "recommendation_reason" in row else None
                score = int(row.get("recommendation_score")) if with_score and not pd.isna(row.get("recommendation_score")) else None
                render_card(row, lang=lang, reason=reason, score=score)


def count_options(total_count: int, defaults: list[int]) -> list[int]:
    if total_count <= 0:
        return []
    options = [count for count in defaults if count < total_count]
    options.append(total_count)
    return list(dict.fromkeys(options))


def format_count_option(lang: str, value: int, total_count: int) -> str:
    if value == total_count:
        return t(lang, "all_results")
    return str(value)


def apply_compass_filters(games: pd.DataFrame, lang: str) -> pd.DataFrame:
    """Render a compact game-picker panel and apply choices in user-facing groups."""
    filtered = ensure_columns(games)

    with st.container(border=True):
        st.markdown(
            f"""
            <div class="filter-heading">
                <div>
                    <h3>{escape(t(lang, "filter_panel_title"))}</h3>
                    <p>{escape(t(lang, "filter_panel_desc"))}</p>
                </div>
                <span class="filter-badge">{escape(t(lang, "filter_badge"))}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(f'<div class="filter-group-title">{escape(t(lang, "filter_group_library"))}</div>', unsafe_allow_html=True)
        starter_columns = st.columns([1.1, 1.3, 0.8])
        with starter_columns[0]:
            selected_platforms = tag_multiselect(
                t(lang, "platform"),
                get_playable_system_options(filtered),
                lang,
                key="finder_panel_playable_system",
            )
        filtered = filter_by_playable_systems(filtered, selected_platforms)

        with starter_columns[1]:
            search_query = st.text_input(t(lang, "search_title"), value="", key="finder_panel_search_title").strip()
        if search_query:
            search_columns = [column for column in ["title", "title_en", "title_ko", "title_zh"] if column in filtered.columns]
            if search_columns:
                search_text = filtered[search_columns].fillna("").agg(" ".join, axis=1).str.lower()
                filtered = filtered.loc[search_text.str.contains(re.escape(search_query.lower()), na=False)].copy()
            else:
                filtered = filtered.iloc[0:0].copy()
        filtered = ensure_columns(filtered)

        with starter_columns[2]:
            min_meta_score = st.slider(t(lang, "minimum_meta"), 0, 100, 0, 5, key="finder_panel_min_meta")
        filtered = filter_with_mask(filtered, "meta_score", lambda value: numeric_value(value) >= min_meta_score)
        filtered = ensure_columns(filtered)

        st.markdown(f'<div class="filter-group-title">{escape(t(lang, "filter_group_feel"))}</div>', unsafe_allow_html=True)
        feel_columns = st.columns(3)
        with feel_columns[0]:
            selected_play_situations = tag_multiselect(
                t(lang, "play_situation"),
                get_unique_tags(filtered, "play_situation"),
                lang,
                key="finder_panel_play_situation",
            )
        filtered = filter_by_tag_choices(filtered, "play_situation", selected_play_situations)

        with feel_columns[1]:
            selected_moods = tag_multiselect(
                t(lang, "mood"),
                get_unique_tags(filtered, "mood"),
                lang,
                key="finder_panel_mood",
            )
        filtered = filter_by_tag_choices(filtered, "mood", selected_moods)

        with feel_columns[2]:
            selected_difficulties = tag_multiselect(
                t(lang, "difficulty"),
                get_unique_tags(filtered, "difficulty"),
                lang,
                key="finder_panel_difficulty",
            )
        filtered = filter_by_tag_choices(filtered, "difficulty", selected_difficulties)

        st.markdown(f'<div class="filter-group-title">{escape(t(lang, "filter_group_practical"))}</div>', unsafe_allow_html=True)
        practical_columns = st.columns(3)
        with practical_columns[0]:
            beginner_friendly = st.selectbox(
                t(lang, "beginner_friendly"),
                ["Any", "Yes", "No"],
                format_func=lambda value: localize_value(lang, value),
                key="finder_panel_beginner_friendly",
            )
        filtered = filter_with_mask(filtered, "beginner_friendly", lambda value: match_yes_no(value, beginner_friendly))

        with practical_columns[1]:
            local_multiplayer = st.selectbox(
                t(lang, "local_multiplayer"),
                ["Any", "Yes", "No"],
                format_func=lambda value: localize_value(lang, value),
                key="finder_panel_local_multiplayer",
            )
        filtered = filter_with_mask(filtered, "local_multiplayer", lambda value: match_yes_no(value, local_multiplayer))

        with practical_columns[2]:
            selected_budgets = tag_multiselect(
                t(lang, "budget_tier"),
                get_unique_tags(filtered, "budget_tier"),
                lang,
                key="finder_panel_budget_tier",
            )
        filtered = filter_by_tag_choices(filtered, "budget_tier", selected_budgets)

        with st.expander(t(lang, "filter_more_title"), expanded=False):
            show_version_filter = "Nintendo Switch 2" in selected_platforms
            selected_platform_groups: list[str] = []
            if show_version_filter:
                more_columns = st.columns(4)
                with more_columns[0]:
                    selected_platform_groups = tag_multiselect(
                        t(lang, "platform_group"),
                        get_unique_tags(filtered, "platform_group"),
                        lang,
                        key="finder_panel_release_type",
                    )
            else:
                if "finder_panel_release_type" in st.session_state:
                    st.session_state["finder_panel_release_type"] = []
                more_columns = st.columns(3)
            filtered = filter_by_tag_choices(filtered, "platform_group", selected_platform_groups)

            genre_column = more_columns[1] if show_version_filter else more_columns[0]
            player_column = more_columns[2] if show_version_filter else more_columns[1]
            relation_column = more_columns[3] if show_version_filter else more_columns[2]

            with genre_column:
                selected_genre_main = tag_multiselect(
                    t(lang, "genre_main"),
                    get_unique_tags(filtered, "genre_main"),
                    lang,
                    key="finder_panel_genre_main",
                )
            filtered = filter_by_tag_choices(filtered, "genre_main", selected_genre_main)

            with player_column:
                selected_player_types = tag_multiselect(
                    t(lang, "player_type"),
                    get_unique_tags(filtered, "player_type"),
                    lang,
                    key="finder_panel_player_type",
                )
            filtered = filter_by_tag_choices(filtered, "player_type", selected_player_types)

            with relation_column:
                selected_relations = tag_multiselect(
                    t(lang, "nintendo_relation"),
                    get_unique_tags(filtered, "nintendo_relation"),
                    lang,
                    key="finder_panel_nintendo_relation",
                )
            filtered = filter_by_tag_choices(filtered, "nintendo_relation", selected_relations)

            online_multiplayer = st.selectbox(
                t(lang, "online_multiplayer"),
                ["Any", "Yes", "No"],
                format_func=lambda value: localize_value(lang, value),
                key="finder_panel_online_multiplayer",
            )
            filtered = filter_with_mask(filtered, "online_multiplayer", lambda value: match_yes_no(value, online_multiplayer))

    return ensure_columns(filtered)


def score_recommendations(
    games: pd.DataFrame,
    mood: str = "Any",
    session_length: str = "Any",
    beginner_friendly: str = "Any",
    local_multiplayer: str = "Any",
    online_multiplayer: str = "Any",
    difficulty: str = "Any",
    player_type: str = "Any",
    platform_group: str = "Any",
    nintendo_relation: str = "Any",
    genre_main: str = "Any",
    lang: str = "en",
) -> pd.DataFrame:
    scored = games.copy()
    scores: list[int] = []
    reasons: list[str] = []

    for _, game in scored.iterrows():
        score = 0
        reason_parts: list[str] = []

        if mood != "Any" and contains_choice(game.get("mood"), mood):
            score += 3
            reason_parts.append(f"{t(lang, 'mood')} +3: {localize_value(lang, mood)}")
        if difficulty != "Any" and contains_choice(game.get("difficulty"), difficulty):
            score += 2
            reason_parts.append(f"{t(lang, 'difficulty')} +2: {localize_value(lang, difficulty)}")
        if session_length != "Any" and contains_choice(game.get("session_length"), session_length):
            score += 2
            reason_parts.append(f"{t(lang, 'session_length')} +2: {localize_value(lang, session_length)}")
        if beginner_friendly != "Any" and match_yes_no(game.get("beginner_friendly"), beginner_friendly):
            score += 3
            reason_parts.append(f"{t(lang, 'beginner_friendly')} +3")
        if local_multiplayer != "Any" and match_yes_no(game.get("local_multiplayer"), local_multiplayer):
            score += 3
            reason_parts.append(f"{t(lang, 'local_multiplayer')} +3")
        if online_multiplayer != "Any" and match_yes_no(game.get("online_multiplayer"), online_multiplayer):
            score += 3
            reason_parts.append(f"{t(lang, 'online_multiplayer')} +3")
        if player_type != "Any" and contains_choice(game.get("player_type"), player_type):
            score += 3
            reason_parts.append(f"{t(lang, 'player_type')} +3: {localize_value(lang, player_type)}")
        if platform_group != "Any" and contains_choice(game.get("platform_group"), platform_group):
            score += 2
            reason_parts.append(f"{t(lang, 'platform_group')} +2: {localize_value(lang, platform_group)}")
        if nintendo_relation != "Any" and contains_choice(game.get("nintendo_relation"), nintendo_relation):
            score += 2
            reason_parts.append(f"{t(lang, 'nintendo_relation')} +2: {localize_value(lang, nintendo_relation)}")
        if genre_main != "Any" and contains_choice(game.get("genre_main"), genre_main):
            score += 2
            reason_parts.append(f"{t(lang, 'genre_main')} +2: {localize_value(lang, genre_main)}")

        meta_score = game.get("meta_score")
        user_score = game.get("user_score")
        if not pd.isna(meta_score) and float(meta_score) >= 80:
            score += 1
            reason_parts.append(f"{t(lang, 'metacritic')} >= 80 +1")
        if not pd.isna(user_score) and float(user_score) >= 8:
            score += 1
            reason_parts.append(f"{t(lang, 'user')} >= 8 +1")

        scores.append(score)
        reasons.append("; ".join(reason_parts) if reason_parts else t(lang, "manual_advice_missing"))

    scored["recommendation_score"] = scores
    scored["recommendation_reason"] = reasons
    return scored.sort_values(["recommendation_score", "meta_score", "user_score"], ascending=[False, False, False])


def render_game_finder(games: pd.DataFrame, lang: str) -> None:
    render_finder_main_header(games, lang)
    filtered = ensure_columns(apply_compass_filters(games, lang))

    if filtered.empty:
        st.info(t(lang, "no_matches"))
        return

    sort_options = ["Best reviewed", "Newest", "Title A-Z"] if lang == "en" else ["Best reviewed", "Newest"]
    sort_mode = st.radio(
        t(lang, "sort_results"),
        sort_options,
        horizontal=True,
        format_func=lambda value: localize_value(lang, value),
    )
    if sort_mode == "Newest":
        filtered = filtered.assign(sort_date=pd.to_datetime(filtered["date"], errors="coerce")).sort_values(
            ["sort_date", "title"],
            ascending=[False, True],
            na_position="last",
        )
    elif sort_mode == "Title A-Z":
        filtered = filtered.sort_values("title")
    else:
        filtered = filtered.assign(
            has_manual_tag=filtered["buying_advice"].map(lambda value: not is_blank(value)),
            has_media=filtered["image_url"].map(lambda value: not is_blank(value)),
        ).sort_values(["has_manual_tag", "has_media", "meta_score", "user_score", "title"], ascending=[False, False, False, False, True], na_position="last")
    render_card_grid(filtered, lang=lang, max_cards=len(filtered))


def render_tonights_pick(games: pd.DataFrame, lang: str) -> None:
    render_section_intro(t(lang, "tab_tonight"), t(lang, "tonight_desc"), t(lang, "quick_tonight"))

    columns = st.columns(4)
    with columns[0]:
        players = st.selectbox(t(lang, "players"), ["1 player", "2 players", "3-4 players", "Family group"], format_func=lambda value: localize_value(lang, value))
    with columns[1]:
        mood = st.selectbox(t(lang, "mood"), ["Any", "Fun", "Healing", "Exciting", "Immersive", "Chaotic", "Active", "Cute", "Creative", "Tense", "Story"], format_func=lambda value: localize_value(lang, value))
    with columns[2]:
        session_length = st.selectbox(t(lang, "session_length"), ["Any", "Short", "Medium", "Long"], format_func=lambda value: localize_value(lang, value))
    with columns[3]:
        beginner_friendly = st.selectbox(t(lang, "any_new"), ["Any", "Yes", "No"], format_func=lambda value: localize_value(lang, value))

    filter_columns = st.columns(4)
    with filter_columns[0]:
        platform_group = st.selectbox(
            t(lang, "platform_group"),
            ["Any", *get_unique_tags(games, "platform_group")],
            format_func=lambda value: localize_value(lang, value),
        )
    with filter_columns[1]:
        nintendo_relation = st.selectbox(
            t(lang, "nintendo_relation"),
            ["Any", *get_unique_tags(games, "nintendo_relation")],
            format_func=lambda value: localize_value(lang, value),
        )
    with filter_columns[2]:
        genre_main = st.selectbox(
            t(lang, "genre_main"),
            ["Any", *get_unique_tags(games, "genre_main")],
            format_func=lambda value: localize_value(lang, value),
        )
    with filter_columns[3]:
        online_multiplayer = st.selectbox(
            t(lang, "online_multiplayer"),
            ["Any", "Yes", "No"],
            format_func=lambda value: localize_value(lang, value),
        )

    local_multiplayer = "Yes" if players in {"2 players", "3-4 players", "Family group"} else "Any"
    recommended = score_recommendations(
        games,
        mood=mood,
        session_length=session_length,
        beginner_friendly=beginner_friendly,
        local_multiplayer=local_multiplayer,
        online_multiplayer=online_multiplayer,
        platform_group=platform_group,
        nintendo_relation=nintendo_relation,
        genre_main=genre_main,
        lang=lang,
    )

    st.markdown(f"#### {t(lang, 'tonight_recs')}")
    render_card_grid(recommended, lang=lang, max_cards=len(recommended), with_score=True)


def render_beginner_roadmap(games: pd.DataFrame, lang: str) -> None:
    render_section_intro(t(lang, "tab_roadmap"), t(lang, "roadmap_desc"), t(lang, "quick_new"))

    preferred_style = st.selectbox(
        t(lang, "preferred_style"),
        ["healing", "adventure", "party", "action", "cute", "immersive", "story", "puzzle", "active"],
        format_func=lambda value: localize_value(lang, value),
    )

    moods = STYLE_TO_MOODS[preferred_style]
    player_types = STYLE_TO_PLAYER_TYPES[preferred_style]
    candidates = score_recommendations(
        games,
        mood=moods[0],
        beginner_friendly="Yes" if preferred_style in {"healing", "party", "cute"} else "Any",
        lang=lang,
    )
    candidates = candidates[
        candidates["mood"].map(lambda value: contains_any(value, moods))
        | candidates["player_type"].map(lambda value: contains_any(value, player_types))
    ]
    candidates = candidates.head(5).reset_index(drop=True)

    if candidates.empty:
        st.info(t(lang, "no_roadmap"))
        return

    for index, (_, game) in enumerate(candidates.iterrows(), start=1):
        step_label = f"{t(lang, 'step')} {index}" if lang != "zh" else f"{t(lang, 'step')}{index} 步"
        st.markdown(f"### {step_label}")
        render_card(game, lang=lang)


def classify_player_type(answers: dict[str, str]) -> str:
    scores = {
        "Relaxed Player": 0,
        "Party Player": 0,
        "Explorer": 0,
        "Core Player": 0,
        "Family Player": 0,
        "Budget Player": 0,
    }

    play_with = answers["play_with"]
    if play_with == "Alone":
        scores["Explorer"] += 2
        scores["Relaxed Player"] += 1
    elif play_with == "Friends":
        scores["Party Player"] += 3
    elif play_with == "Family":
        scores["Family Player"] += 3
    else:
        scores["Relaxed Player"] += 2
        scores["Party Player"] += 1

    pace = answers["pace"]
    if pace == "Slow and cozy":
        scores["Relaxed Player"] += 3
    elif pace == "Quick round":
        scores["Party Player"] += 2
        scores["Budget Player"] += 1
    elif pace == "Long immersion":
        scores["Explorer"] += 3
    else:
        scores["Core Player"] += 3

    difficulty = answers["difficulty"]
    if difficulty == "Easy":
        scores["Family Player"] += 1
        scores["Relaxed Player"] += 2
    elif difficulty == "Medium":
        scores["Explorer"] += 2
    else:
        scores["Core Player"] += 3

    priority = answers["priority"]
    if priority == "Cute style":
        scores["Relaxed Player"] += 2
        scores["Family Player"] += 1
    elif priority == "Story and world":
        scores["Explorer"] += 3
    elif priority == "Action feel":
        scores["Core Player"] += 3
    elif priority == "Funny interaction":
        scores["Party Player"] += 3
    else:
        scores["Explorer"] += 2

    budget = answers["budget"]
    if budget == "Low":
        scores["Budget Player"] += 4
    elif budget == "Medium":
        scores["Budget Player"] += 1
        scores["Relaxed Player"] += 1
    else:
        scores["Core Player"] += 1
        scores["Explorer"] += 1

    return max(scores, key=scores.get)


def accepted_budget_tiers(budget: str) -> list[str]:
    if budget == "Low":
        return ["Low"]
    if budget == "Medium":
        return ["Low", "Medium"]
    return ["Low", "Medium", "High"]


def accepted_difficulties(difficulty: str) -> list[str]:
    if difficulty == "Easy":
        return ["Easy"]
    if difficulty == "Medium":
        return ["Easy", "Medium"]
    return ["Easy", "Medium", "Hard"]


def play_situations_for_answer(play_with: str) -> list[str]:
    if play_with == "Alone":
        return ["Solo"]
    if play_with == "Friends":
        return ["Friends", "Party", "Online"]
    if play_with == "Family":
        return ["Family", "Friends"]
    return ["Couple", "Friends", "Solo"]


def session_for_pace(pace: str) -> str:
    if pace == "Quick round":
        return "Short"
    if pace in {"Slow and cozy", "Long immersion"}:
        return "Long"
    return "Any"


def mood_for_priority(priority: str, pace: str) -> str:
    if priority == "Cute style":
        return "Cute"
    if priority == "Story and world":
        return "Story"
    if priority == "Action feel":
        return "Exciting"
    if priority == "Funny interaction":
        return "Fun"
    if priority == "Free exploration":
        return "Immersive"
    if pace == "Slow and cozy":
        return "Healing"
    if pace == "Tense challenge":
        return "Tense"
    return "Any"


def genre_for_priority(priority: str) -> str:
    if priority == "Action feel":
        return "Action"
    return "Any"


def filter_by_allowed_tags(dataframe: pd.DataFrame, column: str, allowed_values: list[str]) -> pd.DataFrame:
    return filter_by_tag_choices(dataframe, column, allowed_values)


def build_quiz_recommendations(games: pd.DataFrame, answers: dict[str, str], player_type: str, lang: str) -> pd.DataFrame:
    budget_tiers = accepted_budget_tiers(answers["budget"])
    difficulties = accepted_difficulties(answers["difficulty"])
    play_situations = play_situations_for_answer(answers["play_with"])
    session_length = session_for_pace(answers["pace"])
    mood = mood_for_priority(answers["priority"], answers["pace"])
    genre_main = genre_for_priority(answers["priority"])
    local_multiplayer = "Yes" if answers["play_with"] in {"Friends", "Family", "Partner or roommate"} else "Any"

    filtered = games.copy()
    filtered = filter_by_allowed_tags(filtered, "budget_tier", budget_tiers)
    filtered = filter_by_allowed_tags(filtered, "difficulty", difficulties)
    filtered = filter_by_allowed_tags(filtered, "play_situation", play_situations)
    if local_multiplayer != "Any":
        filtered = filter_with_mask(filtered, "local_multiplayer", lambda value: match_yes_no(value, local_multiplayer))

    scored = score_recommendations(
        filtered,
        mood=mood,
        session_length=session_length,
        difficulty=answers["difficulty"],
        player_type=player_type,
        genre_main=genre_main,
        local_multiplayer=local_multiplayer,
        lang=lang,
    )

    budget_text = ", ".join(localize_value(lang, tier) for tier in budget_tiers)
    difficulty_text = ", ".join(localize_value(lang, difficulty) for difficulty in difficulties)
    situation_text = ", ".join(localize_value(lang, situation) for situation in play_situations)
    prefix = (
        f"{t(lang, 'budget_tier')}: {budget_text}; "
        f"{t(lang, 'difficulty')}: {difficulty_text}; "
        f"{t(lang, 'play_situation')}: {situation_text}"
    )
    if not scored.empty:
        scored["recommendation_reason"] = scored["recommendation_reason"].map(lambda reason: f"{prefix}; {reason}")
    return scored


def render_player_type_test(games: pd.DataFrame, lang: str) -> None:
    render_section_intro(t(lang, "tab_quiz"), t(lang, "quiz_desc"), t(lang, "player_type"))

    play_with_options = ["Alone", "Friends", "Family", "Partner or roommate"]
    pace_options = ["Slow and cozy", "Quick round", "Long immersion", "Tense challenge"]
    difficulty_options = ["Easy", "Medium", "Hard"]
    priority_options = ["Cute style", "Story and world", "Action feel", "Funny interaction", "Free exploration"]
    budget_options = ["Low", "Medium", "High"]
    stored_answers = st.session_state.get("player_type_test_answers", {})

    with st.form("player_type_test_form"):
        columns = st.columns(2)
        with columns[0]:
            play_with = st.radio(
                t(lang, "play_with"),
                play_with_options,
                index=play_with_options.index(stored_answers.get("play_with", "Alone")),
                format_func=lambda value: localize_value(lang, value),
            )
            pace = st.radio(
                t(lang, "pace"),
                pace_options,
                index=pace_options.index(stored_answers.get("pace", "Slow and cozy")),
                format_func=lambda value: localize_value(lang, value),
            )
            difficulty = st.radio(
                t(lang, "difficulty_comfort"),
                difficulty_options,
                index=difficulty_options.index(stored_answers.get("difficulty", "Easy")),
                format_func=lambda value: localize_value(lang, value),
            )
        with columns[1]:
            priority = st.radio(
                t(lang, "priority"),
                priority_options,
                index=priority_options.index(stored_answers.get("priority", "Cute style")),
                format_func=lambda value: localize_value(lang, value),
            )
            budget = st.radio(
                t(lang, "budget_comfort"),
                budget_options,
                index=budget_options.index(stored_answers.get("budget", "Medium")),
                format_func=lambda value: localize_value(lang, value),
            )

        submitted = st.form_submit_button(t(lang, "quiz_submit"), type="primary")

    if submitted:
        st.session_state["player_type_test_answers"] = {
            "play_with": play_with,
            "pace": pace,
            "difficulty": difficulty,
            "priority": priority,
            "budget": budget,
        }

    answers = st.session_state.get("player_type_test_answers")
    if not answers:
        st.info(t(lang, "quiz_pending"))
        return

    player_type = classify_player_type(answers)

    st.success(f"{t(lang, 'your_type')}: {localize_value(lang, player_type)}")
    st.caption(t(lang, "quiz_rule_note"))
    recommended = build_quiz_recommendations(games, answers, player_type, lang)
    if recommended.empty:
        st.info(t(lang, "no_matches"))
        return

    recommendation_options = count_options(len(recommended), [5, 8, 10, 15])
    recommendation_count = st.selectbox(
        t(lang, "recommendation_count"),
        recommendation_options,
        index=2 if len(recommendation_options) > 2 else len(recommendation_options) - 1,
        format_func=lambda value: format_count_option(lang, value, len(recommended)),
        key="quiz_recommendation_count",
    )
    render_card_grid(recommended, lang=lang, max_cards=recommendation_count, with_score=True)


def render_budget_planner(games: pd.DataFrame, lang: str) -> None:
    render_section_intro(t(lang, "tab_budget"), t(lang, "budget_desc"), t(lang, "quick_budget"))

    columns = st.columns(3)
    with columns[0]:
        budget_krw = st.number_input(t(lang, "budget_krw"), min_value=20000, max_value=300000, value=100000, step=10000)
    with columns[1]:
        solo_need = st.selectbox(t(lang, "solo_game"), ["One solo game", "No solo game"], format_func=lambda value: localize_value(lang, value))
    with columns[2]:
        multiplayer_need = st.selectbox(t(lang, "multi_game"), ["One multiplayer game", "No multiplayer game"], format_func=lambda value: localize_value(lang, value))

    solo_games = filter_by_tag_choices(games, "play_situation", ["Solo", "Solo or Family", "Solo or Couple"])
    multiplayer_games = filter_with_mask(games, "local_multiplayer", lambda value: match_yes_no(value, "Yes"))

    if solo_need == "No solo game":
        solo_games = games.head(1)
    if multiplayer_need == "No multiplayer game":
        multiplayer_games = games.head(1)

    combinations = []
    for _, solo in solo_games.head(20).iterrows():
        for _, multi in multiplayer_games.head(20).iterrows():
            if solo["normalized_title"] == multi["normalized_title"]:
                continue
            estimated_total = BUDGET_ESTIMATES_KRW.get(clean_text(solo.get("budget_tier"), "Medium"), 50000)
            estimated_total += BUDGET_ESTIMATES_KRW.get(clean_text(multi.get("budget_tier"), "Medium"), 50000)
            combined_score = numeric_value(solo.get("meta_score")) + numeric_value(multi.get("meta_score"))
            if estimated_total <= budget_krw:
                combinations.append((estimated_total, combined_score, solo, multi))

    combinations = sorted(combinations, key=lambda item: (item[1], -item[0]), reverse=True)[:3]

    if not combinations:
        st.info(t(lang, "no_combo"))
        return

    for index, (estimated_total, _, solo, multi) in enumerate(combinations, start=1):
        st.markdown(f"#### {t(lang, 'combo')} {index} - {t(lang, 'estimated_budget')} {estimated_total:,.0f} KRW")
        columns = st.columns(2)
        with columns[0]:
            render_card(solo, lang=lang, reason=t(lang, "solo_pick"))
        with columns[1]:
            render_card(multi, lang=lang, reason=t(lang, "multi_pick"))

    st.info(t(lang, "buying_note"))


def render_data_table(games: pd.DataFrame, lang: str) -> None:
    render_section_intro(t(lang, "tab_table"), t(lang, "table_desc"), t(lang, "tab_table"))

    st.dataframe(games[DISPLAY_COLUMNS], width="stretch", hide_index=True)


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")
    add_page_style()

    selected_language = st.sidebar.selectbox(
        "Language / 언어 / 语言",
        list(LANGUAGE_OPTIONS.keys()),
        index=0,
    )
    lang = LANGUAGE_OPTIONS[selected_language]

    st.sidebar.title(APP_TITLE)
    st.sidebar.caption(t(lang, "sidebar_caption"))
    page_keys = ["tab_finder", "tab_roadmap", "tab_tonight", "tab_table"]
    if st.session_state.get("main_navigation") not in {None, *page_keys}:
        st.session_state["main_navigation"] = "tab_finder"
    selected_page = st.sidebar.radio(
        t(lang, "nav_label"),
        page_keys,
        format_func=lambda page_key: t(lang, page_key),
        key="main_navigation",
    )

    data_path = get_data_path()
    if data_path is None:
        st.warning(t(lang, "run_clean"))
        return

    games = load_games(str(data_path), get_data_cache_token(data_path))
    games = filter_games_for_language(games, lang)

    if games.empty:
        st.info(t(lang, "no_games"))
        return

    tagged_games = int(games["buying_advice"].map(lambda value: not is_blank(value)).sum())
    render_hero(games=games, total_games=len(games), tagged_games=tagged_games, lang=lang)

    if selected_page == "tab_finder":
        render_game_finder(games, lang)
    elif selected_page == "tab_roadmap":
        render_beginner_roadmap(games, lang)
    elif selected_page == "tab_tonight":
        render_tonights_pick(games, lang)
    elif selected_page == "tab_table":
        render_data_table(games, lang)


if __name__ == "__main__":
    main()
