# -*- coding: utf-8 -*-
"""JLA公式スプレッドシートから全国7地区×男女=14リーグの日程・結果を取得し、
data/leagues/<code>/ に正規化JSONとして保存する。

データ出典: 公益社団法人日本ラクロス協会 (https://www.lacrosse.gr.jp/)
全リーグが同一スプレッドシートの別タブ（gid違い・同一列構成）で管理されている。
gid一覧の出典・検証記録は docs/data-sources.md を参照。
"""
import csv
import io
import json
import re
import sys
import urllib.request
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from team_slugs import slug_for

SHEET_ID = "1k7Yxty0ylKVp7TbmlAMwcHOCVXprQRsHMDPD31MEGnw"
SEASON_YEAR = 2026
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "leagues"

LEAGUES = {
    "kanto-m":      {"region": "関東",   "gender": "男子", "gid": "1768695961"},
    "kanto-w":      {"region": "関東",   "gender": "女子", "gid": "2122775238"},
    "kansai-m":     {"region": "関西",   "gender": "男子", "gid": "215098765"},
    "kansai-w":     {"region": "関西",   "gender": "女子", "gid": "228060780"},
    "tokai-m":      {"region": "東海",   "gender": "男子", "gid": "853859232"},
    "tokai-w":      {"region": "東海",   "gender": "女子", "gid": "1401747396"},
    "hokkaido-m":   {"region": "北海道", "gender": "男子", "gid": "531041111"},
    "hokkaido-w":   {"region": "北海道", "gender": "女子", "gid": "140891479"},
    "tohoku-m":     {"region": "東北",   "gender": "男子", "gid": "1795521138"},
    "tohoku-w":     {"region": "東北",   "gender": "女子", "gid": "47363138"},
    "chushikoku-m": {"region": "中四国", "gender": "男子", "gid": "392009888"},
    "chushikoku-w": {"region": "中四国", "gender": "女子", "gid": "2113993352"},
    "kyushu-m":     {"region": "九州",   "gender": "男子", "gid": "2086821834"},
    "kyushu-w":     {"region": "九州",   "gender": "女子", "gid": "1689984693"},
}

SCORE_RE = re.compile(r"^(\d+)\s*[-−]\s*(\d+)$")
DATE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})")
# リーグ戦（総当たり）扱いするカテゴリ。決勝・プレーオフ・入替戦などは順位計算から除外
BLOCK_RE = re.compile(r"^(\d部( [A-C]ブロック)?|リーグ|レギュラー)$")


def fetch_csv(gid: str, retries: int = 3) -> list[list[str]]:
    import time
    url = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export"
        f"?format=csv&gid={gid}"
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as res:
                return list(csv.reader(io.StringIO(res.read().decode("utf-8"))))
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt == retries - 1:
                raise
            print(f"[warn] fetch failed ({e}), retrying in {15 * (attempt + 1)}s...", file=sys.stderr)
            import time as _t
            _t.sleep(15 * (attempt + 1))


def norm_category(raw: str) -> str:
    """「1部A」「1部 Aブロック」「1部」等の表記ゆれを正規化する。"""
    s = raw.strip()
    m = re.match(r"^(\d)部\s*([A-C])(ブロック)?$", s)
    if m:
        return f"{m.group(1)}部 {m.group(2)}ブロック"
    return s


def parse_results(rows: list[list[str]]) -> tuple[list[dict], str, str]:
    """日程表&結果タブをパースし (試合リスト, リーグ名, 連盟更新日) を返す。"""
    matches = []
    league_title = ""
    updated_at = ""
    current_date = None
    in_body = False
    for row in rows:
        cells = [c.strip() for c in row]
        if len(cells) < 10:
            cells += [""] * (10 - len(cells))
        _, d, t, category, _, home, away, venue, score, note = cells[:10]

        joined = ",".join(cells)
        if not league_title:
            for c in cells:
                if re.search(r"第\d+回.+リーグ戦", c):
                    league_title = re.sub(r"[\s　]+", " ", c).strip()
                    break
        m_upd = re.search(r"更新日：(\d{4})年(\d{1,2})月(\d{1,2})日", joined)
        if m_upd:
            updated_at = f"{m_upd.group(1)}-{int(m_upd.group(2)):02d}-{int(m_upd.group(3)):02d}"

        if d == "日付" and home == "HOMEチーム":
            in_body = True
            continue
        if not in_body or not (home and away):
            continue

        m_date = DATE_RE.match(d)
        if m_date:
            try:
                current_date = date(SEASON_YEAR, int(m_date.group(1)), int(m_date.group(2)))
            except ValueError:
                pass
        m_score = SCORE_RE.match(score)
        matches.append({
            "id": f"{current_date.isoformat() if current_date else 'tbd'}-{slug_for(home)}-vs-{slug_for(away)}",
            "date": current_date.isoformat() if current_date else None,
            "time": t or "未定",
            "category": norm_category(category),
            "home": home,
            "away": away,
            "home_slug": slug_for(home),
            "away_slug": slug_for(away),
            "venue": venue or "未定",
            "status": "played" if m_score else "scheduled",
            "home_score": int(m_score.group(1)) if m_score else None,
            "away_score": int(m_score.group(2)) if m_score else None,
            "note": note,
        })
    return matches, league_title, updated_at


def compute_standings(matches: list[dict]) -> dict[str, list[dict]]:
    """ブロック内リーグ戦の結果から順位表を算出する（未消化チームも0試合で掲載）。"""
    blocks: dict[str, dict[str, dict]] = {}
    for m in matches:
        if not BLOCK_RE.match(m["category"]):
            continue
        b = blocks.setdefault(m["category"], {})
        for team in (m["home"], m["away"]):
            b.setdefault(team, {"team": team, "slug": slug_for(team), "points": 0,
                                "games": 0, "wins": 0, "draws": 0, "losses": 0,
                                "gf": 0, "ga": 0})
        if m["status"] != "played":
            continue
        for team, gf, ga in ((m["home"], m["home_score"], m["away_score"]),
                             (m["away"], m["away_score"], m["home_score"])):
            e = b[team]
            e["games"] += 1
            e["gf"] += gf
            e["ga"] += ga
            if gf > ga:
                e["wins"] += 1
                e["points"] += 3
            elif gf == ga:
                e["draws"] += 1
                e["points"] += 1
            else:
                e["losses"] += 1
    result = {}
    for block, teams in sorted(blocks.items()):
        entries = sorted(teams.values(),
                         key=lambda e: (-e["points"], -(e["gf"] - e["ga"]), -e["gf"]))
        for i, e in enumerate(entries, 1):
            e["rank"] = i
            diff = e["gf"] - e["ga"]
            e["goal_diff"] = f"+{diff}" if diff > 0 else str(diff)
            e["goals_for"] = e["gf"]
        result[block] = entries
    return result


def build_teams(matches: list[dict]) -> dict[str, dict]:
    """全試合からチーム一覧を作る。所属ブロックは出場カテゴリの最頻値。"""
    cats: dict[str, Counter] = {}
    for m in matches:
        for team in (m["home"], m["away"]):
            if BLOCK_RE.match(m["category"]):
                cats.setdefault(team, Counter())[m["category"]] += 1
    return {
        team: {"team": team, "slug": slug_for(team), "block": counter.most_common(1)[0][0]}
        for team, counter in cats.items()
    }


def main() -> None:
    ok = 0
    for code, cfg in LEAGUES.items():
        out_dir = DATA_DIR / code
        try:
            rows = fetch_csv(cfg["gid"])
            matches, league_title, updated_at = parse_results(rows)
        except Exception as e:
            if (out_dir / "matches.json").exists():
                print(f"{code}: fetch失敗のため既存データを維持 ({e})", file=sys.stderr)
                continue
            print(f"{code}: fetch失敗・既存データなし ({e})", file=sys.stderr)
            continue
        if not matches:
            print(f"{code}: 試合データ0件のためスキップ", file=sys.stderr)
            continue
        standings = compute_standings(matches)
        teams = build_teams(matches)
        meta = {
            "code": code,
            "region": cfg["region"],
            "gender": cfg["gender"],
            "league": league_title or f'{cfg["region"]}学生ラクロスリーグ戦（{cfg["gender"]}）',
            "season_year": SEASON_YEAR,
            "source": "公益社団法人日本ラクロス協会",
            "source_url": "https://www.lacrosse.gr.jp/event/2026-collegiate-leagues/",
            "source_updated_at": updated_at,
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
        }
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "matches.json").write_text(
            json.dumps(matches, ensure_ascii=False, indent=1), encoding="utf-8")
        (out_dir / "standings.json").write_text(
            json.dumps(standings, ensure_ascii=False, indent=1), encoding="utf-8")
        (out_dir / "teams.json").write_text(
            json.dumps(teams, ensure_ascii=False, indent=1), encoding="utf-8")
        (out_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        played = sum(1 for m in matches if m["status"] == "played")
        print(f"{code}: {meta['league']} 試合{len(matches)}件(結果{played}) "
              f"チーム{len(teams)} ブロック{len(standings)} 更新{updated_at}")
        ok += 1
    print(f"done: {ok}/{len(LEAGUES)} leagues")


if __name__ == "__main__":
    main()
