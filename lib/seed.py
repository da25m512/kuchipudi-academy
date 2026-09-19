"""Default site content. Everything here is editable from the admin portal."""

SITE = {
    "academy_name": "Nrityanjali Kuchipudi Academy",
    "tagline": "Where devotion becomes dance",
    "hero_heading": "Learn Kuchipudi the way it was meant to be taught",
    "hero_sub": (
        "A classical Kuchipudi school rooted in the Andhra tradition — abhinaya, "
        "nritta and the joy of performing, taught step by patient step."
    ),
    "hero_cta": "Book a trial class",
    "guru_name": "Gayathri Varshitha",
    "guru_title": "Founder & Guru",
    "guru_instagram": "https://www.instagram.com/gayathri_varshitha",
    "guru_bio": (
        "Gayathri Varshitha is a Kuchipudi dancer and teacher trained in the "
        "classical Andhra tradition. She has performed across stages and temple "
        "festivals, and founded this academy to pass on the art form the way she "
        "received it — with discipline, devotion and a great deal of warmth.\n\n"
        "Her teaching balances the rigour of adavus and jathis with the "
        "storytelling heart of abhinaya, so that every student learns not only "
        "how to move, but why the movement means what it means."
    ),
    "about_story": (
        "Kuchipudi began in a small village of the same name in Andhra Pradesh, "
        "carried for centuries by families of dancer-actors who performed "
        "dance-dramas in temple courtyards. It is a form that speaks: quick, "
        "buoyant footwork, rounded lines, and a face that carries the whole story.\n\n"
        "This academy teaches that lineage faithfully — from the first namaskaram "
        "to full-length items — while keeping classes joyful and accessible for "
        "children and adults alike."
    ),
    "why_us": [
        {"icon": "ॐ", "title": "Authentic parampara",
         "text": "Traditional Kuchipudi repertoire taught in the guru-shishya way, item by item."},
        {"icon": "✧", "title": "Small batches",
         "text": "Capped class sizes so every student gets corrections, not just instructions."},
        {"icon": "♪", "title": "Live-quality music",
         "text": "Training with nattuvangam, jathis and Telugu keerthanas from day one."},
        {"icon": "⚑", "title": "Stage time",
         "text": "Annual arangetram track, festival shows and temple performances."},
    ],
    "phone": "+91 90000 00000",
    "email": "hello@nrityanjali.in",
    "address": "Studio address, City, India",
    "maps_url": "",
    "whatsapp": "",
    "youtube": "",
    "facebook": "",
    "instagram_embed_note": "Latest reels and performance clips from our Instagram",
    "footer_note": "Established with love for the art of Kuchipudi.",
    "primary_color": "#7B1E3C",
    "accent_color": "#C9A227",
    "announcement_banner": "",
    "show_fees_publicly": True,
    "registration_open": True,
}

BATCHES = [
    {"id": "batch_beginners", "name": "Beginners — Adavus", "level": "Beginner",
     "age_group": "5 years and above", "days": "Sat & Sun",
     "time": "9:00 AM – 10:30 AM", "mode": "In-studio", "seats": 15,
     "fee_monthly": 1500, "fee_quarterly": 4200,
     "description": "Namaskaram, the ten adavu families, basic hastas and taalam. The foundation everything else is built on.",
     "created_at": ""},
    {"id": "batch_intermediate", "name": "Intermediate — Jathiswaram & Abhinaya", "level": "Intermediate",
     "age_group": "8 years and above", "days": "Sat & Sun",
     "time": "11:00 AM – 12:30 PM", "mode": "In-studio", "seats": 12,
     "fee_monthly": 1800, "fee_quarterly": 5100,
     "description": "Jathiswaram, shabdam, navarasa abhinaya and the first taste of Telugu keerthanas.",
     "created_at": ""},
    {"id": "batch_advanced", "name": "Advanced — Repertoire & Tarangam", "level": "Advanced",
     "age_group": "By assessment", "days": "Wed & Sat",
     "time": "6:00 PM – 8:00 PM", "mode": "In-studio", "seats": 10,
     "fee_monthly": 2500, "fee_quarterly": 7000,
     "description": "Full items, Krishna Shabdam, Tarangam on the brass plate, and arangetram preparation.",
     "created_at": ""},
    {"id": "batch_online", "name": "Online Batch (Global)", "level": "All levels",
     "age_group": "6 years and above", "days": "Sun",
     "time": "7:00 PM – 8:30 PM IST", "mode": "Online",
     "seats": 20, "fee_monthly": 1200, "fee_quarterly": 3400,
     "description": "Live online classes for students outside the city, with recorded practice videos in the student portal.",
     "created_at": ""},
]

TESTIMONIALS = [
    {"id": "t1", "name": "Sowmya R.", "relation": "Parent of a beginner student",
     "quote": "My daughter walked in shy and walked out of her first show beaming. The corrections are patient and the discipline is real.",
     "published": True, "created_at": ""},
    {"id": "t2", "name": "Aditi K.", "relation": "Advanced batch",
     "quote": "Abhinaya finally clicked for me here. It stopped being about the face and started being about the story.",
     "published": True, "created_at": ""},
    {"id": "t3", "name": "Ravi Teja", "relation": "Parent",
     "quote": "Classes start on time, fees are transparent, and the annual production is genuinely beautiful.",
     "published": True, "created_at": ""},
]

EVENTS = [
    {"id": "e1", "title": "Annual Day — Nrityotsav", "date": "2026-12-14",
     "venue": "City Cultural Hall", "description": "Our yearly production featuring every batch, from first-year adavus to full Tarangam.",
     "image": "", "published": True, "created_at": ""},
    {"id": "e2", "title": "Temple Festival Performance", "date": "2026-10-22",
     "venue": "Sri Venkateswara Temple", "description": "Selected students perform Krishna Shabdam and Bhama Kalapam excerpts.",
     "image": "", "published": True, "created_at": ""},
]

VIDEOS = [
    {"id": "v1", "title": "Namaskaram — how we begin every class", "url": "",
     "kind": "youtube", "batch_id": "", "level": "Beginner", "public": True,
     "description": "The opening salutation, explained slowly.", "created_at": ""},
]

ANNOUNCEMENTS = [
    {"id": "a1", "title": "New online batch opens this month",
     "body": "Registrations are open for the Sunday evening online batch. Limited seats.",
     "audience": "all", "pinned": True, "created_at": ""},
]

ADAVU_NOTES = [
    ("Tatta adavu", "The very first strike. Feet flat, knees turned out, taalam counted aloud."),
    ("Natta adavu", "Stretch and reach — the line of the leg and the line of the arm agreeing."),
    ("Kuditta metta", "Heel and ball of the foot in conversation with the beat."),
    ("Jaaru adavu", "The glide that gives Kuchipudi its rounded, flowing signature."),
]
