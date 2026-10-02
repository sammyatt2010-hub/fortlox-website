"""CCTV page: introduction, advantages, technology + camera gallery (edit cameras in products.py)."""

import streamlit as st

from common import (contact_band, feature_row, footer, header, icon, product_grid,
                    render_html, setup, tech_cards)
from products import CAMERA_CATEGORIES, CAMERAS

setup()
header("cctv")

has_range = bool(CAMERAS)
cta = (f'<a class="fx-btn primary" href="#range">{icon("camera", 18)}See the cameras</a>' if has_range
       else f'<a class="fx-btn primary" href="#contact">{icon("mail", 18)}Book a site survey</a>')

render_html(f"""
<section class="fx-phero solo">
  <div>
    <div class="fx-tag">{icon('camera', 16)}CCTV and security</div>
    <h1>CCTV that sees clearly, day and night</h1>
    <p class="lede">Professional IP camera systems designed around your site, from a shop front to a farmyard
    or warehouse. Watch live and recorded footage on your phone, and get an alert when something happens.</p>
    <div class="fx-ctas">{cta}</div>
  </div>
</section>
""")

render_html(feature_row(
    "image", "Introduction", "Cameras for homes, shops and small businesses",
    "Our everyday camera range is the most popular choice for homes, small shops and offices: "
    "excellent picture quality at a sensible price, with larger and specialist cameras available "
    "when a site needs them.",
    ["Sharp, clear footage day and night",
     "Watch live and recorded video on your phone",
     "Specialist cameras for larger or higher-risk sites"],
    "CCTV_Intro_Street.jpg", "Quiet residential street at sunset",
))

render_html(feature_row(
    "zap", "Advantage", "Easy to install, simple to live with",
    "Every camera uses smart video compression, so recordings take up far less storage and bandwidth "
    "without losing detail. They're quick to fit and easy to maintain, making them the most "
    "cost-effective option for homes and small businesses.",
    ["Smart compression saves storage and bandwidth",
     "Quick, tidy installation",
     "Low maintenance once fitted"],
    "CCTV_Advantage_Shops.jpg", "Shopping street with shop fronts",
    flip=True,
))

render_html(f"""
<section class="fx-section">
  <h2>The technology inside</h2>
  <p class="intro">Built-in technology that keeps footage safe, sharp and easy to store.</p>
  {tech_cards([
      ("database", "Protected storage", "Recordings are stored safely and efficiently, so the footage is there when you need it."),
      ("image", "Clearer pictures", "Reduces blurring to give clear, bright and colourful images, even when things are moving."),
      ("cpu", "Smart compression", "Dramatically cuts the storage and bandwidth recordings need, without losing image detail."),
  ])}
</section>
""")

if has_range:
    render_html("""
    <div id="range" class="fx-section" style="padding-bottom:0">
      <h2>The range</h2>
      <p class="intro" style="margin-bottom:0">Every camera is supplied, installed and supported by our own team.</p>
    </div>
    """)
    product_grid(CAMERAS, CAMERA_CATEGORIES)

contact_band("Want to see what your site needs?",
             "We'll walk the site with you and show exactly where each camera should go.",
             "CCTV enquiry")
footer()
