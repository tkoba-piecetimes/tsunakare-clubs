/* Year-scoped, source-attributed database. No synthetic scores or inferred official ranks. */
(() => {
  'use strict';
  const root = document.querySelector('#archive-hub');
  if (!root) return;
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let data, state, limit = 30, standingsData, standingsLoading = false, standingsError = false;
  const regions = [['all','全国'],['kanto','関東'],['kansai','関西'],['tokai','東海'],['hokkaido','北海道'],['tohoku','東北'],['chushikoku','中四国'],['kyushu','九州']];
  const views = [['results','試合結果'],['teams','大学別成績'],['h2h','過去の直接対決'],['standings','順位・星取表'],['coverage','収録状況・出典']];
  function fromUrl() {
    const p = new URLSearchParams(location.search), league = p.get('league') || '';
    const y = p.get('year') || String(data.current_year);
    state = {year: y === 'all' || (+y >= 2021 && +y <= data.current_year) ? y : String(data.current_year),
      region: regions.some(([v]) => v === league.split('-')[0]) ? league.split('-')[0] : (p.get('region') || 'all'),
      gender: league.endsWith('-w') || p.get('gender') === 'w' ? 'w' : 'm',
      team: p.get('team') || '', opponent: p.get('opponent') || '',
      view: views.some(([v]) => v === p.get('view')) ? p.get('view') : 'results', table: p.get('table') === 'matrix' ? 'matrix' : 'rank', category: ''};
    if (!regions.some(([v]) => v === state.region)) state.region = 'all';
  }
  const scoped = () => data.seasons.filter(s => (state.year === 'all' || s.year === +state.year) && s.code.endsWith('-' + state.gender) && (state.region === 'all' || s.code.split('-')[0] === state.region));
  const option = (v, label, current) => `<option value="${esc(v)}" ${String(v) === String(current) ? 'selected' : ''}>${esc(label)}</option>`;
  const select = (id,label,options,current) => `<label>${label}<select id="${id}">${options.map(([v,l]) => option(v,l,current)).join('')}</select></label>`;
  const resultUrl = (s,m) => s.year === data.current_year ? `/${s.code}/matches/${encodeURIComponent(m.id)}/` : `/${s.code}/seasons/${s.year}/#match-${encodeURIComponent(m.id)}`;
  function stats(ms,team) {
    const pairs = ms.map(({m}) => m.home === team ? [m.home_score,m.away_score] : [m.away_score,m.home_score]);
    return {games:pairs.length,wins:pairs.filter(([a,b])=>a>b).length,draws:pairs.filter(([a,b])=>a===b).length,losses:pairs.filter(([a,b])=>a<b).length,gf:pairs.reduce((v,[a])=>v+a,0),ga:pairs.reduce((v,[,b])=>v+b,0)};
  }
  function resultList(ms) {
    if (!ms.length) return '<p class="archive-empty">この条件で収録された試合結果はありません。年度・地区・大学の条件を変更してください。</p>';
    return '<div class="archive-fixtures">' + ms.slice(0,limit).map(({s,m}) => `<a class="archive-fixture" href="${resultUrl(s,m)}"><div class="archive-fixture-top"><span>${m.date ? esc(m.date.replaceAll('-','.')) : s.year+'年 / 日付未確認'}</span><span>${esc(s.label)} / ${esc(m.category || '区分未記載')}</span></div><div class="archive-scoreline"><span>${esc(m.home)}</span><strong>${m.home_score}<i>−</i>${m.away_score}</strong><span>${esc(m.away)}</span><b aria-hidden="true">↗</b></div>${m.result_type === 'administrative' ? '<small>不戦勝等の公式記録</small>' : ''}${m.note ? `<small>${esc(m.note)}</small>` : ''}</a>`).join('') + '</div>' + (ms.length > limit ? `<button class="archive-more" id="archive-more">さらに30試合を表示（残り${ms.length-limit}）</button>` : '');
  }
  function sources(seasons) {
    return '<div class="archive-source-grid">'+seasons.map(s=>`<article><div><h3>${s.year}年 ${esc(s.label)}</h3><span class="archive-badge">${s.matches.some(m=>m.status==='played') ? s.coverage==='current'?'今季・更新中':'一部収録':'未収録'}</span></div><p><b>${s.matches.filter(m=>m.status==='played').length}</b>試合のスコア${s.date_unconfirmed ? ` / 日付未確認 ${s.date_unconfirmed}件` : ''}</p><p class="archive-source-links"><a href="${esc(s.source_url)}" target="_blank" rel="noopener">公式日程・結果 ↗</a><a href="${esc(s.standings_url)}" target="_blank" rel="noopener">公式順位・星取表 ↗</a></p><small>資料更新：${esc(s.source_updated_at || '公式資料内を参照')}</small></article>`).join('')+'</div>';
  }
  function currentStandings(s) {
    return {source_url:s.source_url,source_updated_at:s.source_updated_at,reference:true,blocks:Object.entries(s.standings || {}).map(([name,rows]) => ({name,matrix_available:true,rows:rows.map(r => ({...r,against:Object.fromEntries(rows.map(t=>[t.team,s.matches.filter(m=>m.status==='played' && m.category===name && ((m.home===r.team && m.away===t.team)||(m.away===r.team && m.home===t.team))).map(m=>{const [a,b]=m.home===r.team?[m.home_score,m.away_score]:[m.away_score,m.home_score];return `${a>b?'○':a<b?'●':'△'} ${a} − ${b}`;}).join(' / ')]))}))}))};
  }
  function standingSeasons(seasons) {
    return seasons.map(s=>{
      const official=standingsData?.seasons.find(x=>x.year===s.year && x.code===s.code);
      const doc=official || (s.year===data.current_year ? currentStandings(s) : null);
      if(!doc)return null;
      const blocks=doc.blocks.filter(b=>!state.team || b.rows.some(r=>r.team===state.team));
      const chart=doc.original_pages?.length && !doc.blocks.length;
      const chartMatches=chart && (!state.team || s.matches.some(m=>m.home===state.team || m.away===state.team));
      return blocks.length || chartMatches ? {...s,...doc,blocks} : null;
    }).filter(Boolean).sort((a,b)=>b.year-a.year || a.label.localeCompare(b.label,'ja'));
  }
  const standingValue=(r,key)=>r.rounds && key!=='rank' ? r.rounds.map(x=>x[key] ?? '—').join(' / ') : r[key] ?? '—';
  function standingTable(s,b) {
    const rows=[...b.rows].sort((a,b)=>(a.rank ?? Infinity)-(b.rank ?? Infinity));
    const columns=[['rank','順位'],['points','勝ち点'],['games','試合'],['wins','勝'],['draws','分'],['losses','敗'],['goal_diff','得失点差'],['goals_for','総得点']].filter(([k])=>k==='rank'||b.rows.some(r=>r[k]!=null));
    const head=columns.map(([k,l])=>`<th scope="col">${l}</th>${k==='rank'?'<th scope="col" class="archive-sticky-team">大学・チーム</th>':''}`).join('');
    const body=rows.map(r=>`<tr class="${r.team===state.team?'archive-selected-team':''}">${columns.map(([k])=>`<td${k==='rank'?' class="archive-rank-cell"':''}>${esc(standingValue(r,k))}</td>${k==='rank'?`<th scope="row" class="archive-sticky-team">${esc(r.team)}${r.team===state.team?'<span class="archive-you">選択中</span>':''}</th>`:''}`).join('')}</tr>`).join('');
    return `<div class="archive-table-wrap archive-standing-table" tabindex="0" role="region" aria-label="${s.year}年 ${esc(s.label)} ${esc(b.name)} 順位表"><table><caption>${s.year}年 ${esc(s.label)} / ${esc(b.name)}</caption><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
  }
  function matrixTable(s,b) {
    if(!b.matrix_available)return '<p class="archive-table-note">この大会はトーナメント等の形式です。順位表を確認するか、下の「公式資料をこのページで見る」を開いてください。</p>';
    const rows=b.rows;
    return `<div class="archive-table-wrap archive-matrix" tabindex="0" role="region" aria-label="${s.year}年 ${esc(s.label)} ${esc(b.name)} 星取表"><table><caption>${s.year}年 ${esc(s.label)} / ${esc(b.name)} 対戦スコア</caption><thead><tr><th scope="col" class="archive-sticky-team">大学・チーム</th>${rows.map(r=>`<th scope="col" class="${r.team===state.team?'archive-selected-col':''}">${esc(r.team)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr class="${r.team===state.team?'archive-selected-team':''}"><th scope="row" class="archive-sticky-team">${esc(r.team)}</th>${rows.map(t=>`<td class="${t.team===r.team?'archive-diagonal':''}">${t.team===r.team?'<span aria-label="同じチーム">／</span>':esc(r.against?.[t.team] || '—')}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  }
  function originalDocument(s,open=false) {
    if(s.reference)return '';
    const content=s.original_pages?.length ? s.original_pages.map(p=>`<figure><figcaption>公式資料 ${p.page}ページ</figcaption><div class="archive-original-image" tabindex="0" role="region" aria-label="公式資料 ${p.page}ページ。横にスクロールできます"><img src="${esc(p.src)}" alt="${s.year}年 ${esc(s.label)} 公式順位・大会表 ${p.page}ページ" loading="lazy"></div></figure>`).join('') : `<iframe data-official-src="${esc(s.source_url.replace(/#.*$/,''))}#view=FitH" title="${s.year}年 ${esc(s.label)} 公式順位・星取表" loading="lazy" referrerpolicy="no-referrer"></iframe>`;
    // Sheets are already reproduced as native tables. PDF diagrams retain
    // their geometry in a page-local viewer, with the source link alongside.
    if(!s.original_pages?.length && !/\.pdf(?:$|[?#])/.test(s.source_url))return '';
    return `<details class="archive-original" ${open?'open':''}><summary>公式資料をこのページで見る</summary>${content}<p><a href="${esc(s.source_url)}" target="_blank" rel="noopener">公式資料を別タブで開く ↗</a></p></details>`;
  }
  function standings(seasons) {
    if(!standingsData){
      if(standingsError)return '<p role="alert">順位表の読み込みに失敗しました。<button id="archive-retry-standings" class="archive-team-link">再読み込み</button></p>';
      return '<p role="status" class="archive-empty">公式の順位・星取表を読み込んでいます。</p>';
    }
    const docs=standingSeasons(seasons);
    let html=`<div class="archive-standings-intro"><div><h3>あの年の順位と、対戦の記録。</h3><p>${state.team?'選んだ大学が所属する部・ブロックを表示しています。':'年度ごとに開くと、部・ブロック別の表を確認できます。'}</p></div><div class="archive-table-switch" role="group" aria-label="表の種類"><button data-table="rank" aria-pressed="${state.table==='rank'}">順位表</button><button data-table="matrix" aria-pressed="${state.table==='matrix'}">星取表（対戦スコア）</button></div></div><p class="archive-table-note">過去年度は公式資料に記載された順位・数値です。順位は各表の対象範囲のもので、大会全体の最終順位とは異なる場合があります。空欄・資料内の計算エラーは「—」で表示します。${state.table==='matrix'?'スコアは左の大学から見た得点 − 失点。○は勝ち、●は負け、△は引き分けです。':''}</p>`;
    if(!docs.length)return html+'<p class="archive-empty">この条件の順位表は収録されていません。年度・地区・大学の条件を変更してください。</p>';
    html+='<div class="archive-seasons">'+docs.map((s,i)=>{
      const selected=s.blocks.flatMap(b=>b.rows.filter(r=>r.team===state.team).map(r=>`${b.name} / ${r.rank!=null?r.rank+'位':'順位の記載なし'}`));
      const blocks=s.blocks.map(b=>`<section class="archive-standing-block"><h4>${esc(b.name)}</h4>${state.table==='matrix'?matrixTable(s,b):standingTable(s,b)}${b.source_note?`<p class="archive-table-note">${esc(b.source_note)}</p>`:''}${b.rows.some(r=>r.rounds)?'<p class="archive-table-note">数値は公式表の「第1巡 / 第2巡」の順に掲載しています。</p>':''}</section>`).join('');
      return `<details class="archive-season" ${state.team||docs.length===1||i===0?'open':''}><summary><span class="archive-season-year">${s.year}<small>年</small></span><span class="archive-season-label">${esc(s.label)}<small>${esc(selected.join('・') || (s.blocks.length?s.blocks.length+'区分の順位・星取表':'当時のトーナメント表'))}</small></span><span class="archive-season-kind">${s.reference?'今季・参考順位':'公式記録'}</span><span class="archive-expand" aria-hidden="true">＋</span></summary><div class="archive-season-body"><div class="archive-standing-source"><span>${s.reference?'今季の収録スコアから算出した参考順位です。順位決定戦・直接対決等の公式順位決定規則は反映していません。':'出典：日本ラクロス協会 公開資料'}${s.source_updated_at?' / 資料更新 '+esc(s.source_updated_at):''}</span><a href="${esc(s.source_url)}" target="_blank" rel="noopener">公式資料 ↗</a></div>${blocks}${originalDocument(s,!s.blocks.length)}</div></details>`;
    }).join('')+'</div>';
    return html;
  }
  function loadStandings(){
    if(standingsData||standingsLoading)return;
    standingsLoading=true;standingsError=false;
    fetch('/assets/archive-standings.json').then(r=>{if(!r.ok)throw Error(r.status);return r.json();}).then(d=>{standingsData=d;}).catch(()=>{standingsError=true;}).finally(()=>{standingsLoading=false;if(state.view==='standings')render();});
  }
  function render(focusId) {
    const seasons=scoped(), all=seasons.flatMap(s=>s.matches.filter(m=>m.status==='played').map(m=>({s,m})));
    const officialTeams=state.view==='standings' ? seasons.flatMap(s=>standingsData?.seasons.find(x=>x.year===s.year&&x.code===s.code)?.blocks.flatMap(b=>b.rows.map(r=>r.team)) || Object.values(s.standings || {}).flatMap(rs=>rs.map(r=>r.team))) : [];
    const teams=[...new Set([...all.flatMap(({m})=>[m.home,m.away]),...officialTeams])].sort((a,b)=>a.localeCompare(b,'ja'));
    // Preserve a requested team across sparse seasons and disclose missing records.
    const opts=[['','すべての大学'],...([...new Set([...teams,state.team].filter(Boolean))]).map(t=>[t,t])];
    let ms=all.filter(({m})=>(!state.team||m.home===state.team||m.away===state.team) && (!state.opponent||m.home===state.opponent||m.away===state.opponent) && (!state.category||m.category===state.category));
    ms.sort((a,b)=>(b.m.date||`${b.s.year}-00-00`).localeCompare(a.m.date||`${a.s.year}-00-00`));
    const cats=[...new Set(all.map(({m})=>m.category).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'ja'));
    const yearOpts=[['all','全年度'],...Array.from({length:data.current_year-2020},(_,i)=>[String(data.current_year-i),`${data.current_year-i}年`])];
    let html=`<div class="archive-filter-panel"><div class="archive-primary-filters">${select('archive-year','年度',yearOpts,state.year)}${select('archive-gender','男子・女子',[['m','男子'],['w','女子']],state.gender)}${select('archive-region','地区',regions,state.region)}</div><div class="archive-secondary-filters">${select('archive-team','大学を選ぶ',opts,state.team)}${select('archive-opponent','対戦相手',[['','指定なし'],...([...new Set([...teams,state.opponent].filter(t=>t&&t!==state.team))]).map(t=>[t,t])],state.opponent)}${select('archive-category','掲載区分',[['','すべて'],...cats.map(t=>[t,t])],state.category)}</div></div><div class="archive-tabs" role="group" aria-label="記録の表示方法">${views.map(([v,l])=>`<button data-view="${v}" aria-pressed="${state.view===v}">${l}</button>`).join('')}</div><div class="archive-results-head"><div><p class="eyebrow">${state.year==='all'?'2021 — '+data.current_year:state.year+' SEASON'}</p><h2>${esc(state.team || (regions.find(([v])=>v===state.region)?.[1] || '全国'))}${state.opponent?' × '+esc(state.opponent):' / '+(state.gender==='m'?'男子':'女子')}</h2></div><p role="status"><b>${ms.length.toLocaleString()}</b> 試合収録</p></div>`;
    if (state.team && state.view!=='standings') {
      const s=stats(ms,state.team);
      html+=`<div class="archive-stats"><div><b>${s.wins}<small>勝</small>${s.draws}<small>分</small>${s.losses}<small>敗</small></b><span>${esc(state.team)}から見た勝敗</span></div><div><b>${s.gf}<small>−</small>${s.ga}</b><span>得点 − 失点</span></div><div><b>${new Set(ms.map(({s})=>s.year)).size}<small>年度</small></b><span>この条件で結果を収録</span></div></div>`;
    }
    if(state.view!=='standings') html+='<p class="archive-coverage-note">集計は収録済みの公式スコアが対象です。プレーオフ・入替戦・不戦勝等を含みます。過去年度は一部収録のため、全試合・公式順位を表すものではありません。</p>';
    if(state.view==='results') html+=resultList(ms);
    if(state.view==='h2h') html+=state.team&&state.opponent?resultList(ms):'<p class="archive-empty">上の「大学を選ぶ」と「対戦相手」で2校を選ぶと、過去の直接対決と通算勝敗を表示します。「全年度」で2021年からの記録を横断できます。</p>';
    if(state.view==='teams') {
      let rows='';
      if(state.team) {
        for(const y of [...new Set(seasons.map(s=>s.year))].sort((a,b)=>b-a)) {
          const subset=ms.filter(({s})=>s.year===y),st=stats(subset,state.team);
          rows+=`<tr><th>${y}年</th><td>${st.games}</td><td>${st.games?`${st.wins}勝 ${st.draws}分 ${st.losses}敗`:'収録なし'}</td><td>${st.games?st.gf+' − '+st.ga:'—'}</td></tr>`;
        }
      } else for(const t of [...new Set(ms.flatMap(({m})=>[m.home,m.away]))].sort((a,b)=>a.localeCompare(b,'ja'))) {
        const st=stats(ms.filter(({m})=>m.home===t||m.away===t),t);
        rows+=`<tr><th><button class="archive-team-link" data-team="${esc(t)}">${esc(t)} →</button></th><td>${st.games}</td><td>${st.wins}勝 ${st.draws}分 ${st.losses}敗</td><td>${st.gf} − ${st.ga}</td></tr>`;
      }
      html+=`<div class="archive-table-wrap"><table><thead><tr><th>${state.team?'年度':'大学・チーム'}</th><th>収録試合</th><th>勝敗</th><th>得点 − 失点</th></tr></thead><tbody>${rows}</tbody></table></div>`;
    }
    if(state.view==='standings') html+=standings(seasons);
    if(state.view==='coverage') html+='<h3>年度・地区別の収録状況</h3><p>スコアを確認できた記録から公開しています。中止・延期・未確定の対戦枠は試合結果の集計に含めていません。日付が確認できない場合もスコアの出典をたどれます。</p>'+sources(seasons);
    root.innerHTML=html;
    root.classList.toggle('archive-show-standings',state.view==='standings');
    if(state.view==='standings'){
      root.querySelector('.archive-results-head>p').textContent=standingsData ? `${standingSeasons(seasons).length}件の年度・地区別記録` : '順位表を読み込み中';
      root.querySelector('.archive-results-head h2').textContent=`${state.team || regions.find(([v])=>v===state.region)?.[1] || '全国'} / ${state.gender==='m'?'男子':'女子'}`;
      if(!standingsError)loadStandings();
    }
    if(focusId) document.getElementById(focusId)?.focus({preventScroll:true});
  }
  function save(focusId) {
    const p=new URLSearchParams({year:state.year,gender:state.gender,region:state.region,view:state.view});
    if(state.team)p.set('team',state.team);if(state.opponent)p.set('opponent',state.opponent);
    if(state.view==='standings')p.set('table',state.table);
    history.replaceState(null,'','/archive/?'+p);limit=30;render(focusId);
  }
  root.addEventListener('change',e=>{
    const key=e.target.id.replace('archive-','');if(!(key in state))return;
    state[key]=e.target.value;
    if(['year','region','gender'].includes(key))state.category='';
    if(key==='gender'){state.team='';state.opponent='';}
    if(state.team===state.opponent)state.opponent='';
    save(e.target.id);
  });
  root.addEventListener('click',e=>{
    const v=e.target.closest('[data-view]');if(v){state.view=v.dataset.view;save();root.querySelector(`[data-view="${state.view}"]`)?.focus({preventScroll:true});}
    const t=e.target.closest('[data-team]');if(t){state.team=t.dataset.team;save('archive-team');}
    if(e.target.id==='archive-more'){limit+=30;render();document.querySelector('#archive-more')?.focus({preventScroll:true});}
    const table=e.target.closest('[data-table]');if(table){state.table=table.dataset.table;save();root.querySelector(`[data-table="${state.table}"]`)?.focus({preventScroll:true});}
    if(e.target.id==='archive-retry-standings'){standingsError=false;render();}
  });
  root.addEventListener('toggle',e=>{
    if(e.target.open && e.target.matches('.archive-original'))e.target.querySelectorAll('iframe[data-official-src]').forEach(frame=>{frame.src=frame.dataset.officialSrc;delete frame.dataset.officialSrc;});
  },true);
  window.addEventListener('popstate',()=>{if(data){fromUrl();render();}});
  fetch('/assets/archive-data.json').then(r=>{if(!r.ok)throw Error(r.status);return r.json();}).then(d=>{data=d;fromUrl();render();}).catch(()=>{root.innerHTML='<p role="alert">データの読み込みに失敗しました。ページを再読み込みするか、下の「年度・地区別の記録一覧」から確認してください。</p>';});
})();
