# SERP分析メモ: 大学ラクロス 勝率ランキング（2021〜2025年度）

- 初回調査日: 2026-09-25（記事は未公開のまま残っていた）／再調査・制作日: 2026-11-03
- 狙いKW: 「大学ラクロス 勝率ランキング」（KW在庫 K14「大学ラクロス部 通算勝率ランキング」／類型 K＝企画・ハイブリッド方式）
- 近接KW: 「大学ラクロス 強豪 ランキング」「ラクロス 強い大学 地区別」
- 作成記事: `content/articles/lacrosse-win-rate-ranking-2021-2025.md`

## 上位に出てくる顔ぶれ（WebSearch 2026-09-25／2026-11-03）

| # | URL | 内容 |
|---|---|---|
| 1 | https://spaia.jp/column/lacrosse/4083 | 「ラクロスが強い大学を5つご紹介」。定性的な紹介記事。数値の集計なし |
| 2 | https://spaia.jp/column/lacrosse/4727 ・ /4730 | 関東男子・関西女子のチーム紹介型。年度が古い（2016年度時点の記述あり） |
| 3 | https://lacrosse-plus.net/news/japanlacrosse/nlcc/ | 全日本大学選手権の優勝チーム一覧。リーグ戦の勝敗集計はない |
| 4 | https://lacrosse-plus.net/news/kanto-4/ | 関東の歴代優勝回数。関東のみ |
| 5 | https://march-daigakujuken.com/blog/march-lacrosse/ | MARCH限定の塾ブログ |
| 6 | https://www.lacrosse.gr.jp/event/2025-collegiate-leagues/ | JLA公式。7地区×男女の星取表リンク（一次情報）。優勝校の一覧はページ上にない |
| 7 | 中央大学リポジトリ論文（関東2部の試合分析） | 学術的な単一チーム分析でランキングではない |

2026-11-03の再検索（「大学ラクロス 勝率 ランキング」）でも、リーグ戦の勝敗を複数年・全地区で集計したページは見つからなかった。

## 共通点（検索意図の正解）

1. 「結局どの大学が強いのか」を具体的な校名と順位で知りたい
2. 男女別・地区別に知りたい（全国一括では物足りない）
3. 「強い」の根拠（数字）がほしい。全国大会の優勝歴だけでなく直近数年の安定度を知りたい

## 上位陣に欠けている要素（差別化点）

1. 複数年・全地区のリーグ戦勝敗を同じ基準で集計した数値がない
2. 関東・関西以外（北海道・東北・東海・中四国・九州）がほぼ扱われていない
3. 「勝率が高い＝リーグ優勝」ではない（関東はブロック戦の後にFINAL等がある）点に触れていない

## この記事だけの要素

1. `data/history-standings.json`（JLA公開の星取表 2021〜2025年度・70シーズン分）から、各地区の最上位カテゴリ（1部、または部分けのない地区はリーグ戦全体）の勝敗だけを合算した14リーグ別の5年勝率表（最上位カテゴリ在籍3シーズン以上のチーム）
2. 2025年度関東男子: 星取表のAブロック1位は早稲田大学、優勝は関東Final（2025-11-03）で早稲田大学を破った明治学院大学（Aブロック2位）。自サイトデータ＋明治学院大学公式ニュースで裏づけ
3. 5年間リーグ戦無敗（星取表上）のチーム: 東北大学男子20勝0敗・東北大学女子19勝0敗・福岡大学女子27勝0敗

## 集計ルール（記事にも明記）

- 勝率＝勝利数÷試合数（引き分けは勝ちに数えない）。サイト記録室と同じ定義
- 星取表のブロック内総当たり戦のみ。FINAL・プレーオフ・全日本大学選手権・入替戦は含まない
- 2021年度東海女子は星取表が画像のみで数値化できていないため除外（東海女子は2022〜2025年度の4シーズン）
- 2021〜2022年度の中四国は中国・四国の地域ブロック制、2022年度九州女子は予選ブロック＋順位決定リーグ／戦の構成。いずれも全試合を算入
- 2021年度関東は1ブロック4チーム（3試合）の縮小開催
- 表記ゆれ（2023年度北海道の「北翔」「北海道科学」）は同一チームとして合算
- 地区ごとに対戦相手が違うため、地区をまたいだ勝率の比較はしない

## 内部リンク方針

- 一次データ: `../../standings/index.html`、`../../archive/index.html`、`../../records/index.html`、各リーグ記録室 `../../<code>/records/index.html`、`../../kanto-m/seasons/2025/index.html`、各チームページ
- 既存記事: `../lacrosse-university-strength-guide/index.html`、`../lacrosse-league-system-guide/index.html`、`../lacrosse-region-league-guide/index.html`、`../lacrosse-national-championship-winners-history/index.html`

## 出典（本文で明記するもの）

- 日本ラクロス協会「全国地区公式戦：学生リーグ」 https://www.lacrosse.gr.jp/event/collegiate-leagues/
- 同 2021年度 https://www.lacrosse.gr.jp/event/collegiate-leagues/21766/
- 同 2022年度 https://www.lacrosse.gr.jp/event/collegiate-leagues/29361/
- 同 2023年度 https://www.lacrosse.gr.jp/event/2023-collegiate-leagues/
- 同 2024年度 https://www.lacrosse.gr.jp/event/2024-collegiate-leagues/
- 同 2025年度 https://www.lacrosse.gr.jp/event/2025-collegiate-leagues/
- 明治学院大学「ラクロス部男子 関東1部リーグ制覇！創部初の快挙！」（2025年11月4日） https://www.meijigakuin.ac.jp/news/05166.html

## 一次情報バンク

- `docs/primary-sources/` はこのリポに存在しないため、取材由来の一次情報は使用していない（自サイト集計データとJLA公開資料が一次情報）
