const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const C=require('../assets/experience-core.js');
const leagues=JSON.parse(fs.readFileSync(path.join(__dirname,'../site/assets/clubhouse-data.json'),'utf8'));
const identities=JSON.parse(fs.readFileSync(path.join(__dirname,'../site/assets/team-identities.json'),'utf8'));
test('common university abbreviations and kana match real data',()=>{
 for(const [name,queries] of [['早稲田大学',['早大','わせだ','ＷＡＳＥＤＡ']],['慶應義塾大学',['慶応','慶大','keio']],['日本体育大学',['日体大','ニッタイ']]])
  for(const q of queries)assert.ok(C.matches(name,q,identities),`${name} ${q}`);
 assert.equal(C.matches('明治大学','明学',identities),false);
});
test('legacy saved university names migrate to both teams, retaining demo selections',()=>{
 const expected=C.teams(leagues).filter(x=>x.t.team==='早稲田大学').map(x=>x.key);
 const demo=C.teams(leagues).find(x=>x.t.team==='明治大学').key;
 assert.deepEqual(new Set(C.migrateSaved(leagues,['早稲田大学','unknown',null],[demo,'bad'],null)),new Set([...expected,demo]));
 assert.deepEqual(C.migrateSaved(leagues,['早稲田大学'],[demo],[]),[],'explicit empty new favorites must not resurrect legacy teams');
 assert.deepEqual(C.migrateSaved(leagues,{},null,{malformed:true}),[]);
});
test('display preferences are constrained and retain women/regional selection',()=>{
 assert.deepEqual(C.preferences({sex:'女子',region:'関西'},['全国','関西']),{sex:'女子',region:'関西'});
 assert.deepEqual(C.preferences({sex:'bad',region:'bad'},['全国']),{sex:'すべて',region:'全国'});
});
test('scheduled dates use current JST date, never a build snapshot; missing scores stay pending',()=>{
 assert.equal(C.category({status:'scheduled',date:'2026-10-04'},'2026-10-05'),'pending');
 assert.equal(C.category({status:'scheduled',date:'2026-10-05'},'2026-10-05'),'upcoming');
 assert.equal(C.category({status:'played',date:'2026-10-05',home_score:0,away_score:0},'2026-10-05'),'results');
 assert.equal(C.category({status:'scheduled',date:''},'2026-10-05'),'pending');
});
test('compound result filtering uses selected gender and region and matches abbreviations',()=>{
 const rows=C.filter(leagues,{sex:'女子',region:'関東',view:'results',q:'早大'},identities,'2026-10-05');
 assert.ok(rows.length>0);assert.ok(rows.every(x=>x.l.code==='kanto-w'&&(x.m.home==='早稲田大学'||x.m.away==='早稲田大学')));
});
test('each generated match has a distinct existing URL, including undecided finals',()=>{
 for(const l of leagues){const ids=l.matches.map(m=>m.id);assert.equal(new Set(ids).size,ids.length,l.code);for(const id of ids)assert.ok(fs.existsSync(path.join(__dirname,'../site',l.code,'matches',id,'index.html')));}
});
test('next fixtures sort 9:00 before 11:00 with unknown times last',()=>{
 const base={status:'scheduled',date:'2026-10-05',home:'早稲田大学',away:'明治大学'};
 const data=[{code:'kanto-m',meta:{gender:'男子',region:'関東'},matches:['11:00','未定','9:00','00:00'].map(time=>({...base,time}))}];
 const rows=C.filter(data,{sex:'すべて',region:'全国',view:'upcoming',q:''},identities,'2026-10-05');
 assert.deepEqual(rows.map(x=>x.m.time),['9:00','11:00','未定','00:00']);
});
test('university marks use compact, distinct editorial abbreviations',()=>{
 const seen=new Map();for(const [name,d]of Object.entries(identities)){assert.ok(d.mark.length<=4,`${name} ${d.mark}`);if(['—','+'].includes(d.mark))continue;assert.ok(!seen.has(d.mark)||seen.get(d.mark)===d.identity,`${name} shares ${d.mark}`);seen.set(d.mark,d.identity);}
 // 公式データの表記揺れ（慶應大学）は年度によって消えるため、出現時のみ同一校扱いを確認する
 if(identities['慶應大学']){
  assert.equal(identities['慶應大学'].mark,identities['慶應義塾大学'].mark);
  assert.equal(identities['慶應大学'].color,identities['慶應義塾大学'].color);
  assert.ok(C.matches('慶應大学','慶応',identities));
 }
 assert.ok(C.matches('慶應義塾大学','慶応',identities));
});
