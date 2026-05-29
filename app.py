from __future__ import annotations

import pandas as pd
import streamlit as st

from src.character import (
    get_dashboard_comment,
    get_dark_horse_comment,
    get_level_title,
    get_main_candidate_comment,
    get_medium_value_comment,
    get_result_comment,
    get_risky_favorite_comment,
    get_screen_comment,
    get_second_candidate_comment,
    get_value_horse_comment,
)
from src.scoring import axis_grade, compute_axis_scores, pick_by_role, score_horses
from src.utils import (
    HORSE_COLUMNS,
    RACE_COLUMNS,
    RESULT_COLUMNS,
    append_row,
    calculate_result_stats,
    disclaimer_text,
    ensure_data_files,
    load_csv,
    save_csv,
)


st.set_page_config(
    page_title="41g Racing Lab",
    page_icon="🏇",
    layout="wide",
    initial_sidebar_state="expanded",
)

DASHBOARD_COPY = {
    "ja": {
        "hero_title": "今日も狙って、燃やせ!!",
        "hero_subtitle": "勝てば祭り、外せばヤケ酒。おっちゃんの競馬研究所、開幕や!!",
        "top_hit_kicker": "おっちゃんの見立て",
        "top_hit_heading": "おっちゃんのトップヒット3頭",
        "top_hit_lead": "ほれ見ぃ!! 今日の狙いはこの3頭や!!",
        "main_cta": "おっちゃんの本音を見る!!",
        "sake_cta": "酒代おごったる!!",
        "sake_cta_note": "※投げ銭機能は準備中",
        "locked_heading": "🔒 詳細分析ロック",
        "locked_comment_label": "おっちゃんの本音コメント",
        "locked_comment_value": "ロック中",
        "paid_mode_label": "開発用：有料表示モード",
        "paid_mode_help": "決済なしで、課金後の詳細表示を確認するための仮モードです。",
        "paid_detail_heading": "🔥 おっちゃんの本音分析",
        "paid_detail_lead": "ここから先は、課金後に見える想定の詳細分析や。",
        "free_locked_message": "おっちゃんの本音コメント：ロック中",
        "premium_comment_fallback": "この馬の本音コメントはまだ仕込み中や。",
        "risk_detail_label": "危険度",
        "value_detail_label": "妙味",
        "danger_label": "危険度",
        "value_label": "妙味",
        "total_grade_label": "総合評価",
        "empty_race_message": "レース登録後に、おっちゃんのトップヒット3頭が表示されます。",
        "empty_horse_message": "出走馬データを入れると、◎本命 / ○対抗 / ▲穴馬がここに出ます。",
        "not_enough_horse_message": "トップヒット3頭は、出走馬が3頭以上になると表示されます。",
        "axis_labels": {
            "bloodline": "血統",
            "distance": "距離",
            "course": "コース",
            "pace": "展開",
            "jockey": "騎手",
            "condition": "調子",
        },
    },
    "en": {
        "hero_title": "Pick Hard. Burn Bright!!",
        "hero_subtitle": "Win, and it’s a festival. Lose, and it’s yaké-zake. Uncle’s Racing Lab is open.",
        "top_hit_kicker": "TODAY’S RACE HEAT",
        "top_hit_heading": "Uncle’s Top 3 Picks",
        "top_hit_lead": "Listen up!! These are the three horses to watch today.",
        "main_cta": "Unlock Uncle’s Real Take!!",
        "sake_cta": "Buy Uncle a Drink!!",
        "sake_cta_note": "Tips feature coming soon",
        "locked_heading": "🔒 Detailed Analysis Locked",
        "locked_comment_label": "Uncle’s Real Comment",
        "locked_comment_value": "Locked",
        "paid_mode_label": "Dev: Paid Detail Mode",
        "paid_mode_help": "Preview what users will see after unlocking paid details. No real payment is active.",
        "paid_detail_heading": "🔥 Uncle’s Real Analysis",
        "paid_detail_lead": "This is the kind of detail users will see after unlocking the paid view.",
        "free_locked_message": "Uncle’s real comment: Locked",
        "premium_comment_fallback": "Uncle’s real comment is still being prepared.",
        "risk_detail_label": "Risk",
        "value_detail_label": "Value",
        "danger_label": "Risk",
        "value_label": "Value",
        "total_grade_label": "Overall Grade",
        "empty_race_message": "No race data yet.",
        "empty_horse_message": "No horse data yet.",
        "not_enough_horse_message": "Not enough horses to show Top 3.",
        "axis_labels": {
            "bloodline": "Bloodline",
            "distance": "Distance",
            "course": "Course",
            "pace": "Pace",
            "jockey": "Jockey",
            "condition": "Form",
        },
    },
}

CHARACTER_REACTIONS = {
    "ja": {
        "hit": "よっしゃ、取ったで!! 今日は酒がうまい日や!!",
        "miss": "外したか……しゃあない、ヤケ酒して次や次!!",
        "close": "ぐぬぬ……惜しかったな。これは次に繋がる負け方や。",
        "big_win": "ドヤァ!! これは祭りや!! 今日はええ肉食えるで!!",
        "bad_loss": "これはあかん……今日は静かに反省会や。酒だけは濃いめで頼むわ。",
        "label": "キャラクターリアクション",
    },
    "en": {
        "hit": "Boom!! We got it. Drinks taste better tonight.",
        "miss": "We missed it... No crying. One drink, then on to the next race.",
        "close": "That was close... Painful, but useful. We’ll get it next time.",
        "big_win": "That’s a big one!! Festival mode. Dinner’s getting upgraded tonight.",
        "bad_loss": "That one hurt... Quiet review meeting. Make the drink strong.",
        "label": "Character Reaction",
    },
}


def inject_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --lab-green: #0d2a1d;
            --lab-panel: #13251d;
            --lab-gold: #d6ad4b;
            --lab-ink: #f2ead0;
            --lab-muted: #aab7a4;
            --lab-red: #c75c4a;
        }
        .stApp {
            background:
                radial-gradient(circle at 18% 8%, rgba(214, 173, 75, 0.10), transparent 28%),
                linear-gradient(135deg, #050806 0%, #0c1d15 45%, #10100b 100%);
            color: var(--lab-ink);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #07120d 0%, #0e2419 100%);
            border-right: 1px solid rgba(214, 173, 75, 0.25);
        }
        h1, h2, h3 {
            color: #f4d27c;
            letter-spacing: 0;
        }
        .lab-hero {
            border: 1px solid rgba(214, 173, 75, 0.35);
            background: linear-gradient(135deg, rgba(13, 42, 29, 0.92), rgba(24, 31, 18, 0.88));
            padding: 22px 24px;
            border-radius: 8px;
            margin-bottom: 18px;
            box-shadow: 0 18px 44px rgba(0, 0, 0, 0.22);
        }
        .lab-title {
            font-size: 46px;
            font-weight: 900;
            color: #f4d27c;
            margin: 0;
            line-height: 1.05;
        }
        .lab-subtitle {
            color: #c9d4bd;
            margin-top: 8px;
            font-size: 16px;
        }
        .oldman-card {
            border-left: 5px solid var(--lab-gold);
            background: rgba(9, 25, 17, 0.88);
            border-radius: 8px;
            padding: 15px 16px;
            margin: 10px 0 18px;
            color: #fff6d7;
        }
        .oldman-name {
            color: var(--lab-gold);
            font-weight: 800;
            margin-bottom: 4px;
        }
        .role-card {
            border: 1px solid rgba(214, 173, 75, 0.24);
            background: rgba(12, 31, 22, 0.84);
            border-radius: 8px;
            padding: 12px 14px;
            min-height: 110px;
        }
        .top-hit-wrap {
            border: 1px solid rgba(214, 173, 75, 0.34);
            background: linear-gradient(135deg, rgba(8, 22, 15, 0.94), rgba(20, 36, 25, 0.86));
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0 18px;
        }
        .top-hit-head {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: center;
            margin-bottom: 12px;
        }
        .top-hit-kicker {
            color: var(--lab-gold);
            font-size: 13px;
            font-weight: 800;
        }
        .top-hit-title {
            color: #fff4c4;
            font-size: 24px;
            font-weight: 900;
            line-height: 1.2;
        }
        .top-hit-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
        }
        .top-hit-card {
            border: 1px solid rgba(214, 173, 75, 0.22);
            background: rgba(5, 15, 10, 0.72);
            border-radius: 8px;
            padding: 14px;
            min-height: 174px;
        }
        .top-hit-mark {
            color: var(--lab-gold);
            font-size: 20px;
            font-weight: 900;
        }
        .top-hit-horse {
            color: #ffffff;
            font-size: 20px;
            font-weight: 900;
            margin-top: 6px;
        }
        .top-hit-grade {
            display: inline-block;
            margin: 10px 0 8px;
            padding: 4px 9px;
            border-radius: 999px;
            border: 1px solid rgba(214, 173, 75, 0.34);
            color: #f4d27c;
            font-weight: 900;
            background: rgba(214, 173, 75, 0.08);
        }
        .top-hit-button {
            display: inline-block;
            margin-top: 10px;
            padding: 7px 10px;
            border-radius: 6px;
            color: #10100b;
            background: #d6ad4b;
            font-weight: 800;
            font-size: 13px;
        }
        .locked-area {
            margin-top: 12px;
            border: 1px dashed rgba(214, 173, 75, 0.38);
            background: rgba(2, 8, 5, 0.56);
            color: #cfd7c5;
            border-radius: 8px;
            padding: 11px 12px;
            font-size: 13px;
        }
        .locked-title {
            color: #f4d27c;
            font-weight: 900;
            margin-bottom: 7px;
        }
        .locked-axis {
            display: flex;
            flex-wrap: wrap;
            gap: 7px;
            margin: 6px 0;
        }
        .locked-pill {
            border: 1px solid rgba(214, 173, 75, 0.22);
            background: rgba(214, 173, 75, 0.07);
            border-radius: 999px;
            padding: 4px 8px;
            color: #fff4c4;
            font-weight: 800;
        }
        @media (max-width: 900px) {
            .top-hit-grid {
                grid-template-columns: 1fr;
            }
            .top-hit-head {
                display: block;
            }
        }
        .role-title {
            color: #f4d27c;
            font-weight: 800;
            margin-bottom: 4px;
        }
        .small-muted {
            color: var(--lab-muted);
            font-size: 13px;
        }
        [data-testid="stMetric"] {
            background: rgba(9, 24, 17, 0.72);
            border: 1px solid rgba(214, 173, 75, 0.16);
            border-radius: 8px;
            padding: 12px;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid rgba(214, 173, 75, 0.18);
            border-radius: 8px;
        }
        .disclaimer {
            color: #c5c7b8;
            font-size: 12px;
            border-top: 1px solid rgba(214, 173, 75, 0.18);
            padding-top: 12px;
            margin-top: 28px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def oldman_card(comment: str, label: str = "浪速の穴馬おじさん") -> None:
    st.markdown(
        f"""
        <div class="oldman-card">
            <div class="oldman-name">{label}</div>
            <div>{comment}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="lab-hero">
            <div class="lab-title">{title}</div>
            <div class="lab-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_all() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict, int, str]:
    races = load_csv("races.csv", RACE_COLUMNS)
    horses = load_csv("horses.csv", HORSE_COLUMNS)
    results = load_csv("results.csv", RESULT_COLUMNS)
    stats = calculate_result_stats(results)
    level, title = get_level_title(stats)
    return races, horses, results, stats, level, title


def selected_race(races: pd.DataFrame) -> str | None:
    if races.empty:
        return None
    labels = [
        f"{row.race_id} | {row.date} {row.track} {row.race_name}"
        for row in races.itertuples(index=False)
    ]
    picked = st.selectbox("作戦対象レース", labels)
    return picked.split(" | ")[0]


def total_grade(total_score: float) -> str:
    if total_score >= 90:
        return "S"
    if total_score >= 82:
        return "A"
    if total_score >= 74:
        return "B"
    if total_score >= 66:
        return "C"
    if total_score >= 58:
        return "D"
    if total_score >= 50:
        return "E"
    if total_score >= 42:
        return "F"
    return "G"


def first_available(scored: pd.DataFrame, role: str, used_numbers: set[int]) -> pd.Series | None:
    candidates = pick_by_role(scored, role)
    candidates = candidates[~candidates["horse_number"].astype(int).isin(used_numbers)]
    if candidates.empty:
        return None
    return candidates.iloc[0]


def top_hit_section(races: pd.DataFrame, horses: pd.DataFrame, copy: dict, paid_mode: bool) -> None:
    if races.empty:
        st.info(copy["empty_race_message"])
        return

    display_races = races.copy()
    display_races["_display_date"] = pd.to_datetime(display_races["date"], errors="coerce")
    race = display_races.sort_values(["_display_date", "race_id"], na_position="first").iloc[-1]
    target_horses = horses[horses["race_id"] == race["race_id"]]
    if target_horses.empty:
        st.info(copy["empty_horse_message"])
        return

    scored = score_horses(target_horses, race)
    if len(scored) < 3:
        st.info(copy["not_enough_horse_message"])
        return

    used_numbers: set[int] = set()
    main = first_available(scored, "本命候補", used_numbers)
    if main is None:
        main = scored.iloc[0]
    used_numbers.add(int(main["horse_number"]))
    second = first_available(scored, "対抗候補", used_numbers)
    if second is None:
        second = scored[~scored["horse_number"].astype(int).isin(used_numbers)].iloc[0]
    used_numbers.add(int(second["horse_number"]))

    value_pool = pd.concat(
        [
            pick_by_role(scored, "小穴候補"),
            pick_by_role(scored, "中穴候補"),
            pick_by_role(scored, "大穴警戒馬"),
        ],
        ignore_index=False,
    )
    value_pool = value_pool[~value_pool["horse_number"].astype(int).isin(used_numbers)]
    if value_pool.empty:
        hole = scored[~scored["horse_number"].astype(int).isin(used_numbers)].iloc[0]
    else:
        hole = value_pool.sort_values("value_horse_index", ascending=False).iloc[0]

    cards = [
        ("◎ 本命", main, get_main_candidate_comment(main)),
        ("○ 対抗", second, get_second_candidate_comment(second)),
        ("▲ 穴馬", hole, get_value_horse_comment(hole)),
    ]
    card_html = ""
    for mark, row, comment in cards:
        card_html += f"""
        <div class="top-hit-card">
            <div class="top-hit-mark">{mark}</div>
            <div class="top-hit-horse">{int(row['horse_number'])}番 {row['horse_name']}</div>
            <div class="top-hit-grade">{copy['total_grade_label']} {total_grade(float(row['total_score']))}</div>
            <div class="small-muted">{comment}</div>
            <div class="top-hit-button">{copy['main_cta']}</div>
        </div>
        """
    main_axes = compute_axis_scores(main)
    axis_labels = copy["axis_labels"]
    free_axis_html = "".join(
        [
            f"<span class='locked-pill'>{axis_labels['bloodline']} {axis_grade(main_axes['axis_bloodline'])}</span>",
            f"<span class='locked-pill'>{axis_labels['distance']} {axis_grade(main_axes['axis_distance'])}</span>",
            f"<span class='locked-pill'>{axis_labels['course']} {axis_grade(main_axes['axis_course'])}</span>",
            f"<span class='locked-pill'>{axis_labels['pace']} {axis_grade(main_axes['axis_pace'])}</span>",
            f"<span class='locked-pill'>{axis_labels['jockey']} {axis_grade(main_axes['axis_jockey_stable'])}</span>",
            f"<span class='locked-pill'>{axis_labels['condition']} {axis_grade(main_axes['axis_condition'])}</span>",
            f"<span class='locked-pill'>{copy['danger_label']} ???</span>",
            f"<span class='locked-pill'>{copy['value_label']} ???</span>",
        ]
    )
    paid_axis_html = "".join(
        [
            f"<span class='locked-pill'>{axis_labels['bloodline']} {axis_grade(main_axes['axis_bloodline'])}</span>",
            f"<span class='locked-pill'>{axis_labels['distance']} {axis_grade(main_axes['axis_distance'])}</span>",
            f"<span class='locked-pill'>{axis_labels['course']} {axis_grade(main_axes['axis_course'])}</span>",
            f"<span class='locked-pill'>{axis_labels['pace']} {axis_grade(main_axes['axis_pace'])}</span>",
            f"<span class='locked-pill'>{axis_labels['jockey']} {axis_grade(main_axes['axis_jockey_stable'])}</span>",
            f"<span class='locked-pill'>{axis_labels['condition']} {axis_grade(main_axes['axis_condition'])}</span>",
            f"<span class='locked-pill'>{copy['risk_detail_label']} {axis_grade(main_axes['axis_danger'])}</span>",
            f"<span class='locked-pill'>{copy['value_detail_label']} {axis_grade(main_axes['axis_value'])}</span>",
        ]
    )
    premium_comment = str(main.get("premium_comment", "") or "").strip()
    if not premium_comment or premium_comment.lower() == "nan":
        premium_comment = copy["premium_comment_fallback"]
    detail_html = (
        f"""
        <div class="locked-title">{copy['paid_detail_heading']}</div>
        <div class="small-muted">{copy['paid_detail_lead']}</div>
        <div class="locked-axis">{paid_axis_html}</div>
        <div>{premium_comment}</div>
        """
        if paid_mode
        else f"""
        <div class="locked-title">{copy['locked_heading']}</div>
        <div class="locked-axis">{free_axis_html}</div>
        <div>{copy['free_locked_message']}</div>
        """
    )

    st.markdown(
        f"""
        <div class="top-hit-wrap">
            <div class="top-hit-head">
                <div>
                    <div class="top-hit-kicker">{copy['top_hit_kicker']}</div>
                    <div class="top-hit-title">{race['track']} {race['race_name']} {copy['top_hit_heading']}</div>
                </div>
                <div class="small-muted">{copy['top_hit_lead']}</div>
            </div>
            <div class="top-hit-grid">{card_html}</div>
            <div class="locked-area">
                {detail_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def dashboard(races: pd.DataFrame, horses: pd.DataFrame, results: pd.DataFrame, stats: dict, level: int, title: str, copy: dict, paid_mode: bool) -> None:
    hero(copy["hero_title"], copy["hero_subtitle"])
    oldman_card(get_dashboard_comment(stats))
    top_hit_section(races, horses, copy, paid_mode)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("おっちゃん Lv", f"Lv.{level}")
    c2.metric("称号", title)
    c3.metric("総回収率", f"{stats['roi']:.1f}%")
    c4.metric("的中率", f"{stats['hit_rate']:.1f}%")
    c5.metric("予想レース数", f"{stats['race_count']}")

    st.subheader("登録済みレース一覧")
    if races.empty:
        st.info("まだレースが登録されていません。Race Boardで作戦対象を追加してください。")
    else:
        st.dataframe(races, width="stretch", hide_index=True)

    st.subheader("戦績ログ")
    if results.empty:
        st.caption("まだ結果はありません。Result Chronicleで記録すると、おっちゃんが育ちます。")
    else:
        st.dataframe(results, width="stretch", hide_index=True)


def race_board(races: pd.DataFrame) -> None:
    hero("Race Board", "レースの器を整える作戦ボード")
    oldman_card(get_screen_comment("Race Board"))

    with st.form("race_form", clear_on_submit=True):
        cols = st.columns(3)
        race_id = cols[0].text_input("race_id", "20260510_tokyo_11")
        date = cols[1].date_input("開催日")
        track = cols[2].text_input("競馬場", "東京")
        race_name = cols[0].text_input("レース名", "東京11R")
        surface = cols[1].selectbox("芝/ダート", ["芝", "ダート"])
        distance = cols[2].number_input("距離", min_value=800, max_value=4000, value=1600, step=100)
        going = cols[0].selectbox("馬場状態", ["良", "稍重", "重", "不良"])
        grade = cols[1].selectbox("グレード", ["新馬", "未勝利", "1勝", "2勝", "3勝", "OP", "L", "G3", "G2", "G1"])
        field_size = cols[2].number_input("頭数", min_value=2, max_value=24, value=16, step=1)
        submitted = st.form_submit_button("レースを保存")

    if submitted:
        append_row(
            "races.csv",
            RACE_COLUMNS,
            {
                "race_id": race_id,
                "date": date.isoformat(),
                "track": track,
                "race_name": race_name,
                "surface": surface,
                "distance": distance,
                "going": going,
                "grade": grade,
                "field_size": field_size,
            },
        )
        st.success("レースを保存しました。")
        st.rerun()

    st.subheader("登録済みレース")
    st.dataframe(races, width="stretch", hide_index=True)


def horse_scout(races: pd.DataFrame, horses: pd.DataFrame) -> None:
    hero("Horse Scout", "出走馬の匂いをメモするスカウト部屋")
    oldman_card(get_screen_comment("Horse Scout"))

    race_id = selected_race(races)
    if not race_id:
        st.warning("先にRace Boardでレースを登録してください。")
        return

    st.subheader("CSV読み込み")
    uploaded = st.file_uploader("horses.csv形式のCSVを追加または置き換え", type=["csv"])
    mode = st.radio("読み込み方式", ["このレースに追加", "全馬データを置き換え"], horizontal=True)
    if uploaded is not None and st.button("CSVを反映"):
        incoming = pd.read_csv(uploaded)
        for column in HORSE_COLUMNS:
            if column not in incoming.columns:
                incoming[column] = ""
        incoming = incoming[HORSE_COLUMNS]
        if mode == "全馬データを置き換え":
            save_csv(incoming, "horses.csv", HORSE_COLUMNS)
        else:
            merged = pd.concat([horses, incoming], ignore_index=True)
            save_csv(merged, "horses.csv", HORSE_COLUMNS)
        st.success("CSVを反映しました。")
        st.rerun()

    with st.expander("サンプルCSV形式を見る", expanded=False):
        st.dataframe(horses.head(16), width="stretch", hide_index=True)

    st.subheader("手入力スカウト")
    with st.form("horse_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        horse_number = c1.number_input("馬番", min_value=1, max_value=24, value=1)
        frame_number = c2.number_input("枠番", min_value=1, max_value=8, value=1)
        horse_name = c3.text_input("馬名", "ナニワサンプル")
        jockey = c4.text_input("騎手", "浪速")
        popularity = c1.number_input("人気", min_value=1, max_value=24, value=8)
        odds = c2.number_input("単勝オッズ", min_value=1.0, max_value=999.9, value=18.0, step=0.1)
        running_style = c3.selectbox("脚質", ["逃げ", "先行", "自在", "差し", "追込"])
        last_finish = c4.number_input("前走順位", min_value=1, max_value=18, value=5)
        last_margin = c1.number_input("前走着差", min_value=0.0, max_value=9.9, value=0.5, step=0.1)
        bloodline_type = c2.selectbox("血統タイプ", ["スピード", "瞬発力", "スタミナ", "パワー", "バランス", "ロマン"])
        surface_fit = c3.selectbox("芝/ダート適性", ["◎", "○", "△", "×"])
        distance_fit = c4.selectbox("距離適性", ["◎", "○", "△", "×"])
        going_fit = c1.selectbox("馬場適性", ["◎", "○", "△", "×"])
        rotation = c2.selectbox("ローテーション", ["連闘", "中1週", "中2週", "中3週", "中4週", "中5週", "中6週", "中8週", "中10週", "休み明け"])
        transport_load = c3.selectbox("輸送負荷", ["低", "中", "高"])
        memo = c4.text_input("メモ", "妙味チェック")
        submitted = st.form_submit_button("出走馬を保存")

    if submitted:
        append_row(
            "horses.csv",
            HORSE_COLUMNS,
            {
                "race_id": race_id,
                "horse_number": horse_number,
                "frame_number": frame_number,
                "horse_name": horse_name,
                "jockey": jockey,
                "popularity": popularity,
                "odds": odds,
                "running_style": running_style,
                "last_finish": last_finish,
                "last_margin": last_margin,
                "bloodline_type": bloodline_type,
                "surface_fit": surface_fit,
                "distance_fit": distance_fit,
                "going_fit": going_fit,
                "rotation": rotation,
                "transport_load": transport_load,
                "memo": memo,
            },
        )
        st.success("出走馬を保存しました。")
        st.rerun()

    st.subheader("登録済み出走馬")
    st.dataframe(horses[horses["race_id"] == race_id], width="stretch", hide_index=True)


def role_summary(title: str, df: pd.DataFrame, comment_func, limit: int = 3) -> None:
    st.markdown(f"### {title}")
    if df.empty:
        st.caption("該当馬なし。ここは無理に作らんでええ。")
        return
    for _, row in df.head(limit).iterrows():
        st.markdown(
            f"""
            <div class="role-card">
                <div class="role-title">{int(row['horse_number'])}番 {row['horse_name']}</div>
                <div>人気 {int(row['popularity'])} / オッズ {row['odds']:.1f} / 総合 {row['total_score']:.1f} / 穴 {row['value_horse_index']:.1f} / 大穴 {row['huge_upset_index']:.1f}</div>
                <div class="small-muted">{comment_func(row)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def get_result_reaction_type(stake: int, payout: int) -> str:
    if stake <= 0:
        return "miss"
    if payout >= stake * 3:
        return "big_win"
    if payout > stake:
        return "hit"
    if payout > 0:
        return "close"
    if stake >= 5000:
        return "bad_loss"
    return "miss"


def reaction_card(reaction_type: str, lang: str) -> None:
    reactions = CHARACTER_REACTIONS.get(lang, CHARACTER_REACTIONS["ja"])
    message = reactions.get(reaction_type, reactions["miss"])
    oldman_card(message, label=reactions["label"])


def tactics_room(races: pd.DataFrame, horses: pd.DataFrame) -> None:
    hero("Tactics Room", "人気と指数のズレを探すメイン作戦室")
    oldman_card(get_screen_comment("Tactics Room"))

    race_id = selected_race(races)
    if not race_id:
        st.warning("先にRace Boardでレースを登録してください。")
        return
    target_horses = horses[horses["race_id"] == race_id]
    if target_horses.empty:
        st.warning("このレースの出走馬がありません。Horse Scoutで登録してください。")
        return

    race = races[races["race_id"] == race_id].iloc[0]
    scored = score_horses(target_horses, race)
    display_columns = [
        "horse_number",
        "horse_name",
        "jockey",
        "popularity",
        "odds",
        "running_style",
        "total_score",
        "value_horse_index",
        "huge_upset_index",
        "pace_edge",
        "frame_edge",
        "bloodline_fit_score",
        "odds_value",
        "risk",
        "role",
        "memo",
    ]

    st.subheader("予想ランキング")
    st.dataframe(
        scored[display_columns],
        width="stretch",
        hide_index=True,
        column_config={
            "horse_number": "馬番",
            "horse_name": "馬名",
            "total_score": st.column_config.NumberColumn("総合スコア", format="%.1f"),
            "value_horse_index": st.column_config.NumberColumn("穴馬指数", format="%.1f"),
            "huge_upset_index": st.column_config.NumberColumn("大穴警戒指数", format="%.1f"),
            "pace_edge": "展開利",
            "frame_edge": "枠順利",
            "bloodline_fit_score": "血統適性",
            "odds_value": "オッズ妙味",
            "risk": "リスク",
            "role": "分類",
        },
    )

    c1, c2 = st.columns(2)
    with c1:
        role_summary("◎ 本命候補", pick_by_role(scored, "本命候補"), get_main_candidate_comment, 2)
        role_summary("▲ 小穴候補", pick_by_role(scored, "小穴候補"), get_value_horse_comment, 3)
        role_summary("★ 大穴警戒馬", pick_by_role(scored, "大穴警戒馬"), get_dark_horse_comment, 3)
    with c2:
        role_summary("○ 対抗候補", pick_by_role(scored, "対抗候補"), get_second_candidate_comment, 3)
        role_summary("△ 中穴候補", pick_by_role(scored, "中穴候補"), get_medium_value_comment, 3)
        role_summary("危険人気馬", pick_by_role(scored, "危険人気馬"), get_risky_favorite_comment, 3)


def result_chronicle(results: pd.DataFrame, stats: dict, level: int, title: str, races: pd.DataFrame, lang: str) -> None:
    hero("Result Chronicle", "勝ち負けを次の武器に変える戦績記録室")
    oldman_card(get_screen_comment("Result Chronicle"))

    race_id = selected_race(races) if not races.empty else ""
    with st.form("result_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        race_id_input = c1.text_input("race_id", race_id or "")
        first = c2.text_input("1着", "")
        second = c3.text_input("2着", "")
        third = c1.text_input("3着", "")
        bet_type = c2.text_input("買い目", "ワイド")
        bet_horses = c3.text_input("対象馬", "2-6-11")
        stake = c1.number_input("購入金額", min_value=0, max_value=1000000, value=1000, step=100)
        payout = c2.number_input("払戻金", min_value=0, max_value=10000000, value=0, step=100)
        memo = c3.text_input("メモ", "反省ポイントを書く")
        submitted = st.form_submit_button("結果を記録")

    if submitted:
        append_row(
            "results.csv",
            RESULT_COLUMNS,
            {
                "race_id": race_id_input,
                "first": first,
                "second": second,
                "third": third,
                "bet_type": bet_type,
                "bet_horses": bet_horses,
                "stake": stake,
                "payout": payout,
                "memo": memo,
            },
        )
        st.session_state["last_result_reaction_type"] = get_result_reaction_type(stake, payout)
        st.success("結果を記録しました。")
        oldman_card(get_result_comment(stake, payout), label="おっちゃんの即時反省")
        st.rerun()

    if "last_result_reaction_type" in st.session_state:
        reaction_card(st.session_state["last_result_reaction_type"], lang)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("総購入額", f"{stats['total_stake']:,}円")
    c2.metric("総払戻額", f"{stats['total_payout']:,}円")
    c3.metric("回収率", f"{stats['roi']:.1f}%")
    c4.metric("的中率", f"{stats['hit_rate']:.1f}%")
    c5.metric("収支", f"{stats['profit']:,}円")

    st.subheader("おっちゃん成長ログ")
    growth = "プラス収支や。胸張ってええけど、次も同じ買い方でええかは別問題やで。" if stats["profit"] > 0 else "まだ鍛錬中や。負け筋を言語化できたら、もう半分は勝ちに近づいとる。"
    oldman_card(f"現在 Lv.{level} / {title}。{growth}", label="浪速の穴馬おじさん")

    st.subheader("結果一覧")
    if results.empty:
        st.caption("まだ記録はありません。")
    else:
        st.dataframe(results, width="stretch", hide_index=True)


def main() -> None:
    inject_style()
    ensure_data_files()
    races, horses, results, stats, level, title = load_all()

    st.sidebar.title("41g Racing Lab")
    st.sidebar.caption("怪しい作戦室、でも数字は見る。")
    st.sidebar.metric("浪速の穴馬おじさん", f"Lv.{level}", title)
    language_options = {"日本語": "ja", "English": "en"}
    current_lang = st.session_state.get("dashboard_lang", "ja")
    current_label = next((label for label, key in language_options.items() if key == current_lang), "日本語")
    selected_language = st.sidebar.radio(
        "Language",
        list(language_options.keys()),
        index=list(language_options.keys()).index(current_label),
    )
    st.session_state["dashboard_lang"] = language_options[selected_language]
    copy = DASHBOARD_COPY[st.session_state["dashboard_lang"]]
    if "paid_mode" not in st.session_state:
        st.session_state["paid_mode"] = False
    paid_mode = st.sidebar.checkbox(
        copy["paid_mode_label"],
        help=copy["paid_mode_help"],
        key="paid_mode",
    )
    page = st.sidebar.radio(
        "画面切り替え",
        ["Dashboard", "Race Board", "Horse Scout", "Tactics Room", "Result Chronicle"],
    )

    if page == "Dashboard":
        dashboard(races, horses, results, stats, level, title, copy, paid_mode)
    elif page == "Race Board":
        race_board(races)
    elif page == "Horse Scout":
        horse_scout(races, horses)
    elif page == "Tactics Room":
        tactics_room(races, horses)
    elif page == "Result Chronicle":
        result_chronicle(results, stats, level, title, races, st.session_state["dashboard_lang"])

    st.markdown(f"<div class='disclaimer'>{disclaimer_text()}</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
