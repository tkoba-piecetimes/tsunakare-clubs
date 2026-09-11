"""Import official historical standings without deriving ranks from partial results.

Run manually with --cache pointing to the cached JLA sources and manifest.json.
Requires pdfplumber. Daily builds only read the resulting immutable JSON snapshot.
Every row keeps its source location; blank/error cells remain unreported.
"""
import argparse
import csv
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from import_archive import REGIONS, team_name

FIELDS = {
    '順位': 'rank', '勝ち点': 'points', '勝点': 'points', '試合数': 'games',
    '勝ち': 'wins', '勝ち数': 'wins', '勝数': 'wins', '引き分け': 'draws',
    '引分': 'draws', '負け': 'losses', '負け数': 'losses', '負数': 'losses',
    '得失点差': 'goal_diff', '総得点': 'goals_for',
}


def clean(s):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', s or ''))


def number(s):
    s = clean(s).replace('−', '-').replace('―', '-')
    return int(s) if re.fullmatch(r'[+-]?\d+', s) else None


def heading(text):
    text = clean(text).replace('block', 'ブロック').replace('Block', 'ブロック')
    for old,new in [('一部','1部'),('二部','2部'),('三部','3部'),('四部','4部')]:
        text=text.replace(old,new)
    patterns = [r'順位決定(?:リーグ|戦)', r'[1-9]部(?:リーグ)?(?:[A-F](?:ブロック)?)?',
                r'(?:中国|四国|[A-F])ブロック', r'(?:[一二三123]次|上位|下位)リーグ']
    for pattern in patterns:
        found = re.findall(pattern, text)
        if found:
            return found[-1]
    return ''


def normalized_team(raw, year, code):
    # A line break inside a full university name is only typography. A break
    # between complete university names denotes a joint team in these sources.
    raw = re.sub(r'(大学|高校)\s*\n(?=\S)', r'\1・', raw.strip())
    return team_name(raw, year, code)


def parse_block(raw, start, end, fields, team_col, opponents, year, code, name, locator, is_csv):
    entries = []
    i = start + 1
    stat_fields = [j for k, j in fields.items() if k != 'rank']
    while i < end:
        row = raw[i]
        if sum(number(row[j]) is not None for j in stat_fields) < 2:
            i += 1
            continue
        stop = i + 1
        while stop < end:
            following = raw[stop]
            if sum(number(following[j]) is not None for j in stat_fields) >= 2:
                break
            if heading(''.join(x or '' for x in following)) or any(clean(x) in ('HOME', 'AWAY') or '大会形式' in clean(x) or clean(x).startswith(('※','©','【')) or len(clean(x)) > 100 for x in following):
                break
            stop += 1
        pieces = raw[i:stop]
        names = list(dict.fromkeys(p[team_col].strip() for p in pieces if p[team_col] and p[team_col].strip()))
        # Ignore trailing notes after the last team; only adjacent name fragments
        # in otherwise merged rows can extend its name.
        if len(names) > 1:
            names = names[:2] if not is_csv else names[:1]
        source_team = '\n'.join(names)
        if not source_team and (year, code, locator) == (2022, 'kyushu-w', 'page:1:table:5:') and entries:
            previous = entries[-1]
            previous.setdefault('rounds', [{key:previous[key] for key in fields if key!='rank'}]).append({key:number(row[col]) for key,col in fields.items() if key!='rank'})
            for ci,(col,next_col) in enumerate(opponents):
                previous['_cells'][ci] += ' / ' + ' '.join(str(x).strip() for p in pieces for x in p[col:next_col] if x is not None and str(x).strip())
            i = stop
            continue
        if not source_team or len(clean(source_team)) > 70:
            raise ValueError(f'Unrecognized team: {code}/{year}/{locator}/{i+1}: {names}')
        item = {'team': normalized_team(source_team, year, code),
                'source_team': source_team, 'source_locator': f'{locator}row:{i+1}',
                **{key: number(row[col]) for key, col in fields.items()}}
        item['_cells'] = []
        for col, next_col in opponents:
            chunks = [' '.join(str(x).strip() for x in p[col:next_col] if x is not None and str(x).strip()) for p in pieces]
            if is_csv:
                # The score columns retain their meaning if the decorative
                # hyphen cell is blank (2024 Kanto men's 3B has such a cell).
                chunks=[]
                for p in pieces:
                    for offset in range(col,next_col,3):
                        cells=p[offset:offset+3]
                        if len(cells)==3 and number(cells[0]) is not None and number(cells[2]) is not None:
                            chunks.append(f'{clean(cells[0])} − {clean(cells[2])}')
                        else:
                            chunks.append(' '.join(str(x).strip() for x in cells if x is not None and str(x).strip()))
            item['_cells'].append(' '.join(x for x in chunks if x))
        entries.append(item)
        i = stop
    if not entries:
        raise ValueError(f'Empty standings block: {year}/{code}/{name}/{locator}')
    if len({r['team'] for r in entries}) != len(entries):
        raise ValueError(f'Duplicate team: {year}/{code}/{name}')
    block = {'name': name or 'リーグ戦', 'source_locator': f'{locator}row:{start+1}', 'rows': entries}
    # Row/column order is preserved. A mismatched or merged PDF matrix is kept
    # available in the original document instead of guessing column assignments.
    aligned = len(opponents) == len(entries) and not any(re.search(r'\d', r['_cells'][i]) for i, r in enumerate(entries))
    for r in entries:
        cells = r.pop('_cells')
        r['against'] = {t['team']: cells[i] for i, t in enumerate(entries)} if aligned else {}
    block['matrix_available'] = aligned
    if not aligned:
        block['matrix_note'] = 'この大会の対戦図は、下の公式資料でページ内表示できます。'
    if aligned:
        def scores(value):
            return re.findall(r'(\d+)\s*[-−―ー‐–]\s*(\d+)',unicodedata.normalize('NFKC',value))
        if any(sorted(scores(r['against'][t['team']])) != sorted((b,a) for a,b in scores(t['against'][r['team']])) for r in entries for t in entries):
            block['source_note']='公式表内で相手側の記載と一致しないスコアがあります。数値は原資料の記載どおりに掲載しています。'
    return block


def csv_blocks(path, year, code):
    raw = list(csv.reader(path.open(encoding='utf-8-sig', newline='')))
    width = max(map(len, raw)); raw = [r + [''] * (width-len(r)) for r in raw]
    starts = [i for i, row in enumerate(raw) if 'チーム名' in row and '勝ち点' in row]
    blocks = []
    for pos, start in enumerate(starts):
        row = raw[start]
        end = starts[pos+1] if pos+1 < len(starts) else len(raw)
        fields = {FIELDS[clean(c)]: j for j, c in enumerate(row) if clean(c) in FIELDS}
        cols = [j for j, c in enumerate(row) if j > max(fields.values()) and clean(c)]
        # One opponent can occupy six columns in a two-round league.
        opponents = [(col, cols[i+1] if i+1 < len(cols) else col + (cols[-1]-cols[-2] if len(cols)>1 else 3)) for i, col in enumerate(cols)]
        name = heading(''.join(raw[start-1])) or 'リーグ戦'
        blocks.append(parse_block(raw, start, end, fields, row.index('チーム名'), opponents, year, code, name, '', True))
    return blocks, ''


def pdf_blocks(path, year, code):
    import pdfplumber
    blocks = []; full_text = ''
    with pdfplumber.open(path) as pdf:
        for pi, page in enumerate(pdf.pages, 1):
            full_text += (page.extract_text() or '') + '\n'
            lines = page.extract_text_lines()
            for ti, table in enumerate(page.find_tables(), 1):
                raw = table.extract()
                # Verified against the rendered page: a missing PDF cell border
                # merges Iwate's Niigata and Tohoku Gakuin results in extraction.
                if (year,code,pi,ti)==(2022,'tohoku-m',1,1):
                    assert clean(raw[3][5])=='○○7-321-3' and raw[3][7] is None
                    raw[3][5]='○\n7 - 3'; raw[3][7]='○\n21 - 3'
                # This source has vertical, split headers and deliberately no
                # rank column. Preserve its published points (including 6).
                if (year, code, pi, ti) == (2021, 'kyushu-w', 1, 1):
                    fields = {'wins':12, 'draws':15, 'losses':16, 'points':19, 'goal_diff':22}
                    cols = [1,2,3,4,5,6,7,10,11]
                    blocks.append(parse_block(raw,2,len(raw),fields,0,[(c,c+1) for c in cols],year,code,'リーグ戦','page:1:table:1:',False))
                    continue
                starts = [i for i, row in enumerate(raw) if any(clean(c)=='勝ち点' or clean(c)=='勝点' for c in row) and (any(clean(c)=='順位' for c in row) or (not clean(row[0]) and not clean(row[1])))]
                for pos, start in enumerate(starts):
                    row = raw[start]
                    fields = {}
                    for j, c in enumerate(row):
                        key = clean(c)
                        if key in FIELDS:
                            fields[FIELDS[key]] = j
                        elif key.endswith('勝ち数'):
                            fields['wins'] = j
                    if 'points' not in fields:
                        continue
                    if 'rank' not in fields and not clean(row[0]) and not clean(row[1]):
                        fields['rank']=0
                    if (year,code,pi,ti)==(2022,'kanto-w',3,2):
                        fields['wins']=6  # Header overlaps a long joint-team label.
                    team_col = 1 if fields.get('rank') == 0 else 0
                    first_stat = min(v for k,v in fields.items() if k != 'rank')
                    cols = [j for j,c in enumerate(row) if team_col < j < first_stat and clean(c)]
                    end = starts[pos+1] if pos+1 < len(starts) else len(raw)
                    top = table.rows[start].bbox[1]
                    labels = [(line['top'],heading(line['text'])) for line in lines if line['top'] < top and heading(line['text'])]
                    name = max(labels)[1] if labels else 'リーグ戦'
                    blocks.append(parse_block(raw,start,end,fields,team_col,[(c,c+1) for c in cols],year,code,name,f'page:{pi}:table:{ti}:',False))
    updated = re.search(r'(20\d{2})年\s*(\d+)月\s*(\d+)日現在',unicodedata.normalize('NFKC',full_text))
    return blocks, f'{updated[1]}-{int(updated[2]):02}-{int(updated[3]):02}' if updated else ''


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--cache',type=Path,required=True)
    args = parser.parse_args(); repo = Path(__file__).resolve().parents[1]
    manifest = json.loads((args.cache/'manifest.json').read_text(encoding='utf8'))
    seasons = []
    for year, meta in manifest.items():
        for source in meta['sources']:
            if source['kind'] != 'standings': continue
            code = REGIONS[source['region']] + '-' + source['gender']
            ext = 'pdf' if '.pdf' in source['url'] else 'csv'
            path = args.cache/f'{year}-{code}-standings.{ext}'
            blocks, updated = (pdf_blocks if ext=='pdf' else csv_blocks)(path,int(year),code)
            item = {'year':int(year),'code':code,'source_url':source['url'],'source_page':meta['page'],
                    'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                    'source_updated_at':updated,'blocks':blocks,'original_pages':[]}
            # Tournament charts need their geometry. Render the official pages
            # as images, so they also remain visible on mobile PDF-less browsers.
            if (int(year),code) in [(2021,'kanto-m'),(2021,'kanto-w'),(2021,'tokai-w')]:
                import pdfplumber
                with pdfplumber.open(path) as pdf:
                    for pi,page in enumerate(pdf.pages,1):
                        name=f'archive-official-{year}-{code}-{pi}.webp'
                        page.to_image(resolution=160).original.save(repo/'assets'/name,format='WEBP',quality=86)
                        item['original_pages'].append({'src':'/assets/'+name,'page':pi})
            seasons.append(item)
            print(f'{year} {code}: {len(blocks)} blocks, {sum(len(b["rows"]) for b in blocks)} teams',flush=True)
    output = {'version':1,'fetched_at':datetime.now(timezone.utc).isoformat(),'seasons':seasons}
    (repo/'data'/'history-standings.json').write_text(json.dumps(output,ensure_ascii=False,indent=1),encoding='utf8')


if __name__ == '__main__':
    main()
