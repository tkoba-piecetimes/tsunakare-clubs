# ラクロスマニア — 関東学生ラクロス（男子）情報メディア

大学ラクロスの情報メディア「ラクロスマニア」（運営: PieceTimes）。
JLA（日本ラクロス協会）が公開しているリーグ戦スプレッドシートから
試合日程・結果・星取表を自動取得し、静的サイトを生成する。

- 公開URL: https://tsunakereoff.github.io/tsunakare-clubs/ （独自ドメイン移行予定）
- 試合結果・順位表・チームページ（37チーム）・試合ページ（プレビュー/レポート・過去の対戦）
- 過去3年分（2023〜2025）の対戦データ、読みもの（戦術・練習・運営・分析記事）、動画インデックス

## 仕組み

```
JLA公式スプレッドシート（公開CSVエクスポート）
        │  pipeline/fetch_jla.py
        ▼
data/*.json   （matches / standings / teams / meta に正規化）
        │  pipeline/generate_site.py
        ▼
site/         （静的HTML。そのままホスティングに置ける）
```

- データ出典: 公益社団法人日本ラクロス協会
  https://www.lacrosse.gr.jp/event/2026-collegiate-leagues/
- スコア・日程は事実情報（著作権の対象外）。取得はGoogleスプレッドシートの
  公開CSVエクスポート機能を利用しており、スクレイピング的な負荷はかけていない
- 試合レポート文はテンプレート生成（LLM不使用・API費用ゼロ）。
  文章の質を上げたくなったら generate_site.py の match_report() をLLM呼び出しに差し替える

## 実行

```
python pipeline/fetch_jla.py      # データ取得・正規化
python pipeline/generate_site.py  # サイト生成
```

ローカル確認: `python -m http.server 8931 -d site`

## 自動更新（GitHubに載せる場合）

`.github/workflows/update.yml` に毎日1回の自動更新ワークフローを用意済み。
リポジトリをGitHubにpushして、Pages等のホスティングにつなげば全自動運用になる。

## 未実装（設計済みの次ステップ）

- ラクロスプラス等の副次ソースとの照合（2ソース一致で自動公開する安全弁）
- 部活ページの3つのプレースホルダの中身:
  - ツナカレメディア記事への内部リンク
  - Instagram公式埋め込み（公開投稿のURL指定）
  - 協賛企業枠（協賛メニュー連携）
- tsunakare.jp のサブディレクトリ（/clubs/）への設置
- sitemap.xml 生成とSearch Console登録
- 女子リーグ（同じスプレッドシートの gid=2122775238 で取得可能）
