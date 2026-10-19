from flask import Flask, request, redirect, render_template_string, abort, session, flash, url_for, Response
import sqlite3, os, re, csv, io, string, random, hashlib, hmac
from datetime import datetime
from urllib.parse import urlparse
from functools import wraps
from html import escape

app = Flask(__name__)

# Local defaults keep existing local testing simple. On Render, require explicit
# secrets so the public deployment cannot accidentally use the known defaults.
IS_RENDER = os.environ.get("RENDER", "").lower() == "true"
SECRET_KEY = os.environ.get("LINKPULSE_SECRET_KEY", "change-this-secret-key-before-deployment")
ADMIN_PASSWORD = os.environ.get("LINKPULSE_ADMIN_PASSWORD", "change-me")

if IS_RENDER and SECRET_KEY == "change-this-secret-key-before-deployment":
    raise RuntimeError("Set LINKPULSE_SECRET_KEY to a strong random value in Render environment variables.")
if IS_RENDER and ADMIN_PASSWORD == "change-me":
    raise RuntimeError("Set LINKPULSE_ADMIN_PASSWORD to a strong password in Render environment variables.")

app.secret_key = SECRET_KEY
DB = os.environ.get("LINKPULSE_DATABASE", "linkpulse.db")
ALIAS_RE = re.compile(r"^[A-Za-z0-9_-]{3,40}$")
RATE_BUCKETS = {}

BASE = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0b1020"><title>{{ title }} Â· LinkPulse</title>
<style>
:root{color-scheme:dark;--bg:#0b1220;--panel:#172235;--panel2:#111c2d;--border:#2b3b50;--text:#f1f5f9;--muted:#a6b5c8;--purple:#4f8cff;--cyan:#38d6c5;--green:#4adea5;--danger:#fb7185}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:radial-gradient(ellipse at 80% -10%,#123b50 0,transparent 42%),var(--bg);color:var(--text);font:15px/1.65 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:#76e4dc;text-decoration:none}a:hover{color:white}header{position:sticky;top:0;z-index:10;display:flex;align-items:center;gap:22px;flex-wrap:wrap;padding:15px max(5%,calc((100% - 1180px)/2));background:#0b1020eF;border-bottom:1px solid #29334b;backdrop-filter:blur(16px)}header strong{font-size:1.18rem;letter-spacing:-.04em;color:#fff;display:flex;align-items:center;gap:10px;margin-right:auto}header strong:before{content:"â†—";display:grid;place-items:center;width:34px;height:34px;border-radius:11px;background:linear-gradient(135deg,#4f8cff,#38d6c5);font-weight:900;color:white;box-shadow:0 5px 24px #38d6c533}header a{color:#b9c5e2;font-size:.94rem;font-weight:600}header a:hover{color:white}main{max-width:1180px;margin:34px auto 64px;padding:0 22px;min-height:65vh}.card{background:linear-gradient(145deg,#171f35,#12192b);border:1px solid var(--border);border-radius:20px;padding:25px;margin:16px 0;box-shadow:0 18px 45px #00000018;min-width:0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:16px}.grid .card{margin:0}h1,h2,h3{line-height:1.2;letter-spacing:-.035em;color:#f7f8ff}h1{font-size:clamp(2rem,4vw,3.3rem);margin:0 0 15px}h2{font-size:1.35rem;margin:0 0 16px}h3{font-size:1.05rem}p{color:#c0cbe3}small,.muted{color:var(--muted)}label{display:block;font-weight:650;color:#dbe5ff;margin:7px 0 5px}input,button,textarea,select{font:inherit;padding:12px 13px;border:1px solid #35415e;border-radius:10px;max-width:100%;box-sizing:border-box;background:#0c1325;color:var(--text)}input,textarea,select{width:100%;margin:4px 0 13px;outline:none;transition:border-color .18s,box-shadow .18s}input:focus,textarea:focus,select:focus{border-color:var(--cyan);box-shadow:0 0 0 3px #38d6c525}input::placeholder,textarea::placeholder{color:#72809f}button,.btn{background:linear-gradient(110deg,#3978e8,#168f9b);color:white;border:0;cursor:pointer;text-decoration:none;padding:11px 16px;border-radius:10px;display:inline-flex;align-items:center;justify-content:center;gap:7px;font-weight:750;box-shadow:0 7px 20px #168f9b25;transition:transform .15s,filter .15s}button:hover,.btn:hover{filter:brightness(1.1);transform:translateY(-1px);color:white}.secondary{background:#26324c;box-shadow:none;border:1px solid #3a4764}.notice{padding:13px 16px;background:#112c3c;border:1px solid #22546a;border-radius:12px;color:#b8f1ff}.error{background:#351d32;border:1px solid #7f3656;padding:12px;border-radius:10px;color:#ffc5d2}code{overflow-wrap:anywhere;color:#8be9ff;background:#0b1324;border:1px solid #29334b;padding:3px 6px;border-radius:6px}.scroll{overflow:auto;border:1px solid var(--border);border-radius:12px}table{border-collapse:collapse;width:100%;background:#11182a;min-width:600px}th,td{text-align:left;padding:13px 14px;border-bottom:1px solid #29334b;overflow-wrap:anywhere;vertical-align:top}th{background:#1b2540;color:#b9c8e8;font-size:.8rem;text-transform:uppercase;letter-spacing:.07em}td{color:#d8e1f5}tr:hover td{background:#ffffff05}td form{margin-top:7px}td button{padding:7px 10px;font-size:.85rem}.hero{position:relative;overflow:hidden;padding:clamp(28px,5vw,58px);border-radius:26px;border:1px solid #3a356c;background:linear-gradient(125deg,#17243a 0%,#142d3d 52%,#103a43 100%);box-shadow:0 24px 65px #00000030}.hero:after{content:"";position:absolute;width:270px;height:270px;border-radius:50%;right:-90px;top:-100px;background:radial-gradient(circle,#25c6f755,transparent 70%);pointer-events:none}.eyebrow{display:inline-flex;align-items:center;gap:8px;border:1px solid #49447b;background:#15343e;color:#9dece3;padding:6px 11px;border-radius:99px;font-size:.78rem;font-weight:800;text-transform:uppercase;letter-spacing:.09em}.eyebrow:before{content:"";width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 12px var(--green)}.gradient-text{background:linear-gradient(95deg,#fff 8%,#8fd8ff 50%,#65e6d4 95%);-webkit-background-clip:text;background-clip:text;color:transparent}.hero p{max-width:690px;font-size:1.08rem;color:#b9c7e4}.form-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 15px}.section-heading{display:flex;justify-content:space-between;align-items:end;gap:15px;flex-wrap:wrap;margin:30px 0 15px}.feature{padding:22px;border-radius:17px;border:1px solid var(--border);background:#131b2e}.feature-icon{display:grid;place-items:center;width:42px;height:42px;border-radius:13px;background:#193b4a;color:#8ce6df;font-size:1.2rem;margin-bottom:14px}.stat-label{font-size:.85rem;color:var(--muted)}.stat-value{font-size:2rem;line-height:1.2;margin:8px 0 0;font-weight:800;letter-spacing:-.05em}.stat-accent{color:var(--cyan)}.pill{display:inline-block;padding:4px 9px;border-radius:99px;background:#103b35;color:#8df2cf;font-size:.78rem;font-weight:750}.footer{border-top:1px solid var(--border);padding:24px 0;margin-top:40px;color:var(--muted);font-size:.9rem}.actions{display:flex;gap:10px;flex-wrap:wrap}.empty{padding:28px;text-align:center;color:var(--muted)}
.qr-showcase{display:flex;gap:28px;align-items:center;flex-wrap:wrap;margin:26px 0;padding:24px;border:1px solid #2b5260;border-radius:22px;background:linear-gradient(135deg,#17283c,#10363d);box-shadow:0 18px 42px #00000025}.qr-frame{display:grid;place-items:center;flex:0 0 auto;padding:14px;border-radius:20px;background:linear-gradient(135deg,#4f8cff,#38d6c5);box-shadow:0 12px 32px #25c6f733}.qr-frame img{display:block;width:220px;height:220px;max-width:100%;background:white;border-radius:10px;padding:8px}.qr-copy{flex:1;min-width:220px}.qr-copy h2{margin:0 0 10px}.qr-kicker{display:inline-block;margin-bottom:10px;padding:5px 10px;border-radius:99px;background:#153d3b;color:#9cf4df;font-size:.78rem;font-weight:800;letter-spacing:.07em;text-transform:uppercase}.qr-copy p{margin:8px 0 18px}.qr-url{overflow-wrap:anywhere;display:inline-block;max-width:100%}@media(max-width:700px){.qr-showcase{padding:18px;gap:18px}.qr-frame{margin:auto}.qr-frame img{width:200px;height:200px}.qr-copy{text-align:center}}
/* Polished finishing touches: calmer surfaces, clearer navigation, and subtle motion. */
header{box-shadow:0 8px 28px #00000020}
header a{padding:7px 10px;border:1px solid transparent;border-radius:9px;transition:background .18s,border-color .18s,transform .18s}
header a:hover{background:#ffffff0b;border-color:#343b60;transform:translateY(-1px)}
main{animation:page-in .35s ease-out both}
@keyframes page-in{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:translateY(0)}}
.card,.feature{transition:border-color .2s,transform .2s,box-shadow .2s}
.feature:hover{transform:translateY(-3px);border-color:#4a5480;box-shadow:0 16px 34px #00000024}
.card:focus-within{border-color:#49447b}
.hero{isolation:isolate}
.hero:before{content:"";position:absolute;inset:0;z-index:-1;opacity:.16;background-image:radial-gradient(#a9b5ff 1px,transparent 1px);background-size:22px 22px;mask-image:linear-gradient(115deg,black,transparent 72%);pointer-events:none}
.hero .actions{position:relative;z-index:1}
button:focus-visible,.btn:focus-visible,a:focus-visible{outline:3px solid #79e5ff;outline-offset:3px}
button:active,.btn:active{transform:translateY(0) scale(.985)}
::selection{background:#7562e8;color:#fff}
::-webkit-scrollbar{width:10px;height:10px}::-webkit-scrollbar-track{background:#0b1020}::-webkit-scrollbar-thumb{background:#31566a;border-radius:99px;border:2px solid #0b1020}::-webkit-scrollbar-thumb:hover{background:#438c98}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}
@media(max-width:700px){header{gap:12px;padding:12px 18px}header strong{width:100%;margin:0}header a{font-size:.88rem}main{margin-top:20px;padding:0 14px}.card{padding:18px;border-radius:15px}.form-grid{grid-template-columns:1fr}.hero{padding:25px 20px}table{min-width:560px}}
</style></head><body><header><strong>LinkPulse</strong><a href="/">Home</a><a href="/#create">Create link</a><a href="/dashboard">Analytics</a><a href="/campaigns">Campaigns</a><a href="/import-csv">CSV import</a><a href="/admin">Admin</a></header><main>{% for m in get_flashed_messages() %}<p class="notice">{{ m }}</p>{% endfor %}{{ body|safe }}<footer class="footer">LinkPulse <span style="color:#52617f">Â·</span> Smart Link Management Platform <span style="float:right">Shorten. Track. Optimize.</span></footer></main></body></html>'''

def page(body, title="LinkPulse"):
    return render_template_string(BASE, body=body, title=title)

def now():
    return datetime.now().replace(microsecond=0)

def db():
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

def get_columns(c, table):
    return {row["name"] for row in c.execute(f"PRAGMA table_info({table})")}

def init_db():
    c = db()
    try:
        c.execute("CREATE TABLE IF NOT EXISTS links (id INTEGER PRIMARY KEY AUTOINCREMENT, original_url TEXT NOT NULL, short_code TEXT UNIQUE NOT NULL, created_at TEXT NOT NULL, clicks INTEGER NOT NULL DEFAULT 0)")
        c.execute("CREATE TABLE IF NOT EXISTS click_events (id INTEGER PRIMARY KEY AUTOINCREMENT, link_id INTEGER NOT NULL, clicked_at TEXT NOT NULL, referrer TEXT, user_agent TEXT, FOREIGN KEY(link_id) REFERENCES links(id))")
        for name, definition in {"is_active":"INTEGER NOT NULL DEFAULT 1", "expires_at":"TEXT", "max_clicks":"INTEGER", "password_hash":"TEXT", "tags":"TEXT NOT NULL DEFAULT ''", "campaign":"TEXT NOT NULL DEFAULT ''", "notes":"TEXT NOT NULL DEFAULT ''"}.items():
            if name not in get_columns(c, "links"):
                c.execute(f"ALTER TABLE links ADD COLUMN {name} {definition}")
        for name, definition in {"ip_hash":"TEXT", "device_type":"TEXT", "browser":"TEXT", "is_bot":"INTEGER NOT NULL DEFAULT 0"}.items():
            if name not in get_columns(c, "click_events"):
                c.execute(f"ALTER TABLE click_events ADD COLUMN {name} {definition}")
        c.execute("CREATE INDEX IF NOT EXISTS idx_events_link ON click_events(link_id)")
        c.execute("CREATE TABLE IF NOT EXISTS blocked_hosts (id INTEGER PRIMARY KEY AUTOINCREMENT, hostname TEXT UNIQUE NOT NULL, created_at TEXT NOT NULL)")
        c.commit()
    finally:
        c.close()

def valid_url(value):
    if not value or len(value) > 2048 or any(ch.isspace() for ch in value):
        return False
    try:
        p = urlparse(value)
        return p.scheme.lower() in ("http", "https") and bool(p.hostname) and not p.username and not p.password
    except ValueError:
        return False

def generate_code():
    return "".join(random.choices(string.ascii_letters + string.digits, k=6))

def hash_password(value):
    if not value:
        return None
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", value.encode(), salt, 200000)
    return salt.hex() + "$" + digest.hex()

def verify_password(value, stored):
    try:
        salt, digest = stored.split("$", 1)
        actual = hashlib.pbkdf2_hmac("sha256", value.encode(), bytes.fromhex(salt), 200000).hex()
        return hmac.compare_digest(actual, digest)
    except Exception:
        return False

def parse_expiry(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError("Enter a valid expiry date and time.")
    if dt <= now():
        raise ValueError("Expiry must be in the future.")
    return dt.isoformat()

def agent_info(ua):
    u = (ua or "").lower()
    bot = int(any(x in u for x in ("bot", "crawler", "spider", "headless", "slurp", "preview")))
    device = "Tablet" if any(x in u for x in ("ipad", "tablet")) else ("Mobile" if any(x in u for x in ("mobile", "iphone", "android")) else "Desktop/Other")
    browser = "Edge" if "edg/" in u else ("Opera" if "opr/" in u else ("Chrome" if "chrome/" in u else ("Firefox" if "firefox/" in u else ("Safari" if "safari/" in u else "Other"))))
    return device, browser, bot

def link_status(link):
    if not link["is_active"]:
        return "Disabled"
    if link["expires_at"]:
        try:
            if datetime.fromisoformat(link["expires_at"]) <= now():
                return "Expired"
        except ValueError:
            return "Invalid expiry"
    if link["max_clicks"] is not None and link["clicks"] >= link["max_clicks"]:
        return "Click limit reached"
    return "Active"

def short_url(code):
    return request.url_root.rstrip("/") + "/" + code

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login", next=request.path))
        return fn(*args, **kwargs)
    return wrapped

@app.before_request
def rate_limit():
    if request.endpoint not in {"shorten", "csv_import", "admin_login"}:
        return None
    ip = request.remote_addr or "unknown"
    stamp = now().timestamp()
    recent = [x for x in RATE_BUCKETS.get(ip, []) if stamp - x < 60]
    if len(recent) >= 20:
        return "Rate limit exceeded. Wait a minute and retry.", 429
    recent.append(stamp)
    RATE_BUCKETS[ip] = recent

@app.route("/")
def home():
    body = '''<section class="hero"><span class="eyebrow">Smart link management platform</span><h1 style="margin-top:22px">Shorten links.<br><span class="gradient-text">Understand your audience.</span></h1><p>One place to create branded short links, organize campaigns, generate QR codes, and understand what happens after every click.</p><div class="actions" style="margin-top:23px"><a class="btn" href="#create">Create your first link â†—</a><a class="btn secondary" href="/dashboard">Explore analytics</a></div><div class="grid" style="margin-top:30px"><div class="feature"><div class="feature-icon">â†—</div><strong>Smart redirects</strong><p>Fast short links with optional expiry, click limits, and password protection.</p></div><div class="feature"><div class="feature-icon">â—‰</div><strong>Click analytics</strong><p>Track clicks, devices, browsers, referrers, and recent visits.</p></div><div class="feature"><div class="feature-icon">â–¦</div><strong>Campaign tools</strong><p>Organize links with campaign names and tags, or import links from CSV.</p></div></div></section>
<section class="section-heading" id="create"><div><span class="eyebrow">Link builder</span><h2 style="margin:12px 0 0">Create a trackable short link</h2></div><span class="muted">Takes just a few seconds</span></section><section class="card"><form method="post" action="/shorten"><label>Destination URL *</label><input name="original_url" type="text" inputmode="url" autocapitalize="off" spellcheck="false" placeholder="https://example.com/your-long-link" aria-describedby="url-help" required><small id="url-help">Enter a complete address starting with https:// or http://</small><div class="form-grid"><div><label>Custom alias</label><input name="custom_alias" placeholder="my-campaign" minlength="3" maxlength="40"><small>3â€“40 letters, numbers, - or _</small></div><div><label>Expiry date and time</label><input name="expires_at" type="datetime-local"></div><div><label>Maximum clicks</label><input name="max_clicks" type="number" min="1" placeholder="Unlimited"></div><div><label>Password protection</label><input name="link_password" type="password" minlength="4" placeholder="Optional password"></div><div><label>Campaign</label><input name="campaign" placeholder="Product launch"></div><div><label>Tags (comma-separated)</label><input name="tags" placeholder="social, launch, newsletter"></div></div><label>Notes (optional)</label><textarea name="notes" rows="2" placeholder="Add a note to help your team recognize this link"></textarea><button type="submit">âœ¦ Create short link</button></form></section><div class="section-heading"><div><h2>Everything you need to manage links</h2><p style="margin:0">From creation to clicks, keep your links organized and measurable.</p></div></div><div class="grid"><section class="feature"><div class="feature-icon">â–¤</div><h3>Link dashboard</h3><p>Review link status, click counts, campaigns, and quick actions.</p><a href="/dashboard">Open dashboard â†’</a></section><section class="feature"><div class="feature-icon">â—·</div><h3>Detailed analytics</h3><p>Explore click activity, device and browser summaries, and referrers.</p><a href="/dashboard">View analytics â†’</a></section><section class="feature"><div class="feature-icon">â–¦</div><h3>QR codes & bulk import</h3><p>Download a QR code for a link or create many links from a CSV file.</p><a href="/import-csv">Import links â†’</a></section><section class="feature"><div class="feature-icon">â—‡</div><h3>Campaign organization</h3><p>Group your links into campaigns and use tags to keep them tidy.</p><a href="/campaigns">View campaigns â†’</a></section></div>'''
    return page(body, "Create link")

@app.route("/shorten", methods=["POST"])
def shorten():
    original = request.form.get("original_url", "").strip()
    alias = request.form.get("custom_alias", "").strip()
    if not valid_url(original):
        body = '<section class="card"><h1>Invalid destination URL</h1><p class="error">Please enter a complete, valid URL beginning with <code>https://</code> or <code>http://</code>.</p><p>For example: <code>https://www.google.com</code></p><p><a class="btn" href="/#create">Go back and try again</a></p></section>'
        return page(body, "Invalid URL"), 400
    if alias and not ALIAS_RE.fullmatch(alias):
        return "Alias must be 3â€“40 letters, numbers, hyphens or underscores.", 400
    try:
        expiry = parse_expiry(request.form.get("expires_at", "").strip())
        limit_text = request.form.get("max_clicks", "").strip()
        limit = int(limit_text) if limit_text else None
        if limit is not None and limit < 1:
            return "Maximum clicks must be at least 1.", 400
    except ValueError as exc:
        return str(exc), 400
    password = request.form.get("link_password", "")
    if password and len(password) < 4:
        return "Password must contain at least 4 characters.", 400
    c = db()
    try:
        host = (urlparse(original).hostname or "").lower()
        blocked = c.execute("SELECT 1 FROM blocked_hosts WHERE ?=hostname OR ? LIKE '%.'||hostname LIMIT 1", (host, host)).fetchone()
        if blocked:
            return "This destination host is blocked by the administrator.", 400
        code = alias or ""
        if alias and c.execute("SELECT 1 FROM links WHERE short_code=?", (alias,)).fetchone():
            return "Alias already exists. Choose another.", 409
        if not code:
            for _ in range(30):
                code = generate_code()
                if not c.execute("SELECT 1 FROM links WHERE short_code=?", (code,)).fetchone():
                    break
            else:
                return "Could not generate a unique code.", 500
        c.execute("INSERT INTO links(original_url,short_code,created_at,clicks,is_active,expires_at,max_clicks,password_hash,tags,campaign,notes) VALUES(?,?,?,0,1,?,?,?,?,?,?)", (original, code, now().isoformat(), expiry, limit, hash_password(password), request.form.get("tags", "")[:300], request.form.get("campaign", "")[:120], request.form.get("notes", "")[:500]))
        c.commit()
    finally:
        c.close()
    safe_code = escape(code)
    url = escape(short_url(code))
    body = f'<section class="card"><h1>Short link created!</h1><p>Your short URL:</p><p><a href="{url}"><code>{url}</code></a></p><div class="qr-showcase"><div class="qr-frame"><img src="/qr/{safe_code}.svg" alt="QR code for {safe_code}" width="220" height="220"></div><div class="qr-copy"><span class="qr-kicker">✦ Ready to scan</span><h2>Take your link anywhere</h2><p>Point your phone camera at this QR code to open your LinkPulse short link. No file download needed.</p><p><a class="qr-url" href="{url}"><code>{url}</code></a></p><a class="btn secondary" href="/qr/{safe_code}.svg" target="_blank" rel="noopener">View QR image</a></div></div><p><a class="btn" href="/analytics/{safe_code}">View analytics</a></p><p><a href="/">Create another</a> | <a href="/dashboard">Dashboard</a></p></section>'
    return page(body, "Link created")

@app.route("/<short_code>", methods=["GET", "POST"])
def visit(short_code):
    c = db()
    try:
        link = c.execute("SELECT * FROM links WHERE short_code=?", (short_code,)).fetchone()
        if not link:
            abort(404)
        # Enforce link rules at redirect time, not only in the dashboard.
        # Check the stored active flag directly before counting a click or redirecting.
        if int(link["is_active"] or 0) != 1:
            return page('<section class="card"><h1>Link unavailable</h1><p>This short link has been disabled by the administrator.</p></section>'), 403

        state = link_status(link)
        if state != "Active":
            status_code = 410 if state in ("Expired", "Click limit reached") else 403
            return page(f'<section class="card"><h1>Link unavailable</h1><p>Status: {escape(state)}</p></section>'), status_code
        unlocked = session.get("unlocked", [])
        if link["password_hash"] and short_code not in unlocked:
            if request.method == "GET":
                return page('<section class="card"><h1>Password-protected link</h1><form method="post"><label>Password</label><input type="password" name="password" required><button>Continue</button></form></section>')
            if not verify_password(request.form.get("password", ""), link["password_hash"]):
                return page('<section class="card"><h1>Incorrect password</h1><form method="post"><input type="password" name="password" required><button>Try again</button></form></section>'), 401
            session["unlocked"] = (unlocked + [short_code])[-100:]
        ua = request.user_agent.string[:500]
        device, browser, bot = agent_info(ua)
        ip_hash = hashlib.sha256((request.remote_addr or "").encode()).hexdigest() if request.remote_addr else None
        c.execute("UPDATE links SET clicks=COALESCE(clicks,0)+1 WHERE id=?", (link["id"],))
        c.execute("INSERT INTO click_events(link_id,clicked_at,referrer,user_agent,ip_hash,device_type,browser,is_bot) VALUES(?,?,?,?,?,?,?,?)", (link["id"], now().isoformat(), request.referrer, ua, ip_hash, device, browser, bot))
        c.commit()
        destination = link["original_url"]
    finally:
        c.close()
    return redirect(destination, 302)

@app.route("/dashboard")
def dashboard():
    c = db()
    try:
        links = c.execute("SELECT * FROM links ORDER BY id DESC").fetchall()
        total = len(links)
        clicks = c.execute("SELECT COUNT(*) FROM click_events").fetchone()[0]
        nonbot = c.execute("SELECT COUNT(*) FROM click_events WHERE is_bot=0").fetchone()[0]
        device = c.execute("SELECT COALESCE(device_type,'Unknown') label,COUNT(*) n FROM click_events WHERE is_bot=0 GROUP BY label ORDER BY n DESC").fetchall()
        browser = c.execute("SELECT COALESCE(browser,'Unknown') label,COUNT(*) n FROM click_events WHERE is_bot=0 GROUP BY label ORDER BY n DESC").fetchall()
        bots = c.execute("SELECT COUNT(*) FROM click_events WHERE is_bot=1").fetchone()[0]
    finally:
        c.close()
    row_html = []
    for link in links:
        code = escape(link["short_code"])
        url = escape(link["original_url"])
        campaign = escape(link["campaign"] or "â€”")
        action = "Disable" if link["is_active"] else "Enable"
        row_html.append(f'<tr><td><a href="/{code}">{code}</a><br><small>{url}</small></td><td>{link["clicks"]}</td><td>{escape(link_status(link))}</td><td>{campaign}</td><td><a href="/analytics/{code}">Analytics</a> | <a href="/qr/{code}.svg" target="_blank" rel="noopener">View QR</a><form method="post" action="/links/{code}/toggle"><button class="secondary">{action}</button></form></td></tr>')
    device_html = "".join(f'<p>{escape(r["label"])}: {r["n"]}</p>' for r in device) or "<p>No data yet.</p>"
    browser_html = "".join(f'<p>{escape(r["label"])}: {r["n"]}</p>' for r in browser) or "<p>No data yet.</p>"
    rows_joined = "".join(row_html)
    body = (
        f'<h1>Analytics dashboard</h1><div class="grid"><section class="card"><small>Total links</small><h2>{total}</h2></section>'
        f'<section class="card"><small>Recorded clicks</small><h2>{clicks}</h2></section>'
        f'<section class="card"><small>Non-bot clicks</small><h2>{nonbot}</h2></section>'
        f'<section class="card"><small>Detected bot-like requests</small><h2>{bots}</h2></section></div>'
        f'<section class="card"><h2>Links</h2><input id="search" placeholder="Search links, URLs, campaignsâ€¦" oninput="filterRows()">'
        f'<div class="scroll"><table id="links"><thead><tr><th>Link</th><th>Clicks</th><th>Status</th><th>Campaign</th><th>Actions</th></tr></thead><tbody>{rows_joined}</tbody></table></div></section>'
        f'<div class="grid"><section class="card"><h2>Devices</h2>{device_html}</section><section class="card"><h2>Browsers</h2>{browser_html}</section></div>'
        + "<script>function filterRows(){let q=document.getElementById('search').value.toLowerCase();document.querySelectorAll('#links tbody tr').forEach(r=>r.style.display=r.innerText.toLowerCase().includes(q)?'':'none')}</script>"
    )
    return page(body, "Dashboard")

@app.route("/links/<short_code>/toggle", methods=["POST"])
def toggle(short_code):
    c = db()
    try:
        link = c.execute("SELECT * FROM links WHERE short_code=?", (short_code,)).fetchone()
        if not link:
            abort(404)
        c.execute("UPDATE links SET is_active=? WHERE id=?", (0 if link["is_active"] else 1, link["id"]))
        c.commit()
    finally:
        c.close()
    flash("Link status updated.")
    return redirect("/dashboard")

@app.route("/analytics/<short_code>")
def analytics(short_code):
    c = db()
    try:
        link = c.execute("SELECT * FROM links WHERE short_code=?", (short_code,)).fetchone()
        if not link:
            abort(404)
        events = c.execute("SELECT * FROM click_events WHERE link_id=? ORDER BY id DESC LIMIT 50", (link["id"],)).fetchall()
        daily = c.execute("SELECT DATE(clicked_at) d,COUNT(*) n FROM click_events WHERE link_id=? GROUP BY DATE(clicked_at) ORDER BY d", (link["id"],)).fetchall()
        devices = c.execute("SELECT COALESCE(device_type,'Unknown') label,COUNT(*) n FROM click_events WHERE link_id=? AND is_bot=0 GROUP BY label", (link["id"],)).fetchall()
        browsers = c.execute("SELECT COALESCE(browser,'Unknown') label,COUNT(*) n FROM click_events WHERE link_id=? AND is_bot=0 GROUP BY label", (link["id"],)).fetchall()
        refs = c.execute("SELECT COALESCE(NULLIF(referrer,''),'Direct/Unknown') label,COUNT(*) n FROM click_events WHERE link_id=? AND is_bot=0 GROUP BY label ORDER BY n DESC LIMIT 10", (link["id"],)).fetchall()
        unique = c.execute("SELECT COUNT(DISTINCT ip_hash) FROM click_events WHERE link_id=? AND is_bot=0 AND ip_hash IS NOT NULL", (link["id"],)).fetchone()[0]
    finally:
        c.close()
    daily_html = "".join(f'<tr><td>{escape(str(r["d"]))}</td><td>{r["n"]}</td></tr>' for r in daily)
    event_html = "".join(f'<tr><td>{escape(str(e["clicked_at"]))}</td><td>{escape(e["referrer"] or "Direct/Unknown")}</td><td>{escape(e["device_type"] or "Unknown")}</td><td>{escape(e["browser"] or "Unknown")}</td><td>{"Likely bot" if e["is_bot"] else "Human/unknown"}</td></tr>' for e in events)
    device_html = "".join(f'<p>{escape(r["label"])}: {r["n"]}</p>' for r in devices) or "<p>No data yet.</p>"
    browser_html = "".join(f'<p>{escape(r["label"])}: {r["n"]}</p>' for r in browsers) or "<p>No data yet.</p>"
    ref_html = "".join(f'<p>{escape(r["label"])}: {r["n"]}</p>' for r in refs) or "<p>No data yet.</p>"
    url = escape(short_url(short_code))
    body = f'<h1>Link analytics: {escape(short_code)}</h1><section class="card"><p><a href="{url}">{url}</a></p><p><b>Status:</b> {escape(link_status(link))} | <b>Clicks:</b> {link["clicks"]} | <b>Estimated unique visitors:</b> {unique}</p><p><b>Destination:</b> {escape(link["original_url"])}</p><p><b>Campaign:</b> {escape(link["campaign"] or "â€”")} | <b>Tags:</b> {escape(link["tags"] or "â€”")} | <b>Expires:</b> {escape(link["expires_at"] or "Never")} | <b>Click limit:</b> {link["max_clicks"] or "Unlimited"}</p><div class="qr-showcase"><div class="qr-frame"><img src="/qr/{escape(short_code)}.svg" alt="QR code for {escape(short_code)}" width="220" height="220"></div><div class="qr-copy"><span class="qr-kicker">✦ Link QR code</span><h2>Scan to visit your link</h2><p>Use your phone camera to open this short link. Keep this page open to display the QR code whenever you need it.</p><p><a class="qr-url" href="{url}"><code>{url}</code></a></p><a class="btn secondary" href="/qr/{escape(short_code)}.svg" target="_blank" rel="noopener">View QR image</a></div></div></section><div class="grid"><section class="card"><h2>Daily clicks</h2><table><tr><th>Date</th><th>Clicks</th></tr>{daily_html}</table></section><section class="card"><h2>Devices</h2>{device_html}<h2>Browsers</h2>{browser_html}</section></div><section class="card"><h2>Top referrers</h2>{ref_html}</section><section class="card"><h2>Recent visits</h2><div class="scroll"><table><tr><th>Time</th><th>Referrer</th><th>Device</th><th>Browser</th><th>Classification</th></tr>{event_html}</table></div></section>'
    return page(body, "Link analytics")

@app.route("/campaigns")
def campaigns():
    c = db()
    try:
        rows = c.execute("SELECT COALESCE(NULLIF(campaign,''),'(No campaign)') name,COUNT(*) links,COALESCE(SUM(clicks),0) clicks FROM links GROUP BY name ORDER BY clicks DESC").fetchall()
    finally:
        c.close()
    table = "".join(f'<tr><td>{escape(r["name"])}</td><td>{r["links"]}</td><td>{r["clicks"]}</td></tr>' for r in rows)
    return page(f'<h1>Campaigns</h1><section class="card"><table><tr><th>Campaign</th><th>Links</th><th>Clicks</th></tr>{table}</table></section>', "Campaigns")

@app.route("/import-csv", methods=["GET", "POST"])
def csv_import():
    results = []
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename.lower().endswith(".csv"):
            return "Upload a .csv file.", 400
        try:
            reader = csv.DictReader(io.StringIO(file.stream.read().decode("utf-8-sig")))
            if not reader.fieldnames or "original_url" not in reader.fieldnames:
                return "CSV needs an original_url column.", 400
            c = db()
            try:
                for row in reader:
                    original = (row.get("original_url") or "").strip()
                    alias = (row.get("custom_alias") or "").strip()
                    if not valid_url(original):
                        results.append((original, "Skipped: invalid URL")); continue
                    if alias and not ALIAS_RE.fullmatch(alias):
                        results.append((original, "Skipped: invalid alias")); continue
                    if not alias:
                        for _ in range(30):
                            alias = generate_code()
                            if not c.execute("SELECT 1 FROM links WHERE short_code=?", (alias,)).fetchone():
                                break
                    if not alias or c.execute("SELECT 1 FROM links WHERE short_code=?", (alias,)).fetchone():
                        results.append((original, "Skipped: duplicate alias")); continue
                    try:
                        expiry = parse_expiry((row.get("expires_at") or "").strip())
                        limit_text = (row.get("max_clicks") or "").strip()
                        limit = int(limit_text) if limit_text else None
                        if limit is not None and limit < 1:
                            raise ValueError()
                    except ValueError:
                        results.append((original, "Skipped: invalid expiry/click limit")); continue
                    c.execute("INSERT INTO links(original_url,short_code,created_at,clicks,is_active,expires_at,max_clicks,tags,campaign,notes) VALUES(?,?,?,0,1,?,?,?,?,?)", (original, alias, now().isoformat(), expiry, limit, (row.get("tags") or "")[:300], (row.get("campaign") or "")[:120], (row.get("notes") or "")[:500]))
                    results.append((original, "Imported as " + alias))
                c.commit()
            finally:
                c.close()
        except (UnicodeDecodeError, csv.Error) as exc:
            return f"CSV error: {escape(str(exc))}", 400
    result_html = "".join(f'<tr><td>{escape(u)}</td><td>{escape(result)}</td></tr>' for u, result in results)
    body = f'<h1>Bulk CSV import</h1><section class="card"><p>CSV columns: <code>original_url</code> (required), <code>custom_alias</code>, <code>expires_at</code>, <code>max_clicks</code>, <code>tags</code>, <code>campaign</code>, <code>notes</code> (optional).</p><p><a href="/sample.csv">Download sample CSV</a></p><form method="post" enctype="multipart/form-data"><input type="file" name="file" accept=".csv" required><button>Import links</button></form></section><section class="card"><table><tr><th>URL</th><th>Result</th></tr>{result_html}</table></section>'
    return page(body, "CSV import")

@app.route("/sample.csv")
def sample_csv():
    data = "original_url,custom_alias,expires_at,max_clicks,tags,campaign,notes\nhttps://example.com,example-demo,,100,\"demo,test\",Launch,Sample link\n"
    return Response(data, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=linkpulse_sample.csv"})

@app.route("/qr/<short_code>.svg")
def qr(short_code):
    c = db()
    try:
        if not c.execute("SELECT 1 FROM links WHERE short_code=?", (short_code,)).fetchone():
            abort(404)
    finally:
        c.close()
    try:
        import qrcode
        import qrcode.image.svg
        image = qrcode.make(short_url(short_code), image_factory=qrcode.image.svg.SvgImage)
        output = io.BytesIO()
        image.save(output)
        return Response(output.getvalue(), mimetype="image/svg+xml", headers={"Content-Disposition": "inline", "Cache-Control": "public, max-age=300"})
    except ImportError:
        return "Install QR support with: python -m pip install 'qrcode[pil]'", 501

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = ""
    if request.method == "POST":
        if hmac.compare_digest(request.form.get("password", ""), ADMIN_PASSWORD):
            session["admin"] = True
            return redirect(request.args.get("next") or "/admin")
        error = "Incorrect password."
    body = f'<section class="card"><h1>Admin login</h1><p class="error">{escape(error)}</p><form method="post"><label>Admin password</label><input type="password" name="password" required><button>Sign in</button></form><p class="muted">For deployment, configure LINKPULSE_ADMIN_PASSWORD in the hosting environment.</p></section>'
    return page(body, "Admin login")

@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin", None)
    return redirect("/")

@app.route("/admin")
@admin_required
def admin():
    c = db()
    try:
        links = c.execute("SELECT * FROM links ORDER BY id DESC").fetchall()
        blocked = c.execute("SELECT * FROM blocked_hosts ORDER BY hostname").fetchall()
        total = c.execute("SELECT COUNT(*) FROM click_events").fetchone()[0]
    finally:
        c.close()
    link_rows = "".join(f'<tr><td>{escape(l["short_code"])}</td><td>{escape(l["original_url"])}</td><td>{escape(link_status(l))}</td><td><form method="post" action="/admin/disable/{escape(l["short_code"])}"><button>Disable</button></form></td></tr>' for l in links)
    host_rows = "".join(f'<li>{escape(h["hostname"])} <form style="display:inline" method="post" action="/admin/unblock/{h["id"]}"><button class="secondary">Remove</button></form></li>' for h in blocked)
    body = f'<h1>Admin controls</h1><section class="card"><p>Total links: {len(links)} | Recorded clicks: {total}</p><form method="post" action="/admin/block"><label>Block destination hostname</label><input name="hostname" placeholder="example.com" required><button>Add block</button></form><h3>Blocked hosts</h3><ul>{host_rows}</ul><form method="post" action="/admin/logout"><button class="secondary">Log out</button></form></section><section class="card"><h2>All links</h2><div class="scroll"><table><tr><th>Alias</th><th>Destination</th><th>Status</th><th>Action</th></tr>{link_rows}</table></div></section>'
    return page(body, "Admin")

@app.route("/admin/disable/<short_code>", methods=["POST"])
@admin_required
def admin_disable(short_code):
    c = db()
    try:
        cur = c.execute("UPDATE links SET is_active=0 WHERE short_code=?", (short_code,))
        if not cur.rowcount:
            abort(404)
        c.commit()
    finally:
        c.close()
    return redirect("/admin")

@app.route("/admin/block", methods=["POST"])
@admin_required
def admin_block():
    host = request.form.get("hostname", "").strip().lower()
    host = host.removeprefix("https://").removeprefix("http://").split("/")[0]
    if not host or "." not in host or any(ch.isspace() for ch in host):
        return "Enter a valid hostname.", 400
    c = db()
    try:
        c.execute("INSERT OR IGNORE INTO blocked_hosts(hostname,created_at) VALUES(?,?)", (host, now().isoformat()))
        c.commit()
    finally:
        c.close()
    return redirect("/admin")

@app.route("/admin/unblock/<int:host_id>", methods=["POST"])
@admin_required
def admin_unblock(host_id):
    c = db()
    try:
        c.execute("DELETE FROM blocked_hosts WHERE id=?", (host_id,))
        c.commit()
    finally:
        c.close()
    return redirect("/admin")

@app.errorhandler(404)
def missing(error):
    return page('<section class="card"><h1>Not found</h1><p>The requested page or short link does not exist.</p><a href="/">Go home</a></section>', "Not found"), 404

if __name__ == "__main__":
    init_db()
    # Listen on the computer and its local network so a phone on the same Wi-Fi can connect.
    # Keep debug disabled while the server is reachable from other devices.
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False,
    )
