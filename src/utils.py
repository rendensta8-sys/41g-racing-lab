from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"

RACE_COLUMNS = [
    "race_id",
    "date",
    "track",
    "race_name",
    "surface",
    "distance",
    "going",
    "grade",
    "field_size",
]

HORSE_COLUMNS = [
    "race_id",
    "horse_number",
    "frame_number",
    "horse_name",
    "jockey",
    "popularity",
    "odds",
    "running_style",
    "last_finish",
    "last_margin",
    "bloodline_type",
    "surface_fit",
    "distance_fit",
    "going_fit",
    "rotation",
    "transport_load",
    "memo",
]

RESULT_COLUMNS = [
    "race_id",
    "first",
    "second",
    "third",
    "bet_type",
    "bet_horses",
    "stake",
    "payout",
    "memo",
]


def data_path(filename: str) -> Path:
    return DATA_DIR / filename


def ensure_data_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    defaults = {
        "races.csv": RACE_COLUMNS,
        "horses.csv": HORSE_COLUMNS,
        "results.csv": RESULT_COLUMNS,
    }
    for filename, columns in defaults.items():
        path = data_path(filename)
        if not path.exists():
            pd.DataFrame(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def load_csv(filename: str, columns: list[str]) -> pd.DataFrame:
    ensure_data_files()
    path = data_path(filename)
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=columns)
    df = pd.read_csv(path)
    for column in columns:
        if column not in df.columns:
            df[column] = ""
    return df[columns]


def save_csv(df: pd.DataFrame, filename: str, columns: list[str]) -> None:
    ensure_data_files()
    output = df.copy()
    for column in columns:
        if column not in output.columns:
            output[column] = ""
    output[columns].to_csv(data_path(filename), index=False, encoding="utf-8-sig")


def append_row(filename: str, columns: list[str], row: dict) -> pd.DataFrame:
    df = load_csv(filename, columns)
    new_row = {column: row.get(column, "") for column in columns}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_csv(df, filename, columns)
    return df


def calculate_result_stats(results: pd.DataFrame) -> dict:
    if results.empty:
        return {
            "total_stake": 0,
            "total_payout": 0,
            "roi": 0.0,
            "hit_rate": 0.0,
            "race_count": 0,
            "profit": 0,
            "hit_count": 0,
            "longshot_hits": 0,
            "skip_count": 0,
        }

    numeric = results.copy()
    numeric["stake"] = pd.to_numeric(numeric["stake"], errors="coerce").fillna(0)
    numeric["payout"] = pd.to_numeric(numeric["payout"], errors="coerce").fillna(0)
    total_stake = int(numeric["stake"].sum())
    total_payout = int(numeric["payout"].sum())
    settled = numeric[numeric["stake"] > 0]
    hit_count = int((settled["payout"] > 0).sum())
    race_count = int(len(settled))
    roi = (total_payout / total_stake * 100) if total_stake else 0.0
    hit_rate = (hit_count / race_count * 100) if race_count else 0.0
    memo_text = " ".join(numeric["memo"].fillna("").astype(str).tolist())
    bet_text = " ".join(numeric["bet_type"].fillna("").astype(str).tolist())
    return {
        "total_stake": total_stake,
        "total_payout": total_payout,
        "roi": roi,
        "hit_rate": hit_rate,
        "race_count": race_count,
        "profit": total_payout - total_stake,
        "hit_count": hit_count,
        "longshot_hits": memo_text.count("大穴") + bet_text.count("大穴"),
        "skip_count": int((numeric["stake"] == 0).sum()),
    }


def disclaimer_text() -> str:
    return (
        "このアプリは競馬予想の学習・分析・娯楽を目的としたものです。"
        "馬券購入やギャンブルを推奨するものではありません。"
        "競馬に確実な予想はありません。投票する場合は自己責任で、無理のない範囲で行ってください。"
    )
