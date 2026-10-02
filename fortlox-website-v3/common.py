"""
Shared building blocks for every page of the Fortlox Security website:
contact details, styling, header, footer, product cards and image loading.
"""

import base64
import datetime
import html as html_lib
import io
import os
from pathlib import Path
from urllib.parse import quote

import streamlit as st

BASE = Path(__file__).parent

# ───────────────────────────── CONTACT DETAILS ─────────────────────────────
COMPANY = "Fortlox Security"
PHONE_DISPLAY = "01453 702502"
PHONE_LINK = "+441453702502"
EMAIL = "sales@fortloxsecurity.com"
WEBSITE = "www.fortloxsecurity.com"
ADDRESS_LINES = ["2 Taits Hill Barn, Taits Hill", "Stinchcombe GL11 6BN"]
MAP_QUERY = "2 Taits Hill Barn, Taits Hill, Stinchcombe GL11 6BN"

# ───────────────────────────── FEATURE COPY ─────────────────────────────
TELEPHONY_FEATURES = [
    ("devices", "One app for every device",
     "Calls, video meetings and team chat on desk phones, web, Windows, Mac, iPhone and Android."),
    ("chat", "Every channel in one place",
     "SMS, WhatsApp, Facebook Messenger, live chat and email sit alongside your calls, included as standard."),
    ("headset", "Contact-centre tools built in",
     "Call queues, live wallboards, skills-based routing, and supervisor listen, whisper and barge."),
    ("link", "Works with your CRM",
     "Screen pops, click-to-dial and AI call summaries logged into 30+ systems, including Dentally, Cliniko, Reapit and Street."),
    ("mic", "Call recording and voicemail to email",
     "Record calls for training and disputes, and get voicemails in your inbox as audio files."),
    ("sliders", "Simple to change",
     "Call routes are built on a visual planner, new handsets set themselves up, and new staff are added in minutes."),
]

CCTV_FEATURES = [
    ("moon", "Colour footage after dark",
     "Low-light sensors keep night-time recordings in full colour, so clothing and vehicles can be identified."),
    ("zap", "Deters intruders, not just records them",
     "Smart detection tells people and vehicles apart from animals and foliage, then triggers lights and a siren."),
    ("search", "Search footage by description",
     "Type something like \u201cwhite van\u201d to jump to the moment, instead of scrolling through hours of recording."),
    ("camera", "A camera for every spot",
     "Domes, bullets and turrets, 180\u00b0 panoramic, pan-tilt-zoom and thermal cameras for long perimeters."),
    ("sun", "Sites with no power or broadband",
     "4G and solar-powered cameras for car parks, building sites, yards and fields."),
    ("key", "Doors, gates and number plates",
     "Access control, video intercoms and number-plate recognition that work on the same system."),
]

STEPS = [
    ("Site survey", "We look at your building, your current phone lines and exactly what each camera needs to see."),
    ("Written quote", "Equipment, installation and any monthly costs are set out clearly before anything is ordered."),
    ("Installation", "We fit the cameras, set up the phones and move your numbers across, working around your opening hours."),
    ("Ongoing support", "One number to call for both systems, with remote help and on-site visits when they're needed."),
]

# ───────────────────────────── HELPERS ─────────────────────────────

def esc(v):
    return html_lib.escape(str(v if v is not None else ""), quote=True)


def render_html(markup, target=None):
    # Flatten lines: indented HTML inside st.markdown would otherwise become a code block
    (target or st).markdown(" ".join(l.strip() for l in markup.splitlines()), unsafe_allow_html=True)


@st.cache_data
def _file_index():
    """Every file in the repo, so images are found whatever folder they're in."""
    index = {}
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        for f in files:
            index.setdefault(f.lower(), os.path.join(root, f))
    return index


def find_asset(*names):
    """Find a file by name: any folder, any letter case, and tolerant of extra
    text in front of the name (e.g. '123_Yealink_T73W.png' matches 'Yealink_T73W.png')."""
    index = _file_index()
    for n in names:
        n = n.lower()
        if n in index:
            return index[n]
        for fname, path in index.items():
            if fname.endswith(n):
                return path
    return None


@st.cache_data
def b64_file(path) -> str:
    if not path:
        return ""
    return base64.b64encode(Path(path).read_bytes()).decode()


@st.cache_data(show_spinner=False)
def product_image(name: str, max_px: int = 560) -> str:
    """Return a small, web-friendly data URI for a product photo ('' if not found)."""
    path = find_asset(name)
    if not path:
        return ""
    try:
        from PIL import Image
        from PIL import ImageDraw
        src = Image.open(path).convert("RGBA")
        # Many product photos sit on a white box. Flatten onto white, then make the
        # white that touches the edges see-through, so every product sits directly
        # on the card's own backdrop (works for white and transparent backgrounds).
        im = Image.new("RGBA", src.size, (255, 255, 255, 255))
        im.alpha_composite(src)
        w, h = im.size
        seeds = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
                 (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]
        for xy in seeds:
            r, g, b, a = im.getpixel(xy)
            if a == 255 and min(r, g, b) > 235:
                ImageDraw.floodfill(im, xy, (255, 255, 255, 0), thresh=24)
        bbox = im.getchannel("A").getbbox()      # trim empty margins
        if bbox:
            pad = int(max(im.size) * 0.03)
            im = im.crop((max(bbox[0] - pad, 0), max(bbox[1] - pad, 0),
                          min(bbox[2] + pad, w), min(bbox[3] + pad, h)))
        im.thumbnail((max_px, max_px))
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=86)
        return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        ext = Path(path).suffix.lower().lstrip(".").replace("jpg", "jpeg")
        return f"data:image/{ext};base64," + b64_file(path)


ICONS = {
    "phone": '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    "mail": '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>',
    "pin": '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    "devices": '<rect x="5" y="2" width="14" height="20" rx="2"/><line x1="12" y1="18" x2="12.01" y2="18"/>',
    "chat": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "headset": '<path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>',
    "link": '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    "mic": '<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/>',
    "sliders": '<line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/>',
    "moon": '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>',
    "zap": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "search": '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    "camera": '<polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/>',
    "sun": '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>',
    "key": '<path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/>',
}



def icon(name, size=20):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


def feature_grid(features, cols=2):
    cards = "".join(
        f'<div class="fx-feature"><div class="fx-ico">{icon(ic)}</div>'
        f'<h4>{esc(t)}</h4><p>{esc(d)}</p></div>'
        for ic, t, d in features
    )
    extra = " three" if cols == 3 else ""
    return f'<div class="fx-features{extra}">{cards}</div>'


def mailto(subject, body=""):
    url = f"mailto:{EMAIL}?subject={quote(subject)}"
    return url + (f"&body={quote(body)}" if body else "")


# ───────────────────────────── ILLUSTRATIONS ─────────────────────────────
CALL_POP = f"""
<div class="fx-pop" role="img" aria-label="Example of an incoming call showing the caller's customer record">
  <div class="row">
    <div class="ring">{icon('phone', 18)}</div>
    <div><div class="who">Hollis &amp; Grant Dental</div><div class="num">Incoming · 01453 ••• •••</div></div>
  </div>
  <div class="crm"><strong>Customer record found.</strong> Last call 3 days ago: booked a check-up for Thursday at 10:30.</div>
  <div class="acts"><span class="ok">Answer</span><span class="no">Send to voicemail</span></div>
</div>
"""

CAM_TILE = """
<div class="fx-cam" role="img" aria-label="Example camera view detecting a vehicle at night">
  <div class="bldg"></div><div class="van"></div>
  <div class="box"><span>Vehicle detected</span></div>
  <div class="hud"><span class="rec"><i></i>CAM 03 · Yard</span><span>02:14:37</span></div>
</div>
"""

# ───────────────────────────── PAGE PARTS ─────────────────────────────
CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Saira:wght@500;600;700;800&display=swap');
:root{
  --bg:#070C16; --surface:#0E1726; --surface-2:#132036; --surface-3:#1A2A45;
  --border:rgba(148,178,210,.14); --border-strong:rgba(148,178,210,.28);
  --text:#E7EAF3; --muted:#93A1B8; --faint:#5E6E88;
  --cyan:#29A9E1; --cyan-2:#5CCBF4; --blue:#136AA8; --steel:#B9C3CE; --led:#3DDC84;
  --grad:linear-gradient(135deg,#5CCBF4 0%,#29A9E1 45%,#136AA8 100%);
  --radius:16px;
  --display:'Saira','Inter',system-ui,sans-serif;
}
html,body,[class*="css"],.stApp,button,input,textarea,select,
.stApp [data-testid="stMarkdownContainer"] :is(p,div,span,a,li,strong,b,h4),
.stApp [data-testid="stWidgetLabel"] p{font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif!important}
.stApp [data-testid="stMarkdownContainer"] :is(h1,h2,.fx-word,.fx-word b,.fx-word span,.fx-step .n,.fx-form-title),
.stApp [data-testid="stMarkdownContainer"] :is(h1,h2) span{font-family:var(--display)!important}
[data-testid="stHeaderActionElements"],.stMarkdown h1 a[href^="#"],.stMarkdown h2 a[href^="#"]{display:none!important}
.stApp{background:
  radial-gradient(1100px 520px at 88% -8%,rgba(41,169,225,.10),transparent 60%),
  radial-gradient(800px 480px at 0% 30%,rgba(19,106,168,.08),transparent 60%),
  var(--bg)}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none!important}
footer{visibility:hidden}
.block-container{max-width:1180px!important;padding:0 28px 0!important}
[data-testid="stMain"],[data-testid="stAppViewContainer"]{scroll-behavior:smooth}
a{color:var(--cyan-2)}
:focus-visible{outline:2px solid var(--cyan-2)!important;outline-offset:3px;border-radius:6px}
/* Streamlit puts a gap between every element; sections manage their own spacing */
[data-testid="stMarkdownContainer"] p{margin-bottom:0}

/* ---------- Top bar ---------- */
.fx-top{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:18px 0;border-bottom:1px solid var(--border)}
.fx-brand{display:flex;align-items:center;gap:12px;text-decoration:none!important}
.fx-brand img{height:38px;width:auto}
.fx-word{font-family:var(--display);font-weight:800;font-size:1.18rem;letter-spacing:.04em;line-height:1}
.fx-word b{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.fx-word span{color:var(--steel);font-weight:700}
.fx-nav{display:flex;align-items:center;gap:6px}
.fx-nav a{color:var(--muted)!important;text-decoration:none!important;font-size:.9rem;font-weight:500;padding:8px 12px;border-radius:9px}
.fx-nav a:hover{color:var(--text)!important;background:var(--surface)}
.fx-nav a.fx-call{color:var(--text)!important;border:1px solid var(--border-strong);display:inline-flex;align-items:center;gap:8px;margin-left:6px}
.fx-nav a.fx-call svg{color:var(--cyan)}

/* ---------- Buttons ---------- */
.fx-btn{display:inline-flex;align-items:center;gap:10px;padding:13px 20px;border-radius:12px;font-weight:600;font-size:.97rem;text-decoration:none!important;transition:transform .15s ease,border-color .15s ease}
.fx-btn:hover{transform:translateY(-1px)}
.fx-btn.primary{background:var(--grad);color:#04121F!important;box-shadow:0 12px 28px -12px rgba(41,169,225,.9)}
.fx-btn.ghost{border:1px solid var(--border-strong);color:var(--text)!important;background:rgba(14,23,38,.6)}
.fx-btn.ghost:hover{border-color:var(--cyan)}

/* ---------- Hero ---------- */
.fx-hero{display:grid;grid-template-columns:1.05fr .95fr;gap:40px;align-items:center;padding:72px 0 64px}
.fx-where{display:inline-flex;align-items:center;gap:9px;font-size:.86rem;font-weight:500;color:var(--muted);margin-bottom:20px}
.fx-where .dot{width:8px;height:8px;border-radius:50%;background:var(--led);box-shadow:0 0 0 4px rgba(61,220,132,.16),0 0 12px rgba(61,220,132,.7)}
.fx-hero h1{font-family:var(--display);font-weight:800;font-size:clamp(2.3rem,4.6vw,3.6rem);line-height:1.04;letter-spacing:-.01em;color:var(--text);margin:0 0 20px;padding:0}
.fx-hero .lede{font-size:1.1rem;line-height:1.65;color:var(--muted);max-width:34em;margin:0 0 30px}
.fx-ctas{display:flex;flex-wrap:wrap;gap:12px}
.fx-facts{display:flex;flex-wrap:wrap;gap:10px 26px;margin-top:34px;padding-top:24px;border-top:1px solid var(--border);color:var(--muted);font-size:.9rem}
.fx-facts div{display:flex;align-items:center;gap:8px}
.fx-facts svg{color:var(--cyan)}

.fx-stage{position:relative;aspect-ratio:1.25/1;display:grid;place-items:center}
.fx-stage::before{content:"";position:absolute;inset:6% 4%;border-radius:50%;
  background:radial-gradient(closest-side,rgba(41,169,225,.22),rgba(41,169,225,.05) 60%,transparent 75%)}
.fx-stage::after{content:"";position:absolute;inset:0;border-radius:24px;
  background-image:linear-gradient(rgba(148,178,210,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(148,178,210,.07) 1px,transparent 1px);
  background-size:32px 32px;-webkit-mask-image:radial-gradient(closest-side,#000 40%,transparent 100%);mask-image:radial-gradient(closest-side,#000 40%,transparent 100%)}
.fx-emblem{position:relative;z-index:2;width:92%;overflow:hidden}
.fx-emblem img{width:100%;display:block;filter:drop-shadow(0 24px 40px rgba(0,0,0,.55))}
/* scan line sweeps the emblem, rests, then repeats (5s cycle) */
.fx-emblem::after{content:"";position:absolute;left:-5%;right:-5%;height:22%;top:-25%;
  background:linear-gradient(180deg,transparent,rgba(92,203,244,.0) 20%,rgba(92,203,244,.35) 50%,rgba(92,203,244,.0) 80%,transparent);
  mix-blend-mode:screen;animation:fx-scan 5s ease-in-out .4s infinite}
@keyframes fx-scan{0%{top:-25%;opacity:1}52%{top:105%;opacity:1}53%,100%{top:105%;opacity:0}}
@media (prefers-reduced-motion:reduce){.fx-emblem::after{display:none}}

/* ---------- Product sections ---------- */
.fx-section{padding:72px 0;border-top:1px solid var(--border);scroll-margin-top:12px}
.fx-split{display:grid;grid-template-columns:.9fr 1.1fr;gap:48px;align-items:start}
.fx-tag{display:inline-flex;align-items:center;gap:8px;font-size:.88rem;font-weight:600;color:var(--cyan-2);margin-bottom:14px}
.fx-section h2{font-family:var(--display);font-weight:700;font-size:clamp(1.8rem,3.2vw,2.5rem);line-height:1.1;color:var(--text);margin:0 0 16px;padding:0}
.fx-section .intro{color:var(--muted);font-size:1.03rem;line-height:1.7;margin:0 0 28px;max-width:32em}
.fx-features{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden}
.fx-feature{background:var(--surface);padding:24px 22px}
.fx-ico{width:38px;height:38px;border-radius:10px;display:grid;place-items:center;color:var(--cyan-2);background:rgba(41,169,225,.10);border:1px solid rgba(41,169,225,.28);margin-bottom:14px}
.fx-feature h4{font-family:'Inter',sans-serif;font-size:1rem;font-weight:700;color:var(--text);margin:0 0 6px;padding:0}
.fx-feature p{font-size:.92rem;line-height:1.6;color:var(--muted);margin:0}

/* call screen-pop mock */
.fx-pop{background:linear-gradient(180deg,var(--surface-2),var(--surface));border:1px solid var(--border-strong);border-radius:var(--radius);padding:18px;max-width:380px;box-shadow:0 24px 50px -28px rgba(0,0,0,.8)}
.fx-pop .row{display:flex;align-items:center;gap:12px}
.fx-pop .ring{width:42px;height:42px;border-radius:50%;display:grid;place-items:center;background:rgba(61,220,132,.14);color:var(--led);border:1px solid rgba(61,220,132,.4)}
.fx-pop .who{font-weight:700;color:var(--text);font-size:.98rem}
.fx-pop .num{color:var(--muted);font-size:.84rem;font-variant-numeric:tabular-nums}
.fx-pop .crm{margin-top:14px;padding:12px 14px;border-radius:12px;background:rgba(7,12,22,.6);border:1px solid var(--border);font-size:.85rem;color:var(--muted);line-height:1.55}
.fx-pop .crm strong{color:var(--text);font-weight:600}
.fx-pop .acts{display:flex;gap:8px;margin-top:14px}
.fx-pop .acts span{flex:1;text-align:center;padding:9px;border-radius:10px;font-size:.84rem;font-weight:600}
.fx-pop .acts .ok{background:var(--led);color:#05140C}
.fx-pop .acts .no{border:1px solid var(--border-strong);color:var(--muted)}

/* camera tile mock */
.fx-cam{position:relative;aspect-ratio:16/10;max-width:420px;border-radius:var(--radius);overflow:hidden;border:1px solid var(--border-strong);
  background:
    linear-gradient(180deg,rgba(0,0,0,0) 55%,rgba(0,0,0,.35)),
    linear-gradient(170deg,#18304A 0%,#0F2236 38%,#16283A 38.5%,#1B2F40 60%,#0D1A28 100%);
  box-shadow:0 24px 50px -28px rgba(0,0,0,.8)}
.fx-cam .bldg{position:absolute;left:8%;bottom:30%;width:34%;height:34%;background:#0B1826;border-top:3px solid #21405E}
.fx-cam .bldg::after{content:"";position:absolute;left:18%;top:28%;width:22%;height:24%;background:rgba(255,214,140,.35);box-shadow:44px 0 0 rgba(255,214,140,.18)}
.fx-cam .van{position:absolute;left:52%;bottom:17%;width:26%;height:17%;background:#C9D3DC;border-radius:6px 14px 4px 4px}
.fx-cam .van::before,.fx-cam .van::after{content:"";position:absolute;bottom:-7px;width:14px;height:14px;border-radius:50%;background:#0A121C;border:2px solid #39495A}
.fx-cam .van::before{left:12%}.fx-cam .van::after{right:12%}
.fx-cam .box{position:absolute;left:49%;bottom:12%;width:32%;height:29%;border:2px solid var(--led);border-radius:4px}
.fx-cam .box span{position:absolute;top:-24px;left:-2px;background:var(--led);color:#05140C;font-size:.7rem;font-weight:700;padding:3px 7px;border-radius:4px 4px 4px 0;white-space:nowrap}
.fx-cam .hud{position:absolute;top:10px;left:12px;right:12px;display:flex;justify-content:space-between;font-size:.72rem;font-weight:600;color:rgba(231,234,243,.85);font-variant-numeric:tabular-nums}
.fx-cam .rec{display:inline-flex;align-items:center;gap:6px}
.fx-cam .rec i{width:8px;height:8px;border-radius:50%;background:#F05252;box-shadow:0 0 8px #F05252}

/* ---------- Process ---------- */
.fx-steps{display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin-top:30px;counter-reset:s}
.fx-step{position:relative;padding:0 22px 0 0}
.fx-step .n{font-family:var(--display);font-weight:700;font-size:.95rem;color:var(--cyan-2);display:flex;align-items:center;gap:12px;margin-bottom:16px}
.fx-step .n::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,rgba(41,169,225,.5),rgba(41,169,225,.05))}
.fx-step:last-child .n::after{background:transparent}
.fx-step h4{font-size:1.05rem;font-weight:700;color:var(--text);margin:0 0 8px;padding:0}
.fx-step p{font-size:.93rem;line-height:1.6;color:var(--muted);margin:0}

/* ---------- Contact ---------- */
.fx-contact-head{padding:72px 0 26px;border-top:1px solid var(--border);scroll-margin-top:12px}
.fx-contact-head h2{font-family:var(--display);font-weight:700;font-size:clamp(1.8rem,3.2vw,2.5rem);color:var(--text);margin:0 0 10px;padding:0}
.fx-contact-head p{color:var(--muted);font-size:1.03rem;margin:0}
.fx-details{display:flex;flex-direction:column;gap:2px;background:var(--border);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;margin-bottom:16px}
.fx-detail{display:flex;gap:14px;align-items:flex-start;background:var(--surface);padding:16px 18px;text-decoration:none!important}
.fx-detail svg{color:var(--cyan);flex:none;margin-top:2px}
.fx-detail .l{font-size:.8rem;color:var(--faint);font-weight:500}
.fx-detail .v{color:var(--text);font-weight:600;font-size:.98rem;line-height:1.5}
a.fx-detail:hover .v{color:var(--cyan-2)}
.st-key-card-enquiry{background:linear-gradient(180deg,var(--surface-2),var(--surface));border:1px solid var(--border)!important;border-radius:var(--radius);padding:24px 24px 20px;box-shadow:0 24px 50px -30px rgba(0,0,0,.8)}
.fx-form-title{font-family:var(--display);font-weight:700;font-size:1.25rem;color:var(--text)}
.fx-form-sub{color:var(--muted);font-size:.9rem;margin:4px 0 10px}
[data-testid="stWidgetLabel"] p{font-size:.85rem!important;font-weight:600!important;color:var(--muted)!important}
[data-baseweb="input"],[data-baseweb="textarea"],[data-baseweb="select"]>div,[data-baseweb="select"]>div>div{background:var(--bg)!important;border:1px solid var(--border-strong)!important;border-radius:10px!important}
[data-baseweb="input"]:focus-within,[data-baseweb="textarea"]:focus-within{border-color:var(--cyan)!important;box-shadow:0 0 0 3px rgba(41,169,225,.18)!important}
[data-baseweb="input"]>div,[data-baseweb="base-input"]{background:transparent!important}
[data-testid="stBaseLinkButton-primary"],.stLinkButton a[kind="primary"]{background:var(--grad)!important;border:none!important;color:#04121F!important;border-radius:12px!important;font-weight:700!important;box-shadow:0 12px 28px -12px rgba(41,169,225,.9)}
[data-testid="stBaseLinkButton-primary"] p{color:#04121F!important;font-weight:700!important}
[data-testid="stBaseLinkButton-secondary"]{border-radius:12px!important;border:1px solid var(--border-strong)!important;background:transparent!important;color:var(--faint)!important}
.fx-map iframe,[data-testid="stIFrame"]{border-radius:var(--radius);border:1px solid var(--border)!important}

/* ---------- Footer ---------- */
.fx-foot{margin-top:72px;padding:28px 0 36px;border-top:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;color:var(--faint);font-size:.85rem}
.fx-foot .fx-brand img{height:28px}
.fx-foot .fx-word{font-size:.95rem}


/* ---------- Nav state ---------- */
.fx-nav a.on{color:var(--text)!important;background:var(--surface)}

/* ---------- Doorways (home) ---------- */
.fx-doors{display:grid;grid-template-columns:1fr 1fr;gap:22px;padding:8px 0 24px}
.fx-door{display:flex;flex-direction:column;background:linear-gradient(180deg,var(--surface-2),var(--surface));border:1px solid var(--border);border-radius:22px;overflow:hidden}
.fx-door .vis{position:relative;display:grid;place-items:center;padding:28px;height:310px;border-bottom:1px solid var(--border);
  background:radial-gradient(closest-side,rgba(41,169,225,.16),transparent 80%),var(--bg)}
.fx-door .vis::before{content:"";position:absolute;inset:0;
  background-image:linear-gradient(rgba(148,178,210,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(148,178,210,.06) 1px,transparent 1px);
  background-size:28px 28px;-webkit-mask-image:radial-gradient(closest-side,#000 30%,transparent 100%);mask-image:radial-gradient(closest-side,#000 30%,transparent 100%)}
.fx-door .vis>*{position:relative;width:100%}
.fx-door .txt{padding:28px 30px 30px;display:flex;flex-direction:column;flex:1}
.fx-door h2{font-family:var(--display);font-weight:700;font-size:1.8rem;line-height:1.1;color:var(--text);margin:0 0 12px;padding:0}
.fx-door p{color:var(--muted);font-size:1rem;line-height:1.65;margin:0 0 24px}
.fx-door .fx-btn{align-self:flex-start;margin-top:auto}
.fx-door .fx-pop,.fx-door .fx-cam{margin:0 auto;max-width:380px}

/* ---------- Sub-page hero ---------- */
.fx-phero{display:grid;grid-template-columns:1.1fr .9fr;gap:40px;align-items:center;padding:60px 0 56px}
.fx-phero h1{font-family:var(--display);font-weight:800;font-size:clamp(2.2rem,4.2vw,3.2rem);line-height:1.05;color:var(--text);margin:0 0 18px;padding:0}
.fx-phero .lede{font-size:1.08rem;line-height:1.65;color:var(--muted);max-width:32em;margin:0 0 28px}
.fx-phero .vis{display:grid;place-items:center}
.fx-phero .vis>*{width:100%}
.fx-features.three{grid-template-columns:repeat(3,1fr)}

/* ---------- Product cards ---------- */
.fx-cat{margin:56px 0 22px}
.fx-cat h3{font-family:var(--display);font-weight:700;font-size:1.45rem;color:var(--text);margin:0 0 6px;padding:0}
.fx-cat p{color:var(--muted);font-size:.97rem;margin:0}
.fx-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:18px}
.fx-card{display:flex;flex-direction:column;background:var(--surface);border:1px solid var(--border);border-radius:18px;overflow:hidden;transition:border-color .2s ease}
.fx-card:hover{border-color:rgba(41,169,225,.5)}
.fx-card .stage{position:relative;aspect-ratio:4/3;display:grid;place-items:center;overflow:hidden;
  background:radial-gradient(120% 95% at 50% 25%,#FFFFFF 0%,#F3F5FA 62%,#E2E8F1 100%)}
.fx-card .stage img{position:absolute;inset:0;margin:auto;max-width:84%;max-height:84%;width:auto;height:auto;object-fit:contain;filter:drop-shadow(0 10px 14px rgba(15,30,50,.16))}
.fx-card .stage .missing{color:#8C98B0;font-size:.85rem;text-align:center}
.fx-card .body{padding:18px 20px 20px;display:flex;flex-direction:column;flex:1}
.fx-card .brand{font-size:.8rem;font-weight:600;color:var(--cyan-2);margin-bottom:2px}
.fx-card h4{font-family:var(--display);font-weight:700;font-size:1.22rem;color:var(--text);margin:0 0 8px;padding:0}
.fx-card p{font-size:.9rem;line-height:1.55;color:var(--muted);margin:0 0 14px}
.fx-tags{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 16px}
.fx-tags span{font-size:.75rem;font-weight:600;color:var(--text);background:var(--surface-3);border:1px solid var(--border);border-radius:999px;padding:4px 10px}
.fx-card .ask{margin-top:auto;display:inline-flex;align-items:center;gap:8px;font-size:.88rem;font-weight:600;color:var(--cyan-2)!important;text-decoration:none!important}
.fx-card .ask:hover{color:var(--text)!important}

/* ---------- CTA band ---------- */
.fx-band{margin-top:72px;display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;padding:34px 36px;border-radius:22px;
  border:1px solid rgba(41,169,225,.3);background:radial-gradient(600px 200px at 100% 0%,rgba(41,169,225,.16),transparent 70%),var(--surface);scroll-margin-top:12px}
.fx-band h2{font-family:var(--display);font-weight:700;font-size:1.6rem;color:var(--text);margin:0 0 6px;padding:0}
.fx-band p{color:var(--muted);margin:0}

/* ---------- Responsive ---------- */
@media (max-width:900px){
  .fx-hero,.fx-phero{grid-template-columns:1fr;padding:44px 0 48px;gap:28px}
  .fx-stage{order:-1;max-width:440px;margin:0 auto;width:100%}
  .fx-split{grid-template-columns:1fr;gap:32px}
  .fx-doors{grid-template-columns:1fr}
  .fx-features.three{grid-template-columns:1fr 1fr}
  .fx-steps{grid-template-columns:1fr 1fr;gap:30px 0}
  .fx-nav a.hide-m{display:none}
}
@media (max-width:600px){
  .block-container{padding:0 18px!important}
  .fx-features,.fx-features.three{grid-template-columns:1fr}
  .fx-steps{grid-template-columns:1fr}
  .fx-step .n::after{display:none}
  .fx-section,.fx-contact-head{padding-top:52px}
  .fx-nav a.fx-call .t{display:none}
  .fx-nav a{padding:8px 9px;font-size:.86rem}
  .fx-brand .fx-word{display:none}
  .fx-door .vis{height:auto;padding:30px 18px}
  .fx-door .txt{padding:22px 20px 24px}
  .fx-band{padding:26px 22px}
  .fx-grid{grid-template-columns:1fr 1fr;gap:12px}
  .fx-card{border-radius:14px}
  .fx-card .body{padding:12px 12px 14px}
  .fx-card h4{font-size:1.02rem}
  .fx-card p{font-size:.8rem;margin-bottom:10px}
  .fx-tags span{font-size:.66rem;padding:3px 7px}
  .fx-card .ask{font-size:.8rem}
}
</style>
"""


def setup():
    """Inject the site styling. Call once at the top of every page."""
    st.markdown(CSS, unsafe_allow_html=True)


def brand_html():
    emblem = b64_file(find_asset("emblem.png", "logo.png"))
    return (f'<a class="fx-brand" href="/" target="_top" aria-label="{esc(COMPANY)} home">'
            f'<img src="data:image/png;base64,{emblem}" alt="">'
            f'<div class="fx-word"><b>FORTLOX</b> <span>SECURITY</span></div></a>')


def header(active="home"):
    def link(key, href, label, extra=""):
        cls = (" on" if key == active else "") + extra
        return f'<a class="{cls.strip()}" href="{href}" target="_top">{label}</a>'
    render_html(f"""
    <div id="top" class="fx-top">
      {brand_html()}
      <nav class="fx-nav" aria-label="Main">
        {link("home", "/", "Home", " hide-m")}
        {link("phones", "/phones", "Phones")}
        {link("cctv", "/cctv", "CCTV")}
        <a class="hide-m" href="#contact">Contact</a>
        <a class="fx-call" href="tel:{PHONE_LINK}" target="_top">{icon('phone', 16)}<span class="t">{PHONE_DISPLAY}</span></a>
      </nav>
    </div>
    """)


def product_grid(products, categories):
    """Render product cards grouped by category."""
    for cat, blurb in categories:
        items = [p for p in products if p.get("category") == cat]
        if not items:
            continue
        cards = []
        for p in items:
            full_name = f'{p.get("brand", "")} {p["name"]}'.strip()
            src = product_image(p.get("image", ""))
            stage = (f'<img src="{src}" alt="{esc(full_name)}" loading="lazy">' if src
                     else f'<div class="missing">Image not found:<br>{esc(p.get("image", ""))}</div>')
            tags = "".join(f"<span>{esc(t)}</span>" for t in p.get("tags", []))
            brand = f'<div class="brand">{esc(p["brand"])}</div>' if p.get("brand") else ""
            cards.append(
                f'<article class="fx-card"><div class="stage">{stage}</div><div class="body">'
                f'{brand}<h4>{esc(p["name"])}</h4><p>{esc(p.get("desc", ""))}</p>'
                f'<div class="fx-tags">{tags}</div>'
                f'<a class="ask" href="{esc(mailto("Enquiry: " + full_name))}" target="_top">{icon("mail", 16)}Ask about this</a>'
                f'</div></article>'
            )
        render_html(f'<div class="fx-cat"><h3>{esc(cat)}</h3><p>{esc(blurb)}</p></div>'
                    f'<div class="fx-grid">{"".join(cards)}</div>')


def contact_band(title, text, subject):
    render_html(f"""
    <section id="contact" class="fx-band">
      <div><h2>{esc(title)}</h2><p>{esc(text)}</p></div>
      <div class="fx-ctas">
        <a class="fx-btn primary" href="tel:{PHONE_LINK}" target="_top">{icon('phone', 18)}Call {PHONE_DISPLAY}</a>
        <a class="fx-btn ghost" href="{esc(mailto(subject))}" target="_top">{icon('mail', 18)}Email us</a>
      </div>
    </section>
    """)


def footer():
    render_html(f"""
    <div class="fx-foot">
      {brand_html()}
      <div>© {datetime.date.today().year} {esc(COMPANY)}, {esc(', '.join(ADDRESS_LINES))}</div>
    </div>
    """)
