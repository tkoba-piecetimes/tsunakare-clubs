# SERP分析メモ: 大学ラクロス 勝率ランキング（2021〜2025年度）

- 調査日: 2026-09-25
- 狙いKW: 「大学ラクロス 勝率ランキング」（KW在庫 K14「大学ラクロス部 通算勝率ランキング」／類型 K＝企画）
- 近接KW: 「大学ラクロス 強豪 ランキング」「ラクロス 強い大学」「大学ラクロス 順位 集計」
- 作成記事: `content/articles/lacrosse-win-rate-ranking-2021-2025.md`

## 上位に出てくる顔ぶれ（WebSearch 2026-09-25）

| # | URL | 内容 |
|---|---|---|
| 1 | https://spaia.jp/column/lacrosse/4083 | 「ラクロスが強い大学を5つご紹介」。定性的な紹介記事。数値の集計はなく、出典も限定的 |
| 2 | https://spaia.jp/column/lacrosse/4727 | 「関東の大学の強豪は？男子ラクロスチーム紹介」。関東のみ・チーム紹介型 |
| 3 | https://lacrosse-plus.net/news/japanlacrosse/nlcc/ | 全日本大学選手権の年代別優勝チーム一覧。全国大会の優勝校のみで、リーグ戦の勝敗集計はない |
| 4 | https://lacrosse-plus.net/news/kanto-4/ | 「関東で歴代優勝回数多い大学」。関東・優勝回数のみ |
| 5 | https://march-daigakujuken.com/blog/march-lacrosse/ | MARCH限定のラクロス部ランキング。塾のブログで対象が6校に限定 |
| 6 | https://www.lacrosse.gr.jp/event/collegiate-leagues/ | JLA公式。年度別の優勝校一覧と各地区の星取表リンク（一次情報） |
| 7 | https://manabi.benesse.ne.jp/daigaku/nyushi/student/school/school050/index.html | ベネッセ。未経験入部の紹介記事でランキングではない |
| 8 | https://lacrossemania.jp/ | 自サイトトップ |

## 共通点（検索意図の正解）

1. 読者は「結局どの大学が強いのか」を具体的な校名で知りたい。順位づけされた一覧を求めている
2. 男子・女子、関東・関西といった区分ごとの違いを知りたい（一括の全国ランキングでは物足りない）
3. 「強い」の根拠が示されていないと納得しない。全日本大学選手権の優勝歴だけでは足りず、直近数年の実力を知りたい

## 上位陣に欠けている要素（差別化点）

1. **複数年・全地区のリーグ戦を集計した勝率データが1件もない**。上位はすべて「全国大会の優勝歴」または「編集者の定性評価」で、リーグ戦の勝敗を横断集計した記事は存在しない
2. **関東・関西以外の地区（北海道・東北・東海・中四国・九州）がほぼ無視されている**。自サイトは14リーグ×5年分（2021〜2025）の星取表を保有しており、7地区すべてを同じ基準で扱える
3. **「ブロック1位＝リーグ優勝ではない」という関東方式の落とし穴に誰も触れていない**。2025年度関東男子は星取表のブロック1位が早稲田大学（A）・慶應義塾大学（B）だが、JLAが公表するリーグ優勝校はAブロック2位の明治学院大学。この事実を数値と公式情報の両方で示せるのは自サイトのみ

## この記事だけの要素

1. `data/history-standings.json`（JLAの星取表5年分＝70シーズン・1,055チーム×シーズンの行）から集計した、最上位カテゴリ20試合以上のチームの5年間勝率ランキング（男子29チーム／女子23チーム）
2. 2025年度関東男子の「ブロック1位と優勝校のずれ」を、自サイトの星取表データ＋JLA実施概要＋明治学院大学の公式ニュースで裏づけた解説

## 内部リンク方針

- 一次データページ: `../../standings/index.html`（全国順位表）、`../../archive/index.html`（2021〜2025シーズンアーカイブ）、`../../kanto-m/seasons/2025/index.html`、各チームページ（`../../tohoku-m/clubs/tohoku-univ/index.html` 等）
- 既存記事: `../lacrosse-university-strength-guide/index.html`（強豪校の見分け方＝定性面）、`../lacrosse-league-system-guide/index.html`（部・ブロック・入替戦の仕組み）、`../lacrosse-region-league-guide/index.html`（7地区14リーグの構成）

## 出典（本文で明記するもの）

- 公益社団法人日本ラクロス協会「全国地区公式戦：学生リーグ」 https://www.lacrosse.gr.jp/event/collegiate-leagues/
- 同 2021年度 https://www.lacrosse.gr.jp/event/collegiate-leagues/21766/
- 同 2022年度 https://www.lacrosse.gr.jp/event/collegiate-leagues/29361/
- 同 2023年度 https://www.lacrosse.gr.jp/event/2023-collegiate-leagues/
- 同 2024年度 https://www.lacrosse.gr.jp/event/2024-collegiate-leagues/
- 同 2025年度 https://www.lacrosse.gr.jp/event/2025-collegiate-leagues/
- 同「渡辺パイプ presents 第37回関東学生ラクロスリーグ戦 実施概要」 https://www.lacrosse.gr.jp/news/52112/
- 明治学院大学「ラクロス部男子 関東1部リーグ制覇！創部初の快挙！」（2025年11月4日） https://www.meijigakuin.ac.jp/news/05166.html
