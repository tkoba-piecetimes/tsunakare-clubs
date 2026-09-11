"""Historical database views backed by immutable, attributed season snapshots."""
import json
from html import escape as e
from urllib.parse import urlencode

def link(code, **params):
    return '/archive/?'+urlencode({'league':code,**params})

def load(data):
    p=data/'history-archive.json'
    return json.loads(p.read_text(encoding='utf8')) if p.exists() else {'from_year':2021,'seasons':[]}

def team_history(lg,team):
    rows=''
    for h in lg['hist']:
        ms=[m for m in h['matches'] if m['status']=='played' and team in (m['home'],m['away'])]
        if not ms: continue
        scores=[(m['home_score'],m['away_score']) if team==m['home'] else (m['away_score'],m['home_score']) for m in ms]
        wins=sum(a>b for a,b in scores);draws=sum(a==b for a,b in scores)
        cats='・'.join(sorted({m['category'] for m in ms if m['category']!='区分未記載'}))
        rows+=f'<tr><td><a href="{e(link(lg["code"],year=h["year"],team=team))}">{h["year"]}年 →</a></td><td>{len(ms)}</td><td>{wins}勝{draws}分{len(ms)-wins-draws}敗</td><td>{sum(a for a,b in scores)} − {sum(b for a,b in scores)}</td><td>{e(cats) or "公式資料を参照"}</td></tr>'
    if not rows: return ''
    return ('<section class="archive-team-history"><h2>2021年からの年度別記録</h2>'
        '<p>収録した試合結果からの集計です。プレーオフ・入替戦・不戦勝等の公式記録を含みます。</p>'
        '<div class="tbl"><table><thead><tr><th>年度</th><th>収録試合</th><th>勝敗</th><th>得点 − 失点</th><th>掲載区分</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div><p><a href="{e(link(lg["code"],year="all",team=team))}">全年度の試合・対戦成績を見る →</a></p></section>')

def sources(h):
    return (f'<a href="{e(h["source_url"])}" target="_blank" rel="noopener">公式日程・結果 ↗</a> '
        f'<a href="{e(h["standings_url"])}" target="_blank" rel="noopener">公式順位・星取表 ↗</a>')

def build(site,leagues,meta,page,write_page):
    seasons=[]
    for l in leagues:
        for h in l['hist']:
            seasons.append({**h,'label':l['label'],'region':l['meta']['region'],'gender':l['meta']['gender']})
        seasons.append({'code':l['code'],'label':l['label'],'region':l['meta']['region'],'gender':l['meta']['gender'],
            'year':l['meta']['season_year'],'matches':l['matches'],'standings':l['standings'],
            'coverage':'current','source_url':l['meta']['source_url'],'standings_url':l['meta']['source_url'],
            'source_page':l['meta']['source_url'],'source_updated_at':l['meta']['source_updated_at'],
            'coverage_note':'今シーズンの公式公表データを毎日更新。','date_unconfirmed':0})
    (site/'assets'/'archive-data.json').write_text(json.dumps({'from_year':2021,'current_year':meta['season_year'],'seasons':seasons},ensure_ascii=False,separators=(',',':')),encoding='utf8')
    indexed=''.join(f'<li><a href="/{s["code"]}/seasons/{s["year"]}/">{s["year"]}年 {e(s["label"])}（{len(s["matches"])}試合収録）</a></li>' for s in seasons if s['year']<meta['season_year'])
    body=f'''<div class="archive-page"><div class="archive-intro"><div><p class="eyebrow">COLLEGE LACROSSE / SINCE 2021</p><h1>ラクロスの記録を、<br>つなぐ。</h1><p>あの年の母校も、ライバルとの一戦も。<br>年度・地区・大学から、全国の試合を探そう。</p></div><div class="archive-period"><strong>2021<span>—</span>{meta['season_year']}</strong><span>全国7地区 / 男子・女子</span></div></div><div id="archive-hub"><p role="status">データを読み込んでいます。</p></div><details class="archive-index"><summary>年度・地区別の記録一覧</summary><ul>{indexed}</ul></details><p class="archive-footnote">公式資料で確認できたスコアを掲載しています。未収録・日付未確認の記録があります。学校名は当時の表記を基本とし、構成が変わる合同チームは年度ごとに区別しています。</p></div>'''
    write_page('archive',page('../','2021年からの大学ラクロスデータベース | ラクロスマニア',body,meta,path='archive/',desc='2021年以降の全国大学ラクロスを年度・地区・男女・大学別に検索。過去の試合結果、年度別成績、直接対決、公式順位表へのリンクを掲載。',extra_head='<script src="/assets/archive.js" defer></script>'))
    for h in seasons:
        if h['year']>=meta['season_year']: continue
        rows=''
        for m in sorted(h['matches'],key=lambda m:m['date'] or '9999'):
            details=' / '.join(filter(None,[m['category'],m.get('note','')]))
            loc=m.get('source_locator',''); src=h['source_url']+(f'#page={loc.split(":")[1]}' if loc.startswith('page:') else '')
            rows+=(f'<tr id="match-{e(m["id"])}"><td>{e(m["date"] or "日付未確認")}</td><td>{e(m["home"])}</td>'
                f'<td class="score">{m["home_score"]} − {m["away_score"]}</td><td>{e(m["away"])}</td><td>{e(details)}</td><td><a href="{e(src)}" target="_blank" rel="noopener">出典 ↗</a></td></tr>')
        body=(f'<p class="breadcrumb"><a href="/">トップ</a> › <a href="/archive/">データベース</a></p>'
            f'<h1>{h["year"]}年 {e(h["label"])}の記録</h1><p>{len(h["matches"])}試合のスコアを収録。{e(h["coverage_note"])}</p>'
            f'<p class="archive-source-links">{sources(h)}</p><p><a class="cta" href="{e(link(h["code"],year=h["year"]))}">大学・対戦相手で絞り込む →</a></p>'
            '<div class="tbl"><table><thead><tr><th>日付</th><th>HOME</th><th>スコア</th><th>AWAY</th><th>区分・備考</th><th>公式資料</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')
        smeta={**meta,'source_url':h['source_url'],'source_updated_at':h.get('source_updated_at') or '資料内を参照'}
        write_page(f'{h["code"]}/seasons/{h["year"]}',page('../../../',f'{h["year"]}年 {h["label"]} 試合結果・過去記録 | ラクロスマニア',body,smeta,path=f'{h["code"]}/seasons/{h["year"]}/'))
