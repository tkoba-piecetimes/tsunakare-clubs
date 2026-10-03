# 書き戻し指示書: clear-basics

- candidateId: cmukntc4j01pile04kp1ppd9s / stage: diagnose45 / GSC28日: 表示6・クリック0・平均5.8位
- 対象ファイル: `tsunakare-clubs/content/articles/clear-basics.md`
- SERPメモ: `tsunakare-clubs/docs/serp-notes/clear-basics-rewrite-20261003.md`
- 推定KW: ラクロス クリア 基本 / ラクロス クリアとは
- 方式: Sonnet単独で可。事実確認（時間制限・オフサイド）を必須

## 判断
- 需要は極小（28日表示6）。順位より先に、不正確・断定的な記述の修正が必要。そのうえで本文を3,000字まで強化

## 禁止事項
- `date` は変えない。意図は変えない
- クリアの時間制限の数字は World Lacrosse 男子ルールまたは JLA の現行公表情報で確認できた場合のみ書く。英語圏の一般的な解説では「自陣で保持してから20秒以内にセンターラインを越える」等とされるが（NCAA系）、日本の大会で適用される規定は未確認
- 個人名は書かない

## frontmatter
- title（案）: `ラクロスのクリアとは｜数的優位を作る3つの原則と練習法`（「ラクロス」をタイトルに入れる。意図は同じ）
- description（案）: `ラクロスのクリア（自陣からボールを運び出すプレー）の基本を解説。男子のオフサイド規定から生まれる数的優位の使い方、ゴーリーの第一パス、よくある失敗と練習メニューまでまとめます。`

## 本文の変更
1. 冒頭: 2段落目の太字の定義文を1段落目の先頭へ。「クリア成功率がそのまま得点機会の差になります」→「得点機会の差につながりやすい」に
2. 新H2 `## クリアのルール ― 時間制限とオフサイド`: 
   - 男子はオフサイド規定（自陣・敵陣に残る人数の決まり）があるため、ゴーリーを含めるとクリア側7人・ライド側6人の構図になる、と**男子の条件付き**で説明（用語集 [オフサイド](../../glossary/index.html#offside)）
   - 時間制限は一次情報で確認できた数字のみ。確認できなければ「時間制限がある」とだけ書き、[ラクロスのルール完全ガイド](../lacrosse-rules-guide/index.html) と公式ルールへ誘導
   - 女子はルールが異なる旨を1文＋[男子ラクロスと女子ラクロスの違い](../mens-womens-lacrosse/index.html)
3. `## 原則1`: 「構造的に**必ず**1人余っています」→「男子のオフサイド規定上、ゴーリーを含めると1人多い構図になります」
4. `## 原則2`: 「セーブ直後の3秒でほぼ決まります」→「セーブ直後の初動で決まりやすい」。「15秒×回数の制約を意識し」→ **削除**（確認できた規定があれば正しい数字に置き換え）。[ゴーリーの役割と練習法](../lacrosse-goalie-role-training/index.html) へ
5. `## 原則3`: 「クリア失敗の大半は次の3つに分類できます」→「よく見られる失敗として次の3つがあります」
6. 新H2 `## ライド側は何を狙うか`（短く）: 用語集 [ライド](../../glossary/index.html#ride)、[ディフェンスの役割と練習法](../lacrosse-defense-role-training/index.html)・[ミッドフィルダーの役割と練習法](../lacrosse-midfielder-role-training/index.html)
7. `## 練習への落とし込み`: 維持。「選手の意識が変わり、試合での判断も速くなります」→「〜しやすくなります」
8. 新H2 `## よくある質問`（H3×3）
   - Q. クリアとライドの違いは？
   - Q. 女子ラクロスにもクリアはある？（ルールの違いは確認できた範囲のみ）
   - Q. マンダウン後のクリアで気をつけることは？ → [マンダウンディフェンスの基本](../man-down-defense/index.html)
9. 関連: 用語集 [クリア](../../glossary/index.html#clear)

## 内部リンク（すべて実在確認済み）
lacrosse-rules-guide / mens-womens-lacrosse / lacrosse-goalie-role-training / lacrosse-defense-role-training / lacrosse-midfielder-role-training / man-down-defense / video-analysis（既存）/ glossary #clear #ride #offside

## 目安
- 本文3,000字前後。ビルド成功後に push
