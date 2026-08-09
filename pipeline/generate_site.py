# -*- coding: utf-8 -*-
"""data/ の正規化JSONから静的サイト「ラクロスマニア」（site/）を生成する。

生成物:
  site/index.html                トップ（最新結果・今後の試合・順位ダイジェスト）
  site/schedule/index.html       全試合の日程・結果
  site/standings/index.html      全ブロック順位表
  site/teams/index.html          チーム一覧
  site/clubs/<slug>/index.html   チームページ（戦績・年度別成績・日程）
  site/matches/<id>/index.html   試合ページ（レポート/プレビュー・過去の対戦）
  site/sitemap.xml, robots.txt, assets/
"""
import json
import re
import shutil
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"
ASSETS = ROOT / "assets"
CONTENT = ROOT / "content" / "articles"

SITE_BASE = "https://tsunakereoff.github.io/tsunakare-clubs/"  # 独自ドメイン移行時にここを変更
GA_MEASUREMENT_ID = ""  # GA4のG-XXXXXXXXXXを設定すると計測タグが入る

WEEKDAYS_JP = ["月", "火", "水", "木", "金", "土", "日"]

_sitemap_paths: list[str] = []


def load(name):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


def load_history():
    hdir = DATA / "history"
    if not hdir.exists():
        return []
    return [json.loads(f.read_text(encoding="utf-8"))
            for f in sorted(hdir.glob("*.json"), reverse=True)]


def date_jp(iso: str, with_year: bool = False) -> str:
    d = date.fromisoformat(iso)
    wd = WEEKDAYS_JP[d.weekday()]
    return (f"{d.year}年" if with_year else "") + f"{d.month}月{d.day}日（{wd}）"


def score_str(m) -> str:
    return f'{m["home_score"]} - {m["away_score"]}' if m["status"] == "played" else "—"


def match_headline(m) -> str:
    if m["status"] != "played":
        return f'【{m["category"]}】{m["home"]} vs {m["away"]}（{date_jp(m["date"])}）'
    hs, as_ = m["home_score"], m["away_score"]
    if hs == as_:
        return f'【{m["category"]}】{m["home"]} {hs}-{as_} {m["away"]} 引き分け'
    winner = m["home"] if hs > as_ else m["away"]
    return f'【{m["category"]}】{winner} 勝利　{m["home"]} {hs}-{as_} {m["away"]}'


def match_report(m, standings) -> str:
    d = date_jp(m["date"], with_year=True)
    if m["status"] != "played":
        t = f'、{m["time"]}フェイスオフ予定' if m["time"] != "未定" else ""
        return (f'{d}、{m["venue"]}にて第38回関東学生ラクロスリーグ戦 {m["category"]}の'
                f'{m["home"]}対{m["away"]}が行われる予定です{t}。')
    hs, as_ = m["home_score"], m["away_score"]
    base = (f'{d}、{m["venue"]}にて第38回関東学生ラクロスリーグ戦 {m["category"]}の'
            f'{m["home"]}対{m["away"]}が行われました。')
    if hs == as_:
        result = f'試合は両者譲らず{hs}-{as_}の引き分けに終わりました。'
    else:
        winner = m["home"] if hs > as_ else m["away"]
        loser = m["away"] if hs > as_ else m["home"]
        result = f'試合は{winner}が{max(hs, as_)}-{min(hs, as_)}で{loser}を下しました。'
    ctx = ""
    for e in standings.get(m["category"], []):
        if hs != as_ and e["team"] == (m["home"] if hs > as_ else m["away"]):
            ctx = f'この結果、{e["team"]}は{m["category"]}で{e["rank"]}位（勝ち点{e["points"]}）につけています。'
    return base + result + ctx


def h2h_list(a, b, matches_by_year):
    out = []
    for year, ms in matches_by_year:
        for m in ms:
            if m["status"] == "played" and {m["home"], m["away"]} == {a, b}:
                out.append((year, m))
    out.sort(key=lambda ym: ym[1]["date"] or "", reverse=True)
    return out


def recent_results(team, matches, n=3):
    ms = [m for m in matches
          if m["status"] == "played" and team in (m["home"], m["away"])]
    return list(reversed(ms))[:n]


def result_mark(m, team):
    gf = m["home_score"] if m["home"] == team else m["away_score"]
    ga = m["away_score"] if m["home"] == team else m["home_score"]
    return "○" if gf > ga else ("△" if gf == ga else "●")


def badge(mark: str) -> str:
    cls = {"○": "w", "△": "d", "●": "l"}[mark]
    return f'<span class="mk mk-{cls}">{mark}</span>'


def h2h_section(m, matches_by_year) -> str:
    pair = [(y, x) for y, x in h2h_list(m["home"], m["away"], matches_by_year)
            if x["id"] != m["id"]]
    if not pair:
        return ""
    a = m["home"]
    wins = sum(1 for _, x in pair if result_mark(x, a) == "○")
    draws = sum(1 for _, x in pair if result_mark(x, a) == "△")
    losses = len(pair) - wins - draws
    rows = "".join(
        f'<tr><td>{y}年</td><td>{date_jp(x["date"])}</td>'
        f'<td>{escape(x["home"])} {x["home_score"]} - {x["away_score"]} {escape(x["away"])}</td>'
        f'<td>{badge(result_mark(x, a))}</td></tr>'
        for y, x in pair[:6])
    return ('<section><h2>過去の対戦</h2>'
            f'<p>直近の直接対決は{escape(a)}から見て'
            f'<strong>{wins}勝{draws}分{losses}敗</strong>（過去{len(pair)}試合）。</p>'
            '<div class="tbl"><table><thead><tr><th>年度</th><th>日付</th><th>結果</th>'
            f'<th>{escape(a)}</th></tr></thead><tbody>{rows}</tbody></table></div></section>')


def preview_sections(m, matches, standings) -> str:
    body = ""
    rows = ""
    for t in (m["home"], m["away"]):
        e = next((x for x in standings.get(m["category"], []) if x["team"] == t), None)
        if e:
            rows += (f'<tr><td>{escape(t)}</td><td>{e["rank"]}位</td>'
                     f'<td>{e["points"]}</td><td>{e["wins"]}-{e["draws"]}-{e["losses"]}</td>'
                     f'<td>{escape(str(e["goal_diff"]))}</td></tr>')
    if rows:
        body += ('<section><h2>両チームの今季成績</h2>'
                 '<div class="tbl"><table><thead><tr><th>チーム</th><th>順位</th><th>勝点</th>'
                 '<th>勝-分-敗</th><th>得失</th></tr></thead>'
                 f'<tbody>{rows}</tbody></table></div></section>')
    for t in (m["home"], m["away"]):
        rec = recent_results(t, matches)
        if not rec:
            continue
        rows = "".join(
            f'<tr><td>{date_jp(x["date"])}</td><td>{badge(result_mark(x, t))}</td>'
            f'<td>{escape(x["home"])} {x["home_score"]} - {x["away_score"]} {escape(x["away"])}</td></tr>'
            for x in rec)
        body += (f'<section><h2>{escape(t)}の直近の試合</h2>'
                 '<div class="tbl"><table><thead><tr><th>日付</th><th>勝敗</th><th>結果</th></tr></thead>'
                 f'<tbody>{rows}</tbody></table></div></section>')
    return body


def jsonld_sports_event(m) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "SportsEvent",
        "name": f'第38回関東学生ラクロスリーグ戦 {m["category"]} {m["home"]} vs {m["away"]}',
        "startDate": m["date"],
        "location": {"@type": "Place", "name": m["venue"]},
        "homeTeam": {"@type": "SportsTeam", "name": f'{m["home"]}男子ラクロス部'},
        "awayTeam": {"@type": "SportsTeam", "name": f'{m["away"]}男子ラクロス部'},
        "sport": "Lacrosse",
    }
    return ('<script type="application/ld+json">'
            + json.dumps(data, ensure_ascii=False) + "</script>")


NAV_ITEMS = [
    ("index.html", "トップ"),
    ("schedule/index.html", "日程・結果"),
    ("standings/index.html", "順位表"),
    ("teams/index.html", "チーム"),
    ("articles/index.html", "読みもの"),
    ("videos/index.html", "動画"),
]


def md_inline(s: str) -> str:
    s = escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return s


def md_to_html(md: str) -> str:
    """記事用の最小Markdownレンダラ（見出し・段落・リスト・表・強調・リンク）。"""
    out, para = [], []
    in_ul = in_ol = in_table = False

    def close_blocks():
        nonlocal in_ul, in_ol, in_table
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False
        if in_table:
            out.append("</tbody></table></div>")
            in_table = False

    def flush_para():
        nonlocal para
        if para:
            out.append("<p>" + md_inline(" ".join(para)) + "</p>")
            para = []

    for line in md.splitlines():
        s = line.strip()
        if s.startswith("|") and s.endswith("|") and len(s) > 1:
            flush_para()
            if in_ul or in_ol:
                close_blocks()
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r"[-: ]+", c) for c in cells):
                continue
            if not in_table:
                out.append('<div class="tbl"><table><thead><tr>'
                           + "".join(f"<th>{md_inline(c)}</th>" for c in cells)
                           + "</tr></thead><tbody>")
                in_table = True
            else:
                out.append("<tr>" + "".join(f"<td>{md_inline(c)}</td>" for c in cells) + "</tr>")
            continue
        if in_table:
            out.append("</tbody></table></div>")
            in_table = False
        if not s:
            flush_para()
            close_blocks()
        elif s.startswith("### "):
            flush_para(); close_blocks()
            out.append(f"<h3>{md_inline(s[4:])}</h3>")
        elif s.startswith("## "):
            flush_para(); close_blocks()
            out.append(f"<h2>{md_inline(s[3:])}</h2>")
        elif s.startswith("- "):
            flush_para()
            if not in_ul:
                close_blocks()
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{md_inline(s[2:])}</li>")
        elif re.match(r"^\d+\.\s", s):
            flush_para()
            if not in_ol:
                close_blocks()
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{md_inline(re.sub(r'^\\d+\\.\\s', '', s))}</li>")
        else:
            para.append(s)
    flush_para()
    close_blocks()
    return "\n".join(out)


def load_articles():
    if not CONTENT.exists():
        return []
    arts = []
    for f in sorted(CONTENT.glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        _, fm, body = raw.split("---", 2)
        a = {"slug": f.stem, "body": body.strip()}
        for line in fm.strip().splitlines():
            k, _, v = line.partition(":")
            a[k.strip()] = v.strip()
        arts.append(a)
    arts.sort(key=lambda a: (a.get("date", ""), a["slug"]), reverse=True)
    return arts


def article_card(a, rel) -> str:
    return (f'<div class="digest-card"><p class="cat-line"><span class="cat">{escape(a["category"])}</span>'
            f' <span class="note">{escape(a["date"])}</span></p>'
            f'<h3><a href="{rel}articles/{a["slug"]}/index.html">{escape(a["title"])}</a></h3>'
            f'<p class="note">{escape(a["description"])}</p></div>')


def page(rel, title, body, meta, *, path="", desc="", extra_head="", og_type="website"):
    _sitemap_paths.append(path)
    desc = desc or "関東学生ラクロスリーグの試合結果・日程・順位表・チーム戦績を毎日自動更新する大学ラクロス情報メディア。"
    url = SITE_BASE + path
    og_image = ""
    if (ASSETS / "ogp.png").exists():
        og_image = (f'<meta property="og:image" content="{SITE_BASE}assets/ogp.png">\n'
                    '<meta name="twitter:card" content="summary_large_image">\n')
    ga = ""
    if GA_MEASUREMENT_ID:
        ga = (f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>'
              '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}'
              f"gtag('js',new Date());gtag('config','{GA_MEASUREMENT_ID}');</script>")
    nav = "".join(f'<a href="{rel}{href}">{label}</a>' for href, label in NAV_ITEMS)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(desc)}">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(desc)}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{escape(url)}">
<meta property="og:site_name" content="ラクロスマニア">
{og_image}<link rel="icon" href="{rel}assets/favicon.svg" type="image/svg+xml">
<link rel="canonical" href="{escape(url)}">
{extra_head}{ga}
<link rel="stylesheet" href="{rel}style.css">
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="{rel}index.html"><span class="brand-tick"></span>ラクロスマニア<span class="brand-sub">KANTO LACROSSE MEDIA</span></a>
    <nav class="global-nav">{nav}</nav>
  </div>
</header>
<main>
{body}
</main>
<footer class="site-footer">
  <div class="footer-inner">
    <p class="footer-brand">ラクロスマニア</p>
    <nav class="footer-nav">{nav}</nav>
    <p>運営: <a href="https://piecetimes.jp">PieceTimes</a>　|　関連サービス: <a href="https://tunakare.jp">ツナカレ（大学部活×企業マッチング）</a></p>
    <p>試合データ出典: <a href="{escape(meta['source_url'])}">{escape(meta['source'])}</a>
    （連盟データ更新日: {escape(meta['source_updated_at'])} / 本サイト自動更新: {escape(meta['fetched_at'][:10])}）</p>
    <p>ラクロスマニアは大学ラクロスの情報メディアです。試合結果は自動収集のため、確定情報は連盟公式をご確認ください。順位・成績の集計値は試合結果からの自動算出です。</p>
  </div>
</footer>
</body>
</html>"""


def match_row(m, rel) -> str:
    link = f'{rel}matches/{m["id"]}/index.html'
    return (f'<tr><td>{date_jp(m["date"])}</td><td>{escape(m["time"])}</td>'
            f'<td><span class="cat">{escape(m["category"])}</span></td>'
            f'<td><a href="{link}">{escape(m["home"])} vs {escape(m["away"])}</a></td>'
            f'<td class="score">{score_str(m)}</td>'
            f'<td class="venue">{escape(m["venue"])}</td></tr>')


MATCH_TABLE = ('<div class="tbl"><table><thead><tr><th>日付</th><th>時間</th><th>カテゴリ</th>'
               '<th>対戦</th><th>スコア</th><th>会場</th></tr></thead><tbody>')


def standings_table(block, entries, rel) -> str:
    rows = "".join(
        f'<tr><td class="rank">{e["rank"]}</td>'
        f'<td><a href="{rel}clubs/{e["slug"]}/index.html">{escape(e["team"])}</a></td>'
        f'<td><strong>{e["points"]}</strong></td><td>{e["games"]}</td>'
        f'<td>{e["wins"]}-{e["draws"]}-{e["losses"]}</td>'
        f'<td>{escape(str(e["goal_diff"]))}</td></tr>'
        for e in entries)
    return (f'<h3>{escape(block)}</h3>'
            '<div class="tbl"><table><thead><tr><th>順位</th><th>チーム</th><th>勝点</th>'
            '<th>試合</th><th>勝-分-敗</th><th>得失</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')


def build_index(matches, standings, meta, articles):
    rel = ""
    today = date.today().isoformat()
    played = [m for m in matches if m["status"] == "played"]
    scheduled = [m for m in matches if m["status"] == "scheduled"]
    upcoming = [m for m in scheduled if m["date"] and m["date"] >= today][:8]
    recent = list(reversed(played))[:8]

    body = ('<div class="hero"><div class="hero-inner">'
            f'<p class="hero-kicker">{escape(meta["league"])}</p>'
            '<h1>関東学生ラクロスの試合結果・日程・順位を毎日自動更新</h1>'
            f'<p class="hero-sub">全37チームの戦績・過去の対戦データ・試合プレビューを掲載　|　最終更新 {escape(meta["fetched_at"][:10])}</p>'
            '</div></div>')
    body += '<section><h2>最新の試合結果</h2>' + MATCH_TABLE
    body += "".join(match_row(m, rel) for m in recent) + "</tbody></table></div>"
    body += f'<p class="more"><a class="cta" href="{rel}schedule/index.html">全試合の日程・結果を見る →</a></p></section>'
    body += '<section><h2>今後の試合</h2>' + MATCH_TABLE
    body += "".join(match_row(m, rel) for m in upcoming) + "</tbody></table></div>"
    body += '<p class="note">試合ページでは両チームの今季成績・直近試合・過去の対戦をプレビューできます。</p></section>'
    body += '<section><h2>順位表ダイジェスト</h2><div class="digest">'
    for block, entries in standings.items():
        rows = "".join(
            f'<tr><td class="rank">{e["rank"]}</td>'
            f'<td><a href="{rel}clubs/{e["slug"]}/index.html">{escape(e["team"])}</a></td>'
            f'<td>{e["points"]}</td></tr>'
            for e in entries[:3])
        body += (f'<div class="digest-card"><h3>{escape(block)}</h3>'
                 '<div class="tbl"><table><thead><tr><th>順位</th><th>チーム</th><th>勝点</th></tr></thead>'
                 f'<tbody>{rows}</tbody></table></div></div>')
    body += (f'</div><p class="more"><a class="cta" href="{rel}standings/index.html">全ブロックの順位表を見る →</a></p></section>')
    if articles:
        body += ('<section><h2>読みもの</h2><div class="digest">'
                 + "".join(article_card(a, rel) for a in articles[:3])
                 + f'</div><p class="more"><a class="cta" href="{rel}articles/index.html">読みもの一覧へ →</a></p></section>')
    (SITE / "index.html").write_text(
        page(rel, "ラクロスマニア | 関東学生ラクロスの試合結果・日程・順位表", body, meta,
             path="", desc=f'{meta["league"]}の試合結果・日程・順位表・チーム戦績を毎日自動更新。過去の対戦データと試合プレビューも掲載。'),
        encoding="utf-8")


def build_schedule(matches, meta):
    rel = "../"
    today = date.today().isoformat()
    played = [m for m in matches if m["status"] == "played"]
    scheduled = [m for m in matches if m["status"] == "scheduled"]
    upcoming = [m for m in scheduled if m["date"] and m["date"] >= today]
    awaiting = [m for m in scheduled if m["date"] and m["date"] < today]

    body = '<h1>試合日程・結果</h1>'
    body += '<section><h2>今後の試合</h2>' + MATCH_TABLE
    body += "".join(match_row(m, rel) for m in upcoming) + "</tbody></table></div></section>"
    body += '<section><h2>試合結果</h2>' + MATCH_TABLE
    body += "".join(match_row(m, rel) for m in reversed(played)) + "</tbody></table></div></section>"
    if awaiting:
        body += ('<section><h2>結果反映待ちの試合</h2>'
                 '<p class="note">連盟データにまだスコアが入力されていない実施済み日程（延期の可能性あり）。</p>'
                 + MATCH_TABLE
                 + "".join(match_row(m, rel) for m in awaiting)
                 + "</tbody></table></div></section>")
    out = SITE / "schedule" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        page(rel, f'試合日程・結果 | ラクロスマニア', body, meta,
             path="schedule/", desc=f'{meta["league"]}の全試合日程と結果の一覧。'),
        encoding="utf-8")


def build_standings_page(standings, meta):
    rel = "../"
    body = '<h1>順位表</h1>'
    for block, entries in standings.items():
        body += standings_table(block, entries, rel)
    out = SITE / "standings" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        page(rel, f'順位表（全ブロック） | ラクロスマニア', body, meta,
             path="standings/", desc=f'{meta["league"]}の全6ブロックの順位表。勝点・得失点差を毎日自動更新。'),
        encoding="utf-8")


def build_teams_page(teams, standings, meta):
    rel = "../"
    body = '<h1>チーム一覧</h1><div class="digest">'
    blocks: dict[str, list] = {}
    for info in teams.values():
        blocks.setdefault(info["block"], []).append(info)
    for block in sorted(blocks):
        links = "".join(
            f'<li><a href="{rel}clubs/{t["slug"]}/index.html">{escape(t["team"])}</a></li>'
            for t in sorted(blocks[block], key=lambda x: x["team"]))
        body += f'<div class="digest-card"><h3>{escape(block)}</h3><ul class="team-list">{links}</ul></div>'
    body += "</div>"
    out = SITE / "teams" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        page(rel, f'チーム一覧 | ラクロスマニア', body, meta,
             path="teams/", desc=f'{meta["league"]}参加全チームの一覧。各チームの戦績・日程・年度別成績はチームページで。'),
        encoding="utf-8")


def build_articles(articles, meta):
    rel = "../"
    cards = "".join(article_card(a, rel) for a in articles)
    body = ('<h1>読みもの</h1>'
            '<p class="lead">戦術・練習・チーム運営・分析 ― 大学ラクロスの現場で使える知見をまとめています。</p>'
            f'<div class="digest">{cards}</div>')
    out = SITE / "articles" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        page(rel, "読みもの（戦術・練習・チーム運営・分析） | ラクロスマニア", body, meta,
             path="articles/",
             desc="大学ラクロスの戦術・練習メニュー・チーム運営・映像分析の実践的なノウハウ記事。"),
        encoding="utf-8")

    rel = "../../"
    for a in articles:
        others = [x for x in articles if x["slug"] != a["slug"]][:3]
        related = "".join(
            f'<li><a href="../{x["slug"]}/index.html">{escape(x["title"])}</a></li>'
            for x in others)
        body = (f'<p class="breadcrumb"><a href="{rel}index.html">トップ</a> › '
                f'<a href="{rel}articles/index.html">読みもの</a> › {escape(a["category"])}</p>')
        body += (f'<p class="cat-line"><span class="cat">{escape(a["category"])}</span>'
                 f' <span class="note">{escape(a["date"])}</span></p>')
        body += f'<h1>{escape(a["title"])}</h1>'
        body += f'<div class="article">{md_to_html(a["body"])}</div>'
        body += f'<section><h2>あわせて読む</h2><ul>{related}</ul></section>'
        out = SITE / "articles" / a["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            page(rel, f'{a["title"]} | ラクロスマニア', body, meta,
                 path=f'articles/{a["slug"]}/', desc=a["description"], og_type="article"),
            encoding="utf-8")


def build_videos(meta):
    rel = "../"
    vids = []
    vfile = DATA / "videos.json"
    if vfile.exists():
        vids = json.loads(vfile.read_text(encoding="utf-8"))
    cats: dict[str, list] = {}
    for v in vids:
        cats.setdefault(v["category"], []).append(v)
    body = ('<h1>動画インデックス</h1>'
            '<p class="lead">大学ラクロスの試合映像・配信を公式ソースから探せるリンク集です。'
            '映像はすべて権利元の公式プラットフォーム上で視聴します。</p>')
    for cat, items in cats.items():
        cards = "".join(
            f'<div class="digest-card"><h3><a href="{escape(v["url"])}">{escape(v["title"])}</a></h3>'
            f'<p class="note">{escape(v["note"])}</p>'
            f'<p class="cat-line"><span class="cat">{escape(v["source"])}</span></p></div>'
            for v in items)
        body += f'<h2>{escape(cat)}</h2><div class="digest">{cards}</div>'
    body += ('<section><h2>自チームの映像分析に</h2>'
             '<p>集めた映像をチーム強化に生かす方法は'
             '<a href="../articles/video-analysis/index.html">試合映像の分析入門</a>で解説しています。</p></section>')
    out = SITE / "videos" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        page(rel, "動画インデックス（試合映像・ライブ配信） | ラクロスマニア", body, meta,
             path="videos/",
             desc="大学ラクロスの試合映像・ライブ配信を公式ソース（JLA・Japan Lacrosse Live）から探せるリンク集。"),
        encoding="utf-8")


def build_club_pages(matches, standings, teams, meta, hist, articles):
    rel = "../../"
    for team, info in teams.items():
        slug, block = info["slug"], info["block"]
        is_univ = "大学" in team
        club_name = f'{team}男子ラクロス部' if is_univ else f'{team}（男子ラクロス）'
        my_matches = [m for m in matches if m["home"] == team or m["away"] == team]
        my_played = [m for m in my_matches if m["status"] == "played"]
        my_upcoming = [m for m in my_matches if m["status"] == "scheduled"]
        entry = next((e for e in standings.get(block, []) if e["team"] == team), None)

        body = f'<p class="breadcrumb"><a href="{rel}index.html">トップ</a> › <a href="{rel}teams/index.html">チーム</a> › {escape(club_name)}</p>'
        body += f'<h1>{escape(club_name)}</h1>'
        body += f'<p class="lead">第38回関東学生ラクロスリーグ戦 {escape(block)} 所属。</p>'
        if entry:
            body += ('<section><h2>現在の戦績</h2><div class="stat-row">'
                     f'<div class="stat"><span class="num">{entry["rank"]}</span>位</div>'
                     f'<div class="stat"><span class="num">{entry["points"]}</span>勝ち点</div>'
                     f'<div class="stat"><span class="num">{entry["wins"]}-{entry["draws"]}-{entry["losses"]}</span>勝-分-敗</div>'
                     f'<div class="stat"><span class="num">{escape(str(entry["goal_diff"]))}</span>得失点差</div>'
                     '</div></section>')
        if my_played:
            body += '<section><h2>試合結果</h2>' + MATCH_TABLE
            body += "".join(match_row(m, rel) for m in reversed(my_played))
            body += "</tbody></table></div></section>"
        if my_upcoming:
            body += '<section><h2>今後の日程</h2>' + MATCH_TABLE
            body += "".join(match_row(m, rel) for m in my_upcoming)
            body += "</tbody></table></div></section>"
        season_rows = ""
        for h in hist:
            for hblock, entries in h["standings"].items():
                e = next((x for x in entries if x["team"] == team), None)
                if e:
                    season_rows += (f'<tr><td>{h["year"]}年</td><td>{escape(hblock)}</td>'
                                    f'<td>{e["rank"]}位</td>'
                                    f'<td>{e["wins"]}-{e["draws"]}-{e["losses"]}</td>'
                                    f'<td>{e["gf"]} - {e["ga"]}</td></tr>')
        if season_rows:
            body += ('<section><h2>年度別成績</h2>'
                     '<div class="tbl"><table><thead><tr><th>年度</th><th>所属</th><th>順位</th>'
                     '<th>勝-分-敗</th><th>総得点-総失点</th></tr></thead>'
                     f'<tbody>{season_rows}</tbody></table></div>'
                     '<p class="note">※順位はブロック内リーグ戦の結果から自動算出した参考値です。</p></section>')
        if articles:
            art_links = "".join(
                f'<li><a href="{rel}articles/{a["slug"]}/index.html">{escape(a["title"])}</a></li>'
                for a in articles[:3])
            body += (f'<section><h2>読みもの</h2><ul>{art_links}</ul>'
                     f'<p class="more"><a href="{rel}articles/index.html">読みもの一覧へ →</a></p></section>')
        body += ('<section class="placeholder"><h2>Instagram</h2>'
                 '<p class="todo">（部活公式アカウントの公開投稿の公式埋め込みをここに配置）</p></section>')
        body += ('<section class="sponsor"><h2>この部活を応援する企業</h2>'
                 '<p class="todo">（協賛メニュー連携枠：スポンサー企業ロゴ・リンクをここに配置）</p>'
                 '<p><a class="cta" href="#">協賛について問い合わせる →</a></p></section>')

        out = SITE / "clubs" / slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            page(rel, f'{club_name} 試合結果・日程・戦績 | ラクロスマニア', body, meta,
                 path=f"clubs/{slug}/",
                 desc=f'{club_name}の試合結果・今後の日程・年度別成績・過去の対戦データ。{block}所属。'),
            encoding="utf-8")


def build_match_pages(matches, standings, meta, matches_by_year):
    rel = "../../"
    for m in matches:
        report = match_report(m, standings)
        body = (f'<p class="breadcrumb"><a href="{rel}index.html">トップ</a> › '
                f'<a href="{rel}schedule/index.html">日程・結果</a> › {escape(m["category"])}</p>')
        body += f'<h1>{escape(match_headline(m))}</h1>'
        body += f'<p class="report">{escape(report)}</p>'
        if m["status"] == "scheduled":
            body += preview_sections(m, matches, standings)
        body += h2h_section(m, matches_by_year)
        body += ('<div class="tbl"><table class="detail"><tbody>'
                 f'<tr><th>日付</th><td>{date_jp(m["date"], with_year=True)}</td></tr>'
                 f'<tr><th>時間</th><td>{escape(m["time"])}</td></tr>'
                 f'<tr><th>カテゴリ</th><td>{escape(m["category"])}</td></tr>'
                 f'<tr><th>会場</th><td>{escape(m["venue"])}</td></tr>'
                 f'<tr><th>スコア</th><td>{score_str(m)}</td></tr>'
                 '</tbody></table></div>')
        body += ('<p class="links">'
                 f'<a href="{rel}clubs/{m["home_slug"]}/index.html">{escape(m["home"])}のページ</a> / '
                 f'<a href="{rel}clubs/{m["away_slug"]}/index.html">{escape(m["away"])}のページ</a></p>')
        body += ('<p class="note">この試合の映像を探す: '
                 '<a href="https://www.lacrosselive.jp/">Japan Lacrosse Live</a> / '
                 '<a href="https://www.youtube.com/channel/UCpOxINAZ422HSX17E7T84aA">JLA公式YouTube</a>'
                 f'　|　<a href="{rel}videos/index.html">動画インデックス</a></p>')
        out = SITE / "matches" / m["id"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            page(rel, match_headline(m) + " | ラクロスマニア", body, meta,
                 path=f'matches/{m["id"]}/', desc=report[:120], og_type="article",
                 extra_head=jsonld_sports_event(m)),
            encoding="utf-8")


def write_sitemap_and_robots():
    today = date.today().isoformat()
    urls = "".join(
        f"<url><loc>{SITE_BASE}{p}</loc><lastmod>{today}</lastmod></url>"
        for p in _sitemap_paths)
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + urls + "</urlset>", encoding="utf-8")
    (SITE / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_BASE}sitemap.xml\n", encoding="utf-8")


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="14" fill="#16283f"/>
<rect x="10" y="40" width="44" height="8" rx="4" fill="#f97316"/>
<text x="32" y="36" font-family="Arial, sans-serif" font-size="26" font-weight="bold"
 fill="#ffffff" text-anchor="middle">LM</text>
</svg>
"""

STYLE = """
:root {
  --ink:#1a2433; --sub:#5b6b7b; --line:#dfe5ec; --bg:#f5f7f9; --surface:#fff;
  --navy:#16283f; --navy-2:#1f3a5c; --accent:#f97316; --accent-dark:#c2570b;
  --win:#15803d; --draw:#b45309; --loss:#b91c1c;
}
* { box-sizing:border-box; }
body { margin:0; font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",Meiryo,sans-serif;
  color:var(--ink); background:var(--bg); line-height:1.7; }
a { color:var(--navy-2); }
a:hover { color:var(--accent-dark); }

.site-header { background:var(--navy); }
.header-inner { max-width:960px; margin:0 auto; padding:.7rem 1rem .5rem;
  display:flex; flex-wrap:wrap; align-items:center; gap:.3rem 1.5rem; }
.brand { display:flex; align-items:baseline; gap:.5rem; font-weight:800;
  color:#fff; text-decoration:none; font-size:1.25rem; letter-spacing:.02em; }
.brand-tick { width:.55em; height:.55em; background:var(--accent);
  border-radius:2px; align-self:center; }
.brand-sub { font-size:.6rem; color:#9fb2c8; font-weight:600; letter-spacing:.18em; }
.global-nav { display:flex; gap:.2rem; overflow-x:auto; margin-left:auto; }
.global-nav a { color:#d7e0ea; text-decoration:none; font-size:.85rem; font-weight:600;
  padding:.35em .7em; border-radius:6px; white-space:nowrap; }
.global-nav a:hover { background:var(--navy-2); color:#fff; }

.hero { background:linear-gradient(120deg, var(--navy) 0%, var(--navy-2) 70%, #2c4e78 100%);
  color:#fff; margin:0 -1rem; }
.hero-inner { max-width:960px; margin:0 auto; padding:2.2rem 1rem 2.4rem; }
.hero-kicker { color:var(--accent); font-weight:700; font-size:.85rem; margin:0 0 .4rem; }
.hero h1 { font-size:1.5rem; line-height:1.45; margin:0 0 .6rem; }
.hero-sub { color:#c3d1e0; font-size:.85rem; margin:0; }

main { max-width:960px; margin:0 auto; padding:0 1rem 3rem; }
h1 { font-size:1.35rem; line-height:1.45; }
h2 { font-size:1.08rem; border-left:4px solid var(--accent); padding-left:.55em;
  margin-top:2.4em; }
h3 { font-size:.95rem; margin-top:1.6em; }

.tbl { overflow-x:auto; background:var(--surface); border:1px solid var(--line);
  border-radius:10px; }
table { width:100%; border-collapse:collapse; font-size:.85rem; }
th, td { border-bottom:1px solid var(--line); padding:.5em .7em; text-align:left;
  white-space:nowrap; }
tbody tr:last-child td { border-bottom:none; }
thead th { background:var(--navy); color:#fff; font-weight:600; font-size:.78rem; }
tbody tr:nth-child(even) { background:#f8fafc; }
td.score { font-weight:700; }
td.venue { color:var(--sub); font-size:.78rem; max-width:16em; overflow:hidden;
  text-overflow:ellipsis; }
td.rank { font-weight:700; text-align:center; }
.cat { background:#eaeff5; color:var(--navy-2); font-size:.72rem; font-weight:700;
  padding:.15em .5em; border-radius:999px; }
table.detail th { background:#eef2f6; color:var(--ink); width:7em; }

.mk { font-weight:700; }
.mk-w { color:var(--win); }
.mk-d { color:var(--draw); }
.mk-l { color:var(--loss); }

.breadcrumb { font-size:.8rem; color:var(--sub); margin-top:1rem; }
.breadcrumb a { color:var(--sub); }
.lead { color:var(--sub); }
.note { color:var(--sub); font-size:.8rem; }
.more { margin:.9rem 0 0; }
.cta { display:inline-block; background:var(--accent); color:#fff; font-weight:700;
  font-size:.85rem; text-decoration:none; padding:.5em 1.1em; border-radius:8px; }
.cta:hover { background:var(--accent-dark); color:#fff; }

.stat-row { display:flex; gap:.8rem; flex-wrap:wrap; }
.stat { background:var(--surface); border:1px solid var(--line); border-radius:10px;
  padding:.7rem 1.1rem; font-size:.75rem; color:var(--sub); min-width:100px;
  text-align:center; }
.stat .num { display:block; font-size:1.35rem; font-weight:800; color:var(--navy); }

.report { background:var(--surface); border:1px solid var(--line);
  border-left:4px solid var(--accent); border-radius:10px; padding:1rem 1.2rem; }

.digest { display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr));
  gap:1rem; }
.digest-card { background:var(--surface); border:1px solid var(--line);
  border-radius:10px; padding:.9rem 1rem 1rem; }
.digest-card h3 { margin:.1em 0 .6em; }
.digest-card .tbl { border:none; }
.team-list { list-style:none; margin:0; padding:0; columns:2; font-size:.9rem; }
.team-list li { margin:.25em 0; break-inside:avoid; }

.placeholder .todo, .sponsor .todo { color:var(--sub); background:var(--surface);
  border:1px dashed var(--line); border-radius:10px; padding:.8rem; font-size:.85rem; }

.cat-line { font-size:.8rem; margin:.4rem 0; }
.article { background:var(--surface); border:1px solid var(--line); border-radius:10px;
  padding:1.4rem 1.6rem 1.6rem; }
.article h2 { margin-top:1.8em; }
.article h2:first-child { margin-top:.4em; }
.article li { margin:.3em 0; }
.digest-card h3 a { text-decoration:none; color:var(--navy); }
.digest-card h3 a:hover { color:var(--accent-dark); }

.site-footer { background:var(--navy); color:#9fb2c8; font-size:.75rem;
  margin-top:3rem; }
.footer-inner { max-width:960px; margin:0 auto; padding:1.4rem 1rem 2rem; }
.footer-brand { color:#fff; font-weight:800; font-size:.95rem; margin:0 0 .3rem; }
.footer-nav { display:flex; gap:1rem; margin:.2rem 0 .8rem; }
.footer-nav a { color:#c3d1e0; text-decoration:none; }
.site-footer a { color:#c3d1e0; }
"""


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    _sitemap_paths.clear()

    matches = load("matches")
    standings = load("standings")
    teams = load("teams")
    meta = load("meta")
    hist = load_history()
    matches_by_year = ([(meta["season_year"], matches)]
                       + [(h["year"], h["matches"]) for h in hist])

    (SITE / "style.css").write_text(STYLE, encoding="utf-8")
    (SITE / "assets").mkdir()
    (SITE / "assets" / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    if ASSETS.exists():
        for f in ASSETS.iterdir():
            shutil.copy(f, SITE / "assets" / f.name)

    articles = load_articles()

    build_index(matches, standings, meta, articles)
    build_schedule(matches, meta)
    build_standings_page(standings, meta)
    build_teams_page(teams, standings, meta)
    build_articles(articles, meta)
    build_videos(meta)
    build_club_pages(matches, standings, teams, meta, hist, articles)
    build_match_pages(matches, standings, meta, matches_by_year)
    write_sitemap_and_robots()

    print(f"OK: {len(_sitemap_paths)} pages generated in {SITE}")


if __name__ == "__main__":
    main()
