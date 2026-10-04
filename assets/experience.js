(()=>{'use strict';
 const C=window.LMExperience, main=document.getElementById('main');
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const regions=['全国','関東','関西','東海','北海道','東北','中四国','九州'];
 const read=key=>{try{return JSON.parse(localStorage.getItem(key));}catch{return null;}};
 const write=(key,value)=>{try{localStorage.setItem(key,JSON.stringify(value));return true;}catch{return false;}};
 let leagues=[],identities={},saved=[],allTeams=[],toastTimer;
 let suggestionIndex=-1;
 const center=document.querySelector('[data-center]'),params=new URLSearchParams(location.search);
 const state={...C.preferences(read('lm-display-v3'),regions),code:center?.dataset.center||'',view:'results',q:'',limit:12};
 if(['m','w','all'].includes(params.get('gender')))state.sex=({m:'男子',w:'女子',all:'すべて'})[params.get('gender')];
 if(regions.includes(params.get('region')))state.region=params.get('region');
 if(['results','upcoming','pending'].includes(params.get('view')))state.view=params.get('view');
 state.q=params.get('team')||'';
 const path=location.pathname.replace(/index\.html$/,'');
 if(path==='/'&&location.hash==='#my-teams'){location.replace('/my-teams/');return;}
 document.querySelectorAll('.main-nav a,.bottom-nav a').forEach(a=>{const target=new URL(a.href).pathname;const selected=target==='/'?path==='/':target==='/leagues/'?/^\/(leagues|(?:kanto|kansai|tokai|tohoku|hokkaido|kyushu|chushikoku)-[mw])\//.test(path):path.startsWith(target);if(selected)a.setAttribute('aria-current','page');});
 const toggle=document.getElementById('menu-toggle'),menu=document.getElementById('mobile-menu');
 toggle?.addEventListener('click',()=>{menu.hidden=!menu.hidden;toggle.setAttribute('aria-expanded',String(!menu.hidden));});
 document.addEventListener('keydown',ev=>{if(ev.key==='Escape'&&!menu.hidden){menu.hidden=true;toggle.setAttribute('aria-expanded','false');toggle.focus();}});
 function toast(text){const el=document.getElementById('toast');el.textContent=text;el.classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('visible'),2800);}
 function badge(name){const d=identities[name]||{mark:'—',color:'#647a70'};return `<span class="team-badge team-badge--pair" style="--team-color:${esc(d.color)}" aria-hidden="true"><span>${esc(d.mark)}</span></span>`;}
 function matchUrl(l,m){return '/'+l.code+'/matches/'+encodeURIComponent(m.id)+'/';}
 function teamUrl(x){return '/'+x.l.code+'/clubs/'+encodeURIComponent(x.t.slug)+'/';}
 function card(l,m){const played=m.status==='played',kind=C.category(m,C.today());return `<a class="match-card" href="${matchUrl(l,m)}"><div class="match-meta"><span>${esc((m.date||'日付未確認').replaceAll('-','.'))} · ${esc(l.label)}</span><span class="state">${({results:'試合終了',upcoming:'試合予定',pending:'結果未掲載'})[kind]}</span></div>${['home','away'].map((s,i)=>`<div class="score-row"><span class="team-name ${played&&m[s+'_score']>m[(i?'home':'away')+'_score']?'winner':''}">${badge(m[s])}<span>${esc(m[s])}</span></span><strong class="score">${played?m[s+'_score']:'—'}</strong></div>`).join('')}<div class="match-bottom"><span>${esc(m.category||'区分未記載')}</span><span>${played?'詳細 →':esc(m.time&&!['00:00','0:00'].includes(m.time)?m.time:'時間未定')}</span></div></a>`;}
 function updateURL(){const u=new URL(location.href);for(const key of ['gender','region','view','team'])u.searchParams.delete(key);if(state.sex!=='すべて')u.searchParams.set('gender',state.sex==='女子'?'w':'m');if(state.region!=='全国')u.searchParams.set('region',state.region);if(state.view!=='results')u.searchParams.set('view',state.view);if(state.q)u.searchParams.set('team',state.q);history.replaceState(null,'',u);}
 function renderCenter(){if(!center)return;
   const rows=C.filter(leagues,state,identities,C.today()),target=document.getElementById('center-results');
   target.innerHTML=rows.length?rows.slice(0,state.limit).map(({l,m})=>card(l,m)).join(''):`<div class="empty"><h2>この条件の試合はありません</h2><p>${state.q?'大学名の候補を選ぶか、男女・地区を変更してください。':'掲載情報が追加されるまで、リーグやマイチームから確認できます。'}</p><button class="button outline" data-clear>条件を解除する</button></div>`;
   document.getElementById('result-count').textContent=rows.length+'試合';
   document.getElementById('result-label').textContent=(state.code?leagues.find(l=>l.code===state.code)?.label:state.region+'・'+(state.sex==='すべて'?'男女':state.sex))+' / '+({results:'最新の結果',upcoming:'これからの試合',pending:'結果未掲載'})[state.view];
   center.querySelectorAll('[data-sex]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.sex===state.sex)));
   center.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===state.view)));
   const more=document.getElementById('more-results');more.hidden=rows.length<=state.limit;more.textContent=`さらに12試合を見る（残り${Math.max(0,rows.length-state.limit)}）`;
   let hint=document.getElementById('pending-hint');if(!hint){hint=document.createElement('p');hint.id='pending-hint';hint.className='source-note';target.before(hint);}hint.hidden=state.view!=='pending';hint.textContent='予定日を過ぎても結果が掲載されていない試合です。延期・中止の可能性があるため、公式発表をご確認ください。';
   const suggestions=[...new Set(allTeams.filter(x=>(!state.code||x.l.code===state.code)&&C.matches(x.t.team,state.q,identities)).map(x=>x.t.team))].slice(0,10);
   const list=document.getElementById('team-suggestions'),field=document.getElementById('team-search');
   list.innerHTML=suggestions.slice(0,5).map((t,i)=>`<button type="button" role="option" tabindex="-1" aria-selected="false" id="team-option-${i}" data-suggest="${esc(t)}">${badge(t)}<span>${esc(t)}</span><small>選択 →</small></button>`).join('');
   list.hidden=!(state.q&&suggestions.length&&document.activeElement===field);field.setAttribute('aria-expanded',String(!list.hidden));field.removeAttribute('aria-activedescendant');suggestionIndex=-1;
 }
 function preferenceChanged(){state.limit=12;write('lm-display-v3',{sex:state.sex,region:state.region});updateURL();renderCenter();}
 function reflectSaved(){document.querySelectorAll('[data-save]').forEach(b=>{const on=saved.includes(b.dataset.save);b.setAttribute('aria-pressed',String(on));b.textContent=on?'★ 保存済み':'☆ マイチームに追加';b.setAttribute('aria-label',(b.dataset.teamName||'このチーム')+(on?'をマイチームから解除':'をマイチームに追加'));});}
 function pickMatches(x,kind){return C.filter(leagues,{sex:'すべて',region:'全国',code:x.l.code,view:kind,q:''},identities,C.today()).filter(({m})=>m.home_slug===x.t.slug||m.away_slug===x.t.slug);}
 function renderPicks(){
   const picks=allTeams.filter(x=>saved.includes(x.key)),home=document.getElementById('my-teams'),page=document.getElementById('my-team-results');
   if(home){home.hidden=!picks.length;home.innerHTML=`<div class="small-heading"><h2>マイチームの結果</h2><a href="/my-teams/">${picks.length}チームをすべて見る →</a></div><div class="home-pick-list">${picks.slice(0,2).map(x=>{const latest=pickMatches(x,'results')[0],next=pickMatches(x,'upcoming')[0];return `<div class="home-pick"><a class="pick-name" href="${teamUrl(x)}">${badge(x.t.team)}<span>${esc(x.t.team)}<small>${esc(x.l.meta.gender)}</small></span></a>${latest?`<a class="pick-score" href="${matchUrl(latest.l,latest.m)}"><span>${esc(latest.m.date.slice(5))} ${esc(latest.m.home)} – ${esc(latest.m.away)}</span><strong>${latest.m.home_score} : ${latest.m.away_score}</strong></a>`:'<span>結果未掲載</span>'}<span class="pick-next">${next?`次戦 ${esc(next.m.date.slice(5))} <a href="${matchUrl(next.l,next.m)}">日程 →</a>`:'次戦の掲載なし'}</span></div>`;}).join('')}</div>`;}
   if(page){page.innerHTML=picks.length?picks.map(x=>`<section class="saved-team-section"><div class="small-heading"><h2><a href="${teamUrl(x)}">${esc(x.t.team)}・${esc(x.l.meta.gender)}</a></h2><a href="${teamUrl(x)}">全結果・順位 →</a></div><div class="team-summary"><div><h3>最新の結果</h3>${pickMatches(x,'results').slice(0,1).map(({l,m})=>card(l,m)).join('')||'<p>結果は未掲載です。</p>'}</div><div><h3>次の試合</h3>${pickMatches(x,'upcoming').slice(0,1).map(({l,m})=>card(l,m)).join('')||'<p>今後の日程は未掲載です。</p>'}</div></div></section>`).join(''):'<div class="empty"><h2>応援するチームを選びましょう</h2><p>下の検索から保存すると、トップにも結果が表示されます。</p></div>';}
 }
 function renderCatalog(){const q=document.getElementById('catalog-search')?.value||'';let count=0;document.querySelectorAll('[data-team-tile]').forEach(tile=>{tile.hidden=!C.matches(tile.dataset.teamTile,q,identities);if(!tile.hidden)count++;});const el=document.getElementById('catalog-count');if(el)el.textContent=count+'チーム';}
 async function load(){
   try{
     const responses=await Promise.all([fetch('/assets/clubhouse-data.json'),fetch('/assets/team-identities.json')]);
     if(responses.some(r=>!r.ok))throw Error('データの取得に失敗');
     [leagues,identities]=await Promise.all(responses.map(r=>r.json()));allTeams=C.teams(leagues);
     const current=read('lm-favorites-v3');saved=C.migrateSaved(leagues,read('lm-teams'),read('lm-demo-teams-v2'),current);if(!Array.isArray(current))write('lm-favorites-v3',saved);
     if(center){document.getElementById('team-search').value=state.q;const region=document.getElementById('region');if(region)region.value=state.region;renderCenter();}
     reflectSaved();renderPicks();renderCatalog();
   }catch(error){const note=document.createElement('p');note.className='notice';note.setAttribute('role','status');note.innerHTML='絞り込み・保存機能を読み込めませんでした。掲載済みの結果は引き続き閲覧できます。<a href="/leagues/">リーグ一覧から探す →</a>';main.prepend(note);document.querySelectorAll('[data-save],.compact-filters input,.compact-filters select,.compact-filters button,.center-tabs button').forEach(x=>x.disabled=true);}
 }
 if(center||document.querySelector('[data-save]')||document.getElementById('my-team-results'))load();
 center?.addEventListener('click',ev=>{const sex=ev.target.closest('[data-sex]'),view=ev.target.closest('[data-view]');if(sex){state.sex=sex.dataset.sex;preferenceChanged();}if(view){state.view=view.dataset.view;preferenceChanged();}if(ev.target.closest('[data-clear]')){state.sex='すべて';state.region='全国';state.q='';document.getElementById('team-search').value='';const region=document.getElementById('region');if(region)region.value='全国';preferenceChanged();}if(ev.target.closest('#more-results')){state.limit+=12;renderCenter();}});
 document.getElementById('region')?.addEventListener('change',ev=>{state.region=ev.target.value;preferenceChanged();});
 const input=document.getElementById('team-search');function search(){state.q=input.value;state.limit=12;updateURL();renderCenter();}
 input?.addEventListener('input',ev=>{if(!ev.isComposing)search();});input?.addEventListener('compositionend',search);
 function closeSuggestions(){const list=document.getElementById('team-suggestions');if(list)list.hidden=true;input?.setAttribute('aria-expanded','false');input?.removeAttribute('aria-activedescendant');suggestionIndex=-1;}
 function chooseSuggestion(name){input.value=name;state.q=name;state.limit=12;updateURL();renderCenter();closeSuggestions();input.focus();}
 input?.addEventListener('keydown',ev=>{if(ev.isComposing)return;const list=document.getElementById('team-suggestions'),options=[...list.querySelectorAll('[data-suggest]')];if(ev.key==='Escape'){closeSuggestions();return;}if(['ArrowDown','ArrowUp'].includes(ev.key)&&options.length){ev.preventDefault();list.hidden=false;input.setAttribute('aria-expanded','true');suggestionIndex=suggestionIndex<0?(ev.key==='ArrowDown'?0:options.length-1):(suggestionIndex+(ev.key==='ArrowDown'?1:-1)+options.length)%options.length;options.forEach((b,i)=>b.setAttribute('aria-selected',String(i===suggestionIndex)));input.setAttribute('aria-activedescendant',options[suggestionIndex].id);}if(ev.key==='Enter'&&suggestionIndex>=0&&!list.hidden){ev.preventDefault();chooseSuggestion(options[suggestionIndex].dataset.suggest);}});
 document.getElementById('team-suggestions')?.addEventListener('mousedown',ev=>ev.preventDefault());
 document.getElementById('team-suggestions')?.addEventListener('click',ev=>{const b=ev.target.closest('[data-suggest]');if(b)chooseSuggestion(b.dataset.suggest);});
 input?.addEventListener('blur',()=>setTimeout(closeSuggestions,150));
 document.getElementById('catalog-search')?.addEventListener('input',ev=>{if(!ev.isComposing)renderCatalog();});document.getElementById('catalog-search')?.addEventListener('compositionend',renderCatalog);
 document.addEventListener('click',ev=>{const b=ev.target.closest('[data-save]');if(!b||!leagues.length)return;const key=b.dataset.save;saved=saved.includes(key)?saved.filter(x=>x!==key):[...saved,key];const persisted=write('lm-favorites-v3',saved);reflectSaved();renderPicks();toast(persisted?'マイチームを更新しました':'このブラウザでは保存できません。今回の表示中のみ有効です。');});
 const articleSearch=document.getElementById('article-search');function findArticles(){const q=C.normalize(articleSearch.value);let n=0;document.querySelectorAll('.digest-card').forEach(el=>{el.hidden=!C.normalize(el.textContent).includes(q);if(!el.hidden)n++;});document.getElementById('article-count').textContent=n+'記事';}
 articleSearch?.addEventListener('input',ev=>{if(!ev.isComposing)findArticles();});articleSearch?.addEventListener('compositionend',findArticles);if(articleSearch)findArticles();
 // Preserve the existing, optional lacrosse quiz and its saved best score.
 const dialog=document.getElementById('club-dialog'),db=document.getElementById('dialog-body');
 const questions=[['ゴール裏の「X」。ここから攻める狙いは？',['守備の視線を分散させる','必ず2点を取れる','オフサイドをなくす'],0,'ボールと前の選手を同時に見るのは難しい。カットやフィードの起点になります。'],['グラウンドボールとは？',['試合開始の合図','地面にあるボール','ゴールの中のボール'],1,'地面に落ちているボールのこと。拾って攻撃権を得るプレーです。'],['オフボールでの「カット」とは？',['クロスの修理','相手のクロスをたたくこと','パスを受けるために走り込むこと'],2,'ボールを持っていない選手がスペースへ走り込む動きです。']];
 let step=0,score=0,answered=false;let best=Math.min(3,Math.max(0,Number(read('lm-best'))||0));const bestEl=document.getElementById('quiz-best');if(bestEl)bestEl.textContent=best+' / 3';
 function quiz(){answered=false;const q=questions[step];db.innerHTML=`<p class="eyebrow">LACROSSE IQ / ${step+1}</p><h2>${q[0]}</h2><div class="quiz-options">${q[1].map((a,i)=>`<button data-answer="${i}">${a}</button>`).join('')}</div><div id="quiz-feedback" aria-live="polite"></div>`;}
 document.getElementById('start-quiz')?.addEventListener('click',()=>{step=0;score=0;quiz();dialog.showModal();});
 dialog?.querySelector('.dialog-close').addEventListener('click',()=>dialog.close());
 db?.addEventListener('click',ev=>{const a=ev.target.closest('[data-answer]');if(a&&!answered){answered=true;const q=questions[step],ok=Number(a.dataset.answer)===q[2];if(ok)score++;db.querySelectorAll('[data-answer]').forEach(b=>b.disabled=true);db.querySelector('#quiz-feedback').innerHTML=`<p>${ok?'正解！':'正解：'+q[1][q[2]]}</p><p>${q[3]}</p><button id="quiz-next">${step===2?'結果を見る':'次の問題へ'} →</button>`;}if(ev.target.closest('#quiz-next')){step++;if(step<3)quiz();else{best=Math.max(best,score);write('lm-best',best);bestEl.textContent=best+' / 3';db.innerHTML=`<h2>${score===3?'フィールドマスター！':'次の観戦に活かそう。'}</h2><p class="quiz-score">${score} / 3</p><button id="quiz-retry">もう一度挑戦する</button>`;}}if(ev.target.closest('#quiz-retry')){step=0;score=0;quiz();}});
 // No analytics events from local review builds.
 if(location.hostname==='lacrossemania.jp')document.addEventListener('click',ev=>{if(ev.target.closest('.match-card'))window.gtag?.('event','result_open',{surface:center?'results':'detail'});});
})();
