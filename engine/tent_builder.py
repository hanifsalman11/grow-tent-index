import os
import json
import re
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# ==========================================
# ENVIRONMENT CONFIGURATION
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://hanifsalman11.github.io/grow-tent-index").rstrip("/")
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7").strip()
CUSTOM_TENT = os.environ.get("CUSTOM_TENT", "").strip()
PAGES_PER_RUN = int(os.environ.get("PAGES_PER_RUN", "3"))

DOCS_DIR = "docs"
DATA_DIR = "data"
PUBLISHED_FILE = os.path.join(DATA_DIR, "published_tents.json")
MONETIZATION_FILE = os.path.join(DATA_DIR, "monetization.json")

# Format: (Setup / Model Name, Width Ft, Length Ft, Height Ft, LED Watts, Avg PPFD umol, Duct Size Inches)
SEED_TENTS = [
    ("4x4 Grow Tent (48x48x80) Complete Setup", 4.0, 4.0, 6.67, 650, 950, 6),
    ("2x4 Grow Tent (24x48x72) Complete Setup", 2.0, 4.0, 6.00, 320, 880, 4),
    ("5x5 Grow Tent (60x60x80) Complete Setup", 5.0, 5.0, 6.67, 850, 1020, 8),
    ("3x3 Grow Tent (36x36x72) Complete Setup", 3.0, 3.0, 6.00, 300, 860, 4),
    ("4x8 Grow Tent (48x96x80) Dual-Light Setup", 4.0, 8.0, 6.67, 1300, 980, 8),
    ("2x2 Compact Grow Tent (24x24x55) Setup", 2.0, 2.0, 4.58, 150, 780, 4),
    ("AC Infinity CLOUDLINE PRO T6 6-Inch Inline Fan System", 4.0, 4.0, 6.67, 650, 950, 6),
    ("AC Infinity CLOUDLINE PRO T4 4-Inch Inline Fan System", 2.0, 4.0, 6.00, 320, 850, 4),
    ("AC Infinity CLOUDLINE PRO T8 8-Inch Inline Fan System", 5.0, 5.0, 6.67, 1000, 1050, 8),
    ("Spider Farmer SE5000 480W Bar LED (4x4 Coverage)", 4.0, 4.0, 6.67, 480, 920, 6),
    ("Spider Farmer SE7000 730W Commercial LED (5x5)", 5.0, 5.0, 6.67, 730, 1050, 8),
    ("Spider Farmer G3000 300W Bar LED (3x3 Coverage)", 3.0, 3.0, 6.00, 300, 870, 4),
    ("Spider Farmer SF2000 Pro 200W EVO LED (2x4)", 2.0, 4.0, 6.00, 200, 810, 4),
    ("Mars Hydro FC-E4800 480W BridgeLux Bar LED (4x4)", 4.0, 4.0, 6.67, 480, 910, 6),
    ("Mars Hydro FC-E6500 730W Bar LED (5x5 Coverage)", 5.0, 5.0, 6.67, 730, 1040, 8),
    ("Mars Hydro FC-3000 EVO 300W Samsung LED (3x3)", 3.0, 3.0, 6.00, 300, 880, 4),
    ("Mars Hydro TSL-2000 300W Rectangular LED (2x4)", 2.0, 4.0, 6.00, 300, 860, 4),
    ("VIVOSUN AeroLight Wing AW400SE 400W Tunable LED", 4.0, 4.0, 6.67, 400, 890, 6),
    ("VIVOSUN AeroZesh G6 6-Inch Smart Ventilation Kit", 4.0, 4.0, 6.67, 600, 920, 6),
    ("HLG Scorpion Diablo X 700W Quantum Board LED", 5.0, 5.0, 6.67, 700, 1120, 8),
    ("HLG Blackwing 225W USA Quantum Board (2x4)", 2.0, 4.0, 6.00, 225, 830, 4),
    ("Medic Grow Fold-8 760W Full-Spectrum Bar LED (5x5)", 5.0, 5.0, 6.67, 760, 1030, 8),
    ("Medic Grow Mini Sun-2 320W Bar LED (3x3 / 2x4)", 3.0, 3.0, 6.00, 320, 890, 4),
    ("Gorilla Grow Tent 4x4 Pro (84-Inch Height Extension)", 4.0, 4.0, 7.00, 680, 980, 6),
    ("Gorilla Grow Tent 5x5 Pro (84-Inch Height Extension)", 5.0, 5.0, 7.00, 880, 1060, 8),
    ("AC Infinity IONFRAME EVO6 500W Samsung LM301H EVO", 4.0, 4.0, 6.67, 500, 960, 6),
    ("AC Infinity IONFRAME EVO8 730W Bar LED (5x5)", 5.0, 5.0, 6.67, 730, 1080, 8),
    ("AC Infinity IONFRAME EVO3 280W Bar LED (2x4)", 2.0, 4.0, 6.00, 280, 890, 4),
    ("8x8 Walk-In Indoor Grow Room (96x96x80) Setup", 8.0, 8.0, 6.67, 2600, 1020, 10),
    ("3x5 Closet & Utility Grow Tent (36x60x80) Setup", 3.0, 5.0, 6.67, 500, 910, 6)
]


def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Could not parse {filepath}: {e}")
    return default


def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    return re.sub(r"[\s-]+", "-", text).strip("-")


def safe_float(val, default=4.0):
    try:
        cleaned = re.sub(r"[^0-9.]", "", str(val))
        return float(cleaned) if cleaned else float(default)
    except Exception:
        return float(default)


def build_amazon_url(search_keywords, mon_cfg):
    domain = mon_cfg.get("marketplace_domain", "www.amazon.com")
    tag = mon_cfg.get("amazon_associate_tag", "YOUR_AMAZON_TAG-20")
    encoded_q = urllib.parse.quote_plus(search_keywords)
    return f"https://{domain}/s?k={encoded_q}&tag={tag}"


def discover_google_tent_queries():
    """Mengambil kueri kalkulator CFM tenda tanam & lampu LED dari Google Autocomplete US."""
    discovered = []
    seeds = [
        "what size inline fan for ",
        "ac infinity cloudline ",
        "spider farmer ",
        "mars hydro ",
        "how many watts for grow tent "
    ]
    for seed in seeds:
        try:
            url = f"http://suggestqueries.google.com/complete/search?client=firefox&hl=en&gl=us&q={urllib.parse.quote(seed)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for suggestion in data[1]:
                    cleaned = suggestion.lower()
                    for pref in seeds:
                        if "what size" in pref or "how many" in pref:
                            cleaned = cleaned.replace(pref, "")
                    cleaned = re.sub(
                        r"\b(calculator|size|sizing|cfm|setup|review|reddit|for)\b",
                        "",
                        cleaned
                    ).strip()
                    if 5 <= len(cleaned) <= 42:
                        dim_match = re.search(r"([23458])x([23458])", cleaned)
                        w_f = float(dim_match.group(1)) if dim_match else 4.0
                        l_f = float(dim_match.group(2)) if dim_match else 4.0
                        watts_est = int(round(w_f * l_f * 38.0, -1))
                        duct_in = 4 if (w_f * l_f) <= 10 else (6 if (w_f * l_f) <= 20 else 8)
                        discovered.append((cleaned.title(), w_f, l_f, 6.67, watts_est, 920, duct_in))
        except Exception as e:
            print(f"[WARN] Google Suggest notice: {e}")
    return discovered


def build_deterministic_tent_data(tent_tuple):
    """Mesin Fisika Aerodinamika Ventilasi CFM & Fotobiologi PPFD/DLI (100% bebas gagal)."""
    setup_name, w_ft, l_ft, h_ft, led_watts, avg_ppfd, duct_in = tent_tuple

    area_sqft = round(w_ft * l_ft, 1)
    volume_cuft = round(area_sqft * h_ft, 1)

    # Rumus CFM Exhaust: Volume Cu Ft x 1 pertukaran/menit x 1.55 (Carbon Filter 35% + Duct Bend 10% + LED Heat 10%)
    min_active_cfm = int(round(volume_cuft * 1.55))
    # Target fan rating agar kipas bisa berputar tenang di kecepatan 50%-60% (Quiet Headroom)
    recommended_fan_cfm = max(195, int(round(min_active_cfm * 1.65, -1)))

    # Rumus DLI (Daily Light Integral mol/m2/day) pada siklus 18 jam (Veg/Autoflower) dan 12 jam (Flowering)
    dli_18hr = round(avg_ppfd * 18.0 * 0.0036, 1)
    dli_12hr = round(avg_ppfd * 12.0 * 0.0036, 1)

    # Estimasi biaya listrik bulanan (LED + 45W Inline Fan + 25W Canopy Clip Fans) @ 18 jam/hari & $0.16/kWh
    total_draw_w = led_watts + 70
    monthly_kwh = int(round((total_draw_w * 18.0 * 30.0) / 1000.0))
    monthly_cost_usd = round(monthly_kwh * 0.16, 2)

    return {
        "setup_name": setup_name,
        "seo_title": f"{setup_name} CFM Fan, LED Wattage, PPFD/DLI & Cost Calculator (2026)",
        "meta_description": f"Calculate exact inline exhaust fan CFM ({min_active_cfm}–{recommended_fan_cfm} CFM w/ carbon filter), LED wattage ({led_watts}W), DLI ({dli_12hr}–{dli_18hr} mol/d), and power bill (${monthly_cost_usd}/mo) for {setup_name}.",
        "specs": {
            "width_ft": w_ft,
            "length_ft": l_ft,
            "height_ft": h_ft,
            "canopy_sqft": area_sqft,
            "tent_volume_cuft": volume_cuft,
            "led_watts": led_watts,
            "avg_ppfd_umol": avg_ppfd,
            "dli_12hr_mol": dli_12hr,
            "dli_18hr_mol": dli_18hr,
            "min_filtered_cfm": min_active_cfm,
            "recommended_fan_cfm": recommended_fan_cfm,
            "duct_size_inches": duct_in,
            "monthly_cost_usd": monthly_cost_usd
        },
        "cea_verdict": f"Enclosing {area_sqft} sq. ft. of canopy ({volume_cuft} cu. ft. volume), the {setup_name} requires {min_active_cfm} CFM of net airflow to exchange all air once every 60 seconds through a carbon filter and duct bends (best served by a {duct_in}-inch {recommended_fan_cfm}+ CFM EC-motor inline fan running quietly at 55% speed). Paired with a {led_watts}W full-spectrum bar LED (~{avg_ppfd} μmol/m²/s PPFD), it delivers {dli_12hr} mol/m²/day DLI on a 12/12 cycle and costs ~${monthly_cost_usd}/month in electricity.",
        "hardware_bundle": [
            {
                "badge": f"{led_watts}W Bar LED Light",
                "title": f"{led_watts}W Full-Spectrum Samsung LM301H EVO Bar LED Grow Light ({int(w_ft)}x{int(l_ft)} Coverage)",
                "price_range": "$219 - $699",
                "amazon_query": f"{led_watts}W Samsung LM301H EVO Bar LED Grow Light {int(w_ft)}x{int(l_ft)}",
                "grow_note": f"Delivers uniform {avg_ppfd} μmol/m²/s canopy PPFD at 2.9+ μmol/J PPE efficiency with detachable external driver."
            },
            {
                "badge": f"{duct_in}-Inch EC Fan & Filter",
                "title": f"{duct_in}-Inch Smart EC-Motor Inline Duct Fan ({recommended_fan_cfm} CFM) + Australian Charcoal Carbon Filter & VPD Controller",
                "price_range": "$149 - $329",
                "amazon_query": f"AC Infinity {duct_in} Inch Inline Fan Carbon Filter Combo VPD Controller",
                "grow_note": f"Overcomes 35%+ carbon filter static pressure while maintaining negative tent pressure for 100% odor containment."
            },
            {
                "badge": f"{int(w_ft)}x{int(l_ft)} 2000D Mylar Tent",
                "title": f"{int(w_ft)}x{int(l_ft)} Heavy-Duty 2000D Diamond Mylar Indoor Grow Tent (1-Inch Steel Poles)",
                "price_range": "$99 - $289",
                "amazon_query": f"{int(w_ft)}x{int(l_ft)} 2000D Mylar Grow Tent Heavy Duty",
                "grow_note": f"Provides {volume_cuft} cu. ft. of light-proof environment with double-cinched {duct_in}\" duct ports and waterproof floor tray."
            },
            {
                "badge": "PAR Meter & Canopy Fans",
                "title": "Full-Spectrum Quantum PAR/PPFD Sensor Meter + 6-Inch Auto-Oscillating Pole Clip Fan",
                "price_range": "$59 - $159",
                "amazon_query": "Quantum PAR Meter PPFD Tester Grow Tent Oscillating Clip Fan",
                "grow_note": "Verifies exact canopy μmol/m²/s intensity and prevents micro-climate humidity pockets under dense foliage."
            }
        ],
        "vpd_checklist": [
            f"Maintain slight negative air pressure (tent walls gently pulled inward) by running your {duct_in}-inch exhaust fan at least {min_active_cfm} CFM through the carbon filter so zero odor escapes through zipper seams.",
            f"Dial in Vapor Pressure Deficit (VPD): target 0.8–1.1 kPa during vegetative growth and 1.2–1.5 kPa during flowering using a smart thermo-hygrometer fan controller.",
            f"Adjust your {led_watts}W LED dimmer and hanging height (12\"–18\" above canopy) to hit 25–35 mol/m²/day DLI in vegetative stage and 40–50 mol/m²/day DLI in flowering without light-bleaching top colas.",
            "Mount the carbon filter and inline exhaust fan at the highest ceiling crossbars of the tent to evacuate rising LED driver heat while drawing cool passive intake air through lower mesh vents."
        ],
        "faqs": [
            {
                "q": f"What size inline exhaust fan and carbon filter do I need for {setup_name}?",
                "a": f"With {volume_cuft} cubic feet of internal volume, adding a carbon filter (+35% resistance), ducting bends (+10%), and LED heat load (+10%) requires {min_active_cfm} CFM of active airflow. Install a {duct_in}-inch inline fan rated for {recommended_fan_cfm}+ CFM so you can run it quietly at 50%–60% speed."
            },
            {
                "q": f"How many true LED watts are needed for a {int(w_ft)}x{int(l_ft)} ({area_sqft} sq ft) grow tent?",
                "a": f"Using modern high-efficiency Samsung LM301H EVO diodes (2.8–3.1 μmol/J), target 35 to 42 watts per square foot for high-yield flowering. For {area_sqft} sq. ft., a {led_watts}W bar-style LED provides optimal edge-to-edge PPFD uniformity."
            },
            {
                "q": f"How much does {setup_name} add to my monthly electric bill?",
                "a": f"Running a {led_watts}W LED plus 70W of inline and oscillating fans for 18 hours/day consumes {monthly_kwh} kWh per month (~${monthly_cost_usd}/month at the $0.16/kWh US average rate). On a 12-hour flowering schedule, cost drops to ~${round(monthly_cost_usd * 0.67, 2)}/month."
            }
        ]
    }


def generate_tent_data(tent_tuple):
    """Memanggil Gemini 2.5 Flash API; jika gagal otomatis memakai Deterministic Photobiology & CFM Engine."""
    if not GEMINI_API_KEY:
        return build_deterministic_tent_data(tent_tuple)

    setup_name, w_ft, l_ft, h_ft, led_watts, avg_ppfd, duct_in = tent_tuple
    area_sqft = round(w_ft * l_ft, 1)
    volume_cuft = round(area_sqft * h_ft, 1)
    min_cfm = int(round(volume_cuft * 1.55))
    rec_fan_cfm = max(195, int(round(min_cfm * 1.65, -1)))
    dli_12 = round(avg_ppfd * 12.0 * 0.0036, 1)
    dli_18 = round(avg_ppfd * 18.0 * 0.0036, 1)
    monthly_cost = round(((led_watts + 70) * 18.0 * 30.0 / 1000.0) * 0.16, 2)

    prompt = f"""
You are a Controlled Environment Agriculture (CEA) Horticultural Lighting & HVAC Ventilation Engineer. Create an accurate 2026 inline fan CFM, carbon filter static pressure, LED PPFD/DLI, and electricity cost guide for: "{setup_name}".
Baseline reference specs: Dimensions={w_ft}x{l_ft}x{h_ft} ft ({area_sqft} sq ft, {volume_cuft} cu ft), LED={led_watts}W ({avg_ppfd} umol/m2/s PPFD, DLI={dli_12}-{dli_18} mol/d), Min Filtered Airflow={min_cfm} CFM, Recommended Fan={rec_fan_cfm} CFM ({duct_in}-Inch Duct), Est Power Bill=${monthly_cost}/mo.
Return ONLY a valid JSON object matching this exact schema:
{{
  "setup_name": "{setup_name}",
  "seo_title": "{setup_name} CFM Fan, LED Wattage, PPFD/DLI & Cost Calculator (2026)",
  "meta_description": "Calculate exact inline exhaust fan CFM with carbon filter, true LED wattage, PPFD to DLI, and monthly electricity cost for {setup_name}.",
  "specs": {{
    "width_ft": {w_ft},
    "length_ft": {l_ft},
    "height_ft": {h_ft},
    "canopy_sqft": {area_sqft},
    "tent_volume_cuft": {volume_cuft},
    "led_watts": {led_watts},
    "avg_ppfd_umol": {avg_ppfd},
    "dli_12hr_mol": {dli_12},
    "dli_18hr_mol": {dli_18},
    "min_filtered_cfm": {min_cfm},
    "recommended_fan_cfm": {rec_fan_cfm},
    "duct_size_inches": {duct_in},
    "monthly_cost_usd": {monthly_cost}
  }},
  "cea_verdict": "3-sentence technical summary stating tent cubic feet, required CFM with carbon filter static pressure, true LED wattage, DLI output, and monthly kWh cost.",
  "hardware_bundle": [
    {{
      "badge": "Full-Spectrum Bar LED",
      "title": "Exact {led_watts}W Samsung LM301H EVO Bar LED Grow Light recommendation",
      "price_range": "$219 - $699",
      "amazon_query": "{led_watts}W Samsung LM301H EVO LED Grow Light",
      "grow_note": "1-sentence PPFD uniformity and PPE efficiency note"
    }},
    {{
      "badge": "{duct_in}-Inch EC Fan & Filter",
      "title": "{duct_in}-Inch Smart EC Inline Fan ({rec_fan_cfm} CFM) + Charcoal Carbon Filter Combo",
      "price_range": "$149 - $329",
      "amazon_query": "AC Infinity {duct_in} Inch Inline Fan Carbon Filter Combo",
      "grow_note": "1-sentence negative pressure and VPD automation note"
    }},
    {{
      "badge": "{int(w_ft)}x{int(l_ft)} 2000D Grow Tent",
      "title": "{int(w_ft)}x{int(l_ft)} Heavy-Duty 2000D Mylar Reflective Indoor Grow Tent",
      "price_range": "$99 - $289",
      "amazon_query": "{int(w_ft)}x{int(l_ft)} 2000D Mylar Grow Tent",
      "grow_note": "1-sentence steel frame and light-proof zipper note"
    }},
    {{
      "badge": "PAR Meter & Clip Fan",
      "title": "Quantum PAR/PPFD Light Meter + Auto-Oscillating Pole Clip Canopy Fan",
      "price_range": "$59 - $159",
      "amazon_query": "Quantum PAR Meter Grow Tent Oscillating Clip Fan",
      "grow_note": "1-sentence canopy airflow and DLI calibration note"
    }}
  ],
  "vpd_checklist": [
    "Step 1 regarding negative tent pressure and carbon filter static loss",
    "Step 2 regarding VPD kPa targets for veg vs flower",
    "Step 3 regarding PPFD and DLI mol/m2/day dimming targets",
    "Step 4 regarding top-mounted exhaust and bottom passive intake vents"
  ],
  "faqs": [
    {{"q": "What size inline fan and carbon filter do I need for {setup_name}?", "a": "Exact cubic feet, static pressure multiplier, and recommended fan CFM."}},
    {{"q": "How many LED watts and PPFD are needed for {setup_name}?", "a": "Exact true watts per sq ft and target PPFD/DLI numbers."}},
    {{"q": "How much electricity does {setup_name} use per month?", "a": "Exact kWh and dollar cost for 18/6 and 12/12 light schedules."}}
  ]
}}
"""

    for model_id in ["gemini-2.5-flash", "gemini-2.0-flash"]:
        try:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json"
                }
            }
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=35) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)
                parsed = json.loads(raw_text)
                if "specs" in parsed and "hardware_bundle" in parsed:
                    return parsed
        except Exception as e:
            print(f"[WARN] Gemini ({model_id}) notice for '{setup_name}': {e}")

    return build_deterministic_tent_data(tent_tuple)


def build_tent_html_page(data, slug, mon_cfg):
    setup_name = data.get("setup_name", "Indoor Grow Tent Setup")
    sp = data.get("specs", {})
    w_ft = round(safe_float(sp.get("width_ft", 4.0), 4.0), 1)
    l_ft = round(safe_float(sp.get("length_ft", 4.0), 4.0), 1)
    h_ft = round(safe_float(sp.get("height_ft", 6.67), 6.67), 2)
    area_sqft = round(safe_float(sp.get("canopy_sqft", w_ft * l_ft), 16.0), 1)
    vol_cuft = round(safe_float(sp.get("tent_volume_cuft", area_sqft * h_ft), 106.7), 1)
    led_watts = int(safe_float(sp.get("led_watts", 650), 650))
    avg_ppfd = int(safe_float(sp.get("avg_ppfd_umol", 950), 950))
    dli_12 = round(safe_float(sp.get("dli_12hr_mol", 41.0), 41.0), 1)
    min_cfm = int(safe_float(sp.get("min_filtered_cfm", 165), 165))
    rec_fan_cfm = int(safe_float(sp.get("recommended_fan_cfm", 350), 350))
    duct_in = int(safe_float(sp.get("duct_size_inches", 6), 6))
    mo_cost = round(safe_float(sp.get("monthly_cost_usd", 62.0), 62.0), 2)

    header_cta = mon_cfg.get("header_cta", {})
    header_cta_url = build_amazon_url(header_cta.get("search_query", "Samsung+LM301H+EVO+LED+Grow+Light+Inline+Fan"), mon_cfg)

    schema_graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "SoftwareApplication",
                "name": f"{setup_name} CFM Ventilation & PPFD/DLI Calculator",
                "applicationCategory": "UtilitiesApplication",
                "operatingSystem": "Web Browser",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f.get("q", ""),
                        "acceptedAnswer": {"@type": "Answer", "text": f.get("a", "")}
                    } for f in data.get("faqs", [])
                ]
            }
        ]
    }

    bundle_html = ""
    for item in data.get("hardware_bundle", []):
        amz_url = build_amazon_url(item.get("amazon_query", item.get("title", "LED Grow Light")), mon_cfg)
        bundle_html += f"""
        <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex flex-col justify-between hover:border-green-500/60 transition">
          <div>
            <div class="flex items-center justify-between gap-2 mb-2">
              <span class="text-xs font-bold uppercase tracking-wider bg-green-500/10 text-green-400 border border-green-500/20 px-2.5 py-0.5 rounded">{item.get('badge', 'CEA Gear')}</span>
              <span class="text-sm font-bold text-emerald-400">{item.get('price_range', '$99+')}</span>
            </div>
            <h3 class="text-base font-bold text-white mt-2">{item.get('title', '')}</h3>
            <p class="text-xs text-zinc-400 mt-2 leading-relaxed">🌱 {item.get('grow_note', '')}</p>
          </div>
          <a href="{amz_url}" target="_blank" rel="nofollow sponsored" class="mt-5 block text-center bg-green-500 hover:bg-green-400 text-zinc-950 font-extrabold py-2.5 px-4 rounded-lg text-sm transition shadow-lg">
            Check Price on Amazon →
          </a>
        </div>"""

    # Build Standard Grow Tent Size Reference Matrix Table
    tent_tiers = [
        ("2x2 Tent (4 Sq Ft / 18 ft³)", "150W LED", "4\" Fan (195+ CFM Rated)", "30–50 CFM Active", "~$18 / mo"),
        ("2x4 Tent (8 Sq Ft / 48 ft³)", "300W–320W LED", "4\" or 6\" Fan (205–350 CFM)", "75–110 CFM Active", "~$33 / mo"),
        ("3x3 Tent (9 Sq Ft / 54 ft³)", "300W Bar LED", "4\" or 6\" Fan (205–350 CFM)", "85–125 CFM Active", "~$33 / mo"),
        ("4x4 Tent (16 Sq Ft / 107 ft³)", "500W–650W Bar LED", "6\" EC Fan (402 CFM Rated)", "165–240 CFM Active", "~$58 / mo"),
        ("5x5 Tent (25 Sq Ft / 167 ft³)", "730W–850W Bar LED", "8\" EC Fan (740 CFM Rated)", "260–380 CFM Active", "~$78 / mo"),
        ("4x8 Tent (32 Sq Ft / 213 ft³)", "2x 600W (1200W LED)", "8\" EC Fan (740+ CFM Rated)", "330–490 CFM Active", "~$112 / mo")
    ]
    matrix_rows_html = ""
    for sz_s, led_s, fan_s, act_s, cost_s in tent_tiers:
        matrix_rows_html += f"""
        <tr class="border-b border-zinc-800 hover:bg-zinc-800/40">
          <td class="py-3 px-4 font-bold text-white">{sz_s}</td>
          <td class="py-3 px-4 font-bold text-green-400">{led_s}</td>
          <td class="py-3 px-4 text-emerald-400 font-semibold">{fan_s}</td>
          <td class="py-3 px-4 text-zinc-300">{act_s}</td>
          <td class="py-3 px-4 text-xs text-zinc-400">{cost_s} (@$0.16/kWh)</td>
        </tr>"""

    checklist_html = ""
    for idx, step_text in enumerate(data.get("vpd_checklist", []), start=1):
        checklist_html += f"""
        <label class="flex items-start gap-3.5 bg-zinc-900 border border-zinc-800 rounded-xl p-4 cursor-pointer hover:border-zinc-700 transition">
          <input type="checkbox" class="mt-1 w-5 h-5 accent-green-500 rounded cursor-pointer tent-check">
          <span class="text-sm text-zinc-200 leading-relaxed"><strong>CEA Step {idx}:</strong> {step_text}</span>
        </label>"""

    faqs_html = "".join([
        f"<div class='bg-zinc-900 border border-zinc-800 rounded-xl p-5'><h3 class='font-bold text-white text-base mb-2'>{f.get('q', '')}</h3><p class='text-sm text-zinc-300 leading-relaxed'>{f.get('a', '')}</p></div>"
        for f in data.get("faqs", [])
    ])

    canonical_url = f"{SITE_BASE_URL}/{slug}.html"
    amz_domain = mon_cfg.get("marketplace_domain", "www.amazon.com")
    amz_tag = mon_cfg.get("amazon_associate_tag", "YOUR_AMAZON_TAG-20")

    html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{data.get('seo_title', setup_name)}</title>
  <meta name="description" content="{data.get('meta_description', '')}">
  <link rel="canonical" href="{canonical_url}">
  <meta property="og:title" content="{data.get('seo_title', setup_name)}">
  <meta property="og:description" content="{data.get('meta_description', '')}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical_url}">
  <script src="https://cdn.tailwindcss.com"></script>
  <script type="application/ld+json">{json.dumps(schema_graph)}</script>
</head>
<body class="bg-zinc-950 text-zinc-100 antialiased min-h-screen flex flex-col">
  <header class="border-b border-zinc-800 bg-zinc-900/80 backdrop-blur sticky top-0 z-30">
    <div class="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between">
      <a href="index.html" class="text-lg font-black tracking-tight text-white flex items-center gap-2">
        <span class="bg-green-500 text-zinc-950 px-2 py-0.5 rounded font-black">GROW</span>TentIndex
      </a>
      <a href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="text-xs sm:text-sm bg-green-500 hover:bg-green-400 text-zinc-950 font-extrabold px-3.5 py-2 rounded-lg transition">
        {header_cta.get('cta_text', 'Shop LED Grow Lights & Fans →')}
      </a>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-4 py-10 flex-1 w-full">
    <div class="mb-8">
      <div class="flex flex-wrap items-center gap-2.5 mb-3">
        <span class="text-xs font-extrabold uppercase tracking-widest bg-green-500 text-zinc-950 px-3 py-1 rounded-full">{area_sqft} Sq Ft ({vol_cuft} Cu Ft)</span>
        <span class="text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded-full">LED: {led_watts}W ({avg_ppfd} PPFD)</span>
        <span class="text-xs font-semibold bg-zinc-800 text-zinc-300 px-3 py-1 rounded-full">{duct_in}" Fan: {rec_fan_cfm} CFM | ~${mo_cost}/mo</span>
      </div>
      <h1 class="text-3xl sm:text-4xl font-black text-white leading-tight">{data.get('seo_title', setup_name)}</h1>
      <div class="mt-4 bg-zinc-900 border-l-4 border-green-500 p-4 rounded-r-xl text-sm text-zinc-200 leading-relaxed">
        <strong>CEA Photobiology & Airflow Verdict:</strong> {data.get('cea_verdict', '')}
      </div>
    </div>

    <!-- INTERACTIVE EXHAUST CFM, PPFD/DLI & ELECTRICITY BILL CALCULATOR -->
    <section class="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 sm:p-8 mb-12 shadow-2xl">
      <h2 class="text-xl font-extrabold text-white mb-2">Interactive {setup_name} CFM, DLI & Power Cost Calculator</h2>
      <p class="text-xs text-zinc-400 mb-6">Adjust your tent footprint, filtration static resistance, LED wattage/PPFD, and daily photoperiod hours to compute required inline fan CFM, Daily Light Integral (DLI), and monthly electric bill.</p>

      <div class="grid md:grid-cols-2 gap-8 items-center">
        <div class="space-y-5">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label for="tentSizeSelect" class="block text-xs font-medium text-zinc-400 mb-1">Grow Tent Footprint & Volume</label>
              <select id="tentSizeSelect" class="w-full bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-green-500">
                <option value="4|18" {"selected" if area_sqft <= 5 else ""}>2x2 ft (4 sq ft / 18 cu ft)</option>
                <option value="8|48" {"selected" if 5 < area_sqft <= 8.5 else ""}>2x4 ft (8 sq ft / 48 cu ft)</option>
                <option value="9|54" {"selected" if 8.5 < area_sqft <= 11 else ""}>3x3 ft (9 sq ft / 54 cu ft)</option>
                <option value="16|107" {"selected" if 11 < area_sqft <= 20 else ""}>4x4 ft (16 sq ft / 107 cu ft)</option>
                <option value="25|167" {"selected" if 20 < area_sqft <= 28 else ""}>5x5 ft (25 sq ft / 167 cu ft)</option>
                <option value="32|213" {"selected" if area_sqft > 28 else ""}>4x8 ft (32 sq ft / 213 cu ft)</option>
              </select>
            </div>
            <div>
              <label for="filterSelect" class="block text-xs font-medium text-zinc-400 mb-1">Static Pressure Resistance</label>
              <select id="filterSelect" class="w-full bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-green-500">
                <option value="1.25">No Carbon Filter (Duct Only +25%)</option>
                <option value="1.55" selected>Carbon Filter + 1 Bend (+55%)</option>
                <option value="1.80">Carbon Filter + Long Run (+80%)</option>
              </select>
            </div>
          </div>

          <div>
            <div class="flex justify-between text-sm font-medium mb-1.5">
              <label for="ppfdSlider" class="text-zinc-300">Canopy Average PPFD Intensity (μmol/m²/s)</label>
              <span class="text-green-400 font-bold"><span id="ppfdVal">{avg_ppfd}</span> μmol/m²/s</span>
            </div>
            <input id="ppfdSlider" type="range" min="300" max="1500" step="25" value="{avg_ppfd}" class="w-full accent-green-500 cursor-pointer">
          </div>

          <div>
            <div class="flex justify-between text-sm font-medium mb-1.5">
              <label for="photoSlider" class="text-zinc-300">Daily Light Schedule (12h Flower / 18h Veg / 20h Auto)</label>
              <span class="text-green-400 font-bold"><span id="photoVal">18</span> hrs/day</span>
            </div>
            <input id="photoSlider" type="range" min="12" max="24" step="2" value="18" class="w-full accent-green-500 cursor-pointer">
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="bg-zinc-950 border border-green-500/30 rounded-xl p-4">
            <span class="text-xs uppercase text-green-400 font-bold">Required Inline Fan</span>
            <div id="cfmOut" class="text-xl sm:text-2xl font-black text-white mt-1">{rec_fan_cfm} CFM</div>
            <p id="ductNoteOut" class="text-xs text-green-400 font-semibold mt-1">{duct_in}" Fan (Min {min_cfm} Active CFM)</p>
          </div>

          <div class="bg-zinc-950 border border-emerald-500/30 rounded-xl p-4">
            <span class="text-xs uppercase text-emerald-400 font-bold">DLI & Monthly Power</span>
            <div id="dliOut" class="text-xl sm:text-2xl font-black text-emerald-400 mt-1">{dli_12} <span class="text-xs font-normal text-zinc-400">mol/d</span></div>
            <p id="billOut" class="text-xs text-zinc-300 font-semibold mt-1">Bill: ~${mo_cost}/mo ({led_watts}W LED)</p>
          </div>
        </div>
      </div>

      <div class="mt-6 bg-green-950/40 border border-green-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div id="tentAdviceBanner" class="text-sm text-green-100 font-medium"></div>
        <a id="dynamicTentBtn" href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="shrink-0 bg-green-500 hover:bg-green-400 text-zinc-950 font-extrabold px-4 py-2.5 rounded-lg text-xs uppercase tracking-wider transition">
          Shop Matched LED & Fan Kit on Amazon →
        </a>
      </div>
    </section>

    <!-- 4-CARD HARDWARE BUNDLE -->
    <section class="mb-12">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-2xl font-extrabold text-white">Complete {setup_name} LED, Ventilation & VPD Hardware Kit</h2>
        <span class="text-xs text-zinc-400">Samsung LM301H EVO & EC-Motor Rated</span>
      </div>
      <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">{bundle_html}</div>
    </section>

    <!-- TENT FOOTPRINT & VENTILATION MATRIX TABLE -->
    <section class="mb-12">
      <h2 class="text-2xl font-extrabold text-white mb-4">Grow Tent Size, True LED Wattage & Inline Fan CFM Sizing Chart</h2>
      <div class="overflow-x-auto bg-zinc-900 border border-zinc-800 rounded-xl">
        <table class="w-full text-left border-collapse text-sm">
          <thead>
            <tr class="border-b border-zinc-800 bg-zinc-950/60 text-zinc-400 uppercase text-xs">
              <th class="py-3.5 px-4">Tent Dimensions</th>
              <th class="py-3.5 px-4 text-green-400">True LED Wattage</th>
              <th class="py-3.5 px-4 text-emerald-400">Recommended EC Inline Fan</th>
              <th class="py-3.5 px-4">Active Filtered CFM</th>
              <th class="py-3.5 px-4">Est. Power Cost (18/6)</th>
            </tr>
          </thead>
          <tbody>{matrix_rows_html}</tbody>
        </table>
      </div>
    </section>

    <!-- VPD & AIRFLOW CHECKLIST -->
    <section class="mb-12">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-2xl font-extrabold text-white">CEA Negative Pressure, VPD & DLI Calibration Checklist</h2>
        <span id="tentBadge" class="text-xs font-bold bg-zinc-800 text-green-400 px-3 py-1 rounded-full">0 / 4 Completed</span>
      </div>
      <div class="space-y-3">{checklist_html}</div>
    </section>

    <!-- FAQ -->
    <section class="mb-12">
      <h2 class="text-2xl font-extrabold text-white mb-5">Frequently Asked Questions ({setup_name})</h2>
      <div class="space-y-4">{faqs_html}</div>
    </section>
  </main>

  <footer class="border-t border-zinc-800 py-8 text-center text-xs text-zinc-500 px-4">
    <p>© {datetime.now(timezone.utc).year} GrowTentIndex. Independent CEA Photobiology & Ventilation Engineering Database. As an Amazon Associate, we earn from qualifying purchases.</p>
  </footer>

  <script>
    const amzDomain = "{amz_domain}";
    const amzTag = "{amz_tag}";

    const tentSizeSelect = document.getElementById('tentSizeSelect');
    const filterSelect = document.getElementById('filterSelect');
    const ppfdSlider = document.getElementById('ppfdSlider');
    const photoSlider = document.getElementById('photoSlider');
    const ppfdVal = document.getElementById('ppfdVal');
    const photoVal = document.getElementById('photoVal');
    const cfmOut = document.getElementById('cfmOut');
    const ductNoteOut = document.getElementById('ductNoteOut');
    const dliOut = document.getElementById('dliOut');
    const billOut = document.getElementById('billOut');
    const tentAdviceBanner = document.getElementById('tentAdviceBanner');
    const dynamicTentBtn = document.getElementById('dynamicTentBtn');

    function recalculateTent() {{
      const sizeParts = tentSizeSelect.value.split('|');
      const sqFt = parseFloat(sizeParts[0]);
      const cuFt = parseFloat(sizeParts[1]);
      const staticMult = parseFloat(filterSelect.value);
      const ppfd = parseInt(ppfdSlider.value, 10);
      const hrs = parseInt(photoSlider.value, 10);

      ppfdVal.textContent = ppfd;
      photoVal.textContent = hrs;

      const minActiveCfm = Math.round(cuFt * staticMult);
      const quietFanCfm = Math.max(195, Math.ceil((minActiveCfm * 1.65) / 10) * 10);

      let ductDia = 4;
      if (quietFanCfm > 420) ductDia = 8;
      else if (quietFanCfm > 210) ductDia = 6;

      const recLedWatts = Math.round((sqFt * 38.0) / 10) * 10;
      const dliMol = (ppfd * hrs * 0.0036).toFixed(1);
      const totalWatts = recLedWatts + (ductDia * 10);
      const moKwh = (totalWatts * hrs * 30.0) / 1000.0;
      const moUsd = (moKwh * 0.16).toFixed(2);

      cfmOut.textContent = `${{quietFanCfm}}+ CFM`;
      ductNoteOut.textContent = `${{ductDia}}" Fan (Min ${{minActiveCfm}} Active CFM)`;
      dliOut.innerHTML = `${{dliMol}} <span class="text-xs font-normal text-zinc-400">mol/d</span>`;
      billOut.textContent = `Bill: ~$${{moUsd}}/mo (${{recLedWatts}}W LED)`;

      let dliStatus = "Optimal Flowering DLI";
      if (dliMol < 25) dliStatus = "Seedling / Clone DLI Range";
      else if (dliMol <= 38) dliStatus = "Optimal Vegetative DLI";
      else if (dliMol > 52) dliStatus = "High-Intensity (CO2 Recommended)";

      tentAdviceBanner.innerHTML = `🌱 <strong>CEA Build Spec (${{dliStatus}}):</strong> Pair a <strong>${{recLedWatts}}W Bar LED Grow Light</strong> with a <strong>${{ductDia}}-Inch (${{quietFanCfm}} CFM) Smart EC Inline Fan & Carbon Filter Kit</strong>.`;
      dynamicTentBtn.href = `https://${{amzDomain}}/s?k=${{recLedWatts}}W+Samsung+LM301H+LED+Grow+Light+${{ductDia}}+Inch+Inline+Fan+Carbon+Filter+Kit&tag=${{amzTag}}`;
    }}

    tentSizeSelect.addEventListener('change', recalculateTent);
    filterSelect.addEventListener('change', recalculateTent);
    ppfdSlider.addEventListener('input', recalculateTent);
    photoSlider.addEventListener('input', recalculateTent);
    recalculateTent();

    const checks = document.querySelectorAll('.tent-check');
    const badge = document.getElementById('tentBadge');
    checks.forEach(ch => {{
      ch.addEventListener('change', () => {{
        const done = Array.from(checks).filter(c => c.checked).length;
        badge.textContent = `${{done}} / ${{checks.length}} Completed`;
      }});
    }});
  </script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(html)


def rebuild_portal_sitemap_and_rss(published, mon_cfg):
    header_cta = mon_cfg.get("header_cta", {})
    header_cta_url = build_amazon_url(header_cta.get("search_query", "Samsung+LM301H+EVO+LED+Grow+Light+Inline+Fan"), mon_cfg)

    cards_html = ""
    for item in reversed(published):
        cards_html += f"""
        <a href="{item['slug']}.html" class="block bg-zinc-900 border border-zinc-800 hover:border-green-500/60 rounded-xl p-5 transition group">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-black uppercase bg-green-500 text-zinc-950 px-2.5 py-0.5 rounded">{item.get('led_watts', 650)}W LED | {item.get('duct_in', 6)}" Fan</span>
            <span class="text-xs text-zinc-400">{item.get('fan_cfm', 350)} CFM | {item.get('dli_12', 41.0)} DLI</span>
          </div>
          <h2 class="text-base font-bold text-white group-hover:text-green-400 transition">{item['setup_name']} Calculator</h2>
          <p class="text-xs text-zinc-400 mt-2 line-clamp-2">{item['description']}</p>
          <span class="inline-block mt-4 text-xs font-extrabold text-green-400">Calculate Exhaust CFM, DLI & Power Cost →</span>
        </a>"""

    index_html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GrowTentIndex — Grow Tent Inline Fan CFM, LED PPFD/DLI & Power Cost Calculator (2026)</title>
  <meta name="description" content="Calculate exact indoor grow tent inline exhaust fan CFM with carbon filter, true LED wattage, PPFD to Daily Light Integral (DLI), and monthly electric cost for AC Infinity, Spider Farmer, Mars Hydro, and Vivosun setups.">
  <link rel="canonical" href="{SITE_BASE_URL}/">
  <link rel="alternate" type="application/rss+xml" title="GrowTentIndex RSS Feed" href="{SITE_BASE_URL}/rss.xml">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-zinc-950 text-zinc-100 min-h-screen flex flex-col">
  <header class="border-b border-zinc-800 bg-zinc-900/80 sticky top-0 z-30 backdrop-blur">
    <div class="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between">
      <div class="text-lg font-black text-white flex items-center gap-2">
        <span class="bg-green-500 text-zinc-950 px-2 py-0.5 rounded font-black">GROW</span>TentIndex
      </div>
      <a href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="text-xs sm:text-sm bg-green-500 hover:bg-green-400 text-zinc-950 font-extrabold px-3.5 py-2 rounded-lg transition">
        {header_cta.get('cta_text', 'Shop LED Grow Lights & Fans →')}
      </a>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-4 py-12 flex-1 w-full">
    <div class="text-center max-w-2xl mx-auto mb-10">
      <h1 class="text-3xl sm:text-5xl font-black text-white tracking-tight">Grow Tent CFM, LED PPFD/DLI & Power Cost Database</h1>
      <p class="text-zinc-400 mt-3 text-base sm:text-lg">Select your grow tent size, inline duct fan, or LED grow light below to calculate carbon-filtered exhaust CFM, Daily Light Integral (DLI), and monthly kWh electricity cost.</p>
      <div class="mt-6">
        <input id="filterInput" type="text" placeholder="Search tent size, LED or fan (e.g. 4x4 Grow Tent, AC Infinity T6, Spider Farmer SE5000, Mars Hydro, 2x4...)" class="w-full bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-green-500">
      </div>
    </div>

    <div id="tentGrid" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">{cards_html}</div>
  </main>

  <footer class="border-t border-zinc-800 py-8 text-center text-xs text-zinc-500">
    <p>© {datetime.now(timezone.utc).year} GrowTentIndex. As an Amazon Associate, we earn from qualifying purchases.</p>
  </footer>

  <script>
    const filterInput = document.getElementById('filterInput');
    const cards = Array.from(document.getElementById('tentGrid').children);
    filterInput.addEventListener('input', (e) => {{
      const q = e.target.value.toLowerCase();
      cards.forEach(c => {{
        c.style.display = c.textContent.toLowerCase().includes(q) ? 'block' : 'none';
      }});
    }});
  </script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls_xml = f"""  <url>
    <loc>{SITE_BASE_URL}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>\n"""

    for item in published:
        urls_xml += f"""  <url>
    <loc>{SITE_BASE_URL}/{item['slug']}.html</loc>
    <lastmod>{item.get('date', today)}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>\n"""

    with open(os.path.join(DOCS_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(f"""<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls_xml}</urlset>""")

    rss_items = ""
    for item in list(reversed(published))[:30]:
        rss_items += f"""    <item>
      <title>{item['title']}</title>
      <link>{SITE_BASE_URL}/{item['slug']}.html</link>
      <guid>{SITE_BASE_URL}/{item['slug']}.html</guid>
      <description>{item['description']}</description>
    </item>\n"""

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>GrowTentIndex CEA Lighting & Ventilation Database</title>
    <link>{SITE_BASE_URL}/</link>
    <description>Interactive Indoor Grow Tent CFM, LED PPFD/DLI & Electricity Cost Calculators</description>
    <atom:link href="{SITE_BASE_URL}/rss.xml" rel="self" type="application/rss+xml" />
    <atom:link href="https://pubsubhubbub.appspot.com/" rel="hub" />
{rss_items}  </channel>
</rss>"""

    with open(os.path.join(DOCS_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss_xml)

    with open(os.path.join(DOCS_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_BASE_URL}/sitemap.xml\n")

    with open(os.path.join(DOCS_DIR, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)


def notify_search_engines(new_urls):
    if not SITE_BASE_URL or not new_urls:
        return
    parsed_host = urllib.parse.urlparse(SITE_BASE_URL).netloc
    payload = {
        "host": parsed_host,
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_BASE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": new_urls
    }
    try:
        req = urllib.request.Request(
            "https://api.indexnow.org/indexnow",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"[INDEXNOW] Pushed {len(new_urls)} URLs (HTTP {resp.status})")
    except Exception as e:
        print(f"[WARN] IndexNow ping notice: {e}")

    try:
        hub_data = urllib.parse.urlencode({
            "hub.mode": "publish",
            "hub.url": f"{SITE_BASE_URL}/rss.xml"
        }).encode("utf-8")
        req_hub = urllib.request.Request(
            "https://pubsubhubbub.appspot.com/",
            data=hub_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )
        with urllib.request.urlopen(req_hub, timeout=15) as resp_hub:
            print(f"[WEBSUB] Google PubSubHubbub ping status: {resp_hub.status}")
    except Exception as e:
        print(f"[WARN] WebSub ping notice: {e}")


def main():
    published = load_json(PUBLISHED_FILE, [])
    mon_cfg = load_json(MONETIZATION_FILE, {})
    published_slugs = {item["slug"] for item in published}

    candidates = []
    if CUSTOM_TENT:
        candidates.append((CUSTOM_TENT.strip(), 4.0, 4.0, 6.67, 650, 950, 6))
    candidates.extend(SEED_TENTS)
    candidates.extend(discover_google_tent_queries())

    new_urls = []
    count = 0

    for tent_tuple in candidates:
        if count >= PAGES_PER_RUN:
            break
        t_name = tent_tuple[0]
        slug = slugify(f"{t_name}-cfm-ppfd-dli-calculator")
        if slug in published_slugs:
            continue

        print(f"[ENGINE] Generating grow tent CFM & PPFD/DLI calculator for: {t_name}...")
        try:
            data = generate_tent_data(tent_tuple)
            build_tent_html_page(data, slug, mon_cfg)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            sp = data.get("specs", {})

            published.append({
                "setup_name": data.get("setup_name", t_name),
                "slug": slug,
                "title": data.get("seo_title", f"{t_name} CFM & PPFD Calculator"),
                "description": data.get("meta_description", ""),
                "led_watts": int(safe_float(sp.get("led_watts", tent_tuple[4]), tent_tuple[4])),
                "duct_in": int(safe_float(sp.get("duct_size_inches", tent_tuple[6]), tent_tuple[6])),
                "fan_cfm": int(safe_float(sp.get("recommended_fan_cfm", 350), 350)),
                "dli_12": round(safe_float(sp.get("dli_12hr_mol", 41.0), 41.0), 1),
                "date": today
            })
            published_slugs.add(slug)
            if SITE_BASE_URL:
                new_urls.append(f"{SITE_BASE_URL}/{slug}.html")
            count += 1
            time.sleep(2)
        except Exception as e:
            print(f"[ERROR] Failed building {t_name}: {e}")

    save_json(PUBLISHED_FILE, published)
    rebuild_portal_sitemap_and_rss(published, mon_cfg)
    if new_urls and SITE_BASE_URL:
        new_urls.append(f"{SITE_BASE_URL}/")
        notify_search_engines(new_urls)
    print(f"[DONE] Published {count} new grow tent CFM & PPFD calculator pages.")


if __name__ == "__main__":
    main()
