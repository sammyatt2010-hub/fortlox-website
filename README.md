# Fortlox Security website

Three-page Streamlit site: Home, Phones (/phones) and CCTV (/cctv).
Free to host on Streamlit Community Cloud. No secrets needed.

## Files (all can sit in the main repo folder)
- `app.py` – sets up the pages (main file on Streamlit Cloud)
- `home.py`, `phones.py`, `cctv.py` – the three pages
- `products.py` – the phone and camera lists. Edit this to add/remove products
- `common.py` – contact details, styling, header/footer
- `.streamlit/config.toml` – theme colours
- Images (`*.png`, `*.webp`) – any folder is fine; names must match products.py

## Adding a product
1. Upload the photo to GitHub.
2. In `products.py`, copy an existing product block, paste it, and change
   brand, name, image (the exact file name), category, desc and tags.
3. Commit. The site updates itself within a minute.
