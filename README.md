# 41g Racing Lab

41g Racing Lab は、競馬のレースを「流れ」として読み解く無料ローカルアプリです。

確実に勝つAIではなく、データ、血統、展開、枠順、ローテーション、輸送、オッズ妙味、独自メモを整理しながら、小穴・中穴を中心に、熱そうな大穴も見落とさないためのシミュレーションゲーム型予想ラボです。

関西弁の怪しい予想家キャラクター「浪速の穴馬おじさん」が、ユーザーと一緒に予想し、結果を記録しながら成長していきます。

## 画面

- Dashboard: 今日の作戦本部。回収率、的中率、予想レース数、おっちゃんのレベルと称号を表示します。
- Race Board: レース情報を入力して `data/races.csv` に保存します。
- Horse Scout: 出走馬データを手入力またはCSVで読み込み、`data/horses.csv` に保存します。
- Tactics Room: 総合スコア、穴馬指数、大穴警戒指数を計算し、本命・対抗・小穴・中穴・大穴警戒馬・危険人気馬を表示します。
- Result Chronicle: 結果、買い目、購入金額、払戻金を記録し、回収率とおっちゃんの成長を表示します。

## セットアップ

```bash
cd 41g-racing-lab
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

macOS / Linux の場合:

```bash
cd 41g-racing-lab
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## データ

初期データは `data/` に入っています。

- `races.csv`: サンプルレース1件
- `horses.csv`: 架空馬16頭
- `results.csv`: 初期は空

`horses.csv` には、将来の課金版詳細分析・noteレポート用の6軸予想データ列も用意しています。

- 血統: `father`, `maternal_grandsire`, `bloodline_score`
- 距離: `best_distance_range`, `distance_score`
- コース: `track_preference`, `course_score`
- 馬場/適性: `surface_preference`, `going_preference`
- 展開: `pace_score`
- 騎手/厩舎: `jockey_score`, `stable_score`
- 近走/調子: `recent_form`, `condition_score`
- 妙味/危険度: `value_score`, `danger_score`
- 課金版/本音コメント: `premium_comment`

各スコア列は 0〜100 の数値です。空欄や数値変換できない値は、中立値の 50 として扱います。

## スコア設計

Phase 1 では、検証しやすいシンプルなルールベースです。

- 総合スコア = 基礎能力 + 展開利 + 血統適性 + 枠順利 + 距離適性 + 馬場適性 + オッズ妙味 - リスク
- 穴馬指数 = 総合スコア + オッズ妙味 + 人気盲点 + 条件替わり加点 - 明確な不安点
- 大穴警戒指数 = 血統ロマン + 展開ハマり度 + 枠順恩恵 + 騎手一発度 + 人気薄補正

実装は `src/scoring.py` に分離しているため、後から指数や重みを差し替えやすくしています。

6軸予想データがある場合は、血統・距離・コース・展開・騎手/厩舎・調子の平均を補助スコアとして軽く反映します。既存の無料版表示では前面に出さず、詳細分析やロック表示の裏側データとして扱います。

## おっちゃん成長

`data/results.csv` の成績から、以下をもとにレベルと称号を計算します。

- 総回収率
- 的中率
- 大穴発掘数
- 見送り判断の回数
- 予想レース数

称号例:

- 見習い穴馬師
- 小穴ハンター
- 中穴の策士
- 大穴スカウト
- 展開読みのおっちゃん
- 浪速の馬券参謀
- 41g Race Director

## 注意書き

このアプリは競馬予想の学習・分析・娯楽を目的としたものです。

馬券購入やギャンブルを推奨するものではありません。

競馬に確実な予想はありません。

投票する場合は自己責任で、無理のない範囲で行ってください。

## Phase 2 案

- 予想レポートのMarkdown生成
- レースごとの展開シナリオ保存
- 買い目テンプレート作成
- 回収率を券種別・人気帯別に分解
- note販売前のレポートプレビュー
- スコア重みのUI調整
- 結果CSVから得意条件と苦手条件を分析
