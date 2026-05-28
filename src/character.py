from __future__ import annotations


TITLE_TABLE = [
    (1, "見習い穴馬師"),
    (3, "小穴ハンター"),
    (5, "中穴の策士"),
    (7, "大穴スカウト"),
    (9, "展開読みのおっちゃん"),
    (12, "浪速の馬券参謀"),
    (15, "41g Race Director"),
]


def get_level_title(stats: dict) -> tuple[int, str]:
    race_count = stats.get("race_count", 0)
    roi = stats.get("roi", 0)
    hit_rate = stats.get("hit_rate", 0)
    longshot_hits = stats.get("longshot_hits", 0)
    skip_count = stats.get("skip_count", 0)
    level = 1 + race_count // 3
    if roi >= 100:
        level += 2
    if roi >= 130:
        level += 2
    if hit_rate >= 35:
        level += 1
    if longshot_hits:
        level += min(3, longshot_hits)
    if skip_count >= 3:
        level += 1
    level = max(1, min(15, int(level)))
    title = "見習い穴馬師"
    for required, candidate in TITLE_TABLE:
        if level >= required:
            title = candidate
    return level, title


def get_dashboard_comment(stats: dict) -> str:
    roi = stats.get("roi", 0)
    race_count = stats.get("race_count", 0)
    if race_count == 0:
        return "ほな、今日もええ流れ探そか。無理に全部買う必要はないで。勝負どころを見極めるんや。"
    if roi >= 120:
        return "おお、ラボの歯車が噛み合ってきたな。けど調子乗りすぎたらすぐ数字は逃げるで。"
    if roi >= 90:
        return "悪くない流れや。小穴を拾う目線は残しつつ、買いすぎだけ気ぃつけよか。"
    return "負けた時こそデータや。感情で取り返しに行ったらアカン。次の一手を磨くんや。"


def get_value_horse_comment(row) -> str:
    odds = float(row.get("odds", 0) or 0)
    if odds >= 20:
        return "この人気でこの指数なら、ちょっと匂うで。買い方は薄めでも印は置きたいな。"
    return "小穴を拾うんが、このラボの仕事や。指数とオッズの釣り合い、よう見とこか。"


def get_dark_horse_comment(row) -> str:
    odds = float(row.get("odds", 0) or 0)
    if odds >= 50:
        return "大穴はロマンやけど、ロマンだけで飯は食えへんで。3列目の夢枠やな。"
    return "買いすぎ注意やけど、3着に突っ込んできても驚かんで。展開ひとつや。"


def get_risky_favorite_comment(row) -> str:
    return "人気してるけど、指数はそこまでやな。過信は禁物や。オッズが渋いなら見送りも作戦やで。"


def get_main_candidate_comment(row) -> str:
    return "軸にするならこの馬やな。派手さはないけど、崩れにくそうや。"


def get_second_candidate_comment(row) -> str:
    return "相手筆頭はこのへんや。勝ち切るかは別として、馬券内の筋は見えるで。"


def get_medium_value_comment(row) -> str:
    return "ええやん。こういう馬を拾えるかどうかが腕の見せどころや。"


def get_result_comment(stake: int, payout: int) -> str:
    if stake == 0:
        return "見送りも立派な予想や。勝負せん勇気、これが後で効いてくるんや。"
    if payout > stake:
        return "おお、これはええ回収や。こういう勝ち方を積み上げたいんや。"
    if payout > 0:
        return "当たりは拾えたけど回収はもう一歩やな。買い目の組み方、次の宿題や。"
    return "焦ったらアカン。負けた理由を残せば、次の武器になるで。"


def get_screen_comment(screen: str) -> str:
    comments = {
        "Race Board": "レースの器を作るとこや。距離、馬場、頭数。このへんを雑にしたら流れは読めへんで。",
        "Horse Scout": "出走馬のメモは未来の財産や。ちょっとした違和感も残しとき。",
        "Tactics Room": "ほな作戦会議や。人気と指数のズレ、そこに妙味が眠っとる。",
        "Result Chronicle": "勝っても負けても記録や。ラボは反省で強くなるんやで。",
    }
    return comments.get(screen, "ほな、今日も流れ読んでいこか。")
