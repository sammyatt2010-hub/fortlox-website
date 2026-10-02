"""
Fortlox Security - private telephony quotation tool  (page: /quote)
---------------------------------------------------------------------
Staff-only page. It is NOT linked from the public website and is locked
with a password set in Streamlit Secrets:

    QUOTE_PASSWORD       = "..."   # to open the quote tool
    QUOTE_ADMIN_PASSWORD = "..."   # to change prices in the Admin tab

Optional, so price changes survive app restarts (same as the Refyn-IT tool):
    GITHUB_TOKEN  = "..."          # fine-grained token with Contents: read/write on this repo
    GITHUB_REPO   = "user/fortlox-website"
"""

import base64
import hmac
import io
import json
import math
import os
import re as _re
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (HRFlowable, Image as RLImage, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from common import (ADDRESS_LINES, COMPANY, EMAIL, PHONE_DISPLAY, WEBSITE, b64_file, esc, find_asset,
                    header, product_image, render_html, setup)

# #####################################################################
#
#   FORTLOX PRICE BOOK - STARTING PRICES
#
#   These are only the starting values. Once the tool is live, change
#   prices in the "Admin · pricing" tab instead (no code needed).
#   Numbers only, no £ sign or commas.
#
# #####################################################################
DEFAULT_LICENCE_PER_USER_MONTH = 9.00     # hosted user licence, per user per month
DEFAULT_SETUP_PER_USER = 4.00             # user setup & provisioning, per user, one-off
DEFAULT_BASIC_BUILD = 75.00               # basic system build, flat fee
DEFAULT_ADV_1_TO_5 = 250.00               # advanced deployment, 1-5 users
DEFAULT_ADV_6_TO_10 = 500.00              # advanced deployment, 6-10 users
DEFAULT_ADV_PER_EXTRA_10 = 750.00         # advanced deployment, each further band of 10 users

# id, category, tag, name, description, image file (as in GitHub), starting price
HARDWARE = [
    ("v67", "Fanvil Phones", "Flagship Touch", "Fanvil V67",
     "7-inch touchscreen video phone with built-in camera, Wi-Fi and Bluetooth", "Fanvil_V67.webp", 189.00),
    ("v66pro", "Fanvil Phones", "Executive", "Fanvil V66 Pro",
     "7-inch rotating touchscreen with cordless Bluetooth handset and Wi-Fi 6", "V66_Pro.webp", 129.00),
    ("v62pro", "Fanvil Phones", "Standard Desk", "Fanvil V62 Pro",
     "Colour-screen desk phone with cordless Bluetooth handset", "Fanvil_V62_Pro.png", 89.00),
    ("t73w", "Yealink Phones", "Smart Business", "Yealink T73W",
     "2.8-inch colour desk phone with Wi-Fi 6 and Bluetooth", "Yealink_T73W.png", 78.00),
    ("t74w", "Yealink Phones", "Colour Executive", "Yealink T74W",
     "4.3-inch colour desk phone with Wi-Fi 6 and Bluetooth", "Yealink_T74W.png", 111.00),
    ("t85w", "Yealink Phones", "Executive", "Yealink T85W",
     "Adjustable 5.5-inch screen with AI noise cancellation", "Yealink_T85W.png", 115.00),
    ("t87w", "Yealink Phones", "Executive Touch", "Yealink T87W",
     "7-inch multi-touch screen for managers and reception", "Yealink_T87W.png", 155.00),
    ("t88w_pro", "Yealink Phones", "Flagship Touch Pro", "Yealink T88W Pro",
     "7-inch Android touchscreen with cordless Bluetooth handset", "Yealink_T88W_Pro.png", 225.00),
    ("w74p", "Cordless & Wi-Fi", "DECT Package", "Yealink W74P",
     "DECT cordless system: base station plus colour handset", "Yealink_W74P.png", 87.00),
    ("ax83h", "Cordless & Wi-Fi", "Wi-Fi Handset", "Yealink AX83H",
     "Pocket Wi-Fi handset, no base station needed", "Yealink_AX83H.png", 75.00),
    ("ax86r", "Cordless & Wi-Fi", "Rugged", "Yealink AX86R",
     "IP67 rugged Wi-Fi handset with push-to-talk and lone-worker alarms", "Yealink_AX86R.png", 113.00),
    ("w620w", "Cordless & Wi-Fi", "Rugged", "Linkvil W620W",
     "Drop-resistant Wi-Fi handset with push-to-talk, 13h talk time", "Linkvil_W620W_Rugged.png", 149.00),
    ("uh36_mono", "Headsets & Accessories", "Headset", "Yealink UH36 Mono Headset",
     "Single-ear wired headset, USB and 3.5mm", "Yealink_UH36_Mono_Headset_UC.png", 42.00),
    ("psu_10w", "Headsets & Accessories", "Power Supply", "Yealink 10W PSU",
     "UK mains adaptor for desks without PoE", "Yealink_10W_PSU.png", 11.00),
]

VAT_RATE = 0.20
CONTRACT_MONTHS = 36
QUOTE_VALID_DAYS = 30
QUOTE_PREFIX = "FLX"
# #####################################################################
#   END OF PRICE BOOK
# #####################################################################

VAT_PCT = f"{VAT_RATE * 100:g}%"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================
# STYLING (Fortlox colours, same layout as the Refyn-IT tool)
# ==========================================
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Saira:wght@600;700;800&display=swap');
:root{--bg:#070C16;--surface:#0E1726;--surface-2:#132036;--surface-3:#1A2A45;--border:rgba(148,178,210,.14);
--border-strong:rgba(148,178,210,.28);--text:#E7EAF3;--muted:#93A1B8;--faint:#5E6E88;--accent:#29A9E1;--accent-2:#5CCBF4;
--accent-soft:rgba(41,169,225,.14);--good:#3DDC84;--warn:#FBBF24;--bad:#F87171;--radius:14px;
--grad:linear-gradient(135deg,#5CCBF4 0%,#29A9E1 45%,#136AA8 100%)}
html,body,[class*="css"],.stApp,button,input,textarea,select,
.stApp [data-testid="stMarkdownContainer"] :is(p,div,span,a,li,strong,b,td,th,small){font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif!important}
.stApp [data-testid="stMarkdownContainer"] :is(.fx-word,.fx-word b,.fx-word span,.pe-title,.pe-login-head .t,.nl-prop .t){font-family:'Saira','Inter',sans-serif!important}
.stApp{background:radial-gradient(1200px 500px at 85% -10%,rgba(41,169,225,.09),transparent 60%),var(--bg)}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none!important}
footer{visibility:hidden}
.block-container{padding-bottom:3rem!important;max-width:1440px!important}
.pe-hero{margin-top:22px}
.pe-login-head{margin-top:5vh!important}
[data-testid="stWidgetLabel"] p{font-size:.76rem!important;font-weight:600!important;color:var(--muted)!important;text-transform:uppercase;letter-spacing:.06em}
[data-testid="stCaptionContainer"]{color:var(--muted)!important}
.st-key-card-users,.st-key-card-hardware,.st-key-card-details,.st-key-card-summary,.st-key-card-cv-head,.st-key-card-cv-monthly,
.st-key-card-cv-oneoff,.st-key-card-deploy,.st-key-card-admin,.st-key-card-admin-login,.st-key-card-login,.st-key-card-cv-setup,.st-key-card-admin-hw{
background:linear-gradient(180deg,rgba(19,32,54,.85) 0%,rgba(14,23,38,.85) 100%);border:1px solid var(--border)!important;border-radius:var(--radius);
padding:22px 22px 18px;box-shadow:0 1px 0 rgba(255,255,255,.03) inset,0 20px 40px -24px rgba(0,0,0,.6);margin-bottom:18px}
.st-key-card-summary{border-color:rgba(41,169,225,.4)!important}
[data-testid="stColumn"]:has(.st-key-card-summary){position:sticky;top:1rem;align-self:flex-start}
[data-baseweb="input"],[data-baseweb="select"]>div,[data-baseweb="textarea"]{background:var(--surface)!important;border:1px solid var(--border-strong)!important;border-radius:10px!important}
[data-baseweb="input"]:focus-within,[data-baseweb="select"]>div:focus-within,[data-baseweb="textarea"]:focus-within{border-color:var(--accent)!important;box-shadow:0 0 0 3px var(--accent-soft)!important}
[data-baseweb="input"]>div,[data-baseweb="base-input"]{background:transparent!important}
.stButton button,.stDownloadButton button,.stFormSubmitButton button{border-radius:10px!important;font-weight:600!important;border:1px solid var(--border-strong)!important;background:var(--surface-2)!important;color:var(--text)!important}
.stButton button:hover,.stDownloadButton button:hover{border-color:var(--accent)!important}
.stButton button[kind="primary"],.stDownloadButton button[kind="primary"],.stFormSubmitButton button,[data-testid="stBaseButton-primary"]{background:var(--grad)!important;border:none!important;color:#04121F!important;box-shadow:0 8px 24px -10px rgba(41,169,225,.85)}
.stButton button[kind="primary"] p,[data-testid="stBaseButton-primary"] p,.stFormSubmitButton button p{color:#04121F!important;font-weight:700!important}
[data-testid="stTabs"] [role="tablist"]{gap:4px;background:var(--surface);padding:4px;border-radius:12px;border:1px solid var(--border);width:fit-content;margin-bottom:6px}
[data-testid="stTabs"] [role="tab"]{border-radius:9px!important;padding:8px 16px!important;color:var(--muted)!important;background:transparent!important}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{background:var(--surface-3)!important;color:var(--text)!important}
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"],[data-testid="stTabs"] .react-aria-SelectionIndicator{display:none!important}
[data-testid="stExpander"] details{background:var(--surface);border:1px solid var(--border)!important;border-radius:12px!important}
[data-testid="stAlert"]{border-radius:12px!important}
[data-testid="stForm"]{border:none!important;padding:0!important;background:transparent!important}
.pe-hero{display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;padding:6px 2px 22px;margin-bottom:18px;border-bottom:1px solid var(--border)}
.fx-brandrow{display:flex;align-items:center;gap:12px;margin-bottom:14px}
.fx-brandrow img{height:40px}
.fx-word{font-family:'Saira','Inter',sans-serif;font-weight:800;font-size:1.25rem;letter-spacing:.04em}
.fx-word b{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.fx-word span{color:#B9C3CE;font-weight:700}
.pe-eyebrow{display:inline-flex;align-items:center;gap:8px;font-size:.78rem;font-weight:600;color:var(--muted);margin-bottom:8px}
.pe-eyebrow .dot{width:7px;height:7px;border-radius:50%;background:var(--good);box-shadow:0 0 0 4px rgba(61,220,132,.15)}
.pe-title{font-family:'Saira','Inter',sans-serif;font-size:2.1rem;font-weight:800;line-height:1.1;color:var(--text)}
.pe-sub{color:var(--muted);font-size:.95rem;margin-top:8px;max-width:620px}
.pe-stepper{display:flex;align-items:center;gap:6px;background:var(--surface);border:1px solid var(--border);border-radius:999px;padding:6px}
.pe-step{display:flex;align-items:center;gap:8px;padding:7px 14px 7px 7px;border-radius:999px;font-size:.82rem;font-weight:600;color:var(--faint);white-space:nowrap}
.pe-step .num{width:24px;height:24px;border-radius:50%;display:grid;place-items:center;font-size:.72rem;font-weight:700;border:1px solid var(--border-strong)}
.pe-step.done{color:var(--muted)}.pe-step.done .num{background:rgba(61,220,132,.14);border-color:rgba(61,220,132,.45);color:var(--good)}
.pe-step.active{background:var(--surface-3);color:var(--text)}.pe-step.active .num{background:var(--grad);border:none;color:#04121F}
.pe-step-sep{width:14px;height:1px;background:var(--border-strong)}
.pe-section{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.pe-section .badge{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;background:var(--accent-soft);color:var(--accent-2);font-weight:800;font-size:.85rem;border:1px solid rgba(41,169,225,.3)}
.pe-section .t{font-size:1.08rem;font-weight:700;color:var(--text)}.pe-section .s{font-size:.82rem;color:var(--muted);margin-top:2px}
.pe-chips{display:flex;flex-wrap:wrap;gap:6px}
.pe-chip{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;font-size:.76rem;font-weight:600;background:var(--surface-3);color:var(--text);border:1px solid var(--border);white-space:nowrap}
.pe-chip.accent{background:var(--accent-soft);color:#A9E3FA;border-color:rgba(41,169,225,.3)}
.pe-chip.good{background:rgba(61,220,132,.12);color:var(--good);border-color:rgba(61,220,132,.3)}
.pe-chip.warn{background:rgba(251,191,36,.12);color:var(--warn);border-color:rgba(251,191,36,.3)}
.pe-chip.muted{background:transparent;color:var(--muted)}
.pe-hint{display:flex;align-items:center;gap:10px;color:var(--muted);font-size:.86rem;background:var(--surface);border:1px dashed var(--border-strong);border-radius:12px;padding:12px 14px;margin-top:12px}
.pe-panel{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px;margin-bottom:10px}
.pe-panel .h{font-size:.7rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--faint);margin-bottom:10px}
.pe-login-head{text-align:center;margin:8vh 0 22px}
.pe-login-head img{height:70px;margin-bottom:14px}
.pe-login-head .t{font-family:'Saira','Inter',sans-serif;font-size:1.6rem;font-weight:800;color:var(--text)}
.pe-login-head .s{color:var(--muted);font-size:.92rem;margin-top:6px}
.nl-licence{border-radius:14px;padding:20px;background:linear-gradient(135deg,rgba(41,169,225,.16),rgba(92,203,244,.06));border:1px solid rgba(41,169,225,.35)}
.nl-licence .top{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
.nl-licence .name{font-size:1.15rem;font-weight:800;color:var(--text)}.nl-licence .sub{font-size:.82rem;color:var(--muted);margin-top:4px}
.nl-price{background:var(--grad);color:#04121F;font-weight:800;font-size:.9rem;padding:6px 12px;border-radius:999px;white-space:nowrap}
.nl-price small{font-weight:600;font-size:.72rem;opacity:.8}
.nl-feats{display:grid;grid-template-columns:1fr 1fr;gap:8px 16px;margin:16px 0 14px}
.nl-feat{display:flex;align-items:center;gap:9px;font-size:.86rem;color:var(--text)}
.nl-feat .ck{width:20px;height:20px;border-radius:6px;display:grid;place-items:center;flex-shrink:0;background:rgba(61,220,132,.14);color:var(--good);border:1px solid rgba(61,220,132,.35)}
.nl-activation{display:flex;align-items:center;gap:8px;font-size:.8rem;color:var(--muted);border-top:1px solid var(--border);padding-top:12px}
.nl-activation b{color:var(--text)}
.nl-mini{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}
.nl-mini>div{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:12px 14px}
.nl-mini .v{font-size:1.25rem;font-weight:800;color:var(--text)}.nl-mini .l{font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-weight:600}
.nl-mini .s{font-size:.75rem;color:var(--faint);margin-top:2px}
[class*="st-key-prod-"]{background:var(--surface);border:1px solid var(--border)!important;border-radius:14px;padding:14px 14px 12px;height:100%}
[class*="st-key-prod-"]:hover{border-color:rgba(41,169,225,.45)!important}
[class*="st-key-prod-on-"]{border-color:rgba(92,203,244,.6)!important;box-shadow:0 0 0 1px rgba(92,203,244,.25),0 16px 30px -20px rgba(92,203,244,.35)}
.nl-prod-top{display:flex;justify-content:space-between;align-items:center;gap:8px}
.nl-prod-price{font-weight:800;font-size:1.05rem;color:var(--text)}
.nl-stage{height:140px;margin:12px 0 10px;border-radius:12px;display:grid;place-items:center;overflow:hidden;position:relative;
background:radial-gradient(120% 90% at 50% 20%,#FFFFFF 0%,#F3F5FA 65%,#E2E8F1 100%)}
.nl-stage img{position:absolute;inset:0;margin:auto;max-height:84%;max-width:84%;object-fit:contain;filter:drop-shadow(0 8px 10px rgba(15,23,42,.18))}
.nl-prod-name{font-weight:700;font-size:.92rem;color:var(--text);line-height:1.25;min-height:2.4em}
.nl-prod-desc{font-size:.74rem;color:var(--muted);line-height:1.35;margin-top:4px;min-height:3.1em;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.nl-qty{text-align:center;font-weight:800;font-size:1.05rem;color:var(--text);background:var(--surface-2);border:1px solid var(--border-strong);border-radius:10px;padding:7px 0}
.nl-qty.on{border-color:rgba(92,203,244,.6);color:var(--accent-2)}
.nl-sub{text-align:center;font-size:.74rem;margin-top:8px;color:var(--faint)}.nl-sub.on{color:var(--accent-2);font-weight:600}
[class*="st-key-prod-"] .stButton button{padding:.3rem 0!important;min-height:38px;font-size:1.05rem!important}
.nl-sum-h{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.nl-sum-h .t{font-weight:800;font-size:1.05rem;color:var(--text)}
.nl-live{display:inline-flex;align-items:center;gap:6px;font-size:.72rem;font-weight:700;color:var(--good);text-transform:uppercase;letter-spacing:.08em}
.nl-live::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--good);box-shadow:0 0 0 4px rgba(61,220,132,.15)}
.nl-total{border-radius:12px;padding:12px 14px;margin-bottom:8px;background:var(--surface);border:1px solid var(--border)}
.nl-total .l{font-size:.7rem;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:.07em}
.nl-total .v{font-size:1.5rem;font-weight:800;color:var(--text);line-height:1.2;margin-top:2px}
.nl-total .v small{font-size:.78rem;font-weight:600;color:var(--muted)}
.nl-total .i{font-size:.78rem;color:var(--faint);margin-top:1px}
.nl-total.hero{background:linear-gradient(135deg,rgba(41,169,225,.18),rgba(92,203,244,.07));border-color:rgba(41,169,225,.4)}
.nl-total.hero .v{color:var(--accent-2)}
.nl-lines-h{font-size:.7rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--faint);margin:14px 0 6px}
.nl-line{display:flex;justify-content:space-between;gap:10px;font-size:.84rem;padding:7px 0;border-top:1px solid var(--border)}
.nl-line .n{color:var(--text)}.nl-line .n small{color:var(--faint);margin-left:4px}.nl-line .p{color:var(--text);font-weight:600;white-space:nowrap}
.nl-line.nb{border-top:none}
.nl-empty{font-size:.82rem;color:var(--faint);font-style:italic;padding:6px 0}
.nl-term{display:flex;gap:8px;align-items:flex-start;font-size:.75rem;color:var(--muted);margin-top:12px;background:rgba(251,191,36,.07);border:1px solid rgba(251,191,36,.25);border-radius:10px;padding:10px 12px;line-height:1.4}
.nl-term svg{color:var(--warn);flex-shrink:0;margin-top:1px}
[class*="st-key-sumline-"]{border-top:1px solid var(--border);gap:0!important}
[class*="st-key-sumline-"] .stButton button{padding:0!important;min-height:26px!important;height:26px;width:26px;font-size:.72rem!important;background:transparent!important;border:1px solid transparent!important;color:var(--faint)!important}
[class*="st-key-sumline-"] .stButton button:hover{border-color:rgba(248,113,113,.5)!important;color:var(--bad)!important}
[class*="st-key-sumline-"] .stButton{display:flex;justify-content:flex-end;padding-top:7px}
.nl-form-h{display:flex;align-items:center;gap:8px;font-weight:700;font-size:.92rem;color:var(--text);margin:4px 0 6px}
.nl-form-h svg{color:var(--accent-2)}
.nl-prop{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;flex-wrap:wrap}
.nl-prop .k{font-size:.8rem;font-weight:600;color:var(--accent-2)}
.nl-prop .t{font-family:'Saira','Inter',sans-serif;font-size:1.9rem;font-weight:800;color:var(--text);margin-top:6px;line-height:1.1}
.nl-prop .s{color:var(--muted);font-size:.92rem;margin-top:6px}
.nl-kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:20px}
@media (max-width:900px){.nl-kpis{grid-template-columns:1fr}.nl-feats{grid-template-columns:1fr}}
.nl-kpi{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:16px 18px;border-top:2px solid var(--c,var(--accent))}
.nl-kpi .l{font-size:.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.nl-kpi .v{font-size:1.8rem;font-weight:800;color:var(--text);margin-top:6px;line-height:1.1}
.nl-kpi .v small{font-size:.8rem;color:var(--muted);font-weight:600}.nl-kpi .i{font-size:.82rem;color:var(--faint);margin-top:4px}
.nl-table{width:100%;border-collapse:separate!important;border-spacing:0;font-size:.88rem;border:none!important;margin:0!important}
.nl-table th,.nl-table td{border-left:none!important;border-right:none!important;border-top:none!important}
.nl-table th{text-align:left;font-size:.7rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding:10px 12px;border-bottom:1px solid var(--border-strong);background:transparent!important}
.nl-table td{padding:12px;border-bottom:1px solid var(--border);color:var(--text);vertical-align:middle;background:transparent!important}
.nl-table td.num,.nl-table th.num{text-align:right;white-space:nowrap}
.nl-table .desc{color:var(--muted);font-size:.76rem;margin-top:2px}
.nl-table .thumb{width:44px;height:44px;border-radius:10px;background:#F1F2F4;display:grid;place-items:center;overflow:hidden}
.nl-table .thumb img{max-width:38px;max-height:38px;object-fit:contain}
.nl-table tr.sub td{border-bottom:none;padding-top:8px;padding-bottom:4px;color:var(--muted)}
.nl-table tr.grand td{border-top:1px solid var(--border-strong);font-weight:800;font-size:1rem;padding-top:12px}
.nl-table tr.grand td.num{color:var(--accent-2)}
.nl-note{margin-top:14px;font-size:.82rem;color:var(--muted);border:1px dashed var(--border-strong);border-radius:12px;padding:12px 14px}
[class*="st-key-dep-"]{background:var(--surface);border:1px solid var(--border)!important;border-radius:14px;padding:16px 16px 14px;height:100%}
[class*="st-key-dep-on-"]{border-color:rgba(41,169,225,.7)!important;background:linear-gradient(135deg,rgba(41,169,225,.14),rgba(92,203,244,.05))!important}
.rit-dep-top{display:flex;justify-content:space-between;align-items:flex-start;gap:10px}
.rit-dep-name{font-weight:800;font-size:1rem;color:var(--text)}.rit-dep-price{font-weight:800;font-size:1.15rem;color:var(--text);white-space:nowrap}
[class*="st-key-dep-on-"] .rit-dep-price{color:var(--accent-2)}
.rit-dep-desc{font-size:.8rem;color:var(--muted);margin-top:6px;line-height:1.4;min-height:2.3em}
[class*="st-key-dep-on-"] .stButton button:disabled{background:var(--grad)!important;color:#04121F!important;opacity:1!important;border:none!important}
[class*="st-key-dep-on-"] .stButton button:disabled p{color:#04121F!important;font-weight:700!important}
.rit-admin-h{font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--accent-2);margin:14px 0 6px;padding-top:12px;border-top:1px solid var(--border)}
.rit-admin-note{font-size:.84rem;color:var(--muted);margin-bottom:8px}
.rit-admin-bar{display:flex;align-items:center;gap:8px;font-size:.8rem;color:var(--muted);padding:9px 0}
.rit-admin-bar svg{color:var(--accent)}
.st-key-card-admin-login{margin-top:6vh}
.st-key-card-deploy [data-testid="stExpander"]{margin-top:16px}
.st-key-card-deploy [data-testid="stExpander"] summary p{color:var(--text)!important;font-weight:700!important}
.rit-bs-intro{font-size:.82rem;color:var(--muted);margin-bottom:6px;line-height:1.45}
.rit-bs-read{display:flex;align-items:flex-start;gap:8px;font-size:.84rem;color:var(--text);background:var(--surface-2);border:1px solid var(--border);border-radius:10px;padding:9px 12px;margin:2px 0 12px}
.rit-bs-read svg{color:var(--good);flex-shrink:0;margin-top:2px}
.rit-bs-status{margin:14px 0 10px;padding-top:12px;border-top:1px solid var(--border)}
.rit-bs-status .h{font-size:.72rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--accent-2);margin-bottom:8px}
.rit-cv-setup{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
@media (max-width:900px){.rit-cv-setup{grid-template-columns:1fr}}
.rit-cv-setup .big{font-size:1.05rem;font-weight:800;color:var(--text)}.rit-cv-setup .sm{font-size:.8rem;color:var(--muted);margin-top:4px;line-height:1.45}
.rit-cv-opt{display:flex;align-items:center;gap:12px;padding:8px 0;border-top:1px solid var(--border);font-size:.86rem}
.rit-cv-opt .key{width:28px;height:28px;border-radius:8px;display:grid;place-items:center;font-weight:800;background:var(--grad);color:#04121F;flex-shrink:0}
.rit-cv-opt .o{font-weight:700;color:var(--text);min-width:110px}.rit-cv-opt .w{color:var(--muted)}
</style>
"""

_ICON_PATHS = {
    "phone": '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "lock": '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "zap": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "building": '<path d="M3 21h18"/><path d="M5 21V7l8-4v18"/><path d="M19 21V11l-6-4"/><path d="M9 9v.01M9 12v.01M9 15v.01M9 18v.01"/>',
    "user": '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "truck": '<rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>',
    "alert": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>',
}


def icon(name, size=16, stroke=2):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
            f' stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">{_ICON_PATHS[name]}</svg>')


def chip(text, tone=""):
    return f'<span class="pe-chip {tone}">{esc(text)}</span>'


def section_header(num, title, subtitle=""):
    render_html(f'<div class="pe-section"><div class="badge">{num}</div><div><div class="t">{esc(title)}</div>'
                + (f'<div class="s">{esc(subtitle)}</div>' if subtitle else "") + "</div></div>")


FULL_WIDTH = {"width": "stretch"}


def money(v):
    return f"£{v:,.2f}"


EMBLEM_URI = "data:image/png;base64," + b64_file(find_asset("emblem.png", "logo.png"))
PDF_LOGO = find_asset("fortlox_logo_pdf.png", "logo.png")


def brand_row():
    return (f'<div class="fx-brandrow"><img src="{EMBLEM_URI}" alt="">'
            f'<div class="fx-word"><b>FORTLOX</b> <span>SECURITY</span></div></div>')


def _secret(key, default=""):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


# ==========================================
# PASSWORD GATE (fails closed)
# ==========================================
setup()                     # site styling + top menu, so the quote page matches the website
st.markdown(CSS, unsafe_allow_html=True)
header("quote")


def check_password():
    if st.session_state.get("fx_quote_ok"):
        return True
    pw = _secret("QUOTE_PASSWORD")
    _, mid, _ = st.columns([1, 1.25, 1])
    with mid:
        render_html(f'<div class="pe-login-head"><img src="{EMBLEM_URI}" alt="">'
                    '<div class="t">Fortlox quotation portal</div>'
                    '<div class="s">Fortlox staff only. Enter your access password to continue.</div></div>')
        if not pw:
            st.error("QUOTE_PASSWORD isn't set in Streamlit Secrets, so the quote tool is locked. "
                     "Add it under App settings → Secrets.")
            return False
        with st.container(key="card-login"):
            with st.form("fx_login", border=False):
                attempt = st.text_input("Access password", type="password")
                go = st.form_submit_button("Unlock", type="primary", **FULL_WIDTH)
            if go:
                if hmac.compare_digest(attempt.encode(), str(pw).encode()):
                    st.session_state.fx_quote_ok = True
                    st.rerun()
                else:
                    st.error("Incorrect password. Please try again.")
    return False


if not check_password():
    st.stop()

# ==========================================
# SETTINGS (prices, editable in Admin)
# ==========================================
SETTINGS_NAME = "fortlox_pricing.json"
SETTINGS_FILE = os.path.join(BASE_DIR, SETTINGS_NAME)
QUOTES_FILE = os.path.join(BASE_DIR, "fortlox_quotes.csv")

DEFAULT_SETTINGS = {
    "licence_monthly": DEFAULT_LICENCE_PER_USER_MONTH,
    "setup_per_user": DEFAULT_SETUP_PER_USER,
    "basic_deployment": DEFAULT_BASIC_BUILD,
    "adv_1_5": DEFAULT_ADV_1_TO_5,
    "adv_6_10": DEFAULT_ADV_6_TO_10,
    "adv_extra_10": DEFAULT_ADV_PER_EXTRA_10,
    "default_deployment": "basic",
    "hardware": {h[0]: h[6] for h in HARDWARE},
    "company_name": COMPANY,
    "company_email": EMAIL,
    "company_phone": PHONE_DISPLAY,
    "updated": "",
}


def sanitise_settings(raw):
    s = {**DEFAULT_SETTINGS, **(raw or {})}
    for k in ("licence_monthly", "setup_per_user", "basic_deployment", "adv_1_5", "adv_6_10", "adv_extra_10"):
        try:
            s[k] = round(max(0.0, float(s[k])), 2)
        except (TypeError, ValueError):
            s[k] = DEFAULT_SETTINGS[k]
    hw = dict(DEFAULT_SETTINGS["hardware"])
    for pid, price in (s.get("hardware") or {}).items():
        try:
            hw[pid] = round(max(0.0, float(price)), 2)
        except (TypeError, ValueError):
            pass
    s["hardware"] = hw
    if s.get("default_deployment") not in ("basic", "advanced"):
        s["default_deployment"] = "basic"
    for k in ("company_name", "company_email", "company_phone", "updated"):
        s[k] = str(s.get(k) or "")
    return {k: s[k] for k in DEFAULT_SETTINGS}


def _gh_config():
    token, repo = _secret("GITHUB_TOKEN"), _secret("GITHUB_REPO")
    if token and repo:
        return {"token": token, "repo": repo, "branch": _secret("GITHUB_BRANCH", "main"), "path": SETTINGS_NAME}
    return None


def _gh_read(cfg):
    url = f"https://api.github.com/repos/{cfg['repo']}/contents/{cfg['path']}"
    r = requests.get(url, headers={"Authorization": f"Bearer {cfg['token']}", "Accept": "application/vnd.github+json"},
                     params={"ref": cfg["branch"]}, timeout=10)
    if r.status_code == 404:
        return None, None
    r.raise_for_status()
    body = r.json()
    return json.loads(base64.b64decode(body["content"]).decode()), body["sha"]


@st.cache_data(ttl=300, show_spinner=False)
def load_settings():
    cfg = _gh_config()
    if cfg:
        try:
            data, _ = _gh_read(cfg)
            if data:
                return sanitise_settings(data)
        except Exception:
            pass
    if os.path.isfile(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f:
                return sanitise_settings(json.load(f))
        except (json.JSONDecodeError, OSError):
            pass
    return sanitise_settings({})


def save_settings(new):
    clean = sanitise_settings({**new, "updated": datetime.now().strftime("%d %b %Y, %H:%M")})
    payload = json.dumps(clean, indent=2)
    try:
        with open(SETTINGS_FILE, "w") as f:
            f.write(payload)
    except OSError:
        pass
    cfg = _gh_config()
    if cfg:
        try:
            _, sha = _gh_read(cfg)
            body = {"message": "Update Fortlox quote pricing", "branch": cfg["branch"],
                    "content": base64.b64encode(payload.encode()).decode()}
            if sha:
                body["sha"] = sha
            r = requests.put(f"https://api.github.com/repos/{cfg['repo']}/contents/{cfg['path']}",
                             headers={"Authorization": f"Bearer {cfg['token']}", "Accept": "application/vnd.github+json"},
                             json=body, timeout=15)
            r.raise_for_status()
            load_settings.clear()
            return True, "Saved permanently."
        except Exception as exc:
            load_settings.clear()
            return False, f"Saved for now, but couldn't write to GitHub ({exc}). Prices may reset when the app restarts."
    load_settings.clear()
    return True, "Saved. Without GitHub storage set up, prices go back to the starting values if the app restarts."


SETTINGS = load_settings()
LICENCE_MONTHLY_RATE = SETTINGS["licence_monthly"]
SETUP_FEE_PER_USER = SETTINGS["setup_per_user"]
BASIC_DEPLOYMENT_FEE = SETTINGS["basic_deployment"]

PRODUCTS = [{"id": h[0], "category": h[1], "tag": h[2], "name": h[3], "desc": h[4], "image": h[5],
             "price": SETTINGS["hardware"].get(h[0], h[6])} for h in HARDWARE]

DEPLOY_BASIC, DEPLOY_ADVANCED = "basic", "advanced"
DEPLOYMENT_LABELS = {DEPLOY_BASIC: "Basic system build", DEPLOY_ADVANCED: "Advanced system deployment"}
DEPLOYMENT_DESCS = {
    DEPLOY_BASIC: "Device activation & remote configuration · customer self-installation",
    DEPLOY_ADVANCED: "Fully managed deployment · system design, build, installation & go-live support",
}


def advanced_deployment_price(users):
    users = int(users or 0)
    if users <= 0:
        return 0.0
    if users <= 5:
        return SETTINGS["adv_1_5"]
    if users <= 10:
        return SETTINGS["adv_6_10"]
    return SETTINGS["adv_extra_10"] * math.ceil((users - 10) / 10)


def advanced_band_label(users):
    if users <= 5:
        return "1–5 users"
    if users <= 10:
        return "6–10 users"
    top = 10 + 10 * math.ceil((users - 10) / 10)
    return f"{top - 9}–{top} users"


# ==========================================
# SESSION STATE & QUOTE MATHS
# ==========================================
ss = st.session_state
ss.setdefault("fx_deployment", SETTINGS["default_deployment"])
ss.setdefault("fx_basket", {})
ss.setdefault("fx_users", 0)


def update_qty(pid, delta):
    new = max(0, ss.fx_basket.get(pid, 0) + delta)
    if new:
        ss.fx_basket[pid] = new
    else:
        ss.fx_basket.pop(pid, None)


def remove_from_basket(pid):
    ss.fx_basket.pop(pid, None)


def basket_items():
    out = []
    for pid, qty in ss.fx_basket.items():
        p = next((x for x in PRODUCTS if x["id"] == pid), None)
        if p and qty > 0:
            out.append({**p, "qty": qty, "line_total": p["price"] * qty})
    return out


def total_hardware():
    return sum(i["line_total"] for i in basket_items())


def total_monthly():
    return ss.fx_users * LICENCE_MONTHLY_RATE if ss.fx_users > 0 else 0.0


def total_setup(users=None):
    users = ss.fx_users if users is None else users
    return users * SETUP_FEE_PER_USER if users > 0 else 0.0


def deployment_fee(option=None, users=None):
    users = ss.fx_users if users is None else users
    option = option or ss.fx_deployment
    if users <= 0:
        return 0.0
    return advanced_deployment_price(users) if option == DEPLOY_ADVANCED else BASIC_DEPLOYMENT_FEE


def total_one_off():
    return total_setup() + deployment_fee() + total_hardware()


def quote_signature():
    return (ss.fx_users, ss.fx_deployment, LICENCE_MONTHLY_RATE, SETUP_FEE_PER_USER, BASIC_DEPLOYMENT_FEE,
            tuple(sorted(ss.fx_basket.items())), tuple(sorted(SETTINGS["hardware"].items())))


# ==========================================
# PDF QUOTATION (A4)
# ==========================================
C_PRIMARY = colors.HexColor("#1B8CC8")
C_HEAD = colors.HexColor("#0E1726")


def _pdf_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#8A9099"))
    canvas.drawString(27, 18, f"{COMPANY} · {', '.join(ADDRESS_LINES)} · {PHONE_DISPLAY} · {EMAIL}")
    canvas.drawRightString(A4[0] - 27, 18, f"Page {doc.page}")
    canvas.setStrokeColor(C_PRIMARY)
    canvas.setLineWidth(2)
    canvas.line(27, 28, 60, 28)
    canvas.restoreState()


def _pdf_header(story, title, meta_html, styles):
    left = []
    if PDF_LOGO:
        iw, ih = ImageReader(PDF_LOGO).getSize()
        w = 105
        left += [RLImage(PDF_LOGO, width=w, height=w * ih / iw, hAlign="LEFT"), Spacer(1, 6)]
    left.append(Paragraph(title, ParagraphStyle("T", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=15,
                                                leading=19, textColor=colors.HexColor("#0F172A"))))
    left.append(Paragraph(f"{COMPANY} · {WEBSITE}", ParagraphStyle("S", parent=styles["Normal"], fontSize=8, leading=11,
                                                                  textColor=colors.HexColor("#475569"))))
    hdr = Table([[left, Paragraph(meta_html, ParagraphStyle("M", parent=styles["Normal"], fontSize=8.5, leading=12,
                                                             textColor=colors.HexColor("#475569"), alignment=2))]],
                colWidths=[350, 190])
    hdr.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM"), ("LEFTPADDING", (0, 0), (0, 0), 0)]))
    story += [hdr, Spacer(1, 8), HRFlowable(width="100%", thickness=1.5, color=C_PRIMARY, spaceAfter=10)]


def generate_quotation_pdf(meta, seller, customer, num_users, hw_items, deployment_option):
    seller = {k: esc(v) for k, v in seller.items()}
    customer = {k: esc(v) for k, v in customer.items()}
    hw_items = [{**i, "name": esc(i["name"]), "desc": esc(i["desc"])} for i in hw_items]
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=27, leftMargin=27, topMargin=28, bottomMargin=40,
                            title=f"{COMPANY} quotation {meta['ref']}", author=COMPANY)
    styles = getSampleStyleSheet()
    c_dark, c_bg, c_border = colors.HexColor("#0F172A"), colors.HexColor("#F5F8FB"), colors.HexColor("#D4DCE5")
    sec = ParagraphStyle("H", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10.5, leading=14, textColor=C_PRIMARY)
    th = ParagraphStyle("TH", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.white)
    td = ParagraphStyle("TD", parent=styles["Normal"], fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=c_dark)
    tdb = ParagraphStyle("TDB", parent=td, fontName="Helvetica-Bold")

    story = []
    _pdf_header(story, "Telecoms Quotation",
                f"<b>Reference:</b> {meta['ref']}<br/><b>Date:</b> {meta['date']}<br/>"
                f"<b>Contract Term:</b> <b>{CONTRACT_MONTHS} Months Minimum</b><br/><b>Valid for:</b> {QUOTE_VALID_DAYS} days",
                styles)

    addr = f"Site/Delivery: {customer['delivery']}<br/>" if customer["delivery"] and customer["delivery"] != "N/A" else ""
    parties = Table([
        [Paragraph("<b>YOUR FORTLOX CONTACT</b>", tdb), Paragraph("<b>PROPOSED CUSTOMER</b>", tdb)],
        [Paragraph(f"<b>{seller['company']}</b><br/>Account Manager: {seller['name']}<br/>Email: {seller['email']}<br/>"
                   f"Telephone: {seller['phone']}", td),
         Paragraph(f"<b>{customer['company']}</b><br/>Contact Name: {customer['name']}<br/>Email: {customer['email']}<br/>"
                   f"Telephone: {customer['phone']}<br/>{addr}", td)],
    ], colWidths=[270, 270])
    parties.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), c_bg), ("BOX", (0, 0), (-1, -1), 1, c_border),
                                 ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border), ("TOPPADDING", (0, 0), (-1, -1), 5),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
    story += [parties, Spacer(1, 10)]

    def table(rows):
        t = Table(rows, colWidths=[290, 50, 100, 100])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), C_HEAD), ("BOX", (0, 0), (-1, -1), 1, c_border),
                               ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border), ("BACKGROUND", (0, -3), (-1, -3), c_bg),
                               ("BACKGROUND", (0, -1), (-1, -1), c_bg), ("TOPPADDING", (0, 0), (-1, -1), 4.5),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5)]))
        return t

    mrc = num_users * LICENCE_MONTHLY_RATE if num_users > 0 else 0.0
    story += [Paragraph("1. Ongoing Monthly Costs", sec), Spacer(1, 4), table([
        [Paragraph(x, th) for x in ("Description", "Users", "Unit Price (Ex VAT)", "Monthly Total (Ex VAT)")],
        [Paragraph("<b>Hosted VoIP Cloud User Licence</b><br/><font color='#64748B' size=7>Includes PC/Mac softphone, "
                   "iOS/Android mobile apps, cloud call recording, auto-attendant &amp; inclusive UK landline/mobile calls."
                   "</font>", td),
         Paragraph(str(num_users), td), Paragraph(f"£{LICENCE_MONTHLY_RATE:,.2f} / mo", td), Paragraph(f"£{mrc:,.2f} / mo", tdb)],
        [Paragraph("<b>Total Ongoing Monthly Costs (Ex VAT)</b>", tdb), "", "", Paragraph(f"<b>£{mrc:,.2f} / mo</b>", tdb)],
        [Paragraph(f"VAT @ {VAT_PCT}", td), "", "", Paragraph(f"£{mrc * VAT_RATE:,.2f} / mo", td)],
        [Paragraph("<b>Total Ongoing Monthly Costs (Inc VAT)</b>", tdb), "", "",
         Paragraph(f"<b>£{mrc * (1 + VAT_RATE):,.2f} / mo</b>", tdb)],
    ]), Spacer(1, 10)]

    setup_t = num_users * SETUP_FEE_PER_USER if num_users > 0 else 0.0
    dep_t = deployment_fee(deployment_option, num_users)
    one_off = setup_t + dep_t + sum(i["line_total"] for i in hw_items)
    rows = [[Paragraph(x, th) for x in ("Item / Description", "Qty", "Unit Price (Ex VAT)", "Line Total (Ex VAT)")]]
    if num_users > 0:
        rows.append([Paragraph("<b>User Setup &amp; Provisioning</b><br/><font color='#64748B' size=7>Extension setup, "
                               "user provisioning &amp; licence activation.</font>", td),
                     Paragraph(str(num_users), td), Paragraph(f"£{SETUP_FEE_PER_USER:,.2f}", td),
                     Paragraph(f"£{setup_t:,.2f}", tdb)])
        rows.append([Paragraph(f"<b>{DEPLOYMENT_LABELS[deployment_option]}</b><br/><font color='#64748B' size=7>"
                               f"{esc(DEPLOYMENT_DESCS[deployment_option])}.</font>", td),
                     Paragraph("1", td), Paragraph(f"£{dep_t:,.2f}", td), Paragraph(f"£{dep_t:,.2f}", tdb)])
    for i in hw_items:
        rows.append([Paragraph(f"<b>{i['name']}</b><br/><font color='#64748B' size=7>{i['desc']}</font>", td),
                     Paragraph(str(i["qty"]), td), Paragraph(f"£{i['price']:,.2f}", td), Paragraph(f"£{i['line_total']:,.2f}", tdb)])
    rows += [[Paragraph("<b>Total One-Off Upfront Costs (Ex VAT)</b>", tdb), "", "", Paragraph(f"<b>£{one_off:,.2f}</b>", tdb)],
             [Paragraph(f"VAT @ {VAT_PCT}", td), "", "", Paragraph(f"£{one_off * VAT_RATE:,.2f}", td)],
             [Paragraph("<b>Total One-Off Upfront Costs (Inc VAT)</b>", tdb), "", "",
              Paragraph(f"<b>£{one_off * (1 + VAT_RATE):,.2f}</b>", tdb)]]
    story += [Paragraph("2. One-Off Upfront Costs", sec), Spacer(1, 4), table(rows), Spacer(1, 10)]

    m1 = mrc + one_off
    summ = Table([[Paragraph("<b>FINANCIAL SUMMARY</b>", tdb), Paragraph(
        f"<b>Ongoing Monthly Costs:</b> £{mrc:,.2f} Ex VAT (£{mrc * (1 + VAT_RATE):,.2f} Inc VAT / mo)<br/>"
        f"<b>Total One-Off Upfront Costs:</b> £{one_off:,.2f} Ex VAT (£{one_off * (1 + VAT_RATE):,.2f} Inc VAT)<br/>"
        f"<b>Total Month 1 Investment:</b> <b>£{m1:,.2f} Ex VAT (£{m1 * (1 + VAT_RATE):,.2f} Inc VAT)</b>", td)]],
        colWidths=[180, 360])
    summ.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), c_bg), ("BOX", (0, 0), (-1, -1), 1.5, C_PRIMARY),
                              ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                              ("LEFTPADDING", (0, 0), (-1, -1), 10)]))
    story += [summ, Spacer(1, 10)]

    clause = Table([[Paragraph(
        "<b>IMPORTANT CONTRACTUAL COMMITMENT &amp; TERMINATION TERMS:</b><br/>"
        f"All hosted user licences quoted herein are subject to a <b>minimum {CONTRACT_MONTHS}-month agreement term</b>. "
        f"In the event of early termination or cancellation of services before the end of the initial {CONTRACT_MONTHS}-month term, "
        "<b>early termination charges will apply and are payable in full</b> for all outstanding monthly licence fees "
        "for the remainder of the agreement.<br/>"
        f"<b>Commercial Notes:</b> Quotation valid for {QUOTE_VALID_DAYS} calendar days.",
        ParagraphStyle("C", parent=styles["Normal"], fontSize=7.8, leading=11, textColor=colors.HexColor("#0B4566")))]],
        colWidths=[540])
    clause.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF7FC")),
                                ("BOX", (0, 0), (-1, -1), 1.2, C_PRIMARY), ("TOPPADDING", (0, 0), (-1, -1), 6),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
    story += [clause, Spacer(1, 10)]

    sign = Table([[Paragraph("<b>CUSTOMER ACCEPTANCE &amp; AUTHORISATION:</b>", tdb), Paragraph("<b>DATE:</b> ___________________", td)],
                  [Paragraph("Authorised Signature: ______________________________", td), Paragraph("Print Name: ____________________", td)]],
                 colWidths=[330, 210])
    sign.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, c_border), ("BACKGROUND", (0, 0), (-1, -1), c_bg),
                              ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                              ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
    story.append(sign)
    doc.build(story, onFirstPage=_pdf_footer, onLaterPages=_pdf_footer)
    return buf.getvalue()


# ==========================================
# SYSTEM SETUP ("BUILD SHEET")
# ==========================================
BS_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
BS_TIMES = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 15, 30, 45)] + ["23:59"]
BS_HOURS_PRESETS = {
    "Mon–Fri 09:00–17:00": (5, "09:00", "17:00"), "Mon–Fri 08:30–17:30": (5, "08:30", "17:30"),
    "Mon–Fri 08:00–18:00": (5, "08:00", "18:00"), "Mon–Sat 09:00–17:00": (6, "09:00", "17:00"),
    "Open 24/7": (7, "00:00", "23:59"), "Custom hours": None,
}
BS_OOH_ACTIONS = ["Closed message, then voicemail", "Closed message, then hang up",
                  "Divert to a mobile / other number", "Ring as normal (no out-of-hours)"]
BS_AUDIO = ["Text-to-speech from the scripts below", "Customer will supply audio files", "Professional voiceover (quote separately)"]
BS_RING_STYLES = ["All at once", "In order (hunt)", "Longest idle first", "Round robin"]
BS_NO_ANSWER = ["Voicemail", "Overflow to another group", "Overflow to a mobile / number", "Keep queuing", "Back to main menu"]
BS_NO_INPUT = ["Repeat menu once, then go to option 1", "Repeat menu once, then voicemail", "Go straight to option 1", "Hang up"]
BS_NUMBERS = ["Port existing number(s)", "New number(s)", "Port existing + add new"]
BS_CLI = ["Company main number", "Each user's direct dial", "Withheld"]
BS_KEYS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
BS_SOFTPHONE = "Softphone / app only"
_EMAIL_RE = _re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _bs_init():
    defaults = {
        "bs_hours_preset": "Mon–Fri 09:00–17:00", "bs_bank_hols": True, "bs_ooh_action": BS_OOH_ACTIONS[0],
        "bs_ooh_divert": "", "bs_closed_text": ("Thank you for calling. Our office is currently closed. Please leave a message "
                                               "after the tone and we'll call you back on the next working day."),
        "bs_welcome_on": True, "bs_welcome_text": "Thank you for calling [Company name].",
        "bs_gdpr_on": True, "bs_gdpr_text": ("Please note that calls may be recorded for training and quality purposes. "
                                             "To find out how we use your personal data, please see the privacy notice on our website."),
        "bs_audio": BS_AUDIO[0], "bs_ivr_on": True, "bs_no_input": BS_NO_INPUT[0], "bs_vm_email": "",
        "bs_numbers": BS_NUMBERS[0], "bs_main_number": "", "bs_provider": "", "bs_port_postcode": "",
        "bs_cli": BS_CLI[0], "bs_notes": "", "bs_users_ver": 0,
    }
    for k, v in defaults.items():
        ss.setdefault(k, v)
    if "bs_hours_base" not in ss:
        ss.bs_hours_base = pd.DataFrame([{"Day": d, "Open": i < 5, "From": "09:00", "To": "17:00"} for i, d in enumerate(BS_DAYS)])
    if "bs_flow_base" not in ss:
        ss.bs_flow_base = pd.DataFrame([
            {"Key": "1", "Option": "Sales", "Who rings": "", "Ring style": "All at once", "Ring (secs)": 20,
             "If no answer": "Voicemail", "Then / voicemail email": ""},
            {"Key": "2", "Option": "Accounts", "Who rings": "", "Ring style": "All at once", "Ring (secs)": 20,
             "If no answer": "Voicemail", "Then / voicemail email": ""}])
    if "bs_direct_base" not in ss:
        ss.bs_direct_base = pd.DataFrame([{"Who rings": "", "Ring style": "All at once", "Ring (secs)": 20,
                                           "If no answer": "Voicemail", "Then / voicemail email": ""}])


def _bs_user_rows(n, existing):
    rows = (existing.to_dict("records") if existing is not None else [])[:n]
    for i in range(len(rows), n):
        rows.append({"First name": "", "Last name": "", "Email": "", "Extension": str(201 + i), "Device": BS_SOFTPHONE,
                     "Mobile app": True, "Voicemail to email": True, "Direct dial (DDI)": ""})
    return pd.DataFrame(rows, columns=["First name", "Last name", "Email", "Extension", "Device", "Mobile app",
                                       "Voicemail to email", "Direct dial (DDI)"])


def _clean_df(df):
    if df is None:
        return []
    return [{k: ("" if (v is None or (isinstance(v, float) and math.isnan(v))) else v) for k, v in r.items()}
            for r in df.to_dict("records")]


def bs_hours_rows():
    preset = BS_HOURS_PRESETS.get(ss.get("bs_hours_preset"))
    if preset:
        n, a, b = preset
        return [{"Day": d, "Open": i < n, "From": a, "To": b} for i, d in enumerate(BS_DAYS)]
    return _clean_df(ss.get("bs_hours_latest", ss.get("bs_hours_base")))


def bs_hours_summary(rows):
    open_rows = [r for r in rows if r.get("Open")]
    if not open_rows:
        return "Closed all week"
    if len(open_rows) == 7 and all(r["From"] == "00:00" and r["To"] == "23:59" for r in open_rows):
        return "Open 24/7"
    groups = []
    for r in open_rows:
        t = f'{r["From"]}–{r["To"]}'
        if groups and groups[-1][2] == t and BS_DAYS.index(r["Day"]) == BS_DAYS.index(groups[-1][1]) + 1:
            groups[-1][1] = r["Day"]
        else:
            groups.append([r["Day"], r["Day"], t])
    return ", ".join((f"{a[:3]}–{b[:3]}" if a != b else a[:3]) + f" {t}" for a, b, t in groups)


def bs_menu_script(flow):
    return " ".join(f'For {r["Option"]}, press {r["Key"]}.' for r in flow if r.get("Option") and r.get("Key"))


def build_sheet_data():
    ivr = bool(ss.get("bs_ivr_on"))
    df = ss.get("bs_flow_latest", ss.get("bs_flow_base")) if ivr else ss.get("bs_direct_latest", ss.get("bs_direct_base"))
    flow = [r for r in _clean_df(df) if any(str(v).strip() for k, v in r.items() if k != "Ring (secs)")]
    if ivr:
        flow = sorted(flow, key=lambda r: BS_KEYS.index(str(r.get("Key"))) if str(r.get("Key")) in BS_KEYS else 99)
    return {
        "hours": bs_hours_rows(), "bank_hols": ss.get("bs_bank_hols"), "ooh_action": ss.get("bs_ooh_action"),
        "ooh_divert": ss.get("bs_ooh_divert", ""), "closed_text": ss.get("bs_closed_text", ""),
        "welcome_on": ss.get("bs_welcome_on"), "welcome_text": ss.get("bs_welcome_text", ""),
        "gdpr_on": ss.get("bs_gdpr_on"), "gdpr_text": ss.get("bs_gdpr_text", ""), "audio": ss.get("bs_audio"),
        "ivr_on": ivr, "no_input": ss.get("bs_no_input"), "flow": flow, "menu_script": bs_menu_script(flow) if ivr else "",
        "users": _clean_df(ss.get("bs_users_latest")), "vm_email": ss.get("bs_vm_email", ""),
        "numbers": ss.get("bs_numbers"), "main_number": ss.get("bs_main_number", ""), "provider": ss.get("bs_provider", ""),
        "port_postcode": ss.get("bs_port_postcode", ""), "cli": ss.get("bs_cli"), "notes": ss.get("bs_notes", ""),
    }


def build_sheet_checks(bs, n_users):
    porting = bs["numbers"] != "New number(s)"
    uses_vm = any("Voicemail" in str(r.get("If no answer", "")) for r in bs["flow"]) or "voicemail" in (bs["ooh_action"] or "")
    users = bs["users"]
    checks = [
        ("Opening hours", any(r.get("Open") for r in bs["hours"])),
        ("Welcome message", (not bs["welcome_on"]) or (bs["welcome_text"].strip() and "[Company name]" not in bs["welcome_text"])),
        ("Call routing: who answers each option", bool(bs["flow"]) and all(str(r.get("Who rings", "")).strip() for r in bs["flow"])
         and (not bs["ivr_on"] or all(str(r.get("Option", "")).strip() for r in bs["flow"]))),
        (f"User names ({n_users})", n_users > 0 and len(users) == n_users and all(str(u.get("First name", "")).strip() for u in users)),
        ("User email addresses", n_users > 0 and len(users) == n_users
         and all(_EMAIL_RE.match(str(u.get("Email", "")).strip()) for u in users)),
        ("Number details" + (" (porting)" if porting else ""),
         (not porting) or (bool(bs["main_number"].strip()) and bool(bs["provider"].strip()))),
    ]
    if bs["ooh_action"] == BS_OOH_ACTIONS[2]:
        checks.insert(1, ("Out-of-hours divert number", bool(bs["ooh_divert"].strip())))
    if uses_vm:
        checks.insert(-1, ("Main voicemail email", bool(_EMAIL_RE.match(bs["vm_email"].strip()))))
    return checks


def build_sheet_parties():
    d = ss.get("fx_active_details")
    if d:
        return {"ref": d["meta"]["ref"], "customer": d["customer"]["company"], "contact": d["customer"]["name"],
                "site": d["customer"].get("delivery", ""), "seller": d["seller"]["name"]}
    return {"ref": "DRAFT", "customer": "", "contact": "", "site": "", "seller": ""}


def generate_build_sheet_pdf(bs, parties, n_users):
    styles = getSampleStyleSheet()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=27, leftMargin=27, topMargin=28, bottomMargin=40,
                            title=f"Build sheet {parties['ref']}", author=COMPANY)
    c_dark, c_bg, c_border = colors.HexColor("#0F172A"), colors.HexColor("#F5F8FB"), colors.HexColor("#D4DCE5")
    sec = ParagraphStyle("BSH", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10.5, leading=14,
                         textColor=C_PRIMARY, spaceBefore=8, spaceAfter=4)
    td = ParagraphStyle("BSTD", parent=styles["Normal"], fontName="Helvetica", fontSize=8.3, leading=11, textColor=c_dark)
    tdb = ParagraphStyle("BSTDB", parent=td, fontName="Helvetica-Bold")
    th = ParagraphStyle("BSTH", parent=td, fontName="Helvetica-Bold", textColor=colors.white)
    miss = "<font color='#B45309'><i>To confirm</i></font>"

    def v(x):
        x = str(x if x is not None else "").strip()
        return esc(x) if x else miss

    def grid(rows, widths, header=True):
        t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
        style = [("BOX", (0, 0), (-1, -1), 0.8, c_border), ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
                 ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 4),
                 ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("LEFTPADDING", (0, 0), (-1, -1), 6)]
        if header:
            style.append(("BACKGROUND", (0, 0), (-1, 0), C_HEAD))
        t.setStyle(TableStyle(style))
        return t

    def kv(pairs):
        t = grid([[Paragraph(f"<b>{esc(k)}</b>", td), Paragraph(val, td)] for k, val in pairs], [150, 390], header=False)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), c_bg)]))
        return t

    story = []
    _pdf_header(story, "System Build Sheet",
                f"<b>Ref:</b> {esc(parties['ref'])}<br/><b>Date:</b> {datetime.now().strftime('%d %B %Y')}", styles)
    story.append(kv([("Customer", v(parties["customer"])), ("Contact", v(parties["contact"])),
                     ("Site", v(parties["site"] if parties["site"] != "N/A" else "")),
                     ("Prepared by", f"{esc(COMPANY)} · {v(parties['seller'])}"), ("Users / licences", str(n_users)),
                     ("Quote ref", esc(parties["ref"]))]))

    story.append(Paragraph("1. Opening hours", sec))
    hrs = [[Paragraph(x, th) for x in ("Day", "Open?", "From", "To")]]
    for r in bs["hours"]:
        o = bool(r.get("Open"))
        hrs.append([Paragraph(esc(r["Day"]), td), Paragraph("Open" if o else "Closed", tdb if o else td),
                    Paragraph(esc(r["From"]) if o else "—", td), Paragraph(esc(r["To"]) if o else "—", td)])
    story.append(grid(hrs, [150, 130, 130, 130]))
    ooh = esc(bs["ooh_action"] or "") + (f" → {v(bs['ooh_divert'])}" if bs["ooh_action"] == BS_OOH_ACTIONS[2] else "")
    pairs = [("Bank holidays", "Closed" if bs["bank_hols"] else "Normal hours"), ("Out of hours", ooh)]
    if bs["ooh_action"] in BS_OOH_ACTIONS[:2]:
        pairs.append(("Closed message", v(bs["closed_text"])))
    story += [Spacer(1, 4), kv(pairs)]

    story.append(Paragraph("2. Greeting, recording notice &amp; menu", sec))
    pairs = [("Welcome message", v(bs["welcome_text"]) if bs["welcome_on"] else "None"),
             ("Recording / GDPR notice", v(bs["gdpr_text"]) if bs["gdpr_on"] else "None"), ("Recordings", esc(bs["audio"] or ""))]
    pairs += ([("Menu message", v(bs["menu_script"])), ("No key pressed", esc(bs["no_input"] or ""))] if bs["ivr_on"]
              else [("Menu", "No menu — calls ring straight through")])
    story += [kv(pairs), Spacer(1, 4)]
    head = (["Key", "Option"] if bs["ivr_on"] else []) + ["Who rings", "Ring style", "Ring", "If no answer", "Then / VM email"]
    rows = [[Paragraph(x, th) for x in head]]
    for r in bs["flow"] or [{}]:
        secs = r.get("Ring (secs)")
        rows.append(([Paragraph(v(r.get("Key")), tdb), Paragraph(v(r.get("Option")), tdb)] if bs["ivr_on"] else []) + [
            Paragraph(v(r.get("Who rings")), td), Paragraph(v(r.get("Ring style")), td),
            Paragraph(f"{int(secs)}s" if str(secs).replace(".0", "").isdigit() else miss, td),
            Paragraph(v(r.get("If no answer")), td), Paragraph(esc(str(r.get("Then / voicemail email", "") or "—")), td)])
    story.append(grid(rows, [32, 70, 120, 72, 36, 90, 120] if bs["ivr_on"] else [150, 80, 40, 110, 160]))

    story.append(Paragraph("3. Users", sec))
    urows = [[Paragraph(x, th) for x in ("Name", "Email", "Ext.", "Device", "App", "VM mail", "Direct dial")]]
    for u in bs["users"]:
        name = f'{u.get("First name", "")} {u.get("Last name", "")}'.strip()
        urows.append([Paragraph(v(name), tdb), Paragraph(v(u.get("Email")), td), Paragraph(v(u.get("Extension")), td),
                      Paragraph(v(u.get("Device")), td), Paragraph("Yes" if u.get("Mobile app") else "No", td),
                      Paragraph("Yes" if u.get("Voicemail to email") else "No", td),
                      Paragraph(esc(str(u.get("Direct dial (DDI)", "") or "—")), td)])
    if len(urows) == 1:
        urows.append([Paragraph(miss, td)] + [""] * 6)
    story.append(grid(urows, [95, 145, 34, 110, 30, 50, 76]))

    story.append(Paragraph("4. Voicemail &amp; numbers", sec))
    pairs = [("Main voicemail to", v(bs["vm_email"])), ("Outgoing caller ID", esc(bs["cli"] or "")),
             ("Numbers", esc(bs["numbers"] or "")), ("Main number", v(bs["main_number"]))]
    if bs["numbers"] != "New number(s)":
        pairs += [("Current provider", v(bs["provider"])), ("Billing postcode", v(bs["port_postcode"]))]
    pairs.append(("Notes", esc(bs["notes"]) if bs["notes"].strip() else "—"))
    story.append(kv(pairs))
    story += [Spacer(1, 10), Paragraph("<font size=7.5 color='#475569'>By signing, the customer confirms these details are "
                                       "correct. Changes after the system is built may be chargeable.</font>", td), Spacer(1, 4)]
    s = grid([[Paragraph("<b>Customer signature:</b> ______________________________", td),
               Paragraph("<b>Date:</b> ____________________", td)]], [340, 200], header=False)
    s.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), c_bg), ("TOPPADDING", (0, 0), (-1, -1), 8),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    story.append(s)
    doc.build(story, onFirstPage=_pdf_footer, onLaterPages=_pdf_footer)
    return buf.getvalue()


def render_build_sheet_form():
    _bs_init()
    n_users = int(ss.fx_users)
    with st.expander("System setup details  ·  IVR, opening hours, call routing, users & voicemail", expanded=False):
        render_html('<div class="rit-bs-intro">Fill this in with your customer. It becomes the <b>build sheet</b> the system '
                    'is programmed from. Anything left blank can be finished later.</div>')
        t_hours, t_calls, t_users, t_vm = st.tabs(["1 · Hours", "2 · Greeting & menu", "3 · Users", "4 · Voicemail & numbers"])
        with t_hours:
            h1, h2 = st.columns([1.4, 1])
            h1.selectbox("Opening hours", list(BS_HOURS_PRESETS), key="bs_hours_preset")
            h2.checkbox("Closed on UK bank holidays", key="bs_bank_hols")
            if ss.bs_hours_preset == "Custom hours":
                ss.bs_hours_latest = st.data_editor(
                    ss.bs_hours_base, key="bs_hours_ed", hide_index=True, num_rows="fixed", **FULL_WIDTH,
                    column_config={"Day": st.column_config.TextColumn(disabled=True), "Open": st.column_config.CheckboxColumn(),
                                   "From": st.column_config.SelectboxColumn(options=BS_TIMES, required=True),
                                   "To": st.column_config.SelectboxColumn(options=BS_TIMES, required=True)})
            else:
                render_html(f'<div class="rit-bs-read">{icon("check", 13, 3)}{esc(bs_hours_summary(bs_hours_rows()))}</div>')
            o1, o2 = st.columns([1.4, 1])
            o1.selectbox("Out of hours, calls should…", BS_OOH_ACTIONS, key="bs_ooh_action")
            if ss.bs_ooh_action == BS_OOH_ACTIONS[2]:
                o2.text_input("Divert to number", key="bs_ooh_divert", placeholder="e.g. 07700 900123")
            if ss.bs_ooh_action in BS_OOH_ACTIONS[:2]:
                st.text_area("Closed message", key="bs_closed_text", height=80)
        with t_calls:
            g1, g2 = st.columns(2)
            g1.checkbox("Play a welcome message", key="bs_welcome_on")
            g2.checkbox("Play a call-recording / GDPR notice", key="bs_gdpr_on")
            if ss.bs_welcome_on:
                st.text_input("Welcome message", key="bs_welcome_text")
            if ss.bs_gdpr_on:
                st.text_area("Recording / GDPR notice", key="bs_gdpr_text", height=72)
            st.selectbox("How are the messages recorded?", BS_AUDIO, key="bs_audio")
            render_html('<div class="rit-admin-h">Call routing (in hours)</div>')
            st.toggle("Use a menu — “press 1 for sales, 2 for accounts…”", key="bs_ivr_on")
            common_cfg = {
                "Who rings": st.column_config.TextColumn("Who rings", help="Names or extensions, e.g. Jo, Sam, 203", width="medium"),
                "Ring style": st.column_config.SelectboxColumn("Ring style", options=BS_RING_STYLES, required=True),
                "Ring (secs)": st.column_config.NumberColumn("Ring (secs)", min_value=5, max_value=120, step=5),
                "If no answer": st.column_config.SelectboxColumn("If no answer", options=BS_NO_ANSWER, required=True),
                "Then / voicemail email": st.column_config.TextColumn("Then… / voicemail email"),
            }
            if ss.bs_ivr_on:
                ss.bs_flow_latest = st.data_editor(
                    ss.bs_flow_base, key="bs_flow_ed", hide_index=True, num_rows="dynamic", **FULL_WIDTH,
                    column_config={"Key": st.column_config.SelectboxColumn("Key", options=BS_KEYS, required=True, width="small"),
                                   "Option": st.column_config.TextColumn("Option"), **common_cfg})
                script = bs_menu_script(build_sheet_data()["flow"])
                if script:
                    render_html(f'<div class="rit-bs-read">{icon("phone", 13)}<span><b>Menu will say:</b> “{esc(script)}”</span></div>')
                st.selectbox("If the caller doesn't press anything", BS_NO_INPUT, key="bs_no_input")
            else:
                ss.bs_direct_latest = st.data_editor(ss.bs_direct_base, key="bs_direct_ed", hide_index=True,
                                                     num_rows="fixed", **FULL_WIDTH, column_config=common_cfg)
        with t_users:
            if n_users == 0:
                render_html('<div class="nl-empty">Set the number of users in step 01 and a row appears here for each one.</div>')
            else:
                current = ss.get("bs_users_latest")
                if current is None or len(current) != n_users:
                    ss.bs_users_base = _bs_user_rows(n_users, current)
                    ss.bs_users_ver += 1
                devices = [BS_SOFTPHONE] + [i["name"] for i in basket_items()] + ["Customer's own device"]
                ss.bs_users_latest = st.data_editor(
                    ss.bs_users_base, key=f"bs_users_ed_{ss.bs_users_ver}", hide_index=True, num_rows="fixed", **FULL_WIDTH,
                    column_config={"Extension": st.column_config.TextColumn("Ext.", width="small"),
                                   "Device": st.column_config.SelectboxColumn("Device", options=devices, required=True),
                                   "Mobile app": st.column_config.CheckboxColumn("App", width="small"),
                                   "Voicemail to email": st.column_config.CheckboxColumn("VM → email", width="small"),
                                   "Direct dial (DDI)": st.column_config.TextColumn("Direct dial")})
        with t_vm:
            v1, v2 = st.columns(2)
            v1.text_input("Main / shared voicemail goes to (email)", key="bs_vm_email")
            v2.selectbox("Outgoing caller ID", BS_CLI, key="bs_cli")
            n1, n2 = st.columns(2)
            n1.selectbox("Phone numbers", BS_NUMBERS, key="bs_numbers")
            n2.text_input("Main number" + (" to port" if ss.bs_numbers != "New number(s)" else " (if known)"), key="bs_main_number")
            if ss.bs_numbers != "New number(s)":
                p1, p2 = st.columns(2)
                p1.text_input("Current phone provider", key="bs_provider", placeholder="e.g. BT")
                p2.text_input("Postcode the numbers are billed to", key="bs_port_postcode")
            st.text_area("Anything else to note?", key="bs_notes", height=72)

        bs = build_sheet_data()
        checks = build_sheet_checks(bs, n_users)
        done = sum(1 for _, ok in checks if ok)
        chips = "".join(chip(("✓ " if ok else "○ ") + lbl, "good" if ok else "muted") for lbl, ok in checks)
        render_html(f'<div class="rit-bs-status"><div class="h">Build sheet {done}/{len(checks)} complete</div>'
                    f'<div class="pe-chips">{chips}</div></div>')
        b1, b2 = st.columns(2)
        if b1.button("Prepare build sheet PDF", key="bs_make", **FULL_WIDTH):
            ss.bs_pdf = generate_build_sheet_pdf(bs, build_sheet_parties(), n_users)
        if ss.get("bs_pdf"):
            b2.download_button("Download build sheet PDF", data=ss.bs_pdf, key="bs_dl", mime="application/pdf",
                               file_name=f"Build-sheet-{build_sheet_parties()['ref']}.pdf", type="primary", **FULL_WIDTH)


# ==========================================
# PAGE
# ==========================================
LICENCE_FEATURES = ["Mobile app (iOS / Android)", "Cloud call recording", "Desktop PC softphone",
                    "Auto-attendant & IVR", "Voicemail-to-email", "Inclusive UK landline & mobile calls"]
CATEGORIES = ["All hardware", "Yealink Phones", "Fanvil Phones", "Cordless & Wi-Fi", "Headsets & Accessories"]


def hero_html(active_step):
    steps = ["Users", "Deployment", "Hardware", "Details"]
    parts = []
    for i, label in enumerate(steps, 1):
        state = "done" if i < active_step else "active" if i == active_step else ""
        num = icon("check", 12, 3) if state == "done" else str(i)
        parts.append(f'<div class="pe-step {state}"><span class="num">{num}</span>{label}</div>')
    return ('<div class="pe-hero"><div>' +
            f'<div class="pe-eyebrow"><span class="dot"></span>Telephony quotation · {datetime.now().strftime("%d %B %Y")}</div>'
            '<div class="pe-title">Build a quotation</div>'
            '<div class="pe-sub">Add user licences, choose a deployment and pick the hardware. '
            'Totals update live, and the PDF is one click away.</div>'
            f'</div><div class="pe-stepper">{"<div class=pe-step-sep></div>".join(parts)}</div></div>')


hero_slot = st.empty()
tab_builder, tab_cv, tab_admin = st.tabs(["Build quotation", "Customer view", "Admin · pricing"])

# ---------------- BUILD QUOTATION ----------------
with tab_builder:
    left, right = st.columns([1.72, 1], gap="large")
    with left:
        with st.container(key="card-users"):
            section_header("01", "Hosted user licences", f"Ongoing monthly · {CONTRACT_MONTHS}-month minimum term")
            u1, u2 = st.columns([1.35, 1], gap="medium")
            with u1:
                feats = "".join(f'<div class="nl-feat"><span class="ck">{icon("check", 12, 3)}</span>{esc(f)}</div>'
                                for f in LICENCE_FEATURES)
                render_html('<div class="nl-licence"><div class="top"><div><div class="name">Hosted Cloud User Licence</div>'
                            '<div class="sub">A complete unified-communications seat, enterprise features included.</div></div>'
                            f'<div class="nl-price">{money(LICENCE_MONTHLY_RATE)} <small>/ user / mo</small></div></div>'
                            f'<div class="nl-feats">{feats}</div><div class="nl-activation">{icon("zap", 14)}'
                            f'<span>One-off user setup &amp; provisioning: <b>{money(SETUP_FEE_PER_USER)} per user</b>, billed in month 1</span></div></div>')
            with u2:
                st.number_input("Number of users", min_value=0, max_value=500, step=1, key="fx_users")
                mrc = total_monthly()
                render_html('<div class="nl-mini">'
                            f'<div><div class="l">Monthly</div><div class="v">{money(mrc)}</div><div class="s">{money(mrc * (1 + VAT_RATE))} inc VAT</div></div>'
                            f'<div><div class="l">User setup</div><div class="v">{money(total_setup())}</div><div class="s">one-off, ex VAT</div></div></div>')

        with st.container(key="card-deploy"):
            section_header("02", "Deployment", "One-off · choose how the system goes live")
            users = ss.fx_users
            d1, d2 = st.columns(2, gap="medium")
            for col, opt in zip((d1, d2), (DEPLOY_BASIC, DEPLOY_ADVANCED)):
                selected = ss.fx_deployment == opt
                with col, st.container(key=f"dep-{'on' if selected else 'off'}-{opt}"):
                    if opt == DEPLOY_BASIC:
                        price, meta = money(BASIC_DEPLOYMENT_FEE), [chip("Flat fee", "muted"), chip("Self-install", "muted")]
                    else:
                        price = money(advanced_deployment_price(max(users, 1)))
                        meta = [chip(advanced_band_label(max(users, 1)), "accent"), chip("Fully managed", "muted")]
                    render_html(f'<div class="rit-dep-top"><div class="rit-dep-name">{esc(DEPLOYMENT_LABELS[opt])}</div>'
                                f'<div class="rit-dep-price">{price}</div></div><div class="rit-dep-desc">{esc(DEPLOYMENT_DESCS[opt])}</div>'
                                f'<div class="pe-chips" style="margin:10px 0 12px">{"".join(meta)}</div>')
                    st.button("Selected" if selected else "Choose this option", key=f"fx_pick_{opt}",
                              type="primary" if selected else "secondary", disabled=selected,
                              on_click=lambda o=opt: ss.update(fx_deployment=o), **FULL_WIDTH)
            if users == 0:
                render_html(f'<div class="pe-hint">{icon("alert", 14)}<span>Deployment is added once you set the number of users.</span></div>')
            render_build_sheet_form()

        with st.container(key="card-hardware"):
            section_header("03", "Handsets, headsets & hardware", "Optional · one-off upfront · tap + to add")
            chosen = st.segmented_control("Category", CATEGORIES, default="All hardware", key="fx_cat",
                                          label_visibility="collapsed") or "All hardware"
            shown = PRODUCTS if chosen == "All hardware" else [p for p in PRODUCTS if p["category"] == chosen]
            for start in range(0, len(shown), 3):
                cols = st.columns(3, gap="small")
                for col, p in zip(cols, shown[start:start + 3]):
                    pid, qty = p["id"], ss.fx_basket.get(p["id"], 0)
                    with col, st.container(key=f"prod-{'on' if qty else 'off'}-{pid}"):
                        src = product_image(p["image"])
                        img = f'<img src="{src}" alt="{esc(p["name"])}">' if src else f'<span style="color:#94A3B8">{icon("image", 26)}</span>'
                        render_html(f'<div class="nl-prod-top">{chip(p["tag"], "accent")}<span class="nl-prod-price">{money(p["price"])}</span></div>'
                                    f'<div class="nl-stage">{img}</div><div class="nl-prod-name">{esc(p["name"])}</div>'
                                    f'<div class="nl-prod-desc">{esc(p["desc"])}</div>')
                        s1, s2, s3 = st.columns([1, 1.3, 1], gap="small")
                        s1.button("−", key=f"fx_minus_{pid}", on_click=update_qty, args=(pid, -1), disabled=qty == 0, **FULL_WIDTH)
                        render_html(f'<div class="nl-qty {"on" if qty else ""}">{qty}</div>', target=s2)
                        s3.button("+", key=f"fx_plus_{pid}", on_click=update_qty, args=(pid, 1), **FULL_WIDTH)
                        render_html(f'<div class="nl-sub on">{money(qty * p["price"])} ex VAT</div>' if qty
                                    else '<div class="nl-sub">Not in quote</div>')

        with st.container(key="card-details"):
            section_header("04", "Quote details & PDF", "Who it's from, who it's for, and where it's going")
            with st.form("fx_quote_form", border=False):
                cr, cc = st.columns(2, gap="large")
                with cr:
                    render_html(f'<div class="nl-form-h">{icon("building", 16)}From</div>')
                    r_company = st.text_input("Company name *", value=SETTINGS["company_name"])
                    r_contact = st.text_input("Your name / account manager *")
                    r_email = st.text_input("Your email *", value=SETTINGS["company_email"])
                    r_phone = st.text_input("Your phone", value=SETTINGS["company_phone"])
                with cc:
                    render_html(f'<div class="nl-form-h">{icon("user", 16)}Proposed customer</div>')
                    c_company = st.text_input("Customer company *", placeholder="e.g. Apex Logistics Ltd")
                    c_contact = st.text_input("Customer contact *", placeholder="e.g. Sarah Jenkins")
                    c_email = st.text_input("Customer email *")
                    c_phone = st.text_input("Customer phone")
                render_html(f'<div class="nl-form-h" style="margin-top:10px">{icon("truck", 16)}Delivery / site address'
                            ' <span style="color:var(--faint);font-weight:500">(optional)</span></div>')
                a1, a2, a3 = st.columns([2, 1, 1])
                del_addr = a1.text_input("Address line 1")
                del_city = a2.text_input("Town / city")
                del_pc = a3.text_input("Postcode")
                go = st.form_submit_button("Save quotation & generate PDF", type="primary", **FULL_WIDTH)

            if go:
                items = basket_items()
                if not (r_company and r_contact and r_email):
                    st.error("Please complete your details (company, name and email).")
                elif not (c_company and c_contact and c_email):
                    st.error("Please fill in the customer's company, contact name and email.")
                elif ss.fx_users == 0 and not items:
                    st.error("Add at least one user licence or a piece of hardware before generating a quote.")
                else:
                    ref = f"{QUOTE_PREFIX}-{datetime.now().strftime('%y%m%d%H%M')}"
                    meta = {"ref": ref, "date": datetime.now().strftime("%d %B %Y")}
                    delivery = ", ".join(p.strip() for p in (del_addr, del_city, del_pc) if p.strip()) or "N/A"
                    seller = {"company": r_company, "name": r_contact, "email": r_email, "phone": r_phone}
                    customer = {"company": c_company, "name": c_contact, "email": c_email, "phone": c_phone, "delivery": delivery}
                    ss.fx_pdf = generate_quotation_pdf(meta, seller, customer, ss.fx_users, items, ss.fx_deployment)
                    ss.fx_ref, ss.fx_sig, ss.fx_customer = ref, quote_signature(), c_company
                    ss.fx_active_details = {"meta": meta, "seller": seller, "customer": customer}
                    row = pd.DataFrame([{
                        "Quote Ref": ref, "Date": meta["date"], "Account Manager": r_contact, "Customer": c_company,
                        "Contact": c_contact, "Email": c_email, "Users": ss.fx_users,
                        "Monthly Ex VAT (£)": f"{total_monthly():.2f}", "Deployment": DEPLOYMENT_LABELS[ss.fx_deployment],
                        "One-off Ex VAT (£)": f"{total_one_off():.2f}",
                        "Hardware": "; ".join(f"{i['name']} x{i['qty']}" for i in items) or "None", "Site": delivery}])
                    row.to_csv(QUOTES_FILE, mode="a", header=not os.path.isfile(QUOTES_FILE), index=False)
                    st.success(f"Quotation {ref} generated for {c_company}.")

            if ss.get("fx_pdf"):
                if ss.get("fx_sig") != quote_signature():
                    st.warning("The quote has changed since this PDF was made. Generate it again to include the changes.")
                st.download_button(f"Download {ss.fx_ref}.pdf", data=ss.fx_pdf, file_name=f"{ss.fx_ref}.pdf",
                                   mime="application/pdf", key="fx_dl_main", **FULL_WIDTH)

    with right, st.container(key="card-summary"):
        mrc, one = total_monthly(), total_one_off()
        m1 = mrc + one
        render_html('<div class="nl-sum-h"><div class="t">Live quote</div><span class="nl-live">Updating</span></div>'
                    f'<div class="nl-total"><div class="l">Ongoing monthly</div><div class="v">{money(mrc)} <small>/ mo ex VAT</small></div>'
                    f'<div class="i">{money(mrc * (1 + VAT_RATE))} / mo inc VAT</div></div>'
                    f'<div class="nl-total"><div class="l">One-off upfront</div><div class="v">{money(one)} <small>ex VAT</small></div>'
                    f'<div class="i">{money(one * (1 + VAT_RATE))} inc VAT</div></div>'
                    f'<div class="nl-total hero"><div class="l">Month 1 investment</div><div class="v">{money(m1)}</div>'
                    f'<div class="i">{money(m1 * (1 + VAT_RATE))} inc VAT</div></div><div class="nl-lines-h">In this quote</div>')
        items = basket_items()
        if ss.fx_users == 0 and not items:
            render_html('<div class="nl-empty">Nothing added yet. Set the number of users to get started.</div>')
        if ss.fx_users > 0:
            render_html(f'<div class="nl-line"><span class="n">Cloud user licence<small>× {ss.fx_users}</small></span><span class="p">{money(mrc)}/mo</span></div>'
                        f'<div class="nl-line"><span class="n">User setup &amp; provisioning<small>× {ss.fx_users}</small></span><span class="p">{money(total_setup())}</span></div>'
                        f'<div class="nl-line"><span class="n">{esc(DEPLOYMENT_LABELS[ss.fx_deployment])}</span><span class="p">{money(deployment_fee())}</span></div>')
        for it in items:
            with st.container(key=f"sumline-{it['id']}"):
                l1, l2 = st.columns([6, 1], vertical_alignment="center", gap="small")
                render_html(f'<div class="nl-line nb"><span class="n">{esc(it["name"])}<small>× {it["qty"]}</small></span>'
                            f'<span class="p">{money(it["line_total"])}</span></div>', target=l1)
                l2.button("✕", key=f"fx_del_{it['id']}", on_click=remove_from_basket, args=(it["id"],), help=f"Remove {it['name']}")
        render_html(f'<div class="nl-term">{icon("alert", 14)}<span>Licences are on a <b>{CONTRACT_MONTHS}-month minimum term</b>.'
                    f' Early termination charges apply. Quote valid for {QUOTE_VALID_DAYS} days.</span></div>')
        if ss.get("fx_pdf") and ss.get("fx_sig") == quote_signature():
            st.download_button(f"Download {ss.fx_ref}.pdf", data=ss.fx_pdf, file_name=f"{ss.fx_ref}.pdf",
                               mime="application/pdf", type="primary", key="fx_dl_side", **FULL_WIDTH)
        else:
            st.caption("Fill in step 04 to generate the PDF.")

# ---------------- CUSTOMER VIEW ----------------
with tab_cv:
    users = ss.fx_users
    mrc, setup_ex, dep_ex, hw_ex = total_monthly(), total_setup(), deployment_fee(), total_hardware()
    one = setup_ex + dep_ex + hw_ex
    items = basket_items()
    who = ss.get("fx_customer")
    _, mid, _ = st.columns([0.06, 1, 0.06])
    with mid:
        with st.container(key="card-cv-head"):
            render_html(brand_row() + '<div class="nl-prop"><div><div class="k">Proposal'
                        + (f" · prepared for {esc(who)}" if who else "") + '</div>'
                        '<div class="t">Your cloud telephony solution</div>'
                        '<div class="s">Unified communications for every user, on desk, laptop and mobile.</div></div>'
                        f'<div>{chip(datetime.now().strftime("%d %B %Y"), "accent")}</div></div><div class="nl-kpis">'
                        f'<div class="nl-kpi" style="--c:#29A9E1"><div class="l">Ongoing monthly</div><div class="v">{money(mrc)} <small>ex VAT</small></div><div class="i">{money(mrc * (1 + VAT_RATE))} / mo inc VAT</div></div>'
                        f'<div class="nl-kpi" style="--c:#B9C3CE"><div class="l">One-off upfront</div><div class="v">{money(one)} <small>ex VAT</small></div><div class="i">{money(one * (1 + VAT_RATE))} inc VAT</div></div>'
                        f'<div class="nl-kpi" style="--c:#3DDC84"><div class="l">Month 1 investment</div><div class="v">{money(mrc + one)} <small>ex VAT</small></div><div class="i">{money((mrc + one) * (1 + VAT_RATE))} inc VAT</div></div></div>')
        with st.container(key="card-cv-monthly"):
            section_header("1", "Ongoing monthly costs", f"Per user, per month · {CONTRACT_MONTHS}-month minimum term")
            if users > 0:
                render_html('<table class="nl-table"><thead><tr><th>Service</th><th class="num">Users</th><th class="num">Unit (ex VAT)</th>'
                            '<th class="num">Monthly (ex VAT)</th></tr></thead><tbody><tr><td><b>Hosted VoIP cloud user licence</b>'
                            '<div class="desc">Apps, softphone, call recording, auto-attendant &amp; inclusive UK calls</div></td>'
                            f'<td class="num">{users}</td><td class="num">{money(LICENCE_MONTHLY_RATE)}</td><td class="num"><b>{money(mrc)}</b></td></tr>'
                            f'<tr class="sub"><td colspan="3">VAT @ {VAT_PCT}</td><td class="num">{money(mrc * VAT_RATE)}</td></tr>'
                            f'<tr class="grand"><td colspan="3">Total monthly (inc VAT)</td><td class="num">{money(mrc * (1 + VAT_RATE))} / mo</td></tr></tbody></table>')
            else:
                render_html('<div class="nl-empty">No user licences selected yet.</div>')
        if "bs_hours_preset" in ss and users > 0:
            bs = build_sheet_data()
            with st.container(key="card-cv-setup"):
                section_header("✓", "How your system will work", "Summary of your setup · confirm with your account manager")
                named = [u for u in bs["users"] if str(u.get("First name", "")).strip()]
                if bs["ivr_on"] and bs["flow"]:
                    route = "".join(f'<div class="rit-cv-opt"><span class="key">{esc(r.get("Key", ""))}</span><span class="o">{esc(r.get("Option", "") or "—")}</span>'
                                    f'<span class="w">rings {esc(r.get("Who rings", "") or "to confirm")}, then {esc(str(r.get("If no answer", "")).lower())}</span></div>'
                                    for r in bs["flow"])
                else:
                    f0 = (bs["flow"] or [{}])[0]
                    route = (f'<div class="rit-cv-opt"><span class="key">☎</span><span class="o">All calls</span>'
                             f'<span class="w">ring {esc(f0.get("Who rings", "") or "to confirm")}, then {esc(str(f0.get("If no answer", "")).lower())}</span></div>')
                render_html('<div class="rit-cv-setup">'
                            f'<div class="pe-panel"><div class="h">Opening hours</div><div class="big">{esc(bs_hours_summary(bs["hours"]))}</div>'
                            f'<div class="sm">Out of hours: {esc(bs["ooh_action"] or "")}</div></div>'
                            '<div class="pe-panel"><div class="h">Callers hear</div><div class="sm">'
                            + (f'“{esc(bs["welcome_text"])}”<br>' if bs["welcome_on"] else "")
                            + ("Call-recording / GDPR notice<br>" if bs["gdpr_on"] else "")
                            + (f'“{esc(bs["menu_script"])}”' if bs["ivr_on"] and bs["menu_script"] else "") + '</div></div>'
                            f'<div class="pe-panel"><div class="h">Users set up</div><div class="big">{len(named)} of {users}</div>'
                            f'<div class="sm">{esc(", ".join((str(u.get("First name", "")) + " " + str(u.get("Last name", ""))).strip() for u in named[:6]))}'
                            + (" …" if len(named) > 6 else "") + f'</div></div></div><div class="nl-lines-h">Call routing</div>{route}')
        with st.container(key="card-cv-oneoff"):
            section_header("2", "One-off upfront costs", "Setup, deployment and hardware, billed once")
            rows = ""
            if users > 0:
                rows += (f'<tr><td><b>User setup &amp; provisioning</b><div class="desc">Extension setup, user provisioning and licence activation</div></td>'
                         f'<td class="num">{users}</td><td class="num">{money(SETUP_FEE_PER_USER)}</td><td class="num"><b>{money(setup_ex)}</b></td></tr>'
                         f'<tr><td><b>{esc(DEPLOYMENT_LABELS[ss.fx_deployment])}</b><div class="desc">{esc(DEPLOYMENT_DESCS[ss.fx_deployment])}</div></td>'
                         f'<td class="num">1</td><td class="num">{money(dep_ex)}</td><td class="num"><b>{money(dep_ex)}</b></td></tr>')
            for it in items:
                src = product_image(it["image"], 160)
                thumb = f'<img src="{src}" alt="">' if src else icon("phone", 18)
                rows += (f'<tr><td><div style="display:flex;gap:12px;align-items:center"><div class="thumb">{thumb}</div>'
                         f'<div><b>{esc(it["name"])}</b><div class="desc">{esc(it["desc"])}</div></div></div></td>'
                         f'<td class="num">{it["qty"]}</td><td class="num">{money(it["price"])}</td><td class="num"><b>{money(it["line_total"])}</b></td></tr>')
            if rows:
                render_html('<table class="nl-table"><thead><tr><th>Item</th><th class="num">Qty</th><th class="num">Unit (ex VAT)</th>'
                            f'<th class="num">Total (ex VAT)</th></tr></thead><tbody>{rows}'
                            f'<tr class="sub"><td colspan="3">Subtotal (ex VAT)</td><td class="num">{money(one)}</td></tr>'
                            f'<tr class="sub"><td colspan="3">VAT @ {VAT_PCT}</td><td class="num">{money(one * VAT_RATE)}</td></tr>'
                            f'<tr class="grand"><td colspan="3">Total one-off (inc VAT)</td><td class="num">{money(one * (1 + VAT_RATE))}</td></tr></tbody></table>')
            else:
                render_html('<div class="nl-empty">No one-off items yet.</div>')
            render_html(f'<div class="nl-note"><b>Commercial notes:</b> Quotation valid for {QUOTE_VALID_DAYS} calendar days. '
                        f'User licences are subject to a {CONTRACT_MONTHS}-month minimum term.</div>')

# ---------------- ADMIN · PRICING ----------------
with tab_admin:
    admin_pw = _secret("QUOTE_ADMIN_PASSWORD")
    _, amid, _ = st.columns([0.06, 1, 0.06])
    with amid:
        if not admin_pw:
            st.error("QUOTE_ADMIN_PASSWORD isn't set in Streamlit Secrets, so pricing admin is locked.")
        elif not ss.get("fx_admin_ok"):
            _, lc, _ = st.columns([1, 1.2, 1])
            with lc, st.container(key="card-admin-login"):
                render_html(f'<div class="nl-form-h">{icon("lock", 16)}Admin access</div>'
                            '<div class="rit-admin-note">Enter the admin password to change prices.</div>')
                with st.form("fx_admin_login", border=False):
                    a_try = st.text_input("Admin password", type="password")
                    a_go = st.form_submit_button("Unlock pricing", type="primary", **FULL_WIDTH)
                if a_go:
                    if hmac.compare_digest(a_try.encode(), str(admin_pw).encode()):
                        ss.fx_admin_ok = True
                        st.rerun()
                    else:
                        st.error("Incorrect admin password.")
        else:
            k1, k2 = st.columns([5, 1])
            render_html(f'<div class="rit-admin-bar">{icon("lock", 14)}<span>Admin area · prices here are used on every new quote</span></div>',
                        target=k1)
            if k2.button("Lock admin", key="fx_admin_lock", **FULL_WIDTH):
                ss.fx_admin_ok = False
                st.rerun()
            with st.container(key="card-admin"):
                section_header("⚙", "Pricing & quote settings", "Your selling prices · ex VAT")
                storage = "GitHub (permanent)" if _gh_config() else "Local file (resets on app restart)"
                render_html('<div class="pe-chips" style="margin-bottom:14px">' + chip(f"Storage: {storage}", "good" if _gh_config() else "warn")
                            + (chip(f"Last saved {SETTINGS['updated']}", "muted") if SETTINGS["updated"] else "") + "</div>")
                ver = SETTINGS["updated"] or "0"
                with st.form("fx_pricing", border=False):
                    render_html('<div class="rit-admin-h">Licences & setup</div>')
                    p1, p2, p3 = st.columns(3)
                    n_lic = p1.number_input("Licence (£ / user / month)", min_value=0.0, value=float(LICENCE_MONTHLY_RATE), step=0.50, format="%.2f", key=f"fx_a1_{ver}")
                    n_setup = p2.number_input("User setup (£ / user, one-off)", min_value=0.0, value=float(SETUP_FEE_PER_USER), step=1.0, format="%.2f", key=f"fx_a2_{ver}")
                    n_basic = p3.number_input("Basic system build (£, one-off)", min_value=0.0, value=float(BASIC_DEPLOYMENT_FEE), step=5.0, format="%.2f", key=f"fx_a3_{ver}")
                    render_html('<div class="rit-admin-h">Advanced system deployment</div>')
                    q1, q2, q3 = st.columns(3)
                    n_a15 = q1.number_input("1–5 users (£)", min_value=0.0, value=float(SETTINGS["adv_1_5"]), step=10.0, format="%.2f", key=f"fx_a4_{ver}")
                    n_a610 = q2.number_input("6–10 users (£)", min_value=0.0, value=float(SETTINGS["adv_6_10"]), step=10.0, format="%.2f", key=f"fx_a5_{ver}")
                    n_ax = q3.number_input("Each further 10 users (£)", min_value=0.0, value=float(SETTINGS["adv_extra_10"]), step=10.0, format="%.2f", key=f"fx_a6_{ver}")
                    n_def = st.radio("Default deployment on new quotes", [DEPLOY_BASIC, DEPLOY_ADVANCED],
                                     index=0 if SETTINGS["default_deployment"] == DEPLOY_BASIC else 1,
                                     format_func=lambda o: DEPLOYMENT_LABELS[o], horizontal=True, key=f"fx_a7_{ver}")
                    render_html('<div class="rit-admin-h">Hardware prices (£ each, ex VAT)</div>')
                    hw_df = pd.DataFrame([{"id": p["id"], "Product": p["name"], "Category": p["category"], "Price (£)": p["price"]}
                                          for p in PRODUCTS])
                    hw_edit = st.data_editor(hw_df, key=f"fx_hw_{ver}", hide_index=True, num_rows="fixed", **FULL_WIDTH,
                                             column_config={"id": None, "Product": st.column_config.TextColumn(disabled=True),
                                                            "Category": st.column_config.TextColumn(disabled=True),
                                                            "Price (£)": st.column_config.NumberColumn(min_value=0.0, step=1.0, format="£%.2f")})
                    render_html('<div class="rit-admin-h">Quote defaults</div>')
                    r1, r2, r3 = st.columns(3)
                    n_cn = r1.text_input("Company name on quotes", value=SETTINGS["company_name"], key=f"fx_a8_{ver}")
                    n_ce = r2.text_input("Default email", value=SETTINGS["company_email"], key=f"fx_a9_{ver}")
                    n_cp = r3.text_input("Default phone", value=SETTINGS["company_phone"], key=f"fx_a10_{ver}")
                    save = st.form_submit_button("Save pricing", type="primary", **FULL_WIDTH)
                if save:
                    ok, msg = save_settings({
                        "licence_monthly": n_lic, "setup_per_user": n_setup, "basic_deployment": n_basic,
                        "adv_1_5": n_a15, "adv_6_10": n_a610, "adv_extra_10": n_ax, "default_deployment": n_def,
                        "hardware": {r["id"]: r["Price (£)"] for r in hw_edit.to_dict("records")},
                        "company_name": n_cn, "company_email": n_ce, "company_phone": n_cp})
                    ss.fx_flash = ("success" if ok else "warning", msg)
                    st.rerun()
                flash = ss.pop("fx_flash", None)
                if flash:
                    getattr(st, flash[0])(flash[1])

# ---------------- Hero (rendered last so the stepper reflects this run) ----------------
if ss.fx_users == 0 and not ss.fx_basket:
    _step = 1
elif ss.get("fx_pdf") and ss.get("fx_sig") == quote_signature():
    _step = 5
elif ss.fx_basket:
    _step = 4
else:
    _step = 3
render_html(hero_html(_step), target=hero_slot)
