"""Phones page: platform highlights + product gallery (edit products in products.py)."""

import streamlit as st

from common import (contact_band, feature_row, footer, header, icon, product_grid,
                    render_html, setup)
from products import PHONE_CATEGORIES, PHONES

setup()
header("phones")

render_html(f"""
<section class="fx-phero solo">
  <div>
    <div class="fx-tag">{icon('phone', 16)}Telephony</div>
    <h1>A complete phone system, with the handsets to match</h1>
    <p class="lede">Our cloud phone platform brings calls, messaging, contact-centre tools and team collaboration
    together in one place. You keep your existing numbers, and we supply, set up and support the phones.</p>
    <div class="fx-ctas"><a class="fx-btn primary" href="#range">{icon('devices', 18)}See the phones</a></div>
  </div>
</section>
""")

render_html(feature_row(
    "chat", "Omnichannel", "Every channel, included as standard",
    "Voice, video, messaging and email in one system, so customers can reach you however suits them, "
    "with nothing extra to buy.",
    ["Voice, video, messaging and email together",
     "SMS, WhatsApp, Facebook and live chat",
     "No bolt-ons: everything is included"],
    "Telephony_Omnichannel.jpg", "Calls, WhatsApp, Facebook, live chat, SMS and email connected in one system",
))

render_html(feature_row(
    "chart", "Contact centre", "A full contact centre, built in",
    "Call queues, smart routing, live statistics and supervisor tools come as standard, "
    "so busy teams never lose track of a caller.",
    ["Live queue panel and wallboard",
     "Skills-based and intelligent call routing",
     "Supervisor listen, whisper and barge"],
    "Telephony_Wallboard.jpg", "Live wallboard showing waiting calls, answer rates and agents available",
    flip=True,
))

render_html(feature_row(
    "users", "Collaboration", "Your whole team, connected",
    "Messaging, meetings, presence and content sharing sit alongside your calls, "
    "so everyone can see who's free and get answers faster.",
    ["Team chat and video meetings in one app",
     "See who's available at a glance",
     "Share screens and files during calls"],
    "Telephony_Collaboration.jpg", "Team directory showing each colleague's availability",
))

also = ["Call recording", "Voicemail to email", "CRM integrations", "Desktop and mobile apps",
        "Visual call-flow builder", "Keep your numbers"]
render_html('<div class="fx-also"><span class="l">Also included:</span>'
            + "".join(f'<span class="c">{a}</span>' for a in also) + "</div>")

render_html("""
<div id="range" class="fx-section" style="padding-bottom:0;margin-top:48px">
  <h2>The range</h2>
  <p class="intro" style="margin-bottom:0">Yealink and Fanvil handsets, supplied, set up and supported by us.</p>
</div>
""")

product_grid(PHONES, PHONE_CATEGORIES)

contact_band("Not sure which phone suits?",
             "Tell us how many people you have and how they work, and we'll suggest the right mix.",
             "Phone enquiry")
footer()
