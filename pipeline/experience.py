"""Results-first presentation, layered on the existing static publishing pipeline.

Source data, article bodies, canonical URLs and the daily fetch job remain authoritative.
University marks are editorial abbreviations, never presented as official crests.
"""
import json
import re
import hashlib
from datetime import datetime
from html import escape as e
from urllib.parse import urlencode
from zoneinfo import ZoneInfo
import archive

LEAGUES = []
ARTICLES = []
IDENTITIES = {}
TODAY = ''
REGIONS = ['全国', '関東', '関西', '東海', '北海道', '東北', '中四国', '九州']
ALIASES = {
 '早稲田大学':['早大','わせだ','waseda'], '慶應義塾大学':['慶応','慶應','慶大','けいおう','keio'],
 '日本体育大学':['日体大','にったい','nittai'], '日本大学':['日大','にちだい'],
 '明治大学':['明大','めいじ'], '明治学院大学':['明学','明学大'], '中央大学':['中大','ちゅうおう'],
 '法政大学':['法大','ほうせい'], '青山学院大学':['青学','青学大'], '東京大学':['東大','とうだい'],
 '東京農業大学':['農大','東農大'], '東京学芸大学':['学芸大','東学大'], '東京理科大学':['理科大'],
 '横浜国立大学':['横国','横国大'], '京都大学':['京大','きょうだい'], '大阪大学':['阪大','はんだい'],
 '関西大学':['関大','かんだい'], '関西学院大学':['関学','関学大'], '京都産業大学':['京産','京産大'],
 '大阪公立大学':['公立大','大阪公立'], '立命館大学':['立命','立命大'], '同志社大学':['同志社','どうししゃ'],
 '名古屋大学':['名大','めいだい'], '北海道大学':['北大','ほくだい'], '東北大学':['東北大'],
 '九州大学':['九大','きゅうだい'], '筑波大学':['筑波','つくば'], '上智大学':['上智','じょうち','sophia'],
}
MARKS = {'waseda':'WSD','meiji':'MEI','meijigakuin':'MGU','keio':'KEI','keiou':'KEI','kyoto':'KYO','kobe':'KOB','kansai':'KAN','kwansei-gakuin':'KGU','kanagawa':'KNG','kokushikan':'KKS','kindai':'KIN','komazawa':'KMZ','kyushu-univ':'KYU','kyoto-sangyo':'KSU','nittaidai':'NSS','nihon':'NUN','tokyo':'TOK','tokai':'TKI','toyo':'TOY','tohoku-univ':'THK','tohoku-gakuin':'TGU','tokyo-gakugei':'GAK','tokyo-nodai':'NOD','tokyo-rika':'TUS','tokyo-keizai':'TKU','chuo':'CHU','chukyo':'CKY','chiba':'CHB','hosei':'HOS','hokkaido':'HKD','hitotsubashi':'HIT','hiroshima':'HIR','aoyamagakuin':'AGU','gakushuin':'GKU','rikkyo':'RIK','ritsumeikan':'RIT','osaka':'OSK','osaka-keizai':'OKE','osaka-metropolitan':'OMU','doshisha':'DOS','nagoya':'NGY','nanzan':'NAN','fukuoka':'FUK','sophia':'SOP'}
COLORS = ['#395e72','#64507e','#3c6754','#802c40','#785141','#386b74']

def configure(leagues, articles, site):
    global LEAGUES, ARTICLES, IDENTITIES, TODAY
    LEAGUES, ARTICLES = leagues, articles
    # Explicit JST even when the daily job runs on UTC infrastructure.
    TODAY = datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()
    # Existing source IDs can repeat (e.g. two undecided semi-finals).
    # Keep the old URL for its final source row, and give other rows a stable suffix.
    for lg in leagues:
        groups = {}
        for m in lg['matches']: groups.setdefault(m['id'], []).append(m)
        for original, rows in groups.items():
            if len(rows)<2: continue
            counts = {}
            for m in rows[:-1]:
                signature = json.dumps([m.get(k) for k in ('date','time','category','home','away','note')],ensure_ascii=False)
                suffix = hashlib.sha1(signature.encode()).hexdigest()[:8]
                counts[suffix] = counts.get(suffix,0)+1
                m['id'] = original+'--'+suffix+(f'-{counts[suffix]}' if counts[suffix]>1 else '')
    used = {}
    teams = {t['team']:t for lg in leagues for t in lg['teams'].values()}
    names_by_identity = {}
    designs = {}
    for name,t in teams.items():
        canonical = 'keio' if t['slug']=='keiou' else t['slug']
        names_by_identity.setdefault(canonical, []).append(name)
    for i, (name, t) in enumerate(sorted(teams.items())):
        slug = t['slug']; canonical = 'keio' if slug == 'keiou' else slug
        special={'北海道科学大学':'HUS','大阪教育大学':'OKU','愛知教育大学':'AUE','愛知淑徳大学':'ASH','慶應義塾高校':'KHS','東京女子大学':'TWU','福岡教育大学':'FUE','福島大学':'FKU','慶應義塾大学':'KEI'}
        mark = special.get(name,MARKS.get(canonical, re.sub('[^a-zA-Z]', '', canonical).upper()[:3])) or 'UNI'
        if '未定' in name or '勝者' in name or '敗者' in name: mark = '—'
        elif '合同' in name or '・' in name: mark = '+'
        elif canonical in designs:
            mark = designs[canonical]
        elif mark in used and used[mark] != canonical:
            letters = re.sub('[^a-zA-Z]', '', canonical).upper()
            mark = letters[:4]
            nonce = 0
            while mark in used:
                mark = letters[:2]+hashlib.sha1((canonical+str(nonce)).encode()).hexdigest()[:2].upper()
                nonce += 1
        used[mark] = canonical
        designs[canonical] = mark
        color = {'waseda':'#802c40','meiji':'#64507e','keio':'#293e65','hosei':'#a34d2d','chuo':'#a73d43'}.get(canonical, COLORS[sum(map(ord,canonical))%len(COLORS)])
        synonyms=names_by_identity[canonical]
        aliases=list(dict.fromkeys([alias for n in synonyms for alias in ALIASES.get(n,[])]+synonyms+[slug,canonical]))
        IDENTITIES[name] = {'identity':canonical,'mark':mark,'color':color,'aliases':aliases}
    (site/'assets'/'team-identities.json').write_text(json.dumps(IDENTITIES,ensure_ascii=False),encoding='utf8')

def mark(name, size='small'):
    d = IDENTITIES.get(name, {'mark':'—','color':'#647a70'})
    return f'<span class="team-badge team-badge--{size} team-badge--pair" style="--team-color:{d["color"]}" aria-hidden="true"><span>{e(d["mark"])}</span></span>'

def header(meta):
    return '''<a class="skip" href="#main">本文へ</a><header class="site-header"><div class="header-inner"><a class="brand" href="/" aria-label="ラクロスマニア 試合結果へ"><span class="brand-mark" aria-hidden="true">L<span>M</span></span><span>ラクロスマニア<small>JAPAN COLLEGE LACROSSE</small></span></a><nav class="main-nav" aria-label="メインナビゲーション"><a href="/">試合結果</a><a href="/leagues/">リーグ・順位</a><a href="/articles/">読みもの</a><a href="/archive/">過去の記録</a><a href="/videos/">動画</a></nav><a class="myteam-link" href="/my-teams/">☆ マイチーム</a><button class="menu-button" id="menu-toggle" aria-expanded="false" aria-controls="mobile-menu">メニュー</button></div><nav id="mobile-menu" hidden aria-label="全ページ"><a href="/">試合結果</a><a href="/leagues/">リーグ・順位表</a><a href="/articles/">読みもの</a><a href="/archive/">過去の記録</a><a href="/videos/">動画</a><a href="/glossary/">用語辞典</a><a href="/#support">部活の協賛</a><a href="/contact/">お問い合わせ</a></nav></header>'''

def mobile_nav():
    return '<nav class="bottom-nav" aria-label="モバイル主要ページ"><a href="/">試合結果</a><a href="/leagues/">リーグ・順位</a><a href="/articles/">読みもの</a><a href="/my-teams/">マイチーム</a></nav><div id="toast" role="status" aria-live="polite"></div>'

def title(label, name, sub=''):
    return f'<div class="page-title"><div><div class="eyebrow">{e(label)}</div><h1>{e(name)}</h1>{f"<p>{e(sub)}</p>" if sub else ""}</div></div>'

def match_url(lg,m): return f'/{lg["code"]}/matches/{e(m["id"])}/'
def team_url(lg,t): return f'/{lg["code"]}/clubs/{e(t["slug"])}/'
def status(m):
    if m['status']=='played': return '試合終了'
    return '試合予定' if m.get('date','')>=TODAY else '結果未掲載'
def time(m): return m.get('time') if m.get('time') not in ('','0:00','00:00',None) else '時間未定'
def source(meta):
    return f'<p class="source-note">情報更新 {e(meta["fetched_at"][:10])} · <a href="{e(meta["source_url"])}" target="_blank" rel="noopener">日本ラクロス協会の公表データ</a>に基づく掲載。ライブ速報ではありません。</p>'
def minutes(value, fallback):
    m=re.fullmatch(r'(\d{1,2}):(\d{2})',value or '')
    return int(m[1])*60+int(m[2]) if m and int(m[1])<24 and int(m[2])<60 and value not in ('00:00','0:00') else fallback
def sort(rows): return sorted(rows,key=lambda x:(x.get('date') or '',minutes(x.get('time'),-1)),reverse=True)
def upcoming(rows): return sorted([m for m in rows if m['status']!='played' and m.get('date','')>=TODAY],key=lambda x:(x.get('date') or '',minutes(x.get('time'),1440)))

def card(lg,m):
    played=m['status']=='played'
    lines=''
    for side,other in [('home','away'),('away','home')]:
        win=played and m[side+'_score']>m[other+'_score']
        lines+=f'<div class="score-row"><span class="team-name {"winner" if win else ""}">{mark(m[side])}<span>{e(m[side])}</span></span><strong class="score">{m[side+"_score"] if played else "—"}</strong></div>'
    day=(m.get('date') or '日付未確認').replace('-','.')
    return f'<a class="match-card" href="{match_url(lg,m)}"><div class="match-meta"><span>{day} · {e(lg["label"])}</span><span class="state">{status(m)}</span></div>{lines}<div class="match-bottom"><span>{e(m.get("category") or "区分未記載")}</span><span>{"詳細 →" if played else e(time(m))}</span></div></a>'
def cards(lg,rows): return '<div class="match-grid">'+''.join(card(lg,m) for m in rows)+'</div>' if rows else '<p class="empty-message">該当する試合は掲載されていません。</p>'

def related(kind='watch'):
    preferred = ['lacrosse-spectator-guide','video-analysis'] if kind=='watch' else ['lacrosse-club-budget','lacrosse-club-crowdfunding-guide','lacrosse-club-sponsor-outreach']
    selected=[a for slug in preferred for a in ARTICLES if a['slug']==slug][:2]
    links=''.join(f'<a class="related-story" href="/articles/{e(a["slug"])}/"><span>{e(a["category"])}</span><strong>{e(a["title"])}</strong><b aria-hidden="true">↗</b></a>' for a in selected)
    return f'<section class="context-reading"><div class="eyebrow">AFTER THE SCORE</div><h2>{"この一戦を、もっと楽しむ。" if kind=="watch" else "チームの挑戦を、続けるために。"}</h2>{links}<div class="context-pr"><small>部活の協賛 / PR</small><a href="/#support">遠征費・用具費など、チームの活動を支える協賛について →</a></div></section>'

def league_links():
    return '<div class="league-grid">'+''.join(f'<a class="league-card" href="/{lg["code"]}/"><span class="region-number">{i//2+1:02}</span><div><span class="region-en">{lg["code"].split("-")[0].upper()}</span><h2>{e(lg["label"])}</h2><p>{len(lg["teams"])}チーム · 結果・順位・星取表</p></div></a>' for i,lg in enumerate(LEAGUES))+'</div>'

def filters(code=''):
    region = '<label class="region-select"><span class="sr-only">地区</span><select id="region" aria-label="地区">'+''.join(f'<option>{r}</option>' for r in REGIONS)+'</select></label>' if not code else ''
    sex = '<div class="segments" aria-label="男女"><button data-sex="すべて" aria-pressed="true">全て</button><button data-sex="男子" aria-pressed="false">男子</button><button data-sex="女子" aria-pressed="false">女子</button></div>' if not code else ''
    return f'<div class="compact-filters">{sex}{region}<div class="search-wrap"><label class="searchbox"><span aria-hidden="true">⌕</span><input type="search" id="team-search" role="combobox" autocomplete="off" aria-autocomplete="list" aria-expanded="false" aria-controls="team-suggestions" aria-label="大学名で検索" placeholder="大学名・略称で検索"></label><div id="team-suggestions" class="search-suggestions" role="listbox" aria-label="大学の候補" hidden></div></div></div><div class="view-tabs center-tabs"><button data-view="results" aria-pressed="true">試合結果</button><button data-view="upcoming" aria-pressed="false">日程</button><button data-view="pending" aria-pressed="false">結果未掲載</button></div>'

def center(code='',limit=12):
    leagues=[lg for lg in LEAGUES if not code or lg['code']==code]
    rows=sorted([(lg,m) for lg in leagues for m in lg['matches'] if m['status']=='played'],key=lambda x:x[1].get('date') or '',reverse=True)
    body=''.join(card(lg,m) for lg,m in rows[:limit])
    return f'<div class="match-center" data-center="{code}">{filters(code)}<div class="list-context"><h2 id="result-label">{e(leagues[0]["label"]) if code else "全国・男女"}の最新結果</h2><span id="result-count" role="status">{len(rows)}試合</span></div><div id="center-results" class="match-grid">{body}</div><button class="more" id="more-results" hidden>さらに12試合を見る</button><noscript><p>全結果は各リーグの「日程・結果」から確認できます。</p></noscript></div>'

def home(original,meta):
    support=re.search(r'<section class="support-hub".*?</section>',original,re.S)
    quiz=re.search(r'<section id="challenge".*?</section>',original,re.S)
    return title('MATCH CENTER / COLLEGE LACROSSE','試合結果')+'<section id="my-teams" class="home-picks" hidden></section>'+f'<section id="results">{center()}{source(meta)}</section>'+f'''<section class="editorial-feature"><div class="editorial-photo"><img src="/assets/hero.jpg" alt="ラクロスのフィールド" width="1440" height="768" loading="lazy"></div><div class="editorial-copy"><div class="eyebrow">FIELD NOTES / 01</div><h2>スコアの向こうに、<br>チームの物語がある。</h2><p>勝った理由も、次の一歩も。<br>観戦、戦術、チーム運営を深く読む。</p><a class="button lime" href="/articles/lacrosse-spectator-guide/">観戦の楽しみ方を読む ↗</a></div></section><section id="leagues" class="section"><div class="section-heading"><div><div class="eyebrow">7 REGIONS / 14 LEAGUES</div><h2>リーグ・順位を探す</h2></div><a href="/leagues/">すべてのリーグ →</a></div>{league_links()}</section>'''+related()+ (support.group(0) if support else '')+(quiz.group(0) if quiz else '')+'<dialog id="club-dialog"><button class="dialog-close" aria-label="閉じる">×</button><div id="dialog-body"></div></dialog>'

def follow(lg,t): return f'<button class="button outline follow" data-save="{lg["code"]}/{e(t["slug"])}" data-team-name="{e(t["team"])}" aria-pressed="false">☆ マイチームに追加</button>'
def team_stats(lg,t): return next((row for rows in lg['standings'].values() for row in rows if row['slug']==t['slug']),None)
def team_form(lg,t,n=5):
    ms=sort([m for m in lg['matches'] if m['status']=='played' and t['slug'] in (m['home_slug'],m['away_slug'])])[:n]
    items=''
    for m in reversed(ms):
        a,b=(m['home_score'],m['away_score']) if m['home_slug']==t['slug'] else (m['away_score'],m['home_score'])
        result='勝' if a>b else '敗' if a<b else '分'
        items+=f'<a class="form-{result}" href="{match_url(lg,m)}" aria-label="{e(m["date"])} {result} {a}対{b}">{result}</a>'
    return f'<div class="form-strip" aria-label="直近{len(ms)}試合・右が最新">{items}<small>→ 最新</small></div>' if ms else '<p class="source-note">試合結果は未掲載です。</p>'

def team(lg,t):
    ms=[m for m in lg['matches'] if t['slug'] in (m['home_slug'],m['away_slug'])]
    played=sort([m for m in ms if m['status']=='played']); future=upcoming(ms)
    pending=[m for m in ms if m['status']!='played' and m not in future]
    stat=team_stats(lg,t)
    body=f'<p class="bread"><a href="/{lg["code"]}/">{e(lg["label"])}リーグ</a> / チーム</p><header class="team-head">{mark(t["team"],"hero")}<div><div class="eyebrow">TEAM FILE / {e(lg["label"])}</div><h1>{e(t["team"])}</h1><p>{e(lg["meta"]["gender"])}ラクロス部 · {e(t["block"])}</p></div>{follow(lg,t)}</header>'
    body+='<div class="team-summary"><section><h2>最新の結果</h2>'+cards(lg,played[:1])+'</section><section><h2>次の試合</h2>'+cards(lg,future[:1])+'</section></div>'
    if stat:
        body+=f'<section class="team-position"><div><span class="eyebrow">{e(t["block"])} / 参考順位</span><strong>{stat["rank"]}<small>位</small></strong></div><div><span>勝ち点</span><strong>{stat["points"]}</strong></div><div><span>勝–分–敗</span><strong>{stat["wins"]}–{stat["draws"]}–{stat["losses"]}</strong></div><a href="/{lg["code"]}/standings/">リーグの順位表 →</a></section>'
    body+=team_form(lg,t)+source(lg['meta'])
    body+='<section class="section"><h2>今シーズンの全結果</h2>'+cards(lg,played)+'</section><section class="section"><h2>今後の日程</h2>'+cards(lg,future)+'</section>'
    if pending: body+='<details class="pending-details"><summary>結果未掲載の試合 '+str(len(pending))+'件</summary><p>延期・中止の可能性があります。公式発表をご確認ください。</p>'+cards(lg,pending)+'</details>'
    return body+archive.team_history(lg,t['team'])+related('team')

def match(lg,m):
    known={t['slug']:t for t in lg['teams'].values()}
    teams=[known.get(m[s+'_slug'],{'slug':m[s+'_slug'],'team':m[s],'block':m.get('category','')}) for s in ['home','away']]
    def club(t):
        tag='a' if t['slug'] in known else 'div'
        return f'<{tag} class="club-display"'+(f' href="{team_url(lg,t)}"' if tag=='a' else '')+f'>{mark(t["team"],"large")}<span class="club-name">{e(t["team"])}</span><small>{"チームを見る →" if tag=="a" else "対戦相手未確定"}</small></{tag}>'
    played=m['status']=='played'; scores=[m[s+'_score'] if played else '—' for s in ['home','away']]
    body=f'<p class="bread"><a href="/{lg["code"]}/">{e(lg["label"])}リーグ</a> / 試合詳細</p>'+title('MATCH REPORT / '+m.get('category',''),'試合詳細')+f'<section class="big-scoreboard"><div class="scoreboard-meta"><span>{e(lg["label"])} / {e(m.get("category", ""))}</span><span>{e(m.get("date") or "日付未確認")} · {e(time(m))}</span></div><div class="versus">{club(teams[0])}<div class="big-number" aria-label="{scores[0]}対{scores[1]}"><span>{scores[0]}</span><i>:</i><span>{scores[1]}</span></div>{club(teams[1])}</div><div class="scoreboard-footer"><span>{status(m)}</span><span>{e(m.get("venue") or "会場未確認")}</span></div></section>'
    body+=source(lg['meta'])+'<section class="section"><div class="section-heading"><div><div class="eyebrow">TEAM CONTEXT / 最新掲載データ</div><h2>両校の現在地</h2></div><a href="/'+lg['code']+'/standings/">順位表 →</a></div><p class="source-note">順位と直近成績は最新掲載時点です。この試合当日の順位ではありません。</p><div class="team-context-grid">'
    for t in teams:
        stat=team_stats(lg,t);future=upcoming([x for x in lg['matches'] if t['slug'] in (x['home_slug'],x['away_slug'])])
        body+=f'<section class="team-context"><h3>{e(t["team"])}</h3><p>{e(t["block"])}</p>'
        body+=f'<div class="context-rank"><strong>{stat["rank"]}<small>位</small></strong><span>{stat["points"]}勝ち点 · {stat["wins"]}勝{stat["draws"]}分{stat["losses"]}敗</span></div>' if stat else '<p>順位は未掲載です。</p>'
        body+=team_form(lg,t)+'<h4>次の試合</h4>'+cards(lg,future[:1])+'</section>'
    direct=[]
    for year,rows in lg['matches_by_year']:
        direct.extend((year,x) for x in rows if x['status']=='played' and x.get('id')!=m['id'] and {x['home'],x['away']}=={m['home'],m['away']})
    direct.sort(key=lambda v:(v[0],v[1].get('date') or ''),reverse=True)
    body+='</div></section><section class="section"><div class="section-heading"><h2>これまでの直接対決</h2><a href="'+e(archive.link(lg['code'],year='all',team=m['home'],opponent=m['away'],view='h2h'))+'">全年度を見る →</a></div>'
    body+=''.join(f'<div class="h2h-row"><span>{e(x.get("date") or str(y)+"年")}</span><span>{e(x["home"])}</span><strong>{x["home_score"]} – {x["away_score"]}</strong><span>{e(x["away"])}</span></div>' for y,x in direct[:3]) or '<p>収録データに直接対決はありません。</p>'
    return body+'</section><div class="toolbox"><a class="button outline" href="/videos/">公式の映像・配信を探す ↗</a></div>'+related()

def myteams():
    teams=''.join(f'<div class="team-tile" data-team-tile="{e(t["team"])}">{mark(t["team"])}<a href="{team_url(lg,t)}">{e(t["team"])}<small>{e(lg["label"])}</small></a>{follow(lg,t)}</div>' for lg in LEAGUES for t in lg['teams'].values() if t['team'] not in ['未定'] and '勝者' not in t['team'])
    return title('YOUR TEAM. YOUR STORY.','マイチーム','同じ大学の男子・女子を、それぞれ保存できます。')+'<section id="my-team-results" aria-live="polite"><p>保存したチームの結果と次の試合をここに表示します。</p></section><section class="section"><div class="section-heading"><h2>応援するチームを探す</h2></div><label class="searchbox"><input type="search" id="catalog-search" aria-label="大学名で絞り込む" placeholder="大学名・略称で検索"></label><p id="catalog-count" role="status"></p><div class="team-catalog">'+teams+'</div><p class="source-note">保存情報はこのブラウザに保存します。ログインは不要です。</p></section>'

def matrices(lg):
    out='<section class="section"><h2>ブロック別の星取表</h2><p class="source-note">行の大学から見た結果：○ 勝ち / ● 負け / △ 引き分け。横にスクロールして全チームを確認できます。</p>'
    for block,rows in lg['standings'].items():
        table='<div class="tbl"><table class="matrix-table"><thead><tr><th scope="col">大学 / 対戦相手</th>'+''.join(f'<th scope="col">{e(t["team"])}</th>' for t in rows)+'</tr></thead><tbody>'
        for t in rows:
            table+=f'<tr><th scope="row"><a href="{team_url(lg,t)}">{e(t["team"])}</a></th>'
            for o in rows:
                ms=[m for m in lg['matches'] if m.get('category')==block and {m['home_slug'],m['away_slug']}=={t['slug'],o['slug']}]
                values=[]
                for m in ms:
                    a,b=(m['home_score'],m['away_score']) if m['home_slug']==t['slug'] else (m['away_score'],m['home_score'])
                    label=('○' if a>b else '●' if a<b else '△')+f' {a}–{b}' if m['status']=='played' else status(m)
                    values.append(f'<a href="{match_url(lg,m)}">{label}</a>')
                table+='<td>'+('—' if t['slug']==o['slug'] else '<br>'.join(values) or '未掲載')+'</td>'
            table+='</tr>'
        out+=f'<details class="matrix-block"><summary>{e(block)}</summary>{table}</tbody></table></div></details>'
    return out+'</section>'

def enhance(path, body, meta):
    p=path.strip('/').split('/') if path.strip('/') else []
    if not p: return home(body,meta)
    if p==['leagues']: return title('THE LEAGUES','リーグ・順位表','全国7地区・男女14リーグから探す。')+league_links()
    if p==['my-teams']: return myteams()
    lg=next((x for x in LEAGUES if x['code']==p[0]),None)
    if lg:
        if len(p)==1:
            return title(lg['code'].upper(),lg['label']+'リーグ',lg['meta']['league'])+center(lg['code'])+source(meta)+related()
        if len(p)==2 and p[1]=='standings': return body+matrices(lg)
        if len(p)>2 and p[1]=='clubs':
            t=next((t for t in lg['teams'].values() if t['slug']==p[2]),None)
            if t:return team(lg,t)
        if len(p)>2 and p[1]=='matches':
            m=next((m for m in lg['matches'] if m['id']==p[2]),None)
            if m:return match(lg,m)
    if p==['articles']:
        body=body.replace('<div class="digest">','<label class="searchbox article-search"><input id="article-search" type="search" placeholder="読みものを検索" aria-label="読みものを検索"></label><p id="article-count" role="status"></p><div class="digest">',1)
        body=body.replace('<h1>読みもの</h1>',title('THE JOURNAL / FIELD NOTES','読みもの'))
    if len(p)==2 and p[0]=='articles':
        headings=[]
        def heading(m):
            ident='story-'+str(len(headings)+1);text=re.sub('<[^>]*>','',m[1]);headings.append((ident,text))
            return f'<h2 id="{ident}">{m[1]}</h2>'
        # Limit contents to the article itself, leaving existing CTAs and full body intact.
        start=body.find('<div class="article">');end=body.find('</div>',start)
        if start!=-1:
            article=body[start:end];article=re.sub(r'<h2>(.*?)</h2>',heading,article,flags=re.S)
            toc='<details class="story-toc"><summary>この記事の内容</summary>'+''.join(f'<a href="#{ident}">{e(text)}</a>' for ident,text in headings)+'</details>'
            body=body[:start]+toc+article+body[end:]
    return body
