# -*- coding: utf-8 -*-
"""JLA公式スプレッドシートから関東学生ラクロスリーグ（男子）の日程・結果・星取表を取得し、
data/ 配下に正規化JSONとして保存する。

データ出典: 公益社団法人日本ラクロス協会 (https://www.lacrosse.gr.jp/)
スプレッドシートは公開設定のCSVエクスポートを利用（スコア・日程は事実情報であり著作権の対象外）。
"""
import csv
import io
import json
import re
import sys
import urllib.request
from datetime import date, datetime
from pathlib import Path

SHEET_ID = "1k7Yxty0ylKVp7TbmlAMwcHOCVXprQRsHMDPD31MEGnw"
GID_RESULTS = "1768695961"    # 男子 日程表&結果
GID_STANDINGS = "508843350"   # 男子 星取表
SEASON_YEAR = 2026
LEAGUE_NAME = "第38回関東学生ラクロスリーグ戦（男子）"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# チーム名 → URLスラッグ（部活ページのパスになる）
TEAM_SLUGS = {
    "早稲田大学": "waseda",
    "慶應義塾大学": "keio",
    "中央大学": "chuo",
    "明治大学": "meiji",
    "成蹊大学": "seikei",
    "獨協大学": "dokkyo",
    "法政大学": "hosei",
    "明治学院大学": "meijigakuin",
    "学習院大学": "gakushuin",
    "青山学院大学": "aoyamagakuin",
    "日本体育大学": "nittaidai",
    "一橋大学": "hitotsubashi",
    "成城大学": "seijo",
    "東京農業大学": "tokyo-nodai",
    "東京大学": "tokyo",
    "東洋大学": "toyo",
    "千葉大学": "chiba",
    "帝京大学": "teikyo",
    "武蔵大学": "musashi",
    "横浜国立大学": "yokohama-kokudai",
    "立教大学": "rikkyo",
    "東海大学": "tokai",
    "国士舘大学": "kokushikan",
    "東京学芸大学": "tokyo-gakugei",
    "神奈川大学": "kanagawa",
    "東京理科大学": "tokyo-rika",
    "上智大学": "sophia",
    "埼玉大学": "saitama",
    "慶應義塾高校": "keio-hs",
    "筑波大学": "tsukuba",
    "明星大学": "meisei",
    "東京経済大学": "tokyo-keizai",
    "大東文化大学": "daitobunka",
    "専修大学": "senshu",
    "駒澤大学": "komazawa",
    "城西・関東学院": "josai-kantogakuin",
    "日本大学": "nihon",
}

SCORE_RE = re.compile(r"^(\d+)\s*[-−]\s*(\d+)$")
DATE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})")


def fetch_csv(gid: str) -> list[list[str]]:
    url = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export"
        f"?format=csv&gid={gid}"
    )
    with urllib.request.urlopen(url, timeout=30) as res:
        text = res.read().decode("utf-8")
    return list(csv.reader(io.StringIO(text)))


def slug_for(team: str) -> str:
    if team not in TEAM_SLUGS:
        # 未知チーム（合同チーム再編等）はビルドを止めず警告してフォールバック
        print(f"[warn] 未登録のチーム名: {team}", file=sys.stderr)
        return f"team-{abs(hash(team)) % 10**8}"
    return TEAM_SLUGS[team]


def parse_results(rows: list[list[str]]) -> tuple[list[dict], str]:
    matches = []
    updated_at = ""
    current_date = None
    in_body = False
    for row in rows:
        cells = [c.strip() for c in row]
        if len(cells) < 10:
            cells += [""] * (10 - len(cells))
        _, d, t, category, _, home, away, venue, score, note = cells[:10]

        if d == "日付" and home == "HOMEチーム":
            in_body = True
            continue
        m_upd = re.search(r"更新日：(\d{4})年(\d{1,2})月(\d{1,2})日", ",".join(cells))
        if m_upd:
            updated_at = f"{m_upd.group(1)}-{int(m_upd.group(2)):02d}-{int(m_upd.group(3)):02d}"
        if not in_body or not (home and away):
            continue

        m_date = DATE_RE.match(d)
        if m_date:
            current_date = date(SEASON_YEAR, int(m_date.group(1)), int(m_date.group(2)))

        m_score = SCORE_RE.match(score)
        status = "played" if m_score else "scheduled"
        matches.append({
            "id": f"{current_date.isoformat() if current_date else 'tbd'}-{slug_for(home)}-vs-{slug_for(away)}",
            "date": current_date.isoformat() if current_date else None,
            "time": t or "未定",
            "category": category,          # 例: "1部 Bブロック"
            "home": home,
            "away": away,
            "home_slug": slug_for(home),
            "away_slug": slug_for(away),
            "venue": venue or "未定",
            "status": status,
            "home_score": int(m_score.group(1)) if m_score else None,
            "away_score": int(m_score.group(2)) if m_score else None,
            "note": note,
        })
    return matches, updated_at


def parse_standings(rows: list[list[str]]) -> dict[str, list[dict]]:
    blocks: dict[str, list[dict]] = {}
    current_block = None
    for row in rows:
        cells = [c.strip() for c in row]
        if len(cells) < 10:
            cells += [""] * (10 - len(cells))
        col1, col2 = cells[1], cells[2]
        if re.match(r"^\d部\s*[A-C]ブロック$", col1):
            current_block = col1
            blocks[current_block] = []
            continue
        if current_block and col1.isdigit() and col2:
            blocks[current_block].append({
                "rank": int(col1),
                "team": col2,
                "slug": slug_for(col2),
                "points": int(cells[3] or 0),
                "games": int(cells[4] or 0),
                "wins": int(cells[5] or 0),
                "draws": int(cells[6] or 0),
                "losses": int(cells[7] or 0),
                "goal_diff": cells[8],
                "goals_for": int(cells[9] or 0),
            })
    return blocks


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    results_rows = fetch_csv(GID_RESULTS)
    standings_rows = fetch_csv(GID_STANDINGS)

    matches, updated_at = parse_results(results_rows)
    standings = parse_standings(standings_rows)

    teams = {}
    for block, entries in standings.items():
        for e in entries:
            teams[e["team"]] = {"team": e["team"], "slug": e["slug"], "block": block}

    meta = {
        "league": LEAGUE_NAME,
        "season_year": SEASON_YEAR,
        "source": "公益社団法人日本ラクロス協会",
        "source_url": "https://www.lacrosse.gr.jp/event/2026-collegiate-leagues/",
        "source_updated_at": updated_at,
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
    }

    (DATA_DIR / "matches.json").write_text(
        json.dumps(matches, ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA_DIR / "standings.json").write_text(
        json.dumps(standings, ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA_DIR / "teams.json").write_text(
        json.dumps(teams, ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA_DIR / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

    played = sum(1 for m in matches if m["status"] == "played")
    print(f"OK: 試合 {len(matches)}件（結果あり {played}件）/ チーム {len(teams)} / 星取表 {len(standings)}ブロック / 連盟更新日 {updated_at}")


if __name__ == "__main__":
    main()
