"""SEZ Central Asia needs-assessment site: static pages plus the questionnaire API (same contract as the AZFA v2 engine).

Standard library only. Data lives in one SQLite file under DATA_DIR.
"""
import base64, hashlib, hmac, html, json, mimetypes, os, re, secrets, sqlite3, threading, time, urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

ROOT = Path(__file__).resolve().parent.parent
SITE = Path(os.environ.get('SITE_DIR', ROOT / 'site')).resolve()
DATA = Path(os.environ.get('DATA_DIR', ROOT / 'data'))
PORT = int(os.environ.get('PORT', '8000'))
ALLOWED_ORIGINS = {o.strip().rstrip('/') for o in os.environ.get('ALLOWED_ORIGINS', 'https://sez-asia.eregistrations.dev').split(',') if o.strip()}
ADMIN_HASH = os.environ.get('ADMIN_PASSWORD_HASH', '')
CLOSED = os.environ.get('QUESTIONNAIRE_CLOSED', '') in ('1', 'true', 'yes')
MAX_FILE = 5 * 1024 * 1024
MAX_BODY = 8 * 1024 * 1024
FILE_EXT = {'.pdf': 'application/pdf', '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.txt': 'text/plain'}
REQUIRED = ('name', 'role', 'institution', 'institution_type', 'country', 'email', 'language')
# Mail goes out through the Brevo HTTP API (no mail server). Without a key, nothing is sent.
BREVO_KEY = os.environ.get('BREVO_API_KEY', '')
MAIL_FROM = os.environ.get('MAIL_FROM', 'nelsonadpa@gmail.com')
MAIL_FROM_NAME = os.environ.get('MAIL_FROM_NAME', 'SEZ Central Asia needs assessment')
MAIL_REPLY_TO = os.environ.get('MAIL_REPLY_TO', 'nelson.perez@un.org')
NOTIFY_EMAIL = os.environ.get('NOTIFY_EMAIL', '')  # who hears about new and submitted responses
PUBLIC_URL = os.environ.get('PUBLIC_URL', 'https://sez-asia.eregistrations.dev').rstrip('/')

DATA.mkdir(parents=True, exist_ok=True)
DB_LOCK = threading.Lock()
db = sqlite3.connect(DATA / 'sez-asia.sqlite3', check_same_thread=False)
db.row_factory = sqlite3.Row
db.executescript('''
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS respondents(
  id INTEGER PRIMARY KEY, token TEXT UNIQUE NOT NULL, request_id TEXT UNIQUE, participant TEXT NOT NULL,
  answers TEXT NOT NULL DEFAULT '{}', revision INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'draft',
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL, submitted_at TEXT, hidden_at TEXT);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, respondent_id INTEGER NOT NULL, kind TEXT NOT NULL, at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS outbox(id INTEGER PRIMARY KEY, respondent_id INTEGER, to_email TEXT NOT NULL, subject TEXT NOT NULL,
  body TEXT NOT NULL, questionnaire_url TEXT, status TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS files(id TEXT PRIMARY KEY, respondent_id INTEGER NOT NULL, question_id TEXT NOT NULL,
  filename TEXT NOT NULL, size INTEGER NOT NULL, content BLOB NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS visits(id INTEGER PRIMARY KEY, at TEXT NOT NULL, page TEXT NOT NULL, visitor TEXT NOT NULL,
  device TEXT NOT NULL, referrer TEXT NOT NULL DEFAULT '', bot INTEGER NOT NULL DEFAULT 0);
''')
# Page views: no IP is stored, only a salted hash that groups the views of one browser.
SALT_FILE = DATA / 'visit_salt'
if not SALT_FILE.exists():
    SALT_FILE.write_text(secrets.token_hex(16))
VISIT_SALT = SALT_FILE.read_text().strip()
PAGES = {'/': 'Proposal page', '/index.html': 'Proposal page', '/ru/': 'Proposal page (RU)', '/kk/': 'Proposal page (KK)', '/law/': 'Law page', '/questionnaire/': 'Questionnaire', '/admin/': 'Admin'}
BOT_RE = re.compile(r'bot|crawl|spider|slurp|preview|curl|wget|python|headless|playwright|lighthouse|monitor|uptime', re.I)


def device_of(ua):
    for key, label in (('iPhone', 'iPhone'), ('iPad', 'iPad'), ('Android', 'Android'), ('Windows', 'Windows'), ('Macintosh', 'Mac'), ('Linux', 'Linux')):
        if key in ua:
            return label
    return 'Other'


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def load_schema():
    text = (SITE / 'assets/questionnaire-v2/schema.js').read_text('utf-8')
    data = json.loads(text[text.index('{'):text.rindex('}') + 1])
    return {q['id']: q for s in data['sections'] for q in s['questions']}, data.get('version', '')


QUESTIONS, SCHEMA_VERSION = load_schema()

MAIL_HTML = """<!doctype html><html><body style="margin:0;background:#eef1f4;font-family:Arial,Helvetica,sans-serif;color:#1d2733">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#eef1f4;padding:24px 12px"><tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #dfe4ea">
<tr><td style="height:6px;background:#009edb;font-size:0;line-height:0">&nbsp;</td></tr>
<tr><td style="padding:26px 28px 8px"><div style="color:#009edb;font-size:12px;letter-spacing:.08em;text-transform:uppercase;font-weight:bold">Central Asia &middot; Needs assessment</div>
<h1 style="font-size:20px;margin:8px 0 0">{title}</h1></td></tr>
<tr><td style="padding:8px 28px 4px;font-size:15px;line-height:1.55">{body}</td></tr>
{button}
<tr><td style="padding:18px 28px 26px;font-size:12px;color:#5b6673;line-height:1.5;border-top:1px solid #dfe4ea">Special economic zones &middot; a proposal for discussion with technical support from UNCTAD, Digital Government Programme.<br>Questions: nelson.perez@un.org</td></tr>
</table></td></tr></table></body></html>"""


def send_email(to, subject, title, paragraphs, button=None, respondent_id=None, link=None):
    """One sending function for the whole app. Records every message in the outbox; returns accepted / failed / skipped."""
    text = '\n\n'.join(paragraphs + ([button[0] + ': ' + button[1]] if button else []))
    status = 'skipped'
    if BREVO_KEY:
        btn = ('<tr><td style="padding:14px 28px 6px"><a href="%s" style="display:inline-block;background:#009edb;color:#ffffff;'
               'text-decoration:none;font-weight:bold;padding:12px 20px;border-radius:8px">%s</a>'
               '<div style="font-size:12px;color:#5b6673;margin-top:10px;word-break:break-all">%s</div></td></tr>'
               % (html.escape(button[1]), html.escape(button[0]), html.escape(button[1]))) if button else ''
        page = MAIL_HTML.format(title=html.escape(title), button=btn,
                                body=''.join('<p style="margin:0 0 12px">%s</p>' % html.escape(p) for p in paragraphs))
        payload = {'sender': {'email': MAIL_FROM, 'name': MAIL_FROM_NAME}, 'to': [{'email': to}],
                   'replyTo': {'email': MAIL_REPLY_TO}, 'subject': subject, 'htmlContent': page, 'textContent': text}
        req = urllib.request.Request('https://api.brevo.com/v3/smtp/email', data=json.dumps(payload).encode(),
                                     headers={'api-key': BREVO_KEY, 'Content-Type': 'application/json', 'Accept': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                status = 'accepted' if 200 <= r.status < 300 else 'failed'
        except Exception as e:
            print('MAIL ERROR', repr(e)[:200], flush=True)
            status = 'failed'
    db.execute('INSERT INTO outbox(respondent_id, to_email, subject, body, questionnaire_url, status, created_at) VALUES(?,?,?,?,?,?,?)',
               (respondent_id, to, subject, text, link, status, now()))
    return status


def mail_return_link(rid, participant, link):
    return send_email(participant['email'], 'Your personal link to the Central Asia SEZ needs assessment questionnaire',
                      'Your questionnaire is open',
                      ['Dear %s,' % participant['name'],
                       'Thank you for taking part in the needs assessment of special economic zones in Central Asia. '
                       'Your answers are saved as you go. Use your personal link to come back, complete or correct them at any time.',
                       'Keep this link private: anyone who has it can open and edit your response.'],
                      ('Open my questionnaire', link), rid, link)


def notify(rid, kind, participant):
    if not NOTIFY_EMAIL:
        return
    who = '%s, %s (%s)' % (participant['name'], participant['role'], participant['institution'])
    send_email(NOTIFY_EMAIL, 'Central Asia SEZ questionnaire: %s by %s' % (kind, participant['institution']),
               'A response was %s' % kind, ['%s: %s.' % (kind.capitalize(), who), 'Open the responses page to read it.'],
               ('Open the responses', PUBLIC_URL + '/admin/'), rid)


ADMIN_SESSIONS = {}  # token -> expiry
LOGIN_FAILS = []     # timestamps of recent failed logins


def check_password(password):
    # Format: pbkdf2_sha256:<iterations>:<salt hex>:<hash hex> (no "$", so compose does not interpolate it).
    try:
        algo, it, salt, digest = ADMIN_HASH.split(':')
        assert algo == 'pbkdf2_sha256'
        got = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(it)).hex()
        return hmac.compare_digest(got, digest)
    except Exception:
        return False


def valid_answer(q, v):
    if v is None:
        return True
    t = q['type']
    if t == 'multi':
        return isinstance(v, list) and all(isinstance(x, str) and x in q['options'] for x in v)
    if t == 'single':
        return isinstance(v, str) and (v == '' or v in q['options'])
    if t == 'number':
        return isinstance(v, (int, float))
    return isinstance(v, str) and len(v) <= q.get('maxLength', 4000 if t == 'textarea' else 2000)


def answered_count(answers):
    return sum(1 for v in answers.values() if v not in (None, '', []))


class Fail(Exception):
    def __init__(self, status, msg):
        self.status, self.msg = status, msg


class Handler(BaseHTTPRequestHandler):
    server_version = 'sez-asia'

    def log_message(self, fmt, *args):
        print('%s %s' % (self.command, self.path.split('#')[0].split('?')[0][:80]), flush=True)

    # ---------- helpers ----------
    def send_json(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Robots-Tag', 'noindex, nofollow')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def body(self):
        n = int(self.headers.get('Content-Length') or 0)
        if n > MAX_BODY:
            raise Fail(413, 'Request too large')
        try:
            return json.loads(self.rfile.read(n) or b'{}')
        except Exception:
            raise Fail(400, 'Invalid JSON')

    def same_origin(self):
        origin = (self.headers.get('Origin') or '').rstrip('/')
        if origin not in ALLOWED_ORIGINS:
            raise Fail(403, 'Same-origin request required')

    def admin(self):
        auth = self.headers.get('Authorization', '')
        tok = auth[7:] if auth.startswith('Bearer ') else ''
        exp = ADMIN_SESSIONS.get(tok)
        if not exp or exp < time.time():
            ADMIN_SESSIONS.pop(tok, None)
            raise Fail(401, 'Admin login required')
        return tok

    def respondent(self, token):
        r = db.execute('SELECT * FROM respondents WHERE token=?', (token,)).fetchone()
        if not r:
            raise Fail(404, 'Not found')
        return r

    def files_of(self, rid):
        return [dict(f) for f in db.execute('SELECT id, question_id, filename, size FROM files WHERE respondent_id=? ORDER BY created_at', (rid,))]

    def send_file_row(self, f):
        ext = Path(f['filename']).suffix.lower()
        self.send_response(200)
        self.send_header('Content-Type', FILE_EXT.get(ext, 'application/octet-stream'))
        self.send_header('Content-Disposition', 'attachment; filename="%s"' % re.sub(r'[^\w.\- ]', '_', f['filename']))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Length', str(len(f['content'])))
        self.end_headers()
        self.wfile.write(f['content'])

    # ---------- routing ----------
    def do_GET(self): self.route('GET')
    def do_POST(self): self.route('POST')
    def do_PATCH(self): self.route('PATCH')
    def do_HEAD(self): self.route('GET')

    def route(self, method):
        url = urlparse(self.path)
        path = unquote(url.path)
        try:
            if path.startswith('/api/v2/'):
                with DB_LOCK:
                    self.api(method, path[len('/api/v2/'):], parse_qs(url.query))
            elif method == 'GET':
                self.static(path)
                if path in PAGES and self.command == 'GET':
                    self.record_visit(path)
            else:
                raise Fail(405, 'Method not allowed')
        except Fail as e:
            self.send_json(e.status, {'error': e.msg})
        except BrokenPipeError:
            pass
        except Exception as e:  # keep the server up; log the cause
            print('ERROR', repr(e), flush=True)
            self.send_json(500, {'error': 'Server error'})

    def api(self, method, p, query):
        if p == 'meta' and method == 'GET':
            return self.send_json(200, {'version': 'v2', 'mail_mode': 'brevo' if BREVO_KEY else 'none', 'closed': CLOSED, 'local_preview': False})
        if p.startswith('admin/'):
            return self.admin_api(method, p[6:], query)
        if method != 'GET':
            self.same_origin()
        if p == 'register' and method == 'POST':
            return self.register(self.body())
        m = re.fullmatch(r'q/([\w-]{20,64})(?:/(files|submit)(?:/([\w-]+))?)?', p)
        if not m:
            raise Fail(404, 'Not found')
        token, sub, fid = m.groups()
        r = self.respondent(token)
        if sub is None and method == 'GET':
            return self.send_json(200, {'answers': json.loads(r['answers']), 'revision': r['revision'], 'status': r['status'],
                                        'participant': json.loads(r['participant']), 'files': self.files_of(r['id'])})
        if CLOSED and method != 'GET':
            raise Fail(403, 'The consultation is closed')
        if sub is None and method == 'PATCH':
            return self.patch(r, self.body())
        if sub == 'submit' and method == 'POST':
            return self.submit(r, self.body())
        if sub == 'files' and method == 'POST' and not fid:
            return self.upload(r, self.body())
        if sub == 'files' and method == 'GET' and fid:
            f = db.execute('SELECT * FROM files WHERE id=? AND respondent_id=?', (fid, r['id'])).fetchone()
            if not f:
                raise Fail(404, 'Not found')
            return self.send_file_row(f)
        raise Fail(404, 'Not found')

    def register(self, b):
        if CLOSED:
            raise Fail(403, 'The consultation is closed')
        if b.get('notice_accepted') is not True:
            raise Fail(400, 'The notice must be accepted')
        participant = {}
        for k in REQUIRED:
            v = str(b.get(k) or '').strip()
            if not v or len(v) > 250:
                raise Fail(400, 'Missing or invalid field: ' + k)
            participant[k] = v
        if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', participant['email']):
            raise Fail(400, 'Invalid email')
        rid = str(b.get('request_id') or '')[:64] or None
        if rid:
            old = db.execute('SELECT token, participant FROM respondents WHERE request_id=?', (rid,)).fetchone()
            if old:
                if json.loads(old['participant']) != participant:
                    raise Fail(409, 'Registration changed during a retry')
                return self.send_json(200, {'token': old['token'], 'email_status': 'skipped'})
        token, t = secrets.token_urlsafe(24), now()
        cur = db.execute('INSERT INTO respondents(token, request_id, participant, created_at, updated_at) VALUES(?,?,?,?,?)',
                         (token, rid, json.dumps(participant, ensure_ascii=False), t, t))
        db.execute('INSERT INTO events(respondent_id, kind, at) VALUES(?,?,?)', (cur.lastrowid, 'registered', t))
        db.commit()
        link = PUBLIC_URL + '/questionnaire/#q=' + token
        email_status = mail_return_link(cur.lastrowid, participant, link)
        notify(cur.lastrowid, 'started', participant)
        db.commit()
        self.send_json(200, {'token': token, 'email_status': email_status})

    def patch(self, r, b):
        if b.get('revision') != r['revision']:
            raise Fail(409, 'Revision conflict')
        changes = b.get('changes')
        if not isinstance(changes, dict):
            raise Fail(400, 'Invalid changes')
        answers = json.loads(r['answers'])
        for k, v in changes.items():
            q = QUESTIONS.get(k)
            if not q or not valid_answer(q, v):
                raise Fail(400, 'Invalid answer: ' + str(k)[:60])
            if v in (None, '', []):
                answers.pop(k, None)
            else:
                answers[k] = v
        status = 'amended' if r['status'] in ('submitted', 'amended') else 'draft'
        t = now()
        db.execute('UPDATE respondents SET answers=?, revision=revision+1, status=?, updated_at=? WHERE id=?',
                   (json.dumps(answers, ensure_ascii=False), status, t, r['id']))
        last = db.execute('SELECT kind, at FROM events WHERE respondent_id=? ORDER BY id DESC LIMIT 1', (r['id'],)).fetchone()
        if not last or last['kind'] != 'saved' or last['at'][:13] != t[:13]:  # one "saved" event per hour, not per keystroke
            db.execute('INSERT INTO events(respondent_id, kind, at) VALUES(?,?,?)', (r['id'], 'saved', t))
        db.commit()
        self.send_json(200, {'revision': r['revision'] + 1, 'status': status})

    def submit(self, r, b):
        if b.get('revision') != r['revision']:
            raise Fail(409, 'Revision conflict')
        t = now()
        db.execute("UPDATE respondents SET status='submitted', revision=revision+1, submitted_at=?, updated_at=? WHERE id=?", (t, t, r['id']))
        db.execute('INSERT INTO events(respondent_id, kind, at) VALUES(?,?,?)', (r['id'], 'submitted', t))
        notify(r['id'], 'submitted', json.loads(r['participant']))
        db.commit()
        self.send_json(200, {'revision': r['revision'] + 1, 'status': 'submitted'})

    def upload(self, r, b):
        qid, name = str(b.get('question_id') or ''), Path(str(b.get('filename') or '')).name[:200]
        q = QUESTIONS.get(qid)
        if not q or not q.get('attach'):
            raise Fail(400, 'This question does not accept documents')
        if Path(name).suffix.lower() not in FILE_EXT:
            raise Fail(400, 'Use a PDF, DOCX or text file.')
        try:
            content = base64.b64decode(b.get('content_base64') or '', validate=True)
        except Exception:
            raise Fail(400, 'Invalid file content')
        if not content or len(content) > MAX_FILE:
            raise Fail(400, 'The file is empty or larger than 5 MB.')
        n = db.execute('SELECT COUNT(*) FROM files WHERE respondent_id=? AND question_id=?', (r['id'], qid)).fetchone()[0]
        if n >= 3:
            raise Fail(400, 'You can attach up to three documents.')
        fid, t = secrets.token_hex(12), now()
        db.execute('INSERT INTO files VALUES(?,?,?,?,?,?,?)', (fid, r['id'], qid, name, len(content), content, t))
        status = 'amended' if r['status'] in ('submitted', 'amended') else r['status']
        db.execute('UPDATE respondents SET status=?, updated_at=? WHERE id=?', (status, t, r['id']))
        db.commit()
        self.send_json(200, {'file': {'id': fid, 'question_id': qid, 'filename': name, 'size': len(content)}, 'status': status})

    # ---------- admin ----------
    def admin_api(self, method, p, query):
        if p == 'login' and method == 'POST':
            self.same_origin()
            cutoff = time.time() - 900
            LOGIN_FAILS[:] = [x for x in LOGIN_FAILS if x > cutoff]
            if len(LOGIN_FAILS) >= 10:
                raise Fail(429, 'Too many attempts. Try again later.')
            if not ADMIN_HASH or not check_password(str(self.body().get('password') or '')):
                LOGIN_FAILS.append(time.time())
                time.sleep(1)
                raise Fail(401, 'Wrong password')
            tok = secrets.token_urlsafe(32)
            ADMIN_SESSIONS[tok] = time.time() + 8 * 3600
            return self.send_json(200, {'token': tok})
        tok = self.admin()
        if method != 'GET':
            self.same_origin()
        if p == 'logout' and method == 'POST':
            ADMIN_SESSIONS.pop(tok, None)
            return self.send_json(200, {'ok': True})
        if p == 'respondents' and method == 'GET':
            rows = db.execute('SELECT * FROM respondents ORDER BY updated_at DESC').fetchall()
            include_hidden = query.get('include_hidden') == ['1']
            out = []
            for r in rows:
                if r['hidden_at'] and not include_hidden:
                    continue
                pa = json.loads(r['participant'])
                out.append({'id': r['id'], 'institution': pa['institution'], 'name': pa['name'], 'country': pa['country'],
                            'status': r['status'], 'answered_count_raw': answered_count(json.loads(r['answers'])),
                            'updated_at': r['updated_at'], 'hidden_at': r['hidden_at']})
            return self.send_json(200, {'respondents': out})
        if p == 'outbox' and method == 'GET':
            rows = db.execute('SELECT to_email, subject, body, questionnaire_url, status, created_at FROM outbox ORDER BY id DESC LIMIT 200').fetchall()
            return self.send_json(200, {'messages': [dict(m) for m in rows]})
        if p == 'visits' and method == 'GET':
            rows = db.execute('SELECT at, page, visitor, device, referrer FROM visits WHERE bot=0 ORDER BY id DESC LIMIT 500').fetchall()
            return self.send_json(200, {'visits': [dict(v) for v in rows]})
        if p == 'export' and method == 'GET':
            rows = db.execute('SELECT * FROM respondents WHERE hidden_at IS NULL ORDER BY created_at').fetchall()
            return self.send_json(200, {'schema_version': SCHEMA_VERSION, 'exported_at': now(), 'respondents': [self.full(r) for r in rows]})
        m = re.fullmatch(r'respondents/(\d+)(?:/(hide|restore|files)(?:/([\w-]+))?)?', p)
        if not m:
            raise Fail(404, 'Not found')
        rid, sub, fid = int(m.group(1)), m.group(2), m.group(3)
        r = db.execute('SELECT * FROM respondents WHERE id=?', (rid,)).fetchone()
        if not r:
            raise Fail(404, 'Not found')
        if sub is None and method == 'GET':
            return self.send_json(200, self.full(r))
        if sub in ('hide', 'restore') and method == 'POST':
            t = now()
            db.execute('UPDATE respondents SET hidden_at=? WHERE id=?', (t if sub == 'hide' else None, rid))
            db.execute('INSERT INTO events(respondent_id, kind, at) VALUES(?,?,?)', (rid, 'hidden' if sub == 'hide' else 'restored', t))
            db.commit()
            return self.send_json(200, {'ok': True})
        if sub == 'files' and fid and method == 'GET':
            f = db.execute('SELECT * FROM files WHERE id=? AND respondent_id=?', (fid, rid)).fetchone()
            if not f:
                raise Fail(404, 'Not found')
            return self.send_file_row(f)
        raise Fail(404, 'Not found')

    def full(self, r):
        return {'id': r['id'], 'participant': json.loads(r['participant']), 'status': r['status'], 'revision': r['revision'],
                'answers': json.loads(r['answers']), 'created_at': r['created_at'], 'updated_at': r['updated_at'],
                'submitted_at': r['submitted_at'], 'files': self.files_of(r['id']),
                'events': [dict(e) for e in db.execute('SELECT kind, at FROM events WHERE respondent_id=? ORDER BY id', (r['id'],))]}

    def record_visit(self, path):
        ua = self.headers.get('User-Agent', '')
        ip = (self.headers.get('X-Forwarded-For') or self.client_address[0]).split(',')[0].strip()
        ref = urlparse(self.headers.get('Referer', '')).netloc
        if ref == urlparse(PUBLIC_URL).netloc:
            ref = ''
        visitor = hashlib.sha256((VISIT_SALT + ip + ua).encode()).hexdigest()[:8]
        with DB_LOCK:
            db.execute('INSERT INTO visits(at, page, visitor, device, referrer, bot) VALUES(?,?,?,?,?,?)',
                       (now(), PAGES[path], visitor, device_of(ua), ref[:80], 1 if BOT_RE.search(ua) else 0))
            db.commit()

    # ---------- static site ----------
    def static(self, path):
        target = (SITE / path.lstrip('/')).resolve()
        if SITE not in target.parents and target != SITE:
            raise Fail(404, 'Not found')
        if target.is_dir():
            if not path.endswith('/'):
                self.send_response(301)
                self.send_header('Location', path + '/')
                self.end_headers()
                return
            target = target / 'index.html'
        if not target.is_file():
            target, status = SITE / '404.html', 404
            if not target.is_file():
                raise Fail(404, 'Not found')
        else:
            status = 200
        data = target.read_bytes()
        ctype = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
        if ctype.startswith('text/') or ctype in ('application/javascript', 'image/svg+xml'):
            ctype += '; charset=utf-8'
        self.send_response(status)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        if target.suffix == '.html':
            self.send_header('Cache-Control', 'no-cache')
            # The public pages stay indexable; only the questionnaire and admin are hidden from search engines.
            if path.lstrip('/').startswith(('questionnaire', 'admin')):
                self.send_header('X-Robots-Tag', 'noindex, nofollow')
        else:
            self.send_header('Cache-Control', 'public, max-age=3600')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(data)


if __name__ == '__main__':
    print('SEZ Central Asia site on :%d · site %s · data %s · admin %s · mail %s' % (PORT, SITE, DATA, 'on' if ADMIN_HASH else 'OFF', 'brevo' if BREVO_KEY else 'off'), flush=True)
    ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
