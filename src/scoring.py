from __future__ import annotations

import pandas as pd


FIT_SCORE = {"◎": 12, "○": 8, "△": 2, "×": -6}
TRANSPORT_RISK = {"低": 0, "中": 4, "高": 9}
STYLE_FLOW = {"逃げ": 8, "先行": 9, "自在": 7, "差し": 6, "追込": 4}
BLOODLINE_SCORE = {
    "スピード": 8,
    "瞬発力": 9,
    "スタミナ": 7,
    "パワー": 7,
    "バランス": 8,
    "ロマン": 5,
}
SIX_AXIS_SCORE_COLUMNS = [
    "bloodline_score",
    "distance_score",
    "course_score",
    "pace_score",
    "jockey_score",
    "stable_score",
    "condition_score",
    "value_score",
    "danger_score",
]


def _num(value, default=0.0) -> float:
    converted = pd.to_numeric(value, errors="coerce")
    if pd.isna(converted):
        return default
    return float(converted)


def safe_numeric(value, default: float = 50.0) -> float:
    converted = pd.to_numeric(value, errors="coerce")
    if pd.isna(converted):
        return default
    return max(0.0, min(100.0, float(converted)))


def axis_grade(score: float) -> str:
    score = safe_numeric(score)
    if score >= 90:
        return "S"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    if score >= 50:
        return "D"
    if score >= 40:
        return "E"
    if score >= 30:
        return "F"
    return "G"


def compute_axis_scores(row: pd.Series) -> dict:
    jockey = safe_numeric(row.get("jockey_score"))
    stable = safe_numeric(row.get("stable_score"))
    return {
        "axis_bloodline": safe_numeric(row.get("bloodline_score")),
        "axis_distance": safe_numeric(row.get("distance_score")),
        "axis_course": safe_numeric(row.get("course_score")),
        "axis_pace": safe_numeric(row.get("pace_score")),
        "axis_jockey_stable": round((jockey + stable) / 2, 1),
        "axis_condition": safe_numeric(row.get("condition_score")),
        "axis_value": safe_numeric(row.get("value_score")),
        "axis_danger": safe_numeric(row.get("danger_score")),
    }


def compute_six_axis_average(row: pd.Series) -> float:
    axes = compute_axis_scores(row)
    core = [
        axes["axis_bloodline"],
        axes["axis_distance"],
        axes["axis_course"],
        axes["axis_pace"],
        axes["axis_jockey_stable"],
        axes["axis_condition"],
    ]
    return round(sum(core) / len(core), 1)


def frame_advantage(frame_number: int, field_size: int = 16) -> float:
    frame = int(_num(frame_number, 4))
    if field_size <= 12:
        table = {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}
    else:
        table = {1: 7, 2: 7, 3: 6, 4: 5, 5: 5, 6: 4, 7: 3, 8: 2}
    return table.get(frame, 3)


def odds_value(popularity: int, odds: float) -> float:
    popularity = int(_num(popularity, 10))
    odds = _num(odds, 20)
    if popularity <= 3 and odds < 8:
        return 1
    if 5 <= popularity <= 7:
        return 9
    if 8 <= popularity <= 12:
        return 13
    if popularity >= 13 or odds >= 30:
        return 16
    return 6


def base_ability(last_finish: int, last_margin: float) -> float:
    finish = int(_num(last_finish, 10))
    margin = _num(last_margin, 1.0)
    finish_score = max(0, 18 - finish * 1.6)
    margin_score = max(0, 12 - margin * 6)
    return finish_score + margin_score


def condition_change_bonus(row: pd.Series) -> float:
    rotation = str(row.get("rotation", ""))
    bonus = 0.0
    if "中3週" in rotation or "中4週" in rotation or "中5週" in rotation:
        bonus += 5
    if "休み明け" in rotation or "中8週" in rotation or "中10週" in rotation:
        bonus += 3
    if str(row.get("bloodline_type", "")) == "ロマン":
        bonus += 4
    return bonus


def risk_score(row: pd.Series) -> float:
    popularity = int(_num(row.get("popularity"), 10))
    last_finish = int(_num(row.get("last_finish"), 10))
    margin = _num(row.get("last_margin"), 1.0)
    risk = TRANSPORT_RISK.get(str(row.get("transport_load", "中")), 4)
    if last_finish >= 10:
        risk += 7
    if margin >= 1.2:
        risk += 5
    if popularity <= 3 and last_finish >= 8:
        risk += 8
    if "連闘" in str(row.get("rotation", "")):
        risk += 7
    return risk


def score_horse(row: pd.Series, field_size: int = 16) -> dict:
    popularity = int(_num(row.get("popularity"), 10))
    odds = _num(row.get("odds"), 20)
    bloodline = str(row.get("bloodline_type", ""))
    style = str(row.get("running_style", ""))

    foundation = base_ability(row.get("last_finish"), row.get("last_margin"))
    flow = STYLE_FLOW.get(style, 5)
    bloodline_fit = BLOODLINE_SCORE.get(bloodline, 5) + FIT_SCORE.get(str(row.get("surface_fit")), 4)
    distance_fit = FIT_SCORE.get(str(row.get("distance_fit")), 4)
    going_fit = FIT_SCORE.get(str(row.get("going_fit")), 4)
    frame_fit = frame_advantage(row.get("frame_number"), field_size)
    value = odds_value(popularity, odds)
    risk = risk_score(row)
    blind_spot = max(0, popularity - 4) * 1.1
    change_bonus = condition_change_bonus(row)
    clear_worry = max(0, risk - 7)
    axis_scores = compute_axis_scores(row)
    six_axis_average = compute_six_axis_average(row)
    six_axis_bonus = (six_axis_average - 50) * 0.12
    value_bonus = (axis_scores["axis_value"] - 50) * 0.08
    danger_penalty = (axis_scores["axis_danger"] - 50) * 0.08

    total = foundation + flow + bloodline_fit + frame_fit + distance_fit + going_fit + value - risk + six_axis_bonus
    value_index = total + value + blind_spot + change_bonus + value_bonus - clear_worry - max(0, danger_penalty)
    huge_upset = (
        (10 if bloodline == "ロマン" else BLOODLINE_SCORE.get(bloodline, 4))
        + flow
        + frame_fit
        + (6 if popularity >= 10 else 2)
        + (12 if odds >= 30 else 4)
        + value_bonus
        - risk * 0.4
        - max(0, danger_penalty)
    )
    adjusted_risk = risk + max(0, danger_penalty)

    return {
        "basis": round(foundation, 1),
        "pace_edge": round(flow, 1),
        "frame_edge": round(frame_fit, 1),
        "bloodline_fit_score": round(bloodline_fit, 1),
        "distance_fit_score": round(distance_fit, 1),
        "going_fit_score": round(going_fit, 1),
        "odds_value": round(value, 1),
        "risk": round(adjusted_risk, 1),
        "six_axis_average": six_axis_average,
        "six_axis_grade": axis_grade(six_axis_average),
        "axis_bloodline": round(axis_scores["axis_bloodline"], 1),
        "axis_distance": round(axis_scores["axis_distance"], 1),
        "axis_course": round(axis_scores["axis_course"], 1),
        "axis_pace": round(axis_scores["axis_pace"], 1),
        "axis_jockey_stable": round(axis_scores["axis_jockey_stable"], 1),
        "axis_condition": round(axis_scores["axis_condition"], 1),
        "axis_value": round(axis_scores["axis_value"], 1),
        "axis_danger": round(axis_scores["axis_danger"], 1),
        "total_score": round(total, 1),
        "value_horse_index": round(value_index, 1),
        "huge_upset_index": round(huge_upset, 1),
    }


def score_horses(horses: pd.DataFrame, race: pd.Series | None = None) -> pd.DataFrame:
    if horses.empty:
        return horses.copy()
    field_size = 16
    if race is not None and "field_size" in race:
        field_size = int(_num(race.get("field_size"), 16))
    scored = horses.copy()
    numeric_cols = ["horse_number", "frame_number", "popularity", "odds", "last_finish", "last_margin"]
    numeric_cols += [col for col in SIX_AXIS_SCORE_COLUMNS if col in scored.columns]
    for col in numeric_cols:
        scored[col] = pd.to_numeric(scored[col], errors="coerce")
    score_df = scored.apply(lambda row: pd.Series(score_horse(row, field_size)), axis=1)
    scored = pd.concat([scored, score_df], axis=1)
    return classify_horses(scored)


def classify_horses(scored: pd.DataFrame) -> pd.DataFrame:
    df = scored.copy()
    df["role"] = ""
    top_total = df["total_score"].rank(ascending=False, method="first")
    low_total = df["total_score"].rank(ascending=True, method="first")
    df.loc[(top_total <= 4) & (df["popularity"].between(1, 4)), "role"] += "本命候補 "
    df.loc[(top_total <= 5) & (df["role"] == ""), "role"] += "対抗候補 "
    value_rank = df["value_horse_index"].rank(ascending=False, method="first")
    upset_rank = df["huge_upset_index"].rank(ascending=False, method="first")
    df.loc[df["popularity"].between(5, 7) & (value_rank <= 8), "role"] += "小穴候補 "
    df.loc[df["popularity"].between(8, 12) & (value_rank <= 8), "role"] += "中穴候補 "
    df.loc[((df["popularity"] >= 13) | (df["odds"] >= 30)) & (upset_rank <= 8), "role"] += "大穴警戒馬 "
    df.loc[(df["popularity"].between(1, 3)) & ((low_total <= 5) | (df["risk"] >= 13)), "role"] += "危険人気馬 "
    df["role"] = df["role"].str.strip().replace("", "注視")
    return df.sort_values(["total_score", "value_horse_index"], ascending=False)


def pick_by_role(scored: pd.DataFrame, role: str) -> pd.DataFrame:
    if scored.empty or "role" not in scored:
        return scored.head(0)
    return scored[scored["role"].str.contains(role, na=False)].copy()
