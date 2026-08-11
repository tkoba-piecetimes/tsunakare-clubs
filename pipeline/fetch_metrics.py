# -*- coding: utf-8 -*-
"""GA4とSearch Consoleからリリース後の実数を取得し data/metrics.json に保存する。

認証: Workload Identity連携（鍵レス）。GitHub Actions上でのみ動作する。
環境変数 GOOGLE_APPLICATION_CREDENTIALS に google-github-actions/auth が生成する
一時クレデンシャルファイルのパスが入っている前提（未設定ならスキップして正常終了）。
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

RELEASE_DATE = "2026-08-09"  # lacrossemania.jp 公開日
GA4_PROPERTY_ID = "549194490"
GSC_SITE = "sc-domain:lacrossemania.jp"

OUT = Path(__file__).resolve().parent.parent / "data" / "metrics.json"


def main() -> None:
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("GOOGLE_APPLICATION_CREDENTIALS未設定のためメトリクス取得をスキップ")
        return

    import google.auth
    from google.auth.transport.requests import AuthorizedSession

    creds, _ = google.auth.default(scopes=[
        "https://www.googleapis.com/auth/analytics.readonly",
        "https://www.googleapis.com/auth/webmasters.readonly",
    ])
    session = AuthorizedSession(creds)
    today = date.today().isoformat()
    metrics = {"updated_at": today, "release_date": RELEASE_DATE}

    # ---- GA4 Data API
    try:
        res = session.post(
            f"https://analyticsdata.googleapis.com/v1beta/properties/{GA4_PROPERTY_ID}:runReport",
            json={
                "dateRanges": [{"startDate": RELEASE_DATE, "endDate": today}],
                "dimensions": [{"name": "date"}],
                "metrics": [{"name": "activeUsers"}, {"name": "screenPageViews"},
                            {"name": "sessions"}],
                "orderBys": [{"dimension": {"dimensionName": "date"}}],
            },
            timeout=30,
        )
        res.raise_for_status()
        data = res.json()
        daily = [
            {"date": r["dimensionValues"][0]["value"],
             "users": int(r["metricValues"][0]["value"]),
             "pageviews": int(r["metricValues"][1]["value"]),
             "sessions": int(r["metricValues"][2]["value"])}
            for r in data.get("rows", [])
        ]
        metrics["ga"] = {
            "daily": daily,
            "total_users": sum(d["users"] for d in daily),
            "total_pageviews": sum(d["pageviews"] for d in daily),
            "total_sessions": sum(d["sessions"] for d in daily),
        }
        print(f"GA4: {len(daily)}日分 users計{metrics['ga']['total_users']}")
    except Exception as e:
        print(f"[warn] GA4取得失敗: {e}", file=sys.stderr)

    # ---- Search Console API
    try:
        from urllib.parse import quote
        base = f"https://searchconsole.googleapis.com/webmasters/v3/sites/{quote(GSC_SITE, safe='')}/searchAnalytics/query"
        res = session.post(base, json={
            "startDate": RELEASE_DATE, "endDate": today, "dimensions": ["date"],
        }, timeout=30)
        res.raise_for_status()
        rows = res.json().get("rows", [])
        daily = [
            {"date": r["keys"][0], "clicks": int(r["clicks"]),
             "impressions": int(r["impressions"]),
             "position": round(r["position"], 1)}
            for r in rows
        ]
        gsc = {
            "daily": daily,
            "total_clicks": sum(d["clicks"] for d in daily),
            "total_impressions": sum(d["impressions"] for d in daily),
        }
        res = session.post(base, json={
            "startDate": RELEASE_DATE, "endDate": today, "dimensions": ["query"],
            "rowLimit": 10,
        }, timeout=30)
        res.raise_for_status()
        gsc["top_queries"] = [
            {"query": r["keys"][0], "clicks": int(r["clicks"]),
             "impressions": int(r["impressions"])}
            for r in res.json().get("rows", [])
        ]
        metrics["gsc"] = gsc
        print(f"GSC: {len(daily)}日分 clicks計{gsc['total_clicks']}")
    except Exception as e:
        print(f"[warn] GSC取得失敗: {e}", file=sys.stderr)

    OUT.write_text(json.dumps(metrics, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK: {OUT}")


if __name__ == "__main__":
    main()
