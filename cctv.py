"""CCTV page: CCTV features + camera gallery (edit cameras in products.py)."""

import streamlit as st

from common import (CAM_TILE, CCTV_FEATURES, contact_band, feature_grid, footer,
                    header, icon, product_grid, render_html, setup)
from products import CAMERA_CATEGORIES, CAMERAS

setup()
header("cctv")

has_range = bool(CAMERAS)
range_btn = (f'<div class="fx-ctas"><a class="fx-btn primary" href="#range">{icon("camera", 18)}See the cameras</a></div>'
             if has_range else
             f'<div class="fx-ctas"><a class="fx-btn primary" href="#contact">{icon("mail", 18)}Book a site survey</a></div>')

render_html(f"""
<section class="fx-phero">
  <div>
    <div class="fx-tag">{icon('camera', 16)}CCTV and security</div>
    <h1>CCTV that sees clearly, day and night</h1>
    <p class="lede">Professional IP camera systems designed around your site, from a shop front to a farmyard
    or warehouse. Watch live and recorded footage on your phone, and get an alert when something happens.</p>
    {range_btn}
  </div>
  <div class="vis">{CAM_TILE}</div>
</section>

<section class="fx-section">
  <h2>What our camera systems do</h2>
  <p class="intro">Every system is designed for your site, then fitted and supported by our own team.</p>
  {feature_grid(CCTV_FEATURES, cols=3)}
</section>
""")

if has_range:
    render_html("""
    <div id="range" class="fx-section" style="padding-bottom:0">
      <h2>The range</h2>
      <p class="intro" style="margin-bottom:0">Cameras, recorders and accessories, supplied, installed and supported by us.</p>
    </div>
    """)
    product_grid(CAMERAS, CAMERA_CATEGORIES)

contact_band("Want to see what your site needs?",
             "We'll walk the site with you and show exactly where each camera should go.",
             "CCTV enquiry")
footer()
