"""Validate the publishing contract against the pre-change repository tree."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'site'
baseline=subprocess.check_output(['git','ls-tree','-r','--name-only','HEAD','site'],cwd=ROOT,text=True).splitlines()
missing=[p for p in baseline if p.endswith('/index.html') and not (ROOT/p).exists()]
assert not missing, f'Existing URLs removed: {missing}'
class Page(HTMLParser):
 def __init__(self): super().__init__();self.canonical=[];self.robots=[];self.links=[];self.h1=0;self.contact=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='h1':self.h1+=1
  if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a.get('href'))
  if tag=='meta' and a.get('name')=='robots':self.robots.append(a.get('content'))
  if tag=='a':self.links.append(a.get('href',''))
  if tag=='form':self.contact+=1
broken=[];checked=0
for file in SITE.rglob('index.html'):
 text=file.read_text(encoding='utf8'); p=Page();p.feed(text)
 if 'http-equiv="refresh"' in text:
  assert len(p.canonical)==1,file
  destination=urlparse(p.canonical[0])
  assert destination.netloc=='lacrossemania.jp',(file,p.canonical)
  assert (SITE/unquote(destination.path).lstrip('/')/'index.html').exists(),(file,p.canonical)
  continue
 checked+=1
 assert len(p.canonical)==1,file
 assert p.h1==1,(file,p.h1)
 if 'dash-lm-ops' not in str(file):assert not any('noindex' in x for x in p.robots),file
 for href in p.links:
  u=urlparse(href)
  if u.scheme or u.netloc or not u.path:continue
  target=SITE/unquote(u.path).lstrip('/') if u.path.startswith('/') else file.parent/unquote(u.path)
  if u.path.endswith('/'):target=target/'index.html'
  if not target.exists():broken.append((str(file.relative_to(SITE)),href))
articles=list((ROOT/'content/articles').glob('*.md'))
for article in articles:
 target=SITE/'articles'/article.stem/'index.html'
 assert target.exists(),article
 text=target.read_text(encoding='utf8')
 assert '<div class="article">' in text and 'このデモでは記事の概要' not in text,article
assert '<form' in (SITE/'contact/index.html').read_text(encoding='utf8')
report={'pages_checked':checked,'existing_page_urls_preserved':len([p for p in baseline if p.endswith('/index.html')]),'full_articles':len(articles),'broken_links':broken}
print(json.dumps(report,ensure_ascii=False,indent=2))
assert not broken, 'Internal links must resolve before publication'
