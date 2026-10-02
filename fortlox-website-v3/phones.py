"""Phones page: telephony features + product gallery (edit products in products.py)."""

import streamlit as st

from common import (CALL_POP, TELEPHONY_FEATURES, contact_band, feature_grid, footer,
                    header, icon, product_grid, render_html, setup)
from products import PHONE_CATEGORIES, PHONES

setup()
header("phones")

render_html(f"""
<section class="fx-phero">
  <div>
    <div class="fx-tag">{icon('phone', 16)}Telephony</div>
    <h1>Phones and handsets for every desk</h1>
    <p class="lede">Every phone below works with our cloud phone system. You keep your existing numbers,
    and we'll recommend the right mix of desk phones, cordless handsets and headsets for how your team works.</p>
    <div class="fx-ctas"><a class="fx-btn primary" href="#range">{icon('devices', 18)}See the range</a></div>
  </div>
  <div class="vis">{CALL_POP}</div>
</section>

<section class="fx-section">
  <h2>What the phone system does</h2>
  <p class="intro">The phone is only half of it. Every handset connects to a cloud platform with these built in.</p>
  {feature_grid(TELEPHONY_FEATURES, cols=3)}
</section>

<div id="range" class="fx-section" style="padding-bottom:0">
  <h2>The range</h2>
  <p class="intro" style="margin-bottom:0">Yealink and Fanvil handsets, supplied, set up and supported by us.</p>
</div>
""")

product_grid(PHONES, PHONE_CATEGORIES)

contact_band("Not sure which phone suits?",
             "Tell us how many people you have and how they work, and we'll suggest the right mix.",
             "Phone enquiry")
footer()
