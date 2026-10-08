(function(root){
 'use strict';
 const normalize=s=>String(s||'').normalize('NFKC').toLowerCase().replace(/慶応/g,'慶應').replace(/[\s・･‐ー\-]/g,'').replace(/[ァ-ヶ]/g,c=>String.fromCharCode(c.charCodeAt(0)-0x60));
 function matches(name,query,identities){const q=normalize(query);return !q||[name,...(identities[name]?.aliases||[])].some(s=>normalize(s).includes(q));}
 function today(){return new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Tokyo'}).format(new Date());}
 function category(m,date){return m.status==='played'?'results':m.date&&m.date>=date?'upcoming':'pending';}
 function minutes(time,fallback){const match=/^(\d{1,2}):(\d{2})$/.exec(time||'');return match&&Number(match[1])<24&&Number(match[2])<60&&time!=='0:00'&&time!=='00:00'?Number(match[1])*60+Number(match[2]):fallback;}
 function teams(leagues){return leagues.flatMap(l=>Object.values(l.teams).map(t=>({l,t,key:l.code+'/'+t.slug})));}
 function migrateSaved(leagues,legacy,demo,current){
   const all=teams(leagues),valid=new Set(all.map(x=>x.key));
   if(Array.isArray(current))return [...new Set(current.filter(x=>typeof x==='string'&&valid.has(x)))];
   const result=Array.isArray(demo)?demo.filter(x=>valid.has(x)):[];
   if(Array.isArray(legacy))for(const name of legacy){if(typeof name!=='string')continue;for(const x of all)if(normalize(x.t.team)===normalize(name))result.push(x.key);}
   return [...new Set(result)];
 }
 function preferences(value,regions){return {sex:['すべて','男子','女子'].includes(value?.sex)?value.sex:'すべて',region:regions.includes(value?.region)?value.region:'全国'};}
 function filter(leagues,state,identities,date){
   return leagues.filter(l=>(!state.code||state.code===l.code)&&(state.code||state.sex==='すべて'||l.meta.gender===state.sex)&&(state.code||state.region==='全国'||state.region===l.meta.region))
    .flatMap(l=>l.matches.filter(m=>category(m,date)===state.view&&(matches(m.home,state.q,identities)||matches(m.away,state.q,identities))).map(m=>({l,m})))
    .sort((a,b)=>state.view==='upcoming'?(a.m.date||'').localeCompare(b.m.date||'')||minutes(a.m.time,1440)-minutes(b.m.time,1440):(b.m.date||'').localeCompare(a.m.date||'')||minutes(b.m.time,-1)-minutes(a.m.time,-1));
 }
 const api={normalize,matches,today,category,teams,migrateSaved,preferences,filter};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.LMExperience=api;
})(typeof window!=='undefined'?window:globalThis);
