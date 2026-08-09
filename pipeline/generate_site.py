# -*- coding: utf-8 -*-
"""data/ の正規化JSONから静的サイト（site/）を生成する。

生成物:
  site/index.html                リーグトップ（星取表・最新結果・今後の日程）
  site/clubs/<slug>/index.html   部活ページ（戦績・日程・協賛枠・メディア記事枠）
  site/matches/<id>/index.html   試合ページ（自動生成レポート + schema.org構造化データ）
"""
import json
import shutil
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"

WEEKDAYS_JP = ["月", "火", "水", "木", "金", "土", "日"]


def load(name):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


def date_jp(iso: str, with_year: bool = False) -> str:
    from datetime import date
    d = date.fromisoformat(iso)
    wd = WEEKDAYS_JP[d.weekday()]
    if with_year:
        return f"{d.year}年{d.month}月{d.day}日（{wd}）"
    return f"{d.month}月{d.day}日（{wd}）"


def score_str(m) -> str:
    if m["status"] == "played":
        return f'{m["home_score"]} - {m["away_score"]}'
    return "—"


def match_headline(m) -> str:
    if m["status"] != "played":
        return f'【{m["category"]}】{m["home"]} vs {m["away"]}（{date_jp(m["date"])}）'
    hs, as_ = m["home_score"], m["away_score"]
    if hs == as_:
        return f'【{m["category"]}】{m["home"]} {hs}-{as_} {m["away"]} 引き分け'
    winner = m["home"] if hs > as_ else m["away"]
    return f'【{m["category"]}】{winner} 勝利　{m["home"]} {hs}-{as_} {m["away"]}'


def match_report(m, standings) -> str:
    """事実ベースの短文レポートを生成（テンプレート方式・LLM不使用）。"""
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
        ws, ls = max(hs, as_), min(hs, as_)
        result = f'試合は{winner}が{ws}-{ls}で{loser}を下しました。'
    ctx = ""
    for e in standings.get(m["category"], []):
        if m["status"] == "played" and hs != as_ and e["team"] == (m["home"] if hs > as_ else m["away"]):
            ctx = f'この結果、{e["team"]}は{m["category"]}で{e["rank"]}位（勝ち点{e["points"]}）につけています。'
    return base + result + ctx


def load_history():
    """data/history/*.json を新しい年度順に読み込む。"""
    hdir = DATA / "history"
    if not hdir.exists():
        return []
    return [json.loads(f.read_text(encoding="utf-8"))
            for f in sorted(hdir.glob("*.json"), reverse=True)]


def h2h_list(a: str, b: str, matches_by_year):
    """全年度から2チームの直接対決（結果確定分）を新しい順に返す。"""
    out = []
    for year, ms in matches_by_year:
        for m in ms:
            if m["status"] == "played" and {m["home"], m["away"]} == {a, b}:
                out.append((year, m))
    out.sort(key=lambda ym: ym[1]["date"] or "", reverse=True)
    return out


def recent_results(team: str, matches, n: int = 3):
    """今季の直近n試合（結果確定分）を新しい順に返す。"""
    ms = [m for m in matches
          if m["status"] == "played" and team in (m["home"], m["away"])]
    return list(reversed(ms))[:n]


def result_mark(m, team: str) -> str:
    gf = m["home_score"] if m["home"] == team else m["away_score"]
    ga = m["away_score"] if m["home"] == team else m["home_score"]
    return "○" if gf > ga else ("△" if gf == ga else "●")


def h2h_section(m, matches_by_year, rel: str) -> str:
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
        f'<td>{result_mark(x, a)}</td></tr>'
        for y, x in pair[:6])
    return ('<section><h2>過去の対戦</h2>'
            f'<p>直近の直接対決は{escape(a)}から見て'
            f'<strong>{wins}勝{draws}分{losses}敗</strong>（過去{len(pair)}試合）。</p>'
            '<table><thead><tr><th>年度</th><th>日付</th><th>結果</th>'
            f'<th>{escape(a)}</th></tr></thead><tbody>{rows}</tbody></table></section>')


def preview_sections(m, matches, standings) -> str:
    """未実施試合向けの分析セクション（今季成績・直近の試合）。"""
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
                 '<table><thead><tr><th>チーム</th><th>順位</th><th>勝点</th>'
                 '<th>勝-分-敗</th><th>得失</th></tr></thead>'
                 f'<tbody>{rows}</tbody></table></section>')
    for t in (m["home"], m["away"]):
        rec = recent_results(t, matches)
        if not rec:
            continue
        rows = "".join(
            f'<tr><td>{date_jp(x["date"])}</td><td>{result_mark(x, t)}</td>'
            f'<td>{escape(x["home"])} {x["home_score"]} - {x["away_score"]} {escape(x["away"])}</td></tr>'
            for x in rec)
        body += (f'<section><h2>{escape(t)}の直近の試合</h2>'
                 '<table><thead><tr><th>日付</th><th>勝敗</th><th>結果</th></tr></thead>'
                 f'<tbody>{rows}</tbody></table></section>')
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


def page(rel: str, title: str, body: str, meta, extra_head: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
{extra_head}
<link rel="stylesheet" href="{rel}style.css">
</head>
<body>
<header class="site-header">
  <a class="brand" href="{rel}index.html">ラクロスマニア<span class="by">関東学生ラクロス情報</span></a>
</header>
<main>
{body}
</main>
<footer class="site-footer">
  <p>試合データ出典: <a href="{escape(meta['source_url'])}">{escape(meta['source'])}</a>
  （連盟データ更新日: {escape(meta['source_updated_at'])} / 本サイト自動更新: {escape(meta['fetched_at'][:10])}）</p>
  <p>ラクロスマニアは大学ラクロスの情報メディアです。試合結果は自動収集のため、確定情報は連盟公式をご確認ください。順位・成績の集計値は試合結果からの自動算出です。</p>
</footer>
</body>
</html>"""


def match_row(m, rel: str, hide_team: str | None = None) -> str:
    link = f'{rel}matches/{m["id"]}/index.html'
    label = f'{m["home"]} vs {m["away"]}'
    return (f'<tr><td>{date_jp(m["date"])}</td><td>{escape(m["time"])}</td>'
            f'<td>{escape(m["category"])}</td>'
            f'<td><a href="{link}">{escape(label)}</a></td>'
            f'<td class="score">{score_str(m)}</td>'
            f'<td class="venue">{escape(m["venue"])}</td></tr>')


MATCH_TABLE_HEAD = ('<table><thead><tr><th>日付</th><th>時間</th><th>カテゴリ</th>'
                    '<th>対戦</th><th>スコア</th><th>会場</th></tr></thead><tbody>')


def standings_table(block: str, entries, rel: str) -> str:
    rows = "".join(
        f'<tr><td>{e["rank"]}</td>'
        f'<td><a href="{rel}clubs/{e["slug"]}/index.html">{escape(e["team"])}</a></td>'
        f'<td>{e["points"]}</td><td>{e["games"]}</td>'
        f'<td>{e["wins"]}-{e["draws"]}-{e["losses"]}</td>'
        f'<td>{escape(str(e["goal_diff"]))}</td></tr>'
        for e in entries)
    return (f'<h3>{escape(block)}</h3>'
            '<table><thead><tr><th>順位</th><th>チーム</th><th>勝点</th>'
            '<th>試合</th><th>勝-分-敗</th><th>得失</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>')


def build_index(matches, standings, meta):
    from datetime import date
    today = date.today().isoformat()
    rel = ""
    played = [m for m in matches if m["status"] == "played"]
    scheduled = [m for m in matches if m["status"] == "scheduled"]
    upcoming = [m for m in scheduled if m["date"] and m["date"] >= today][:10]
    awaiting = [m for m in scheduled if m["date"] and m["date"] < today]
    recent = list(reversed(played))[:10]

    body = f'<h1>{escape(meta["league"])}</h1>'
    body += '<section><h2>最新の試合結果</h2>' + MATCH_TABLE_HEAD
    body += "".join(match_row(m, rel) for m in recent) + "</tbody></table></section>"
    body += '<section><h2>今後の試合日程</h2>' + MATCH_TABLE_HEAD
    body += "".join(match_row(m, rel) for m in upcoming) + "</tbody></table></section>"
    if awaiting:
        body += ('<section><h2>結果反映待ちの試合</h2>'
                 '<p class="club-lead">連盟データにまだスコアが入力されていない実施済み日程（延期の可能性あり）。</p>'
                 + MATCH_TABLE_HEAD
                 + "".join(match_row(m, rel) for m in awaiting)
                 + "</tbody></table></section>")
    body += '<section><h2>星取表</h2>'
    for block, entries in standings.items():
        body += standings_table(block, entries, rel)
    body += "</section>"
    (SITE / "index.html").write_text(
        page(rel, f'{meta["league"]} 試合結果・日程 | ラクロスマニア', body, meta),
        encoding="utf-8")


def build_club_pages(matches, standings, teams, meta, hist):
    rel = "../../"
    for team, info in teams.items():
        slug, block = info["slug"], info["block"]
        is_univ = "大学" in team
        club_name = f'{team}男子ラクロス部' if is_univ else f'{team}（男子ラクロス）'
        my_matches = [m for m in matches if m["home"] == team or m["away"] == team]
        my_played = [m for m in my_matches if m["status"] == "played"]
        my_upcoming = [m for m in my_matches if m["status"] == "scheduled"]
        entry = next((e for e in standings.get(block, []) if e["team"] == team), None)

        body = f'<p class="breadcrumb"><a href="{rel}index.html">リーグトップ</a> › {escape(club_name)}</p>'
        body += f'<h1>{escape(club_name)}</h1>'
        body += f'<p class="club-lead">第38回関東学生ラクロスリーグ戦 {escape(block)} 所属。</p>'
        if entry:
            body += ('<section><h2>現在の戦績</h2><div class="stat-row">'
                     f'<div class="stat"><span class="num">{entry["rank"]}</span>位</div>'
                     f'<div class="stat"><span class="num">{entry["points"]}</span>勝ち点</div>'
                     f'<div class="stat"><span class="num">{entry["wins"]}-{entry["draws"]}-{entry["losses"]}</span>勝-分-敗</div>'
                     f'<div class="stat"><span class="num">{escape(str(entry["goal_diff"]))}</span>得失点差</div>'
                     '</div></section>')
        if my_played:
            body += '<section><h2>試合結果</h2>' + MATCH_TABLE_HEAD
            body += "".join(match_row(m, rel) for m in reversed(my_played))
            body += "</tbody></table></section>"
        if my_upcoming:
            body += '<section><h2>今後の日程</h2>' + MATCH_TABLE_HEAD
            body += "".join(match_row(m, rel) for m in my_upcoming)
            body += "</tbody></table></section>"
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
                     '<table><thead><tr><th>年度</th><th>所属</th><th>順位</th>'
                     '<th>勝-分-敗</th><th>総得点-総失点</th></tr></thead>'
                     f'<tbody>{season_rows}</tbody></table>'
                     '<p class="club-lead">※順位はブロック内リーグ戦の結果から自動算出した参考値です。</p></section>')
        body += ('<section class="placeholder"><h2>関連記事</h2>'
                 '<p class="todo">（取材記事・特集記事への内部リンクをここに配置）</p></section>')
        body += ('<section class="placeholder"><h2>Instagram</h2>'
                 '<p class="todo">（部活公式アカウントの公開投稿の公式埋め込みをここに配置）</p></section>')
        body += ('<section class="sponsor"><h2>この部活を応援する企業</h2>'
                 '<p class="todo">（協賛メニュー連携枠：スポンサー企業ロゴ・リンクをここに配置）</p>'
                 '<p><a class="cta" href="#">協賛について問い合わせる →</a></p></section>')

        out = SITE / "clubs" / slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        title = f'{club_name} 試合結果・日程・戦績 | ラクロスマニア'
        out.write_text(page(rel, title, body, meta), encoding="utf-8")


def build_match_pages(matches, standings, meta, matches_by_year):
    rel = "../../"
    for m in matches:
        body = (f'<p class="breadcrumb"><a href="{rel}index.html">リーグトップ</a> › '
                f'{escape(m["category"])}</p>')
        body += f'<h1>{escape(match_headline(m))}</h1>'
        body += f'<p class="report">{escape(match_report(m, standings))}</p>'
        if m["status"] == "scheduled":
            body += preview_sections(m, matches, standings)
        body += h2h_section(m, matches_by_year, rel)
        body += ('<table class="detail"><tbody>'
                 f'<tr><th>日付</th><td>{date_jp(m["date"], with_year=True)}</td></tr>'
                 f'<tr><th>時間</th><td>{escape(m["time"])}</td></tr>'
                 f'<tr><th>カテゴリ</th><td>{escape(m["category"])}</td></tr>'
                 f'<tr><th>会場</th><td>{escape(m["venue"])}</td></tr>'
                 f'<tr><th>スコア</th><td>{score_str(m)}</td></tr>'
                 '</tbody></table>')
        body += ('<p class="links">'
                 f'<a href="{rel}clubs/{m["home_slug"]}/index.html">{escape(m["home"])}のページ</a> / '
                 f'<a href="{rel}clubs/{m["away_slug"]}/index.html">{escape(m["away"])}のページ</a></p>')
        out = SITE / "matches" / m["id"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        title = match_headline(m) + " | ラクロスマニア"
        out.write_text(
            page(rel, title, body, meta, extra_head=jsonld_sports_event(m)),
            encoding="utf-8")


STYLE = """
:root { --ink:#1c2733; --sub:#5b6b7b; --line:#dde4ea; --accent:#0f6f5c; --bg:#f7f9fa; }
* { box-sizing:border-box; }
body { margin:0; font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",Meiryo,sans-serif;
  color:var(--ink); background:var(--bg); line-height:1.7; }
.site-header { background:#fff; border-bottom:1px solid var(--line); padding:.7rem 1rem; }
.brand { font-weight:700; color:var(--ink); text-decoration:none; font-size:1.05rem; }
.brand .by { font-size:.75rem; color:var(--accent); margin-left:.5em; font-weight:600; }
main { max-width:860px; margin:0 auto; padding:1rem 1rem 3rem; }
h1 { font-size:1.35rem; line-height:1.4; }
h2 { font-size:1.05rem; border-left:4px solid var(--accent); padding-left:.5em; margin-top:2.2em; }
h3 { font-size:.95rem; margin-top:1.6em; }
section > table, table.detail { width:100%; border-collapse:collapse; background:#fff;
  font-size:.85rem; }
th, td { border:1px solid var(--line); padding:.45em .6em; text-align:left; }
thead th { background:#eef2f5; font-weight:600; white-space:nowrap; }
td.score { white-space:nowrap; font-weight:700; }
td.venue { color:var(--sub); font-size:.8rem; }
a { color:var(--accent); }
.breadcrumb { font-size:.8rem; color:var(--sub); }
.club-lead { color:var(--sub); }
.stat-row { display:flex; gap:.8rem; flex-wrap:wrap; }
.stat { background:#fff; border:1px solid var(--line); border-radius:8px;
  padding:.6rem 1rem; font-size:.75rem; color:var(--sub); min-width:96px; text-align:center; }
.stat .num { display:block; font-size:1.3rem; font-weight:700; color:var(--ink); }
.report { background:#fff; border:1px solid var(--line); border-radius:8px; padding:1rem; }
.placeholder .todo, .sponsor .todo { color:var(--sub); background:#fff;
  border:1px dashed var(--line); border-radius:8px; padding:.8rem; font-size:.85rem; }
.sponsor .cta { font-weight:700; }
.site-footer { border-top:1px solid var(--line); color:var(--sub); font-size:.75rem;
  padding:1rem; max-width:860px; margin:0 auto; }
table { display:block; overflow-x:auto; }
@media (min-width:700px){ table { display:table; overflow:visible; } }
"""


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    matches = load("matches")
    standings = load("standings")
    teams = load("teams")
    meta = load("meta")

    hist = load_history()
    matches_by_year = ([(meta["season_year"], matches)]
                       + [(h["year"], h["matches"]) for h in hist])

    (SITE / "style.css").write_text(STYLE, encoding="utf-8")
    build_index(matches, standings, meta)
    build_club_pages(matches, standings, teams, meta, hist)
    build_match_pages(matches, standings, meta, matches_by_year)

    n_pages = 1 + len(teams) + len(matches)
    print(f"OK: {n_pages} pages generated in {SITE}")


if __name__ == "__main__":
    main()
