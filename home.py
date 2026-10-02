"""Home page: hero, two doorways (phones / CCTV), how we work, contact."""

from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components

from common import (ADDRESS_LINES, CALL_POP, CAM_TILE, COMPANY, EMAIL, MAP_QUERY, PHONE_DISPLAY,
                    PHONE_LINK, STEPS, WEBSITE, b64_file, door_link, esc, find_asset, footer, header,
                    icon, photo, render_html, setup)

setup()
header("home")

EMBLEM = b64_file(find_asset("emblem.png", "logo.png"))

# ───────────────────────────── HERO ─────────────────────────────
render_html(f"""
<section class="fx-hero">
  <div>
    <div class="fx-where"><span class="dot"></span>Stinchcombe, Gloucestershire</div>
    <h1>Business phones and CCTV, fitted and looked after.</h1>
    <p class="lede">{COMPANY} supplies cloud telephone systems and professional camera systems to businesses,
    with one local team handling the survey, the installation and the support afterwards.</p>
    <div class="fx-ctas">
      <a class="fx-btn primary" href="tel:{PHONE_LINK}">{icon('phone', 18)}Call {PHONE_DISPLAY}</a>
      <a class="fx-btn ghost" href="#contact">{icon('mail', 18)}Send an enquiry</a>
    </div>
  </div>
  <div class="fx-stage">
    <div class="fx-emblem"><img src="data:image/png;base64,{EMBLEM}" alt="{esc(COMPANY)} emblem"></div>
  </div>
</section>
""")

# ───────────────────────────── DOORWAYS ─────────────────────────────
d1, d2 = st.columns(2, gap="medium")
with d1:
    with st.container(key="door-phones"):
        render_html(f"""
        <article class="fx-door">
          <div class="vis photo"><img src="{photo('Telephony_Omnichannel.jpg')}" alt="Calls, WhatsApp, Facebook, live chat, SMS and email connected in one system"></div>
          <div class="txt">
            <div class="fx-tag">{icon('phone', 16)}Telephony</div>
            <h2>Cloud phone systems</h2>
            <p>Keep your numbers and answer from desk phones, mobiles or laptops, with call recording,
            CRM links and contact-centre tools built in. Handsets from Yealink and Fanvil.</p>
          </div>
        </article>
        """)
        door_link("phones.py", "See phones and features")
with d2:
    with st.container(key="door-cctv"):
        render_html(f"""
        <article class="fx-door">
          <div class="vis photo"><img src="{photo('CCTV_Hero_Camera.jpg')}" alt="Security camera mounted on a building at night"></div>
          <div class="txt">
            <div class="fx-tag">{icon('camera', 16)}CCTV and security</div>
            <h2>Camera systems</h2>
            <p>Colour night vision, smart intruder detection, and footage you can search and watch from your phone,
            designed around your site.</p>
          </div>
        </article>
        """)
        door_link("cctv.py", "See CCTV and features")

# ───────────────────────────── HOW WE WORK ─────────────────────────────
steps_html = "".join(
    f'<div class="fx-step"><div class="n">{i:02d}</div><h4>{esc(t)}</h4><p>{esc(d)}</p></div>'
    for i, (t, d) in enumerate(STEPS, 1)
)
render_html(f"""
<section id="how-we-work" class="fx-section" style="margin-top:56px">
  <h2>How we work</h2>
  <p class="intro">The same team looks after you from the first visit onwards.</p>
  <div class="fx-steps">{steps_html}</div>
</section>
""")

# ───────────────────────────── CONTACT ─────────────────────────────
render_html("""
<div id="contact" class="fx-contact-head">
  <h2>Talk to us</h2>
  <p>Call, email or send a quick enquiry and we'll come back to you.</p>
</div>
""")

left, right = st.columns([1, 1.15], gap="large")

with left:
    address_html = "<br>".join(esc(l) for l in ADDRESS_LINES)
    render_html(f"""
    <div class="fx-details">
      <a class="fx-detail" href="tel:{PHONE_LINK}">{icon('phone')}<div><div class="l">Phone</div><div class="v">{PHONE_DISPLAY}</div></div></a>
      <a class="fx-detail" href="mailto:{EMAIL}">{icon('mail')}<div><div class="l">Email</div><div class="v">{EMAIL}</div></div></a>
      <div class="fx-detail">{icon('pin')}<div><div class="l">Address</div><div class="v">{address_html}</div></div></div>
      <a class="fx-detail" href="https://{WEBSITE}" target="_blank" rel="noopener">{icon('globe')}<div><div class="l">Website</div><div class="v">{WEBSITE}</div></div></a>
    </div>
    """)
    map_url = f"https://www.google.com/maps?q={quote(MAP_QUERY)}&z=14&output=embed"
    if hasattr(st, "iframe"):
        st.iframe(map_url, height=260)
    else:
        components.iframe(map_url, height=260)

with right:
    with st.container(key="card-enquiry"):
        render_html('<div class="fx-form-title">Quick enquiry</div>'
                    '<div class="fx-form-sub">Fill this in and your email app will open with the message ready to send.</div>')
        c1, c2 = st.columns(2)
        name = c1.text_input("Your name")
        business = c2.text_input("Business name")
        c3, c4 = st.columns(2)
        phone = c3.text_input("Phone number")
        interest = c4.selectbox("Interested in", ["Telephony", "CCTV", "Both"])
        message = st.text_area("How can we help?", height=120,
                               placeholder="e.g. 8 staff, moving office in March, need cameras on the yard")

        ready = bool(name.strip() and (phone.strip() or message.strip()))
        subject = f"Website enquiry: {interest}" + (f" - {business.strip()}" if business.strip() else "")
        body = "\n".join([
            f"Name: {name.strip()}",
            f"Business: {business.strip()}",
            f"Phone: {phone.strip()}",
            f"Interested in: {interest}",
            "",
            message.strip(),
        ])
        mailto_url = f"mailto:{EMAIL}?subject={quote(subject)}&body={quote(body)}"
        if ready:
            st.link_button("Open email to send", mailto_url, type="primary", use_container_width=True)
        else:
            st.link_button("Add your name and a phone number or message", f"mailto:{EMAIL}",
                           disabled=True, use_container_width=True)

footer()
