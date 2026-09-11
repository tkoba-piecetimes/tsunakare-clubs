"""Clubhouse design, backed by the production daily league data."""
import json
from html import escape as e


def header(meta):
    year = meta.get('season_year', 2026)
    return f'''<header class="header"><a class="brand official-brand" href="/"><span class="brand-tick"></span><span>ラクロスマニア<small>JAPAN COLLEGE LACROSSE</small></span></a><nav aria-label="メインナビゲーション"><a href="/#results">試合・結果</a><a href="/#leagues">リーグ</a><a href="/articles/">読みもの</a><a href="/glossary/">用語辞典</a><a href="/videos/">動画</a><a href="/#support">部活の協賛</a></nav><a class="myteam" href="/#my-teams">マイチーム →</a></header><div class="seasonbar"><span><i></i> COLLEGE LACROSSE {year}</span><span>7地区。14リーグ。その一瞬を、見逃すな。</span><a href="/#support">部活の挑戦をツナカレでつなぐ ↗ <span>PR</span></a></div>'''


def mobile_nav():
    return '<nav class="mobile-nav" aria-label="モバイルメニュー"><a href="/#results">試合結果</a><a href="/articles/">読みもの</a><a href="/#support">部活の協賛</a><a href="/#my-teams">マイチーム</a></nav>'


def export_data(site, leagues):
    data = []
    for lg in leagues:
        data.append({k: lg[k] for k in ('code', 'label', 'meta', 'matches', 'standings', 'teams', 'hist')})
    (site / 'assets' / 'clubhouse-data.json').write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')


def portal(leagues, articles, meta, article_card):
    recent = sorted([(m['date'], lg, m) for lg in leagues for m in lg['matches']
                     if m['status'] == 'played' and m['date']], key=lambda x: x[0], reverse=True)
    featured = next((x for x in recent if abs(x[2]['home_score']-x[2]['away_score']) == 1), None)
    feature = ''
    if featured:
        d, lg, m = featured
        feature = f'''<a class="hero-match" href="/{lg['code']}/matches/{e(m['id'])}/"><div class="hero-match-top"><span>ϟ 1点を争った一戦</span><span>{d[5:].replace('-', '.')} / {lg['label']}</span></div><div class="hero-score"><span>{e(m['home'])}</span><b>{m['home_score']} <i>−</i> {m['away_score']}</b><span>{e(m['away'])}</span>↗</div></a>'''
    year = meta['season_year']
    cards = ''.join(f'''<a href="/{lg['code']}/" data-league-gender="{lg['meta']['gender']}"><span class="league-index">{i//2+1:02}</span><span>{lg['meta']['region']}<small>{lg['code'].split('-')[0].upper()}</small></span><span class="league-count">{len(lg['teams'])}<small>TEAMS</small></span>↗</a>''' for i, lg in enumerate(leagues))
    fallback = ''.join(f'<li><a href="/{lg["code"]}/matches/{e(m["id"])}/">{d} {e(lg["label"])}：{e(m["home"])} {m["home_score"]} − {m["away_score"]} {e(m["away"])}</a></li>' for d, lg, m in recent[:8])
    support_student = 'https://lp.tunakare.jp/s01/?utm_source=lacrossemania&utm_medium=referral&utm_campaign=listing#contact'
    support_company = 'https://tunakare.jp/sponsorship/search?activity=%E3%83%A9%E3%82%AF%E3%83%AD%E3%82%B9&utm_source=lacrossemania&utm_medium=referral&utm_campaign=sponsor'
    return f'''<div class="clubhouse-home"><section class="hero"><img src="/assets/hero.jpg" alt="ラクロスマニアのメインビジュアル" width="1440" height="768" fetchpriority="high"><div class="hero-shade"></div><div class="hero-copy"><div class="eyebrow"><span class="edition">{year}</span> COLLEGE LACROSSE JOURNAL</div><h1>その一瞬に、<br><span>すべてを。</span></h1><p>仲間の勝利も、ライバルの一戦も。<br>ラクロスに夢中な、すべての人へ。</p><div class="hero-actions"><a class="primary" href="#results">試合結果をチェック →</a><a class="hero-secondary" href="#support">部活の協賛について知る →</a></div><div class="hero-stats"><div><b>7</b><span>地区</span></div><div><b>{len(leagues)}</b><span>男女リーグ</span></div><div><b>{sum(len(lg['teams']) for lg in leagues)}</b><span>チーム</span></div></div></div>{feature}</section>
<div class="pagebody"><section class="results" id="results"><div class="section-head"><div><div class="eyebrow">01 / 全国の試合結果と日程</div><h2 class="display-heading">MATCH CENTER<span>試合の熱を、追いかけよう。</span></h2></div><span class="season-label">{year} SEASON</span></div><div id="match-hub"><p>最新の掲載結果</p><ul>{fallback}</ul><p>地区別の全結果・順位は<a href="#leagues">リーグ一覧</a>から確認できます。</p></div><p class="data-note">情報更新：{e(meta['fetched_at'][:10])}。スコアは連盟の公表データに基づき毎日更新します。ライブ速報ではありません。</p></section>
<section class="support-hub" id="support"><div class="support-heading"><div><span class="eyebrow">BEYOND THE SCORE / PR</span><h2>その熱量を、<br>部活の未来につなげよう。</h2><p>遠征も、練習も、次の挑戦も。<br>ツナカレが、学生団体と企業のつながりをつくります。</p></div><div class="official-partner"><img src="/assets/tunakare-logo.png" alt="ツナカレ" width="1380" height="364"><span>学生と企業をつなぐサービス</span></div></div><div class="support-options"><article class="support-option student"><span class="audience">部員・主将・マネージャーの方へ</span><h3>活動資金のこと、<br>チームだけで抱え込まない。</h3><p>遠征費や用具費、活動を知ってもらう方法。企業協賛について、部活の状況に合わせて相談できます。</p><div class="support-steps"><span><b>01</b>無料相談</span> → <span><b>02</b>活動・希望をヒアリング</span> → <span><b>03</b>企業とのつながりへ</span></div><a class="support-cta" href="{support_student}" target="_blank" rel="noopener sponsored" data-cta="support_student" data-position="support">ツナカレで協賛を無料相談 ↗</a><small>学生団体の利用は無料。相談フォームが別タブで開きます。</small></article><article class="support-option sponsor"><span class="audience">部活を応援したい企業の方へ</span><h3>頑張るチームの、<br>次の挑戦を支える。</h3><p>ラクロス部の協賛募集を探し、活動内容や条件を確認。応援したい団体との接点をつくれます。</p><a class="support-cta" href="{support_company}" target="_blank" rel="noopener sponsored" data-cta="support_sponsor" data-position="support">ラクロス部の協賛募集を見る ↗</a><small>ラクロスに絞った募集一覧が別タブで開きます。</small></article></div><p class="support-note">協賛条件・募集状況はツナカレでご確認ください。試合への掲載と協賛募集の有無は異なります。</p></section>
<div class="lower-grid"><section id="leagues" class="leagues"><div class="section-head"><div><div class="eyebrow">02 / 全国7地区・男女14リーグ</div><h2 class="display-heading">THE LEAGUES<span>あなたのリーグは、ここに。</span></h2></div></div><div class="gender-tabs league-sex"><button aria-pressed="true" data-gender="男子">男子リーグ</button><button aria-pressed="false" data-gender="女子">女子リーグ</button></div><div class="league-grid">{cards}</div></section><section id="challenge" class="challenge"><div class="challenge-top"><span class="eyebrow">LACROSSE IQ CHALLENGE</span></div><span class="challenge-watermark" aria-hidden="true">IQ</span><span class="challenge-tag">PLAY. LEARN. REPEAT.</span><h2>そのラクロス脳、<br>覚醒させよう。</h2><p>プレーの見方が変わる、ラクロスの基礎。<br>全問正解で「フィールドマスター」へ。</p><button class="primary" id="start-quiz">チャレンジする →</button><div class="challenge-footer"><span>約1分 / 無料</span><span>MY BEST <b id="quiz-best">0 / 3</b></span></div></section></div>
<section class="team-banner" id="my-teams"><div><div class="eyebrow">YOUR TEAM, YOUR STORY</div><h2>母校も、仲間も。あなたのマイチームに。</h2><p>気になるチームの結果をチェック。協賛募集もツナカレで探せます。</p></div><button id="choose-team">マイチームを選ぶ →</button></section><div id="saved-teams"></div>
<section class="home-articles"><div class="section-head"><div><div class="eyebrow">READ THE GAME</div><h2 class="display-heading">JOURNAL<span>ラクロスを、もっと深く。</span></h2></div><a href="/articles/">読みもの一覧 →</a></div><div class="digest">{''.join(article_card(a, '') for a in articles[:3])}</div></section></div></div><dialog id="club-dialog"><button class="dialog-close" aria-label="閉じる">×</button><div id="dialog-body"></div></dialog>'''
