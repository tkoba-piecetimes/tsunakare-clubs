"""Import cached JLA public results. Run manually; daily refresh never overwrites history.

Usage: python pipeline/import_archive.py --cache /path/to/history-sources
Cache contains manifest.json, official CSVs and PDFs. Requires pdfplumber for PDFs.
Only numeric official scores are imported. Each record retains its source locator.
"""
import argparse
import csv
import hashlib
import json
import re
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from team_slugs import TEAM_SLUGS, slug_for

REGIONS = dict(zip(['北海道','東北','関東','東海','関西','中四国','九州'],
                   ['hokkaido','tohoku','kanto','tokai','kansai','chushikoku','kyushu']))

def clean(s):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', s or ''))

ALIASES = {'独協':'獨協大学','国士館':'国士舘大学','椙山':'椙山女学園大学',
           '愛学':'愛知学院大学','名古屋外語':'名古屋外国語大学',
           '東京農大':'東京農業大学','東京農業':'東京農業大学',
           '日本女子体育':'日本女子体育大学','宮城学院女子':'宮城学院女子大学'}
ALIASES.update({'新潟':'新潟大学','愛教':'愛知教育大学','日本福祉':'日本福祉大学','日福':'日本福祉大学',
    '金城':'金城学院大学','東京女子体育':'東京女子体育大学','国際基督教':'国際基督教大学',
    '創価':'創価大学','桜美林':'桜美林大学','西武文理':'西武文理大学','駒沢女子':'駒沢女子大学',
    '北九州市立大':'北九州市立大学','東京家政':'東京家政大学','実践':'実践女子大学',
    '共立大学':'共立女子大学'})

def team_name(raw, year, code=''):
    n = clean(raw).strip('★☆○〇')
    # Remove spectator markers; retain joint teams and historic names as separate teams.
    n = re.sub(r'\((?:白|色|HOME|AWAY)\)', '', n, flags=re.I)
    n = re.sub(r'\([^()]*(?:部|ブロック|[A-F]勝)[^()]*\)$', '', n)
    if n in ALIASES: return ALIASES[n]
    if n in TEAM_SLUGS: return n
    if n+'大学' in TEAM_SLUGS: return n+'大学'
    if re.fullmatch(r'合同(?:チーム)?[1-9①②③④⑤]?', n):
        region=next((r for r,c in REGIONS.items() if c==code.split('-')[0]),'')
        return f'{n}（{year}年・{region}）'
    return n

def category(raw):
    n=clean(raw)
    n=re.sub(r'\[?\s*(?:男子|女子)?開幕戦\s*\]?', '', n)
    m=re.fullmatch(r'(\d)部?([A-D])(?:ブロック)?',n)
    if m: return f'{m[1]}部 {m[2]}ブロック'
    if re.fullmatch(r'\d',n): return n+'部'
    return n or '区分未記載'

def match(year, code, home, away, hs, aws, month, day, time, cat, venue, note, locator):
    hs,aws=clean(hs),clean(aws)
    if not re.fullmatch(r'\d{1,2}',hs) or not re.fullmatch(r'\d{1,2}',aws): return None
    home,away=team_name(home,year,code),team_name(away,year,code)
    junk=r'予備|未定|勝者|敗者|勝ち|負け|[1-9]位|[1-9]部[A-D]$|開会式|閉会式'
    if not home or not away or home==away or re.search(junk,home+away): return None
    if any(n.count('(')!=n.count(')') for n in (home,away)): return None
    try: d=date(year,int(month),int(day)).isoformat()
    except (ValueError,TypeError): d=None
    note=unicodedata.normalize('NFKC',note or '').strip()
    kind='administrative' if re.search('不戦|棄権|実施無|実施な|没収',note) else 'played'
    raw=f'{year}|{code}|{locator}|{home}|{away}'
    return {'id':f'{year}-'+hashlib.sha256(raw.encode()).hexdigest()[:14],
        'season_year':year,'date':d,'time':clean(time) or '未記載',
        'home':home,'away':away,'home_slug':slug_for(home),'away_slug':slug_for(away),
        'home_score':int(hs),'away_score':int(aws),'status':'played','result_type':kind,
        'category':category(cat),'venue':(venue or '').replace('\n','').strip() or '未記載',
        'note':note,'source_locator':locator}

def parse_csv(path, year, code):
    rows=list(csv.reader(path.open(encoding='utf-8-sig',newline='')))
    out=[]; month=None; skipped=0
    start=next(i for i,r in enumerate(rows) if any('HOME' in c for c in r))
    for i,r in enumerate(rows[start+1:],start+2):
        c=[x.strip() for x in r]+['']*20
        if year>=2025:
            mo,day,tm,cat,round_,home,away,venue,hs,aws,note=(c[1],c[2],c[4],c[5],c[6],c[7],c[8],c[9],c[10],c[12],c[13])
            if round_ and round_!='開幕戦': cat=' '.join(filter(None,[cat,round_]))
        else:
            o=1 if year==2024 else 0
            mo,day,tm,cat,home,hs,aws,away,venue,note=(c[o],c[o+2],c[o+4],c[o+5],c[o+6],c[o+7],c[o+9],c[o+10],c[o+11],c[o+13])
        if clean(mo).isdigit(): month=int(clean(mo))
        if not clean(day).isdigit():
            if clean(hs).isdigit() and clean(aws).isdigit(): skipped+=1
            continue
        m=match(year,code,home,away,hs,aws,month,clean(day),tm,cat,venue,note,f'row:{i}')
        if m: out.append(m)
        elif home and away: skipped+=1
    return out,skipped

def parse_pdf(path, year, code):
    import pdfplumber
    out=[]; skipped=0
    with pdfplumber.open(path) as pdf:
        header=None; prev={}; month=None; lastday=None; withheld_month=None
        for pageno,page in enumerate(pdf.pages,1):
            for ti,table in enumerate(page.extract_tables()):
                for ri,row in enumerate(table):
                    # The month column is outside the detected table on this PDF page.
                    if year==2022 and code=='kanto-w' and pageno==2 and len(row)==8:
                        row=['']+row
                    c=[clean(x) for x in row]
                    if any('HOME' in x for x in c) and any('AWAY' in x for x in c):
                        header=c; continue
                    if not header or len(c)!=len(header): continue
                    def ix(label): return next((i for i,h in enumerate(header) if label(h)),None)
                    hi=ix(lambda h:'HOME' in h); ai=ix(lambda h:'AWAY' in h); si=ix(lambda h:'スコア' in h)
                    if si is None: continue
                    score=re.fullmatch(r'(\d{1,2})[-−ー–―](\d{1,2})(\*.*)?',c[si])
                    if not score:
                        if c[hi] and c[ai]: skipped+=1
                    # Fill only truly merged cells. Blank cells do not establish a date.
                    vals=[]
                    for j,v in enumerate(c):
                        if row[j] is None: vals.append(prev.get(j,''))
                        else: prev[j]=v; vals.append(v)
                    mi=ix(lambda h:h=='月'); di=ix(lambda h:h=='日')
                    datei=ix(lambda h:h in ('開催日','日程'))
                    tm=ix(lambda h: '時刻' in h or h in ('時間','試合時間'))
                    ci=ix(lambda h:'リーグ' in h or h=='部')
                    if ci is None and year==2021 and code.startswith('hokkaido'): ci=3
                    vi=ix(lambda h:'会場' in h)
                    if datei is not None:
                        md=re.fullmatch(r'(\d{1,2})月(\d{1,2})日',vals[datei])
                        mo,da=(md[1],md[2]) if md else (None,None)
                    else:
                        mo=vals[mi] if mi is not None else ''; da=vals[di] if di is not None else ''
                        mm=re.fullmatch(r'(\d{1,2})月?',mo)
                        mo=int(mm[1]) if mm else None
                        if da.isdigit():
                            # If a cell extraction misses a month boundary, withhold the date.
                            if lastday is not None and int(da)<lastday and mo==month: withheld_month=mo
                            lastday=int(da)
                        if mo!=withheld_month: withheld_month=None
                        if withheld_month is not None: mo=None
                        if mo is None: month=None
                        else: month=mo
                    if not score: continue
                    cat=vals[ci] if ci is not None else ''
                    if ('女子' in cat and code.endswith('-m')) or ('男子' in cat and code.endswith('-w')): continue
                    note=' '.join(c[si+1:])
                    if note in (c[hi],c[ai],'引き分け'): note=''
                    if score[3]: note=score[3]+' '+note
                    # Withhold inconsistent dates rather than guessing a missing PDF month.
                    wi=ix(lambda h:h=='曜日')
                    weekday=vals[wi][:1] if wi is not None else ''
                    if weekday in '月火水木金土日' and weekday:
                        try:
                            if '月火水木金土日'[date(year,int(mo),int(da)).weekday()]!=weekday: mo=None
                        except (ValueError,TypeError): pass
                    m=match(year,code,c[hi],c[ai],score[1],score[2],mo,da,
                            vals[tm] if tm is not None else '',cat,
                            vals[vi] if vi is not None else '',note,f'page:{pageno}:table:{ti+1}:row:{ri+1}')
                    if m: out.append(m)
                    else: skipped+=1
    return out,skipped

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cache',type=Path,required=True);args=ap.parse_args()
    manifest=json.loads((args.cache/'manifest.json').read_text(encoding='utf8'))
    seasons=[]
    for yr,group in sorted(manifest.items()):
        year=int(yr)
        for source in group['sources']:
            if source['kind']!='results': continue
            code=REGIONS[source['region']]+'-'+source['gender']
            ext='pdf' if '.pdf' in source['url'] else 'csv'
            p=args.cache/f'{year}-{code}-results.{ext}'
            matches,skipped=(parse_pdf(p,year,code) if ext=='pdf' else parse_csv(p,year,code)) if p.exists() else ([],0)
            # Do not silently collapse conflicting records. Exact repeats are reported and deduplicated.
            seen=set(); unique=[]
            for m in matches:
                key=(m['date'],m['home'],m['away'],m['home_score'],m['away_score'],m['category'])
                if m['date'] and key in seen: skipped+=1;continue
                seen.add(key);unique.append(m)
            standings_url=next((s['url'] for s in group['sources'] if s['kind']=='standings' and s['region']==source['region'] and s['gender']==source['gender']),'')
            text=p.with_suffix('.txt').read_text(encoding='utf8') if ext=='pdf' and p.with_suffix('.txt').exists() else p.read_text(encoding='utf8') if p.exists() else ''
            title=next((line for line in text.splitlines() if '第' in line and '学生' in line),'').strip(',')
            update=re.search(r'20\d\d[年/.-]\d{1,2}[月/.-]\d{1,2}',unicodedata.normalize('NFKC',text[:1800]))
            seasons.append({'code':code,'year':year,'league':title,'matches':unique,'standings':{},
                'coverage':'partial' if unique else 'unavailable','source_url':source['url'],
                'standings_url':standings_url,'source_page':group['page'],
                'source_updated_at':update[0] if update else '',
                'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else '',
                'unscored_or_unparsed_rows':skipped,'date_unconfirmed':sum(m['date'] is None for m in unique),
                'coverage_note':'公式資料のうちスコアを確認できた試合を収録。中止・延期・未確定の対戦枠等は集計に含みません。日付を確認できない記録は日付未確認と表示します。'})
            print(year,code,len(unique),'date?',sum(m['date'] is None for m in unique),'excluded',skipped)
    out=Path(__file__).resolve().parent.parent/'data'/'history-archive.json'
    out.write_text(json.dumps({'version':1,'from_year':2021,'fetched_at':datetime.now(timezone.utc).isoformat(),'seasons':seasons},ensure_ascii=False,indent=1),encoding='utf8')

if __name__=='__main__': main()
