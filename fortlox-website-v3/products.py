"""
PRODUCT LISTS - edit this file to add, remove or reword products.

Each product is one block between { }:
  "brand":    shown as a small label on the card (leave "" to hide)
  "name":     product name
  "image":    the image file name exactly as it is in GitHub (any folder is fine)
  "category": which group it appears under (must match one of the CATEGORY lists)
  "desc":     one or two sentences
  "tags":     2-3 short highlights shown as chips

To add a product: copy a block, paste it below, change the details,
upload the image to GitHub, commit. Done.
"""

# ───────────────────────────── PHONES ─────────────────────────────
PHONE_CATEGORIES = [
    ("Desk phones", "From compact everyday handsets to 7-inch touchscreens for reception and management."),
    ("Cordless and Wi-Fi handsets", "Stay reachable anywhere in the building, from the office floor to the warehouse."),
    ("Headsets and accessories", "The extras that make every desk work properly."),
]

PHONES = [
    # --- Desk phones ---
    {
        "brand": "Yealink", "name": "T73W", "image": "Yealink_T73W.png", "category": "Desk phones",
        "desc": "A compact everyday desk phone with a clear colour screen and built-in Wi-Fi, so it can go anywhere, even without a network cable.",
        "tags": ['2.8" colour screen', "Wi-Fi 6", "Bluetooth"],
    },
    {
        "brand": "Yealink", "name": "T74W", "image": "Yealink_T74W.png", "category": "Desk phones",
        "desc": "A larger 4.3-inch colour screen with more line keys on show, for desks that handle more calls.",
        "tags": ['4.3" colour screen', "Wi-Fi 6", "Bluetooth"],
    },
    {
        "brand": "Fanvil", "name": "V62 Pro", "image": "Fanvil_V62_Pro.png", "category": "Desk phones",
        "desc": "An affordable desk phone with a cordless Bluetooth handset, so nobody is tied to the desk by a curly cable.",
        "tags": ["Cordless handset", '2.8" colour screen', "Gigabit network"],
    },
    {
        "brand": "Yealink", "name": "T85W", "image": "Yealink_T85W.png", "category": "Desk phones",
        "desc": "A tilting 5.5-inch screen and AI noise cancellation that keeps background chatter off your calls.",
        "tags": ['5.5" adjustable screen', "AI noise cancellation", "Wi-Fi 6"],
    },
    {
        "brand": "Yealink", "name": "T87W", "image": "Yealink_T87W.png", "category": "Desk phones",
        "desc": "A 7-inch touchscreen that works like a smartphone, ideal for managers and busy reception desks.",
        "tags": ['7" touchscreen', "Wi-Fi 6", "Bluetooth"],
    },
    {
        "brand": "Fanvil", "name": "V66 Pro", "image": "V66_Pro.webp", "category": "Desk phones",
        "desc": "A 7-inch rotating touchscreen, a cordless handset and an antimicrobial finish, made for shared desks.",
        "tags": ['7" rotating touchscreen', "Cordless handset", "Wi-Fi 6"],
    },
    {
        "brand": "Yealink", "name": "T88W Pro", "image": "Yealink_T88W_Pro.png", "category": "Desk phones",
        "desc": "The executive choice: a 7-inch Android touchscreen with a cordless handset that roams up to 10 metres from the desk mid-call.",
        "tags": ["Cordless handset", '7" Android touchscreen', "Wi-Fi 6"],
    },
    {
        "brand": "Fanvil", "name": "V67", "image": "Fanvil_V67.webp", "category": "Desk phones",
        "desc": "A flagship video phone with a 7-inch touchscreen and built-in camera for face-to-face calls from the desk.",
        "tags": ["Video calling", '7" touchscreen', "Dual-band Wi-Fi"],
    },

    # --- Cordless and Wi-Fi handsets ---
    {
        "brand": "Yealink", "name": "W74P", "image": "Yealink_W74P.png", "category": "Cordless and Wi-Fi handsets",
        "desc": "A classic cordless system: a base station plus a colour-screen handset, with more handsets added as the team grows.",
        "tags": ["DECT cordless", "Colour screen", "Expandable"],
    },
    {
        "brand": "Yealink", "name": "AX83H", "image": "Yealink_AX83H.png", "category": "Cordless and Wi-Fi handsets",
        "desc": "A pocket-sized handset that works straight off your Wi-Fi with no base station, roaming between access points.",
        "tags": ["No base station", '2.4" colour screen', "Bluetooth"],
    },
    {
        "brand": "Yealink", "name": "AX86R", "image": "Yealink_AX86R.png", "category": "Cordless and Wi-Fi handsets",
        "desc": "Built for warehouses, farms and kitchens: waterproof, dustproof and drop-tested, with push-to-talk and lone-worker alarms.",
        "tags": ["IP67 rugged", "Push-to-talk", "13h talk time"],
    },
    {
        "brand": "Linkvil", "name": "W620W", "image": "Linkvil_W620W_Rugged.png", "category": "Cordless and Wi-Fi handsets",
        "desc": "A tough, drop-resistant Wi-Fi handset with a push-to-talk button and a removable battery that lasts a full shift.",
        "tags": ["Drop-resistant", "Push-to-talk", "13h talk time"],
    },

    # --- Headsets and accessories ---
    {
        "brand": "Yealink", "name": "UH36 Mono headset", "image": "Yealink_UH36_Mono_Headset_UC.png", "category": "Headsets and accessories",
        "desc": "A comfortable single-ear headset that plugs into a desk phone or computer by USB or 3.5mm jack.",
        "tags": ["USB and 3.5mm", "Single ear", "Inline controls"],
    },
    {
        "brand": "Yealink", "name": "Power supply", "image": "Yealink_10W_PSU.png", "category": "Headsets and accessories",
        "desc": "UK mains adaptor for Yealink desk phones, for desks without a powered (PoE) network point.",
        "tags": ["UK plug", "For non-PoE desks"],
    },
]

# ───────────────────────────── CCTV ─────────────────────────────
# No brand shown on cameras (leave "brand" empty). Image files have had the
# manufacturer's logo removed, so use these files rather than the originals.
CAMERA_CATEGORIES = [
    ("Everyday cameras", "Domes, turrets and bullets for entrances, car parks, shop floors and yards."),
    ("Specialist cameras", "Wide-area, long-range and thermal cameras for larger or higher-risk sites."),
]

CAMERAS = [
    # --- Everyday cameras ---
    {
        "brand": "", "name": "4MP Vandal-Resistant Dome", "image": "CCTV_Dome_Vandal.png", "category": "Everyday cameras",
        "desc": "A tough, low-profile dome with a wide 2.8mm lens, ideal for receptions, corridors and anywhere it could be knocked or tampered with.",
        "tags": ["4MP", "Wide-angle view", "40m night vision"],
    },
    {
        "brand": "", "name": "5MP Turret with Audio", "image": "CCTV_Turret_Audio.png", "category": "Everyday cameras",
        "desc": "A compact turret with a wide view and a built-in microphone, so you hear what happened as well as see it.",
        "tags": ["5MP", "Built-in microphone", "Wide-angle view"],
    },
    {
        "brand": "", "name": "5MP Motorised Zoom Turret", "image": "CCTV_Turret_Motorised.png", "category": "Everyday cameras",
        "desc": "A remote-adjustable zoom lens lets us frame the view perfectly from a phone or laptop, with no ladder needed later.",
        "tags": ["5MP", "Motorised zoom", "40m night vision"],
    },
    {
        "brand": "", "name": "5MP Motorised Zoom Bullet", "image": "CCTV_Bullet_Motorised.png", "category": "Everyday cameras",
        "desc": "A highly visible bullet camera for gates, driveways and perimeters, zoomed in remotely to capture faces and number plates.",
        "tags": ["5MP", "Motorised zoom", "Long-range night vision"],
    },

    # --- Specialist cameras ---
    {
        "brand": "", "name": "360° Fisheye Camera", "image": "CCTV_Fisheye_360.png", "category": "Specialist cameras",
        "desc": "One 12MP camera covers a whole room with no blind spots, ideal for shops, open-plan offices and warehouses.",
        "tags": ["12MP", "360° view", "Two-way audio"],
    },
    {
        "brand": "", "name": "22x Zoom PTZ Camera", "image": "CCTV_PTZ_22x.png", "category": "Specialist cameras",
        "desc": "Pan, tilt and zoom across large sites like yards and car parks, picking out detail far into the distance, day or night.",
        "tags": ["22x optical zoom", "Pan and tilt", "Long-range night vision"],
    },
    {
        "brand": "", "name": "Thermal and Colour Turret", "image": "CCTV_Thermal_Turret.png", "category": "Specialist cameras",
        "desc": "Two cameras in one: a thermal sensor that spots people in total darkness and detects fire or overheating, plus a 4MP colour camera, with red and blue warning lights.",
        "tags": ["Thermal + 4MP colour", "Fire detection", "Warning lights"],
    },
]
