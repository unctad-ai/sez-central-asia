# -*- coding: utf-8 -*-
# Builds kk/index.html from ../index.html. Run: python3 kk/translate.py
# Self-contained (no external json). The Kazakh page keeps Gulnura's chat but not the
# guided tour (no Kazakh narration audio/video yet): the tour button, narration bar,
# bust videos and their engine are removed here.
import re, os, sys

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "..", "index.html"), encoding="utf-8").read()

T = [
('<html lang="en">', '<html lang="kk">'),
('<title>Central Asia&rsquo;s zones are entering a new stage · WFZO</title>',
 '<title>Орталық Азия аймақтары жаңа кезеңге өтуде · WFZO</title>'),
# nav
('<a class="topbar-brand" href="#top"><span>WFZO</span> › Central Asia</a>',
 '<a class="topbar-brand" href="#top"><span>WFZO</span> › Орталық Азия</a>'),
('aria-label="Menu"', 'aria-label="Мәзір"'),
('<nav class="topbar-nav" aria-label="Sections">', '<nav class="topbar-nav" aria-label="Бөлімдер">'),
('<a class="navlink" href="#why">Why</a>', '<a class="navlink" href="#why">Неліктен</a>'),
('<a class="navlink" href="#assessment">The assessment</a>', '<a class="navlink" href="#assessment">Бағалау</a>'),
('<a class="navlink" href="#nar-practica">Examples</a>', '<a class="navlink" href="#nar-practica">Мысалдар</a>'),
('<a class="navlink" href="#apply">Questionnaire</a>', '<a class="navlink" href="#apply">Сауалнама</a>'),
('<span class="lang-switch" aria-label="Language"><a class="on" href="#" aria-current="page" lang="en">EN</a><span class="sep">|</span><a href="kk/" lang="kk">ҚАЗ</a><span class="sep">|</span><a href="ru/" lang="ru">РУС</a></span>',
 '<span class="lang-switch" aria-label="Тіл"><a href="../" lang="en">EN</a><span class="sep">|</span><a class="on" href="#" aria-current="page" lang="kk">ҚАЗ</a><span class="sep">|</span><a href="../ru/" lang="ru">РУС</a></span>'),
('<button class="btn-print" id="btn-print" type="button">Print / PDF</button>',
 '<button class="btn-print" id="btn-print" type="button">Басып шығару / PDF</button>'),
# hero
('<h1 id="nar-hero">Central Asia&rsquo;s zones are <br>entering a new stage</h1>',
 '<h1 id="nar-hero">Орталық Азия аймақтары <br>жаңа кезеңге өтуде</h1>'),
('<div class="audience">A regional needs assessment to identify priorities and possible pathways for cooperation.</div>',
 '<div class="audience">Басымдықтар мен ынтымақтастықтың ықтимал жолдарын айқындауға арналған өңірлік қажеттіліктерді бағалау.</div>'),
('An initiative of the WFZO Regional Office for Central Asia, with technical support from UNCTAD and UNITAR.</div>',
 'WFZO Орталық Азия өңірлік кеңсесінің бастамасы, ЮНКТАД пен ЮНИТАР-дың техникалық қолдауымен.</div>'),
('rel="noopener">Answer the questionnaire →</a>\n          <a class="hero-cta secondary" href="#nar-practica">See working examples</a>',
 'rel="noopener">Сауалнамаға жауап беріңіз →</a>\n          <a class="hero-cta secondary" href="#nar-practica">Мысалдарды қараңыз</a>'),
# Yerbol band
('aria-label="Listen to the address by Yerbol Bukharbayev"',
 'aria-label="Ербол Бұхарбаевтың сөзін тыңдау"'),
('<b>Yerbol Bukharbayev</b>', '<b>Ербол Бұхарбаев</b>'),
('Head of the Regional Office for Central Asia, World Free Zones Organization &middot; Address to the International Investment Forum on the digitalization of free economic zones, Tajikistan, August 2026',
 'Дүниежүзілік еркін аймақтар ұйымының (World FZO) Орталық Азия өңірлік кеңсесінің басшысы &middot; Еркін экономикалық аймақтарды цифрландыру жөніндегі халықаралық инвестициялық форумдағы сөзі, Тәжікстан, 2026 жылғы тамыз'),
('id="yb-label">Listen to the address<', 'id="yb-label">Сөзін тыңдау<'),
('id="yb-time">9:53<', 'id="yb-time">7:12<'),
('total="9:53"', 'total="7:12"'),
('src="assets/yerbol-audio/yerbol-en.mp3"', 'src="assets/yerbol-audio/yerbol-kk.mp3"'),
# why
('<p class="scope-eyebrow">Why this assessment</p>', '<p class="scope-eyebrow">Бұл бағалау неліктен қажет</p>'),
('<h2 class="scope-title" id="scope-title">Simpler, more transparent, digital zone services</h2>',
 '<h2 class="scope-title" id="scope-title">Қарапайым, ашық және цифрлық аймақ қызметтері</h2>'),
('<p class="scope-aside">An investor should understand where to go, what they will receive, how long it will take, and who is responsible for the result. The assessment starts there: it documents, country by country, what is in place, what is already digital and what each country wants to improve first, so that cooperation is built on evidence.</p>',
 '<p class="scope-aside">Инвестор қайда бару керегін, не алатынын, қанша уақыт кететінін және нәтижеге кім жауап беретінін түсінуі тиіс. Бағалау осыдан басталады: ол елден елге не бар екенін, ненің цифрланғанын және әр елдің алдымен нені жақсартқысы келетінін құжаттайды — ынтымақтастық осылайша дәлелдерге сүйеніп құрылады.</p>'),
('<p class="scope-copy">The next stage for the region&rsquo;s zones goes beyond tax incentives and infrastructure: a digital, integrated, internationally oriented zone. An investor should be able to go from choosing a location to launching a project in a digital environment, with land and buildings, connection costs, incentives, registration and customs regimes all online. Digitalisation is not simply a technological tool; it is becoming an instrument of investment policy.<br><br>And investors no longer choose one country and one market: they look at the region as a whole. Production may take place in one country, inputs may come from another, and the logistics route may cross a third. That calls for moving from competition between individual zones towards cooperation between zones across countries, so that an investor who comes to Central Asia sees a single, clear, digital and competitive investment region.</p>',
 '<p class="scope-copy">Өңір аймақтарының келесі кезеңі салықтық жеңілдіктер мен инфрақұрылымнан әрі асады: цифрлық, кіріктірілген, халықаралық бағдардағы аймақ. Инвестор орын таңдаудан жобаны іске қосуға дейінгі жолды цифрлық ортада өтуі тиіс: жер мен ғимараттар, қосылу құны, жеңілдіктер, тіркеу және кеден режимдері — барлығы онлайн. Цифрландыру — жай технологиялық құрал емес; ол инвестициялық саясаттың құралына айналып келеді.<br><br>Инвесторлар енді бір ел мен бір нарықты ғана таңдамайды: олар өңірге тұтас қарайды. Өндіріс бір елде, шикізат екінші елден, логистикалық бағыт үшінші ел арқылы өтуі мүмкін. Бұл жекелеген аймақтар арасындағы бәсекеден елдер арасындағы аймақтар ынтымақтастығына көшуді талап етеді — сонда Орталық Азияға келген инвестор біртұтас, түсінікті, цифрлық және бәсекеге қабілетті инвестициялық өңірді көреді.</p>'),
# three questions
('<p class="regional-eyebrow">What the assessment covers</p>', '<p class="regional-eyebrow">Бағалау нені қамтиды</p>'),
('<h2 class="regional-title" id="nar-services">Three questions</h2>', '<h2 class="regional-title" id="nar-services">Үш сұрақ</h2>'),
('<h3>What exists today?</h3>\n          <p>Rules, responsible institutions, procedures, and which of them are already digital.</p>',
 '<h3>Бүгінде не бар?</h3>\n          <p>Қағидалар, жауапты мекемелер, рәсімдер және олардың қайсысы цифрланған.</p>'),
('<h3>What do you want to achieve?</h3>\n          <p>The improvements the country wants first, and how urgent they are.</p>',
 '<h3>Неге қол жеткізгіңіз келеді?</h3>\n          <p>Ел бірінші кезекте қалайтын жақсартулар және олардың қаншалықты шұғыл екені.</p>'),
('<h3>What is underway?</h3>\n          <p>Reforms, initiatives and partners already at work, to build on and never duplicate.</p>',
 '<h3>Қазір не жүріп жатыр?</h3>\n          <p>Жұмыс істеп жатқан реформалар, бастамалар мен әріптестер — соларға сүйену және қайталамау үшін.</p>'),
# after
('<p class="collaboration-eyebrow">After the assessment</p>', '<p class="collaboration-eyebrow">Бағалаудан кейін</p>'),
('<h2 class="collaboration-title" id="collaboration-title">Transparency, simplification,<br>digitalisation,<br>better regulations</h2>',
 '<h2 class="collaboration-title" id="collaboration-title">Ашықтық, оңайлату,<br>цифрландыру,<br>жақсартылған реттеу</h2>'),
('<p class="collaboration-lead">A digital zone service means an investor can go from choosing a location to launching a project without leaving the digital environment: available land and buildings, infrastructure and connection costs, incentives, registration, customs regime, all online, with one process and one verified certificate at the end. Reaching that takes three steps: make the procedures transparent, simplify them, then digitise them. Digitising a procedure nobody has simplified only makes it faster to get wrong.</p>',
 '<p class="collaboration-lead">Цифрлық аймақ қызметі инвестордың орын таңдаудан жобаны іске қосуға дейінгі жолды цифрлық ортадан шықпай өтуін білдіреді: бос жер мен ғимараттар, инфрақұрылым мен қосылу құны, жеңілдіктер, тіркеу, кеден режимі — барлығы онлайн, бір процесте, соңында бір тексерілетін сертификатпен. Бұған үш қадам жеткізеді: рәсімдерді ашық ету, оларды оңайлату, содан кейін цифрландыру. Ешкім оңайлатпаған рәсімді цифрландыру — қатеге тезірек жету ғана.</p>'),
('<h3>Transparency</h3>', '<h3>Ашықтық</h3>'),
("<p>Publish each procedure from the user's point of view: steps, documents, costs, timelines, legal basis, kept up to date by the competent authority.</p>",
 '<p>Әр рәсімді пайдаланушы тұрғысынан жариялау: қадамдар, құжаттар, құны, мерзімдері, құқықтық негізі; өзектілігін құзыретті орган қамтамасыз етеді.</p>'),
('<h3>Simplification</h3>', '<h3>Оңайлату</h3>'),
('<p>Remove steps and requirements that add no control. Clarify who is responsible for what.</p>',
 '<p>Бақылау қоспайтын қадамдар мен талаптарды алып тастау. Кім не үшін жауап беретінін нақтылау.</p>'),
('<h3>Digitalisation</h3>', '<h3>Цифрландыру</h3>'),
("<p>Turn the simplified procedures into online services: applications, approvals, payments, renewals. UNCTAD's eRegistrations platform is one available tool; the country chooses what fits its law and capacity.</p>",
 '<p>Оңайлатылған рәсімдерді онлайн-қызметтерге айналдыру: өтінімдер, келісулер, төлемдер, ұзарту. ЮНКТАД-тың eRegistrations платформасы — қолжетімді құралдардың бірі; ел өз заңнамасы мен мүмкіндіктеріне сай келетінін таңдайды.</p>'),
('<h3>Better regulations</h3>', '<h3>Жақсартылған реттеу</h3>'),
('<p>Read the zone law as an offer: what the country offers investors and what it expects in return. Move procedure below the law so services can improve without reopening parliament; a model regulation to adapt is in preparation. <a href="law/">Read more →</a></p>',
 '<p>Аймақ туралы заңды ұсыныс ретінде оқу: ел инвесторларға не ұсынады және оның орнына не күтеді. Рәсімді заң деңгейінен төмен түсіру — сонда қызметтер парламентке қайта жүгінбей-ақ жақсара алады; бейімдеуге арналған үлгілік реттеу әзірленуде. <a href="../law/">Толығырақ →</a></p>'),
# examples
('<p class="example-eyebrow">In practice</p>', '<p class="example-eyebrow">Тәжірибеде</p>'),
('<h2 class="example-title">Working examples</h2>', '<h2 class="example-title">Жұмыс істеп тұрған мысалдар</h2>'),
('<p class="example-lead">These experiences illustrate possible approaches. They are not proposed projects for Central Asia and would not be replicated without adaptation to each country&rsquo;s priorities, institutions and legal framework.</p>',
 '<p class="example-lead">Бұл мысалдар ықтимал тәсілдерді көрсетеді. Олар Орталық Азияға ұсынылған жобалар емес және әр елдің басымдықтарына, мекемелеріне және құқықтық базасына бейімдеместен қайталанбайды.</p>'),
('<span class="reference-country-label">Central Asia</span>\n            <h3>Transparency of procedures</h3>',
 '<span class="reference-country-label">Орталық Азия</span>\n            <h3>Рәсімдердің ашықтығы</h3>'),
('<p>The Central Asia Gateway (<a href="https://infotradecentralasia.org/" target="_blank" rel="noopener">infotradecentralasia.org</a>) brings together the national trade portals of the five countries. For each import, export or transit procedure it shows what the user needs to know: steps, required documents, institutions and contact persons, costs and legal basis. It covers trade, not zones. The same regional approach can be applied to zone procedures.</p>',
 '<p>Central Asia Gateway (<a href="https://infotradecentralasia.org/" target="_blank" rel="noopener">infotradecentralasia.org</a>) бес елдің ұлттық сауда порталдарын біріктіреді. Импорт, экспорт немесе транзиттің әр рәсімі бойынша ол пайдаланушыға қажет ақпаратты көрсетеді: қадамдар, талап етілетін құжаттар, мекемелер мен байланыс тұлғалары, құны және құқықтық негізі. Ол сауданы қамтиды, аймақтарды емес. Дәл осы өңірлік тәсілді аймақ рәсімдеріне де қолдануға болады.</p>'),
('<ul class="country-chips" aria-label="Countries covered"><li>Kazakhstan</li><li>Kyrgyzstan</li><li>Tajikistan</li><li>Turkmenistan</li><li>Uzbekistan</li></ul>',
 '<ul class="country-chips" aria-label="Қамтылған елдер"><li>Қазақстан</li><li>Қырғызстан</li><li>Тәжікстан</li><li>Түрікменстан</li><li>Өзбекстан</li></ul>'),
('alt="Screenshot of the Central Asia Gateway showing a step-by-step trade procedure"',
 'alt="Central Asia Gateway порталының скриншоты: сауда рәсімі қадам-қадаммен"'),
('<div class="screen-showcase" aria-label="Jamaica SEZ digital service screens">',
 '<div class="screen-showcase" aria-label="Ямайка ЕЭА цифрлық қызмет экрандары">'),
('<span class="reference-country-label">Jamaica</span>\n                <h3>Digitalisation of zone services</h3>',
 '<span class="reference-country-label">Ямайка</span>\n                <h3>Аймақ қызметтерін цифрландыру</h3>'),
("<p>Jamaica's institutional set-up is simpler than most in Central Asia. What matters here is what the investor sees at the end: one entry point, every zone on a map, one process, one certificate.</p>",
 '<p>Ямайканың институционалдық құрылымы Орталық Азиядағы көп елден қарапайым. Мұнда маңыздысы — инвестордың соңында көретіні: бір кіру нүктесі, картадағы барлық аймақ, бір процесс, бір сертификат.</p>'),
('role="tablist" aria-label="Jamaica digital service screens"',
 'role="tablist" aria-label="Ямайка цифрлық қызмет экрандары"'),
('<strong>Public zone portal</strong>\n                    <span>A front door for investors and zone services.</span>',
 '<strong>Аймақтардың ашық порталы</strong>\n                    <span>Инвесторлар мен аймақ қызметтеріне арналған бір есік.</span>'),
('<strong>Interactive zone map</strong>\n                    <span>Explore approved zones, developers, locations and industries.</span>',
 '<strong>Интерактивті аймақ картасы</strong>\n                    <span>Бекітілген аймақтар, девелоперлер, орналасу және салалар.</span>'),
('<strong>Zone details</strong>\n                    <span>Review status, available land and buildings, occupants and service providers.</span>',
 '<strong>Аймақ мәліметтері</strong>\n                    <span>Мәртебесі, бос жер мен ғимараттар, резиденттер және қызмет көрсетушілер.</span>'),
('<strong>Digital certificate</strong>\n                    <span>See verified outputs once the process is approved.</span>',
 '<strong>Цифрлық сертификат</strong>\n                    <span>Процесс бекітілген соң тексерілетін нәтиже.</span>'),
('alt="Jamaica Special Economic Zone Authority public portal landing page"',
 'alt="Ямайка арнайы экономикалық аймақтар басқармасы ашық порталының басты беті"'),
('alt="Jamaica zone map with filters and zone locations"',
 'alt="Сүзгілері мен аймақ орналасуы көрсетілген Ямайка аймақтарының картасы"'),
('alt="Details for Montego Bay Free Zone shown on the Jamaica zone map"',
 'alt="Ямайка картасындағы Монтего-Бей еркін аймағының мәліметтері"'),
('alt="Digital special economic zone developer certificate with QR verification"',
 'alt="QR-тексерілімі бар аймақ девелоперінің цифрлық сертификаты"'),
# apply band
('<h2 class="section-title" id="nar-collab">Answer the questionnaire</h2>',
 '<h2 class="section-title" id="nar-collab">Сауалнамаға жауап беріңіз</h2>'),
('<strong>Any country can start.</strong>\n          <span>Answer the questionnaire, and decide afterwards whether to go further.</span>',
 '<strong>Кез келген ел бастай алады.</strong>\n          <span>Сауалнамаға жауап беріңіз, әрі қарай жүру-жүрмеуді кейін шешесіз.</span>'),
('rel="noopener">Answer the questionnaire →</a>\n      </div>',
 'rel="noopener">Сауалнамаға жауап беріңіз →</a>\n      </div>'),
('The assessment and the national report are provided by the partners. This initiative is exploratory and creates no commitment for participants or the partners. Regional results are presented in consolidated form; any reference to an individual country requires its consent.',
 'Бағалау мен ұлттық есепті әріптестер ұсынады. Бұл бастама зерттеу сипатында және қатысушыларға да, әріптестерге де міндеттеме жүктемейді. Өңірлік нәтижелер жинақталған түрде ұсынылады; жекелеген елге сілтеме жасау үшін оның келісімі қажет.'),
# footer
('<div class="footer-logos" aria-label="Partners">', '<div class="footer-logos" aria-label="Әріптестер">'),
('An initiative of the WFZO Regional Office for Central Asia, with technical support from UNCTAD and UNITAR, Digital Government Programme',
 'WFZO Орталық Азия өңірлік кеңсесінің бастамасы, ЮНКТАД пен ЮНИТАР Цифрлық үкімет бағдарламасының техникалық қолдауымен'),
('This page is a basis for discussion and an invitation to express interest. It does not constitute a commitment by UNCTAD or any United Nations entity. Further technical assistance is subject to mandates, resources and formal agreements. The designations employed do not imply any judgement concerning the legal status of any country or territory.',
 'Бұл бет — талқылауға негіз және мүдделілік білдіруге шақыру. Ол ЮНКТАД-тың немесе Біріккен Ұлттар Ұйымының қандай да бір құрылымының міндеттемесі болып табылмайды. Одан әрі техникалық көмек мандаттарға, ресурстарға және ресми келісімдерге байланысты. Қолданылған белгілеулер қандай да бір елдің немесе аумақтың құқықтық мәртебесіне қатысты ешқандай пікірді білдірмейді.'),
# Gulnura chat (the guided-tour widgets are removed below, not translated)
('<span class="md-name">Questions?</span>', '<span class="md-name">Сұрақтарыңыз бар ма?</span>'),
('aria-label="Ask Gulnura"', 'aria-label="Гүлнұраға сұрақ қою"'),
('<b>Gulnura</b><small>Assistant · SEZ Central Asia · UNCTAD + WFZO</small></div><button class="x" id="md-x" aria-label="Close">',
 '<b>Гүлнұра</b><small>Көмекші · ЕЭА Орталық Азия · ЮНКТАД + WFZO</small></div><button class="x" id="md-x" aria-label="Жабу">'),
("Hello, I'm Gulnura. This page proposes an assessment of zone procedures, one country at a time, so that what is made simple and digital in one country can be adopted by the others. I can explain what the assessment looks at, what Jamaica did, or how a country applies.",
 'Сәлеметсіз бе, мен — Гүлнұра. Бұл бет аймақ рәсімдерін елден елге бағалауды ұсынады: бір елде оңайлатылып цифрланғанды басқалары қабылдай алуы үшін. Бағалау нені қарайтынын, Ямайка не істегенін немесе ел қалай қатысатынын түсіндіре аламын.'),
('<div id="md-sug"><button>What does the assessment involve?</button><button>What does my country get?</button><button>What was done in Jamaica?</button><button>How do we take part?</button></div>',
 '<div id="md-sug"><button>Бағалау нені қамтиды?</button><button>Менің елім не алады?</button><button>Ямайкада не істелді?</button><button>Қалай қатысамыз?</button></div>'),
('placeholder="Type your question…"', 'placeholder="Сұрағыңызды жазыңыз…"'),
('id="md-send">Send</button>', 'id="md-send">Жіберу</button>'),
('id="md-talk">🎤 Talk to Gulnura</button>', 'id="md-talk">🎤 Гүлнұрамен сөйлесу</button>'),
("'Connecting microphone…'", "'Микрофон қосылуда…'"),
("'Connecting…'", "'Қосылуда…'"),
("voice?'Listening…':''", "voice?'Тыңдап тұрмын…':''"),
("o.mode==='speaking'?'Gulnura is answering…':(voice?'Тыңдап тұрмын…':'')", "o.mode==='speaking'?'Гүлнұра жауап беруде…':(voice?'Тыңдап тұрмын…':'')"),
("add('Connection error: '", "add('Байланыс қатесі: '"),
("add('Microphone unavailable: '", "add('Микрофон қолжетімсіз: '"),
("add('Error: '", "add('Қате: '"),
("b.textContent='🎤 Talk to Gulnura';stat('');return;}", "b.textContent='🎤 Гүлнұрамен сөйлесу';stat('');return;}"),
("b.textContent='⏹ Stop';", "b.textContent='⏹ Тоқтату';"),
("b.textContent='🎤 Talk to Gulnura';}};", "b.textContent='🎤 Гүлнұрамен сөйлесу';}};"),
]

out = src
missing = []
for a, b in T:
    if a not in out:
        missing.append(a[:70]); continue
    out = out.replace(a, b)

# ---- remove the guided tour (no Kazakh narration audio/video yet) ----
# 1. the "Gulnura guides you" button in the launch group
btn_start = out.index('<button class="md-go" id="md-guide"')
btn_end = out.index('</button>', btn_start) + len('</button>')
out = out[:btn_start] + out[btn_end:]
# 2. the whole narration block: md-bar style+markup, mdn-audio, bust videos, engine script
blk_start = out.index('<style>\n  #md-bar{')
eng_anchor = out.index('stopAll(true)', blk_start)
blk_end = out.index('</script>', eng_anchor) + len('</script>')
out = out[:blk_start] + out[blk_end:]
# structural check: the elements are gone (the Yerbol script may still *mention*
# these ids inside null-guarded getElementById calls, which is harmless)
assert 'id="md-bar"' not in out and 'id="gl-video"' not in out
assert 'id="mdn-audio"' not in out and 'gulnura-bust' not in out and 'id="md-guide"' not in out

# translate the GREET constant in the chat script (same text as the visible greeting)
# (already covered by the greeting replacement above, which appears twice)

# ---- asset paths: kk/ sits inside the page folder ----
out = re.sub(r'(src|href)="assets/', r'\1="../assets/', out)
out = out.replace("url('assets/", "url('../assets/")
out = out.replace('url("assets/', 'url("../assets/')

open(os.path.join(here, 'index.html'), 'w', encoding='utf-8').write(out)
print('written; untranslated:', len(missing))
for m in missing: print(' -', m)
