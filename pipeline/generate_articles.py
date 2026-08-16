# -*- coding: utf-8 -*-
"""data/leagues/ の試合結果からデータ記事を自動生成し、content/articles/ に
Markdown（generate_site.pyのload_articles()が読める平文frontmatter形式）として書き出す
（Type A: テンプレート生成・LLM不使用・API費用ゼロ。soccermaniaの
pipeline/generate_articles.py を移植・ラクロスのデータ構造に適合）。

生成する記事タイプは2種類:

  1. 結果まとめ（review-<league>-<YYYYMMDD>）
     当該リーグの「試合日クラスタ」（開催日が近い試合をまとめた週末単位、
     WEEKEND_GAP_DAYS以内なら同一クラスタ）の結果をまとめる。対象は全14リーグ
     （7地域 × 男女）共通。ラクロスの試合データには節番号ではなく「カテゴリ」
     （例: 1部Aブロック）が付いており、1つのクラスタに複数カテゴリの試合が
     混在することがあるため、結果テーブルにはカテゴリ列を出し、順位表は
     クラスタに登場したカテゴリ（ブロック）分だけ掲載する（登場しないブロックの
     順位表は出さない＝無関係な情報を混ぜない）。
     クラスタの試合数がMIN_CLUSTER_MATCHES未満（薄い週末）はスキップする
     （品質ゲート）。まだ日程が残っているリーグでは直近1クラスタは今後の
     試合追加でまだ変わりうるため候補から除外する。
     開催日が未確定（date=null）の試合はクラスタ化の対象外（エラーにはしない）。

  2. チームシーズン記録（season-<league>-<team_slug>-<year>）
     完結済みシーズン（data/leagues/<league>/history/<year>.json）の中から、
     規定試合数（MIN_TEAM_GAMES）以上戦ったチームについて、そのチームの
     シーズン全成績（試合結果一覧・最終順位）をまとめる。進行中の現シーズン
     （2026年）は結果が今後変わるため対象外（historyの確定済み過去シーズンのみ）。
     2026-08時点で14リーグ中history/を持つのは kanto-m（関東男子）のみ
     （2023〜2025年の3年分）。他13リーグはfetch_history.py未実行のため対象外
     （このスクリプトの責務外。データが増えれば自動的に対象になる）。

1回の実行につき最大 MAX_ARTICLES_PER_RUN 件まで生成する。全リーグ横断で、
まず「結果まとめ」（鮮度の高い今シーズン情報）を代表日の古い順に優先し、
枠が余ればチームシーズン記録（過去シーズンの在庫）で埋める。
既存のslug（content/articles/<slug>.md が既に存在する）はスキップする（冪等）。

このスクリプトは pipeline/generate_site.py の直前（.github/workflows/update.yml内）に
実行する。generate_site.py 側の変更は不要（load_articles/build_articles は既存の
仕組みをそのまま使う）。
"""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "leagues"
CONTENT_DIR = ROOT / "content" / "articles"

MAX_ARTICLES_PER_RUN = 2

WEEKEND_GAP_DAYS = 2        # クラスタ区切りの日付ギャップ閾値（日）
MIN_CLUSTER_MATCHES = 3     # 結果まとめを生成する最低試合数（薄い週末はスキップ）
MIN_TEAM_GAMES = 4          # チームシーズン記録を生成する最低試合数（規定未満はスキップ）

WEEKDAYS_JP = ["月", "火", "水", "木", "金", "土", "日"]

CATEGORY_REVIEW = "結果まとめ"
CATEGORY_SEASON = "シーズン記録"


# ---------------------------------------------------------------- data loading

def load_league(code: str) -> dict:
    d = DATA_DIR / code
    hist = []
    hdir = d / "history"
    if hdir.exists():
        for f in sorted(hdir.glob("*.json")):
            hist.append(json.loads(f.read_text(encoding="utf-8")))
    return {
        "code": code,
        "matches": json.loads((d / "matches.json").read_text(encoding="utf-8")),
        "standings": json.loads((d / "standings.json").read_text(encoding="utf-8")),
        "teams": json.loads((d / "teams.json").read_text(encoding="utf-8")),
        "meta": json.loads((d / "meta.json").read_text(encoding="utf-8")),
        "history": hist,
    }


def existing_slugs() -> set[str]:
    if not CONTENT_DIR.exists():
        return set()
    return {f.stem for f in CONTENT_DIR.glob("*.md")}


# ---------------------------------------------------------------- text helpers

def date_jp(iso: str) -> str:
    d = date.fromisoformat(iso)
    wd = WEEKDAYS_JP[d.weekday()]
    return f"{d.month}月{d.day}日（{wd}）"


def date_range_label(dates: list[str]) -> str:
    uniq = sorted(set(dates))
    start = date.fromisoformat(uniq[0])
    end = date.fromisoformat(uniq[-1])
    if start == end:
        return f"{start.month}月{start.day}日"
    if start.month == end.month:
        return f"{start.month}月{start.day}日～{end.day}日"
    return f"{start.month}月{start.day}日～{end.month}月{end.day}日"


def team_link(name: str, slug: str, league_code: str, current_slugs: set[str]) -> str:
    # articles/<slug>/index.html から見た相対パス（サイトルートへ2階層上がる）。
    # 過去シーズンにしか登場しないチーム（現行teams.jsonにいない＝クラブページ未生成）は
    # リンク切れを避けるため太字表記に留める。
    if slug in current_slugs:
        return f"[{name}](../../{league_code}/clubs/{slug}/index.html)"
    return f"**{name}**"


def source_line(meta: dict) -> str:
    return f'- [{meta["source"]}]({meta["source_url"]})'


# ---------------------------------------------------------------- Type 1: 結果まとめ

def cluster_by_weekend(matches: list[dict]) -> tuple[list[list[dict]], int]:
    """開催日が確定している試合だけを日付順に並べ、近い日付同士を1つの試合日クラスタ
    （週末単位）にまとめる。date=null の試合は対象から除外する（件数のみ返す）。"""
    played = [m for m in matches if m["status"] == "played" and m.get("home_score") is not None]
    dated = sorted((m for m in played if m["date"]), key=lambda m: m["date"])
    undated_count = sum(1 for m in played if not m["date"])
    clusters: list[list[dict]] = []
    cur: list[dict] = []
    cur_last: str | None = None
    for m in dated:
        d = m["date"]
        if not cur:
            cur = [m]
            cur_last = d
            continue
        gap = (date.fromisoformat(d) - date.fromisoformat(cur_last)).days
        if gap <= WEEKEND_GAP_DAYS:
            cur.append(m)
            cur_last = d
        else:
            clusters.append(cur)
            cur = [m]
            cur_last = d
    if cur:
        clusters.append(cur)
    return clusters, undated_count


def results_table(matches: list[dict], league_code: str, multi_category: bool,
                   current_slugs: set[str]) -> str:
    if multi_category:
        rows = ["| 日付 | カテゴリ | 対戦 | スコア |", "| --- | --- | --- | --- |"]
    else:
        rows = ["| 日付 | 対戦 | スコア |", "| --- | --- | --- |"]
    for m in sorted(matches, key=lambda x: (x["date"], x["category"])):
        d = date_jp(m["date"])
        home = team_link(m["home"], m["home_slug"], league_code, current_slugs)
        away = team_link(m["away"], m["away_slug"], league_code, current_slugs)
        score = f'{m["home_score"]} - {m["away_score"]}'
        if multi_category:
            rows.append(f'| {d} | {m["category"]} | {home} vs {away} | {score} |')
        else:
            rows.append(f'| {d} | {home} vs {away} | {score} |')
    return "\n".join(rows)


def standings_table(entries: list[dict], league_code: str, current_slugs: set[str]) -> str:
    rows = ["| 順位 | チーム | 勝点 | 得失点差 |", "| --- | --- | --- | --- |"]
    for e in entries:
        team = team_link(e["team"], e["slug"], league_code, current_slugs)
        rows.append(f'| {e["rank"]} | {team} | {e["points"]} | {e["goal_diff"]} |')
    return "\n".join(rows)


def build_review_candidate(league: dict, cluster: list[dict]) -> dict:
    meta = league["meta"]
    code = league["code"]
    league_name = meta["league"]
    dates = [m["date"] for m in cluster]
    rep_date = min(dates)
    slug = f'review-{code}-{rep_date.replace("-", "")}'
    round_label = date_range_label(dates)

    categories = sorted(set(m["category"] for m in cluster))
    multi_category = len(categories) > 1
    current_slugs = {v["slug"] for v in league["teams"].values()}

    n = len(cluster)
    lead = f"{league_name}、{round_label}に行われた試合の結果をまとめました（全{n}試合）。"

    body_parts = [lead, "", "## 試合結果", "",
                  results_table(cluster, code, multi_category, current_slugs)]

    body_parts += ["", "## 順位表（勝点・得失点差）"]
    for cat in categories:
        entries = league["standings"].get(cat, [])
        if not entries:
            continue
        if multi_category:
            body_parts += ["", f"### {cat}"]
        body_parts += ["", standings_table(entries, code, current_slugs)]

    body_parts += ["", "## 出典", "", source_line(meta)]
    body = "\n".join(body_parts)

    title = f"【{league_name}】{round_label}の結果まとめ"
    description = f"{league_name}、{round_label}の試合結果と最新の順位表（勝点・得失点差）をまとめました。"

    return {
        "slug": slug, "sort_date": rep_date, "title": title,
        "description": description, "category": CATEGORY_REVIEW,
        "date": rep_date, "body": body,
    }


def review_candidates(league: dict) -> list[dict]:
    matches = league["matches"]
    scheduled_remaining = any(m["status"] == "scheduled" for m in matches)
    clusters, undated_count = cluster_by_weekend(matches)
    if undated_count:
        print(f'  [info] {league["code"]}: 開催日未確定の試合{undated_count}件は'
              f'クラスタ化の対象外としてスキップ（エラーにはしない）')
    if scheduled_remaining and clusters:
        # 直近のクラスタは今後の試合追加でまだ変わる可能性があるため除外する
        # （シーズン終了済みのリーグは対象外にしない）。
        clusters = clusters[:-1]
    out = []
    for c in clusters:
        if len(c) < MIN_CLUSTER_MATCHES:
            continue
        out.append(build_review_candidate(league, c))
    return out


# ---------------------------------------------------------------- Type 2: チームシーズン記録

def build_season_candidate(league: dict, year: int, year_league_name: str,
                            block: str, entry: dict, year_matches: list[dict]) -> dict:
    code = league["code"]
    team, slug = entry["team"], entry["slug"]
    team_matches = sorted(
        (m for m in year_matches
         if m["status"] == "played" and team in (m["home"], m["away"])),
        key=lambda m: m["date"] or "")

    current_slugs = {v["slug"] for v in league["teams"].values()}
    rows = ["| 日付 | 対戦 | スコア | 結果 |", "| --- | --- | --- | --- |"]
    for m in team_matches:
        d = date_jp(m["date"]) if m["date"] else "日付不明"
        opp = m["away"] if m["home"] == team else m["home"]
        my_score = m["home_score"] if m["home"] == team else m["away_score"]
        opp_score = m["away_score"] if m["home"] == team else m["home_score"]
        result = "分" if my_score == opp_score else ("勝" if my_score > opp_score else "敗")
        rows.append(f'| {d} | vs **{opp}** | {my_score} - {opp_score} | {result} |')
    match_table = "\n".join(rows)

    block_label = "" if block in ("総合", "") else f"・{block}"
    lead = (f'{year}年の{year_league_name}{block_label}で、'
            f'{team}は{entry["wins"]}勝{entry["draws"]}分{entry["losses"]}敗（勝点{entry["points"]}）、'
            f'最終順位{entry["rank"]}位という成績でシーズンを終えました。')

    body_parts = [lead, "", "## シーズンの全試合結果", "", match_table]
    body_parts += ["", "## 最終成績", "",
                   f'- 最終順位: {entry["rank"]}位',
                   f'- 勝点: {entry["points"]}',
                   f'- 戦績: {entry["wins"]}勝{entry["draws"]}分{entry["losses"]}敗',
                   f'- 得失点差: {entry["goal_diff"]}']
    body_parts += ["", "## 出典", "", source_line(league["meta"])]
    body = "\n".join(body_parts)

    title = f"【{year}年 {year_league_name}】{team}のシーズン記録"
    description = (f'{year}年の{year_league_name}における{team}のシーズン全試合結果と'
                    f'最終成績（{entry["rank"]}位）をまとめました。')

    rep_date = max((m["date"] for m in team_matches if m["date"]), default=f"{year}-12-31")

    return {
        "slug": f"season-{code}-{slug}-{year}", "sort_date": rep_date, "title": title,
        "description": description, "category": CATEGORY_SEASON,
        "date": rep_date, "body": body,
    }


def season_candidates(league: dict) -> list[dict]:
    out = []
    for h in league["history"]:
        year = h["year"]
        year_league_name = h["league"]
        for block, entries in h["standings"].items():
            for e in entries:
                if e["games"] < MIN_TEAM_GAMES:
                    continue
                out.append(build_season_candidate(league, year, year_league_name, block, e, h["matches"]))
    return out


# ---------------------------------------------------------------- write

FRONTMATTER_TMPL = """---
title: {title}
description: {description}
category: {category}
date: {date}
cta: sponsor
---

{body}
"""


def write_article(c: dict) -> None:
    # cta: sponsor固定（部活メディア→ツナカレ接続設計。データ記事は読者がファン・OB中心
    # のため「この部活・競技を応援したい方へ」CTA帯を表示する）。
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    text = FRONTMATTER_TMPL.format(
        title=c["title"], description=c["description"],
        category=c["category"], date=c["date"], body=c["body"])
    (CONTENT_DIR / f'{c["slug"]}.md').write_text(text, encoding="utf-8")


def main() -> None:
    league_codes = sorted(p.name for p in DATA_DIR.iterdir() if p.is_dir()) if DATA_DIR.exists() else []
    if not league_codes:
        print("[generate_articles] リーグデータがありません（先にfetch_jla.pyを実行）。スキップします。")
        return
    leagues = [load_league(code) for code in league_codes]

    existing = existing_slugs()

    review_all, season_all = [], []
    for lg in leagues:
        for c in review_candidates(lg):
            if c["slug"] not in existing:
                review_all.append(c)
        for c in season_candidates(lg):
            if c["slug"] not in existing:
                season_all.append(c)

    review_all.sort(key=lambda c: (c["sort_date"], c["slug"]))
    season_all.sort(key=lambda c: (c["sort_date"], c["slug"]))

    # 優先度: 結果まとめ（鮮度の高い今シーズン情報）を先に、余った枠をチームシーズン記録
    # （過去シーズンの在庫）で埋める。
    all_candidates = review_all + season_all
    to_write = all_candidates[:MAX_ARTICLES_PER_RUN]
    for c in to_write:
        write_article(c)
        print(f'[生成] {c["slug"]}: {c["title"]}')

    remaining = len(all_candidates) - len(to_write)
    print(f"[generate_articles] 生成{len(to_write)}件 / 未生成ストック{remaining}件"
          f"（結果まとめ{len(review_all)}件・シーズン記録{len(season_all)}件のうち）")


if __name__ == "__main__":
    main()
