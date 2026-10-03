# 書き戻し指示書: faceoff-training

- candidateId: cmukntc4b01pgle04odwvr363 / stage: diagnose45 / GSC28日: 表示17・クリック3・CTR17.6%・平均5.1位
- 対象ファイル: `tsunakare-clubs/content/articles/faceoff-training.md`
- SERPメモ: `tsunakare-clubs/docs/serp-notes/faceoff-training-rewrite-20261003.md`
- 推定KW: ラクロス フェイスオフ 練習 / フェイスオフ コツ
- 方式: Sonnet単独で可（部員向け定番P相当）。「根拠と言い切りのルール」の自己点検を必須

## 判断
- 5位台・CTR良好で、タイトル・descriptionの変更は最小。需要は小さい（表示17）。本文強化（約1,000字→3,000字）と、出典の無い断定の除去が中心

## 禁止事項
- `date` は変えない。意図は変えない
- ルールの数値（ヘッド間の距離・笛までの静止など）は World Lacrosse または JLA の現行公表情報で確認できたもののみ。確認できなければ書かず、既存の「最新の公式ルールを確認してください」に留める
- 研究論文（早稲田大学の卒業論文PDF等）はWebFetchで本文を確認できた場合のみ引用（今回は403で未確認）
- 個人名は書かない

## frontmatter
- title: 維持
- description（案）: `ラクロスのフェイスオフの基本技術（クランプ）と流れ、ウィングとの連携、記録を前提にした練習メニューの組み方を解説。部内でフェイスオフ勝率を上げたいチーム向けです。`

## 本文の変更
1. 冒頭: 試算（15回×勝率+20pt=3回）は「仮の数字での計算例です」と明記。「これはエース1人の獲得に匹敵する改善です」は削除
2. 新H2 `## フェイスオフの流れと基本ルール`（冒頭の次）: センターでの開始、ウィング位置からの開始、笛で開始、の流れを一般的な説明として。数値は確認できたもののみ。用語集 [フェイスオフ](../../glossary/index.html#faceoff)・[FOGO](../../glossary/index.html#fogo)、[ラクロスのルール完全ガイド](../lacrosse-rules-guide/index.html) へ
3. `## 基本技術: クランプを最初に固める` 維持。「ここは才能ではなく反復量で決まる」→「反復で伸ばしやすい要素です」に弱める
4. 新H2 `## クランプ以外の主な技術`: 一般に知られる技術名（例: ラケ、プランジャー等）を英語圏の解説で確認できた範囲で1〜2文ずつ。「大学から始めた選手はまずクランプから」は現行の主張と同じ範囲で
5. `## フェイスオフは3人のプレー`: 「フェイスオファー単独で勝ち切れる割合は実際には高くありません」→「五分五分のボールになる場面も多く、ウィングの関与が勝敗を左右しやすい」程度に。「グラウンドボール練習の量がそのまま勝率に直結する」→「〜につながりやすい」。用語集 [グラウンドボール](../../glossary/index.html#ground-ball)、[ミッドフィルダーの役割と練習法](../lacrosse-midfielder-role-training/index.html)
6. `## 週次練習メニューの例`: 表に区切り行を追加。各メニューに目的を1文ずつ追記。[練習計画の立て方](../practice-planning/index.html) へ
7. 新H2 `## 用具の選び方`（短く）: フェイスオフ用ヘッドの存在のみ → [ポジション別スティックの選び方](../lacrosse-stick-selection-by-position/index.html)
8. `## スカウティングへの接続`: 「勝率が数%変わります」→ 数字を削除し「傾向が分かれば準備ができる」程度に
9. 新H2 `## よくある質問`（H3×3）
   - Q. フェイスオフは誰が担当する？ → 専門選手（FOGO）を置くチームもある
   - Q. 女子ラクロスにもフェイスオフはある？ → 女子はドローで再開（[男子ラクロスと女子ラクロスの違い](../mens-womens-lacrosse/index.html)）
   - Q. 一人でできる練習は？ → 反応ドリル（笛の音源を使う等）を一般論として

## 内部リンク（すべて実在確認済み）
lacrosse-rules-guide / lacrosse-midfielder-role-training / practice-planning / lacrosse-stick-selection-by-position / mens-womens-lacrosse / video-analysis（既存）/ glossary #faceoff #fogo #ground-ball

## 目安
- 本文3,000字前後（下限3,000字）。ビルド成功後に push
