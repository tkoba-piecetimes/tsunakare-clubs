# -*- coding: utf-8 -*-
"""過去年度のリーグ戦結果をJLA公開スプレッドシートから取得し、data/history/{year}.json に保存する。

年度ごとにシートの列構成が異なるため、年度別パーサを持つ。
順位表は公式星取表を解析せず、試合結果から算出する（勝ち3点・分け1点、得失点差→総得点の順）。
"""
import csv
import io
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

from team_slugs import slug_for

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "leagues" / "kanto-m" / "history"

HISTORY = {
    2025: {
        "league": "第37回関東学生ラクロスリーグ戦（男子）",
        "sheet": "14J3iH_vZt9WS-5ZADV72kXzF70zP8rWMcOuc2bAYMWw",
        "gid": "0",
        "fmt": "v2025",
    },
    2024: {
        "league": "第36回関東学生ラクロスリーグ戦（男子）",
        "sheet": "12EQfq0BWkRNINalFCePgbUSQWYaHr5sAYvi54DPd5Lk",
        "gid": "0",
        "fmt": "v2024",
    },
    2023: {
        "league": "第35回関東学生ラクロスリーグ戦（男子）",
        "sheet": "1eFtUFUPBd_sy6P0vWmza_0jiQTAlMb2p8FjUIhlcJvs",
        "gid": "0",
        "fmt": "v2023",
    },
}

BLOCK_RE = re.compile(r"^(\d)部\s*([A-C])(ブロック)?$")


def fetch_csv(sheet_id: str, gid: str, retries: int = 3) -> list[list[str]]:
    import time
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as res:
                return list(csv.reader(io.StringIO(res.read().decode("utf-8"))))
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt == retries - 1:
                raise
            print(f"[warn] fetch failed ({e}), retrying in {15 * (attempt + 1)}s...", file=sys.stderr)
            time.sleep(15 * (attempt + 1))


def norm_category(raw: str) -> str:
    m = BLOCK_RE.match(raw.strip())
    if m:
        return f"{m.group(1)}部 {m.group(2)}ブロック"
    return raw.strip()


JUNK_TEAMS = {"雨天予備枠"}


def normalize_team(name: str):
    """年度による表記ゆれを正規化する（略称・注記・異体字・ダミー行）。"""
    from team_slugs import TEAM_SLUGS
    n = re.sub(r"[（(].*?[）)]\s*$", "", name.strip()).strip()
    if not n or n in JUNK_TEAMS:
        return None
    if n in TEAM_SLUGS:
        return n
    if n + "大学" in TEAM_SLUGS:
        return n + "大学"
    aliases = {"独協": "獨協大学", "国士館": "国士舘大学"}
    if n in aliases:
        return aliases[n]
    return n


def make_match(year, month, day, time, cat, home, away, venue, hs, as_, note):
    home, away = normalize_team(home), normalize_team(away)
    if not home or not away:
        return None
    try:
        d = date(year, int(month), int(day)).isoformat()
    except (ValueError, TypeError):
        d = None
    played = hs.strip().isdigit() and as_.strip().isdigit()
    return {
        "id": f"{d or 'tbd'}-{slug_for(home)}-vs-{slug_for(away)}",
        "date": d,
        "time": time.strip() or "未定",
        "category": norm_category(cat),
        "home": home.strip(),
        "away": away.strip(),
        "venue": venue.strip() or "未定",
        "status": "played" if played else "scheduled",
        "home_score": int(hs) if played else None,
        "away_score": int(as_) if played else None,
        "note": note.strip(),
    }


def parse_v2025(rows, year):
    """列: 1=月 2=日 3=曜 4=FO時刻 5=カテゴリ 6=ラウンド 7=HOME 8=AWAY 9=会場 10=得点H 11='-' 12=得点A 13=備考"""
    matches, month = [], None
    for row in rows:
        c = [x.strip() for x in row] + [""] * (14 - len(row))
        if c[1].isdigit():
            month = c[1]
        if not (c[2].isdigit() and c[7] and c[8] and month):
            continue
        m = make_match(year, month, c[2], c[4], c[5],
                       c[7], c[8], c[9], c[10], c[12], c[13])
        if m:
            matches.append(m)
    return matches


def parse_v2024(rows, year, off=1):
    """列(off=1): 1=月 2='/' 3=日 4=曜 5=時刻 6=ブロック 7=HOME 8=得点H 9='-' 10=得点A 11=AWAY 12=会場 14=備考
    2023年は同形式で先頭の空列がないため off=0。"""
    matches, month = [], None
    for row in rows:
        c = [x.strip() for x in row] + [""] * (15 + off - len(row))
        if c[off].isdigit():
            month = c[off]
        if not (c[off + 2].isdigit() and c[off + 6] and c[off + 10] and month):
            continue
        m = make_match(year, month, c[off + 2], c[off + 4], c[off + 5],
                       c[off + 6], c[off + 10], c[off + 11],
                       c[off + 7], c[off + 9], c[off + 13])
        if m:
            matches.append(m)
    return matches


def parse_v2023(rows, year):
    return parse_v2024(rows, year, off=0)


PARSERS = {"v2025": parse_v2025, "v2024": parse_v2024, "v2023": parse_v2023}


def compute_standings(matches):
    """ブロック内リーグ戦（プレーオフ・入替戦除く）から順位表を算出する。"""
    blocks: dict[str, dict[str, dict]] = {}
    for m in matches:
        if m["status"] != "played" or not re.match(r"^\d部 [A-C]ブロック$", m["category"]):
            continue
        b = blocks.setdefault(m["category"], {})
        for team, gf, ga in ((m["home"], m["home_score"], m["away_score"]),
                             (m["away"], m["away_score"], m["home_score"])):
            e = b.setdefault(team, {"team": team, "slug": slug_for(team), "points": 0,
                                    "games": 0, "wins": 0, "draws": 0, "losses": 0,
                                    "gf": 0, "ga": 0})
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


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for year, src in HISTORY.items():
        try:
            rows = fetch_csv(src["sheet"], src["gid"])
        except Exception as e:
            if (DATA_DIR / f"{year}.json").exists():
                print(f"{year}: fetch失敗のため既存データを維持 ({e})", file=sys.stderr)
                continue
            raise
        matches = PARSERS[src["fmt"]](rows, year)
        standings = compute_standings(matches)
        out = {
            "year": year,
            "league": src["league"],
            "matches": matches,
            "standings": standings,
        }
        (DATA_DIR / f"{year}.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        played = sum(1 for m in matches if m["status"] == "played")
        print(f"{year}: {len(matches)} matches ({played} played), "
              f"{len(standings)} blocks -> data/history/{year}.json")


if __name__ == "__main__":
    main()
