# -*- coding: utf-8 -*-
# Builds ru/index.html from ../index.html. Run: python3 ru/translate.py
import re,json,sys,os
here=os.path.dirname(os.path.abspath(__file__)); src=open(os.path.join(here,"..","index.html"),encoding="utf-8").read()
T=[
('<html lang="en">','<html lang="ru">'),
('<title>SEZ services made simple and digital · Central Asia</title>','<title>Простые и цифровые услуги СЭЗ · Центральная Азия</title>'),
# nav
('<a class="topbar-brand" href="#top"><span>SEZ</span> › Central Asia</a>','<a class="topbar-brand" href="#top"><span>СЭЗ</span> › Центральная Азия</a>'),
('<a class="navlink" href="#why">Why</a>','<a class="navlink" href="#why">Зачем</a>'),
('<a class="navlink" href="#assessment">The assessment</a>','<a class="navlink" href="#assessment">Оценка</a>'),
('<a class="navlink" href="#nar-regional">Regional approach</a>','<a class="navlink" href="#nar-regional">Региональный подход</a>'),
('<a class="navlink" href="#nar-practica">Experiences</a>','<a class="navlink" href="#nar-practica">Примеры</a>'),
('<a class="navlink" href="#apply">Apply</a>','<a class="navlink" href="#apply">Подать заявку</a>'),
('<span class="lang-switch" aria-label="Language"><a class="on" href="#" aria-current="page" lang="en">EN</a><span class="sep">|</span><a href="ru/" lang="ru">RU</a></span>',
 '<span class="lang-switch" aria-label="Язык"><a href="../" lang="en">EN</a><span class="sep">|</span><a class="on" href="#" aria-current="page" lang="ru">RU</a></span>'),
('<button class="btn-print" id="btn-print" type="button">Print / PDF</button>','<button class="btn-print" id="btn-print" type="button">Печать / PDF</button>'),
# hero
('<h1 id="nar-hero">SEZ services made<br>simple and digital</h1>','<h1 id="nar-hero">Услуги СЭЗ:<br>просто и в цифре</h1>'),
('<div class="audience">A needs assessment for the zones of Central Asia, proposed by the WFZO Regional Office for Central Asia with the technical support of UNCTAD and UNITAR.</div>','<div class="audience">Оценка потребностей зон Центральной Азии по предложению Регионального офиса WFZO для Центральной Азии при технической поддержке ЮНКТАД и ЮНИТАР.</div>'),
('rel="noopener">Apply for the assessment →</a>\n          <a class="hero-cta secondary" href="#nar-practica">View reference experiences</a>','rel="noopener">Подать заявку на оценку →</a>\n          <a class="hero-cta secondary" href="#nar-practica">Посмотреть примеры</a>'),
# why
('<p class="scope-eyebrow">Why do an assessment</p>','<p class="scope-eyebrow">Зачем нужна оценка</p>'),
('<h2 class="scope-title" id="scope-title">Every country has its own procedure for the same service</h2>','<h2 class="scope-title" id="scope-title">В каждой стране своя процедура для одной и той же услуги</h2>'),
('<p class="scope-aside">This assessment is the first step. It documents, country by country, what is in place, what is already digital and what the country wants to improve first. Each country applies individually and receives its own report. The regional picture is built one country at a time.</p>',
 '<p class="scope-aside">Оценка — первый шаг. Она фиксирует, страна за страной, что уже есть, что уже переведено в цифру и что страна хочет улучшить в первую очередь. Каждая страна подаёт заявку самостоятельно и получает собственный отчёт. Региональная картина складывается по одной стране за раз.</p>'),
('<p class="scope-copy">The zones of Central Asia serve the same investors and offer them the same services: land and buildings, registration, incentives, customs regimes, renewals. Each country has built its own way of delivering them, and an investor who works in several countries relearns the procedure each time. Making these procedures transparent, simple and digital is therefore more than a technical improvement. It is an instrument of investment policy, and it works best when what is done in one country can be adopted by the others.</p>',
 '<p class="scope-copy">Зоны Центральной Азии работают с одними и теми же инвесторами и предлагают им одни и те же услуги: земля и здания, регистрация, льготы, таможенные режимы, продление. Каждая страна выстроила свой порядок их предоставления, и инвестор, работающий в нескольких странах, каждый раз осваивает процедуру заново. Сделать эти процедуры прозрачными, простыми и цифровыми — значит не просто улучшить технику. Это инструмент инвестиционной политики, и он работает лучше всего, когда сделанное в одной стране могут перенять другие.</p>'),
# three questions
('<p class="regional-eyebrow">What the assessment covers</p>','<p class="regional-eyebrow">Что охватывает оценка</p>'),
('<h2 class="regional-title" id="nar-services">Three questions</h2>','<h2 class="regional-title" id="nar-services">Три вопроса</h2>'),
('<h3>What is in place?</h3>\n          <p>Rules, responsible institutions, procedures.</p>','<h3>Что уже есть?</h3>\n          <p>Правила, ответственные органы, процедуры.</p>'),
('<h3>What is digital?</h3>\n          <p>Which services are available online.</p>','<h3>Что в цифре?</h3>\n          <p>Какие услуги доступны онлайн.</p>'),
('<h3>What are the priorities?</h3>\n          <p>The improvements the country wants first.</p>','<h3>Каковы приоритеты?</h3>\n          <p>Улучшения, которых страна хочет в первую очередь.</p>'),
# after
('<p class="collaboration-eyebrow">After the assessment</p>','<p class="collaboration-eyebrow">После оценки</p>'),
('<h2 class="collaboration-title" id="collaboration-title">Transparency, simplification, digitalisation</h2>','<h2 class="collaboration-title" id="collaboration-title">Прозрачность, упрощение, цифровизация</h2>'),
('<p class="collaboration-lead">A digital zone service means an investor can go from choosing a location to launching a project without leaving the digital environment: available land and buildings, infrastructure and connection costs, incentives, registration, customs regime, all online, with one process and one verified certificate at the end. Reaching that takes three steps: make the procedures transparent, simplify them, then digitise them. Digitising a procedure nobody has simplified only makes it faster to get wrong.</p>',
 '<p class="collaboration-lead">Цифровая услуга зоны означает, что инвестор проходит путь от выбора площадки до запуска проекта, не выходя из цифровой среды: свободные земля и здания, инфраструктура и стоимость подключения, льготы, регистрация, таможенный режим — всё онлайн, в одном процессе, с одним проверяемым сертификатом на выходе. Для этого нужны три шага: сделать процедуры прозрачными, упростить их, затем перевести в цифру. Оцифровать процедуру, которую никто не упростил, — значит лишь быстрее получить ошибку.</p>'),
('<h3>Transparency</h3>','<h3>Прозрачность</h3>'),
("<p>Publish each procedure from the user's point of view: steps, documents, costs, timelines, legal basis, kept up to date by the competent authority.</p>",'<p>Опубликовать каждую процедуру с точки зрения пользователя: шаги, документы, стоимость, сроки, правовая основа; поддерживается в актуальном состоянии компетентным органом.</p>'),
('<h3>Simplification</h3>','<h3>Упрощение</h3>'),
('<p>Remove steps and requirements that add no control. Clarify who is responsible for what.</p>','<p>Убрать шаги и требования, которые не добавляют контроля. Уточнить, кто за что отвечает.</p>'),
('<h3>Digitalisation</h3>','<h3>Цифровизация</h3>'),
("<p>Turn the simplified procedures into online services: applications, approvals, payments, renewals. UNCTAD's eRegistrations platform is one available tool; the country chooses what fits its law and capacity.</p>",'<p>Превратить упрощённые процедуры в онлайн-услуги: заявки, согласования, платежи, продление. Платформа ЮНКТАД eRegistrations — один из доступных инструментов; страна выбирает то, что соответствует её законодательству и возможностям.</p>'),
# regional
('<p class="scope-eyebrow">Regional approach</p>','<p class="scope-eyebrow">Региональный подход</p>'),
('<h2 class="scope-title" id="regional-approach-title">Start in one country, extend to the region</h2>','<h2 class="scope-title" id="regional-approach-title">Начать в одной стране, распространить на регион</h2>'),
('<div class="scope-copy"><p>The first country does not only improve its own procedures. It produces a <strong>reference procedure</strong> for each zone service: a standard, simplified sequence of steps, documents and timelines that the other countries can adopt and adapt. What transfers is the method, the reference procedure, the service design and the tools. What stays national is the legal basis and the institutions.</p><p style="margin-top:1rem;">Over time this gives the region what investors are asking for: the same steps wherever the zone is, while each country keeps its own policy, incentives and specialisation. Cooperation between zones starts with procedures investors can recognise from one country to the next.</p></div>',
 '<div class="scope-copy"><p>Первая страна не только улучшает собственные процедуры. Она создаёт <strong>эталонную процедуру</strong> для каждой услуги зоны: стандартную упрощённую последовательность шагов, документов и сроков, которую другие страны могут перенять и адаптировать. Передаются метод, эталонная процедура, дизайн услуги и инструменты. Национальными остаются правовая основа и институты.</p><p style="margin-top:1rem;">Со временем регион получает то, о чём просят инвесторы: одни и те же шаги, где бы ни находилась зона, при том что каждая страна сохраняет свою политику, льготы и специализацию. Сотрудничество между зонами начинается с процедур, которые инвестор узнаёт от одной страны к другой.</p></div>'),
# examples
('<p class="example-eyebrow">In practice</p>','<p class="example-eyebrow">На практике</p>'),
('<h2 class="example-title">Reference experiences</h2>','<h2 class="example-title">Примеры из практики</h2>'),
('<p class="example-lead">These experiences illustrate possible approaches. They are not proposed projects for Central Asia and would not be replicated without adaptation to each country&rsquo;s priorities, institutions and legal framework.</p>','<p class="example-lead">Эти примеры иллюстрируют возможные подходы. Это не предлагаемые проекты для Центральной Азии, и они не будут воспроизводиться без адаптации к приоритетам, институтам и правовой базе каждой страны.</p>'),
('<span class="reference-country-label">Central Asia</span>\n            <h3>Transparency of procedures</h3>','<span class="reference-country-label">Центральная Азия</span>\n            <h3>Прозрачность процедур</h3>'),
('<p>The Central Asia Gateway (<a href="https://infotradecentralasia.org/" target="_blank" rel="noopener">infotradecentralasia.org</a>) brings together the national trade portals of the five countries. For each import, export or transit procedure it shows what the user needs to know: steps, required documents, institutions and contact persons, costs and legal basis. It covers trade, not zones. The same regional approach can be applied to zone procedures.</p>',
 '<p>Central Asia Gateway (<a href="https://infotradecentralasia.org/" target="_blank" rel="noopener">infotradecentralasia.org</a>) объединяет национальные торговые порталы пяти стран. Для каждой процедуры импорта, экспорта или транзита он показывает то, что нужно знать пользователю: шаги, требуемые документы, органы и контактные лица, стоимость и правовую основу. Он охватывает торговлю, а не зоны. Тот же региональный подход применим к процедурам зон.</p>'),
('<li>Kazakhstan</li><li>Kyrgyzstan</li><li>Tajikistan</li><li>Turkmenistan</li><li>Uzbekistan</li>','<li>Казахстан</li><li>Кыргызстан</li><li>Таджикистан</li><li>Туркменистан</li><li>Узбекистан</li>'),
('<span class="reference-country-label">Jamaica</span>\n                <h3>Digitalisation of zone services</h3>','<span class="reference-country-label">Ямайка</span>\n                <h3>Цифровизация услуг зон</h3>'),
("<p>Jamaica's institutional set-up is simpler than most in Central Asia. What matters here is what the investor sees at the end: one entry point, every zone on a map, one process, one certificate.</p>",'<p>Институциональное устройство Ямайки проще, чем в большинстве стран Центральной Азии. Важно то, что видит инвестор в итоге: одна точка входа, все зоны на карте, один процесс, один сертификат.</p>'),
('<strong>Public zone portal</strong>\n                    <span>A front door for investors and zone services.</span>','<strong>Публичный портал зон</strong>\n                    <span>Единый вход для инвесторов и услуг зон.</span>'),
('<strong>Interactive zone map</strong>\n                    <span>Explore approved zones, developers, locations and industries.</span>','<strong>Интерактивная карта зон</strong>\n                    <span>Утверждённые зоны, девелоперы, расположение и отрасли.</span>'),
('<strong>Zone details</strong>\n                    <span>Review status, available land and buildings, occupants and service providers.</span>','<strong>Карточка зоны</strong>\n                    <span>Статус, свободные земля и здания, резиденты и поставщики услуг.</span>'),
('<strong>Digital certificate</strong>\n                    <span>See verified outputs once the process is approved.</span>','<strong>Цифровой сертификат</strong>\n                    <span>Проверяемый результат после утверждения.</span>'),
# apply band
('<h2 class="section-title" id="nar-collab">Apply</h2>','<h2 class="section-title" id="nar-collab">Подать заявку</h2>'),
('<strong>Any country can start.</strong>\n          <span>Apply, receive your national report, and decide afterwards whether to go further.</span>','<strong>Начать может любая страна.</strong>\n          <span>Подайте заявку, получите национальный отчёт и затем решите, идти ли дальше.</span>'),
('rel="noopener">Apply for the assessment →</a>\n      </div>','rel="noopener">Подать заявку на оценку →</a>\n      </div>'),
('The assessment and the national report are provided by the partners. This initiative is exploratory and creates no commitment for participants or the partners. Regional results are presented in consolidated form; any reference to an individual country requires its consent.','Оценка и национальный отчёт предоставляются партнёрами. Инициатива носит предварительный характер и не создаёт обязательств ни для участников, ни для партнёров. Региональные результаты представляются в обобщённом виде; любое упоминание отдельной страны требует её согласия.'),
# footer
('An initiative of the WFZO Regional Office for Central Asia, with the technical support of UNCTAD and UNITAR, Digital Government Programme','Инициатива Регионального офиса WFZO для Центральной Азии при технической поддержке ЮНКТАД и ЮНИТАР, Программа цифрового правительства'),
('This page is a basis for discussion and an invitation to express interest. It does not constitute a commitment by UNCTAD or any United Nations entity. Further technical assistance is subject to mandates, resources and formal agreements. The designations employed do not imply any judgement concerning the legal status of any country or territory.','Эта страница — основа для обсуждения и приглашение выразить заинтересованность. Она не является обязательством ЮНКТАД или какой-либо структуры Организации Объединённых Наций. Дальнейшая техническая помощь зависит от мандатов, ресурсов и официальных соглашений. Употребляемые обозначения не подразумевают какого-либо суждения о правовом статусе какой-либо страны или территории.'),
# Gulnura widgets
('Gulnura guides you</button>','Гульнура проведёт вас</button>'),
('<span class="md-name">Questions?</span>','<span class="md-name">Вопросы?</span>'),
('aria-label="Ask Gulnura"','aria-label="Спросить Гульнуру"'),
('<b>Gulnura</b><small>Assistant · SEZ Central Asia · UNCTAD + WFZO</small>','<b>Гульнура</b><small>Ассистент · СЭЗ Центральная Азия · ЮНКТАД + WFZO</small>'),
('<button>What does the assessment involve?</button><button>What does my country get?</button><button>What was done in Jamaica?</button><button>How do we apply?</button>','<button>Что включает оценка?</button><button>Что получает моя страна?</button><button>Что сделано на Ямайке?</button><button>Как подать заявку?</button>'),
('placeholder="Type your question…"','placeholder="Введите вопрос…"'),
('>Send</button>','>Отправить</button>'),
('🎤 Talk to Gulnura</button>','🎤 Поговорить с Гульнурой</button>'),
('<b>Gulnura</b><small>walks you through the proposal</small>','<b>Гульнура</b><small>проведёт вас по предложению</small>'),
]
out=src
missing=[]
for a,b in T:
    if a not in out: missing.append(a[:70]); continue
    out=out.replace(a,b)
# asset paths: ru/ sits inside the page folder
out=re.sub(r'(src|href)="assets/',r'\1="../assets/',out)
out=out.replace("url('assets/","url('../assets/").replace('url("assets/','url("../assets/')
out=out.replace('audio:"../assets/gulnura-audio/','audio:"../assets/gulnura-audio-ru/')
# Russian greeting + narration + agent
G=json.load(open(os.path.join(here,'ru-texts.json'),encoding='utf-8'))
out=re.sub(r'GREET="(?:[^"\\]|\\.)*"','GREET='+json.dumps(G['greet'],ensure_ascii=False),out)
m=re.search(r'"Hello, I\'m Gulnura\.(?:[^"\\]|\\.)*"',out)
a=out.index('  var SEGS=['); b=out.index('  ];',a)+4
lines=['  var SEGS=[']
for i,seg in enumerate(G['segs'],1):
    extra=' cycleTabs:true,' if seg['block']=='nar-practica' else ''
    lines.append(f'    {{block:"{seg["block"]}", audio:"../assets/gulnura-audio-ru/seg{i}.mp3",{extra} text:{json.dumps(seg["text"],ensure_ascii=False)}}},')
lines.append('  ];'); out=out[:a]+'\n'.join(lines)+out[b:]
out=re.sub(r'<div class="b ai">(?:[^<]|<(?!/div>))*</div>','<div class="b ai">'+G['greet']+'</div>',out,count=1)
out=out.replace('var AGENT="agent_5801m1040rvjf6w961q4r8eh5gq4"','var AGENT="'+G['agent']+'"')
# status strings in chat JS
for a,b in [("'Connecting microphone…'","'Подключаю микрофон…'"),("'Connecting…'","'Подключаюсь…'"),("'Listening…'","'Слушаю…'"),("'Gulnura is answering…'","'Гульнура отвечает…'"),("'🎤 Talk to Gulnura'","'🎤 Поговорить с Гульнурой'")]:
    out=out.replace(a,b)
open(os.path.join(here,'index.html'),'w',encoding='utf-8').write(out)
print('written; untranslated:',len(missing)); [print(' -',m) for m in missing]
