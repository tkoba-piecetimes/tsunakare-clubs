# SERPメモ: 「ラクロス スティックの手入れ 方法」（keyword-inventory.md P3）

確認日: 2026-10-09（WebSearch／WebFetchで実施）
選定理由: P群のうち用具(P1/P2/P4)・怪我(P6/P7)・栄養(P10)・ポジション(P18-21)・用語(P11)・単位両立(P27)等は既存記事でカバー済み。P3は`content/articles/`に手入れ・メンテ専門記事がなく（stick-price-guideに中古時のポケット確認の一文のみ）、10-06のSERPメモでも「日本語上位がなく英語中心」と確認済み。
クエリ類型: 部員向け定番（P）／用具・維持

## 検索クエリ
- 「ラクロス スティック 手入れ 方法 ポケット メッシュ 調整」
- 「ラクロス スティック ポケット 張り替え ストリング 調整 初心者 日本 ショップ」
- 「ラクロス ヘッド 険編み STRING ROOM ポケット 編み直し 時期 目安 ストリング 劣化」
- 「ラクロス スティック 保管 濡れた 乾かす ポケット 型崩れ 部活」

## 上位表示サイト
- 日本語の手入れ専門記事は上位に見当たらず、結果は英語の用品店・ストリング専門店が中心（sportstop.com、stringerssociety.com、lacrosseunlimited.com、laxallstars.com）
- kewastrings.com（険編みのSTRING ROOM）: ポケット編み専門の日本語サイト。ヘッドのパーツ解説と「クロスメンテナンス」カテゴリあり（手入れの具体的な本文は今回未精読）
- 国内ECサイトは商品ページ中心で、手入れ・点検・編み直し判断をまとめた一般向け記事は確認できず

## 共通点・欠けている要素（3行）
1. 海外上位は「乾かす・保管・点検・編み直し」の4点を共通して扱うが、英語で、米国の気候・シーズン前提。
2. 日本の部活（雨・泥のグラウンド、部室ロッカー保管、リーグ戦中心）に合わせた日本語の整理がない。
3. 症状から原因箇所（ボトム／シューター／サイドウォール）を切り分ける点検手順と、公式戦前のルール確認を1本にした記事がない。

## 差別化方針（実装）
- 海外情報は出典と「米国用品店の解説」であることを明記し、日本環境への適用は断定しない
- 症状→点検→自分でできる範囲／お店に任せる範囲の順に整理、チーム運用の取り決め例を付与
- 既存記事（値段ガイド・ポジション別選び方・防具・ルール・用語集・投げ方・部費・遠征費）と順位表・チーム一覧へ内部リンク
- 日本国内の編み直し料金は一次情報が確認できず、数値を書かない

## 出典（本文記載）
- https://stringerssociety.com/blog/when-to-restring-lacrosse-stick/
- https://stringerssociety.com/blog/how-to-adjust-lacrosse-pockets/
- https://sportstop.com/blogs/about-lacrosse/lacrosse-gear-maintenance-101-tips-for-prolonging-the-life-of-your-equipment
- https://www.sportstop.com/blogs/about-lacrosse/how-to-tune-your-lacrosse-stick-for-peak-performance
- https://laxallstars.com/articles/how-to-treat-your-lacrosse-stick
- https://www.lacrosseunlimited.com/blogs/the-scoop/when-should-you-get-your-lacrosse-stick-restrung
- https://www.lacrosse.gr.jp/pdf/lacrosse/JLAOfficialRule_w_2024.pdf （女子ポケット深さ6.4cm＝既存記事で確認済みの記述を再掲）
- https://www.lacrosse.gr.jp/lacrosse/men/ （男子は2026年度版PDFが機械読取できず、数値は書かず参照先のみ）
- https://kewastrings.com/frame-parts/

## 未確認・注意
- 男子ルールのポケット規定は2026年度版PDFを読み取れず未確認（本文は数値を記載せず参照を促す）
- 海外情報はいずれも英語サイトのWebFetch要約ベース。日本の気候・素材（メッシュ種別）での適用は未検証
- 日本のストリング店の料金・対応は未確認のため不記載。米国店の価格も不採用
- laxallstarsは日なた干しも紹介するが、sportstopは直射日光回避。本文は日陰推奨と編集部見解として明記
- docs/primary-sources/ はこのリポに存在せず、取材一次情報は未使用
- 内部リンク先slug（lacrosse-stick-price-guide, lacrosse-glossary-complete-guide, lacrosse-club-travel-expense-guide, lacrosse-throw-basics, lacrosse-club-budget, lacrosse-rules-guide, lacrosse-protective-gear-guide, lacrosse-stick-selection-by-position）はcontent/articlesに存在確認済み
