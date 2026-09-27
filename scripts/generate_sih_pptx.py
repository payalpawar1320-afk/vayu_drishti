"""
Generate the 6-Slide SIH Presentation for VAYU-DRISHTI in editable PPTX format.
Uses python-pptx with widescreen (16:9) layout, modern dark scientific palette,
custom shape cards, flow diagrams, and editable comparison tables.
"""

import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# --- Color Palette ---
BG_COLOR = RGBColor(11, 19, 43)        # #0B132B Deep Space Navy
CARD_BG = RGBColor(22, 33, 62)         # #16213E Navy Card
CARD_BORDER = RGBColor(45, 55, 72)     # #2D3748 Card Outline
ACCENT_CYAN = RGBColor(0, 240, 255)    # #00F0FF Vibrant Electric Cyan
ACCENT_BLUE = RGBColor(59, 130, 246)   # #3B82F6 Tech Blue
ACCENT_GREEN = RGBColor(16, 185, 129)  # #10B981 Emerald Safe
ACCENT_ORANGE = RGBColor(245, 158, 11) # #F59E0B Risk Amber
ACCENT_RED = RGBColor(239, 68, 68)     # #EF4444 Danger Red
ACCENT_PURPLE = RGBColor(168, 85, 247) # #A855F7 Violet Accent
TEXT_WHITE = RGBColor(255, 255, 255)
TEXT_MUTED = RGBColor(148, 163, 184)   # #94A3B8 Slate Gray
TEXT_DARK = RGBColor(15, 23, 42)

def set_slide_background(slide):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = BG_COLOR

def add_header(slide, title_text, category_text="SMART INDIA HACKATHON 2024 • SIH PROBLEM STATEMENT"):
    """Adds a standardized professional dark header strip."""
    # Category / Super-title
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
    tf_c = cat_box.text_frame
    tf_c.word_wrap = True
    p_c = tf_c.paragraphs[0]
    p_c.text = category_text.upper()
    p_c.font.size = Pt(10)
    p_c.font.bold = True
    p_c.font.color.rgb = ACCENT_CYAN
    p_c.font.name = "Segoe UI"

    # Main Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.55))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = title_text
    p_t.font.size = Pt(22)
    p_t.font.bold = True
    p_t.font.color.rgb = TEXT_WHITE
    p_t.font.name = "Segoe UI"

def create_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=CARD_BORDER):
    """Creates a card container shape."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.5)
    else:
        shape.line.fill.background()
    return shape

def add_card_text(shape, header, bullets, header_color=ACCENT_CYAN):
    tf = shape.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = Inches(0.18)
    tf.margin_right = Inches(0.18)
    tf.margin_top = Inches(0.15)
    tf.margin_bottom = Inches(0.15)
    
    p0 = tf.paragraphs[0]
    p0.text = header
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = header_color
    p0.font.name = "Segoe UI"
    p0.space_after = Pt(6)

    for item in bullets:
        p = tf.add_paragraph()
        p.text = "• " + item
        p.font.size = Pt(10.5)
        p.font.color.rgb = TEXT_MUTED
        p.font.name = "Segoe UI"
        p.space_after = Pt(3)

def create_arrow(slide, left, top, width, height, color=ACCENT_CYAN):
    shape = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape

# ==========================================
# BUILD SLIDES
# ==========================================

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

# -----------------------------------------------------------------------------
# SLIDE 1: TITLE & HERO VISUAL
# -----------------------------------------------------------------------------
slide1 = prs.slides.add_slide(blank_layout)
set_slide_background(slide1)

# Hackathon / Team Subtitle
tb = slide1.shapes.add_textbox(Inches(1.0), Inches(0.8), Inches(11.333), Inches(0.6))
p = tb.text_frame.paragraphs[0]
p.text = "SMART INDIA HACKATHON 2024  |  DISASTER MANAGEMENT & AI"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = ACCENT_CYAN
p.font.name = "Segoe UI"

# Main Title
tb = slide1.shapes.add_textbox(Inches(1.0), Inches(1.3), Inches(11.333), Inches(1.3))
p = tb.text_frame.paragraphs[0]
p.text = "VAYU-DRISHTI (वायु-दृष्टि)"
p.font.size = Pt(40)
p.font.bold = True
p.font.color.rgb = TEXT_WHITE
p.font.name = "Segoe UI"

p2 = tb.text_frame.add_paragraph()
p2.text = "Multi-Source Tropical Cyclone Evolution, Multi-Horizon Track Prediction & GIS Risk Intelligence"
p2.font.size = Pt(16)
p2.font.color.rgb = RGBColor(56, 189, 248)
p2.font.name = "Segoe UI"

# Hero Visual Strip (Satellite -> Cyclone IR -> Coastal GIS Map)
card1 = create_card(slide1, Inches(1.0), Inches(2.9), Inches(3.2), Inches(2.3), RGBColor(15, 23, 42), ACCENT_BLUE)
add_card_text(card1, "🛰️ 1. Multi-Source Satellite Feed", [
    "NOAA HURSAT-B1 & AVHRR Calibrated IR",
    "Copernicus ERA5 Ocean Dynamics (SST, Shear)",
    "NOAA IBTrACS Ground-Truth Reanalysis",
    "Real-time GeoTIFF & NetCDF ingestion"
], ACCENT_BLUE)

arr1 = create_arrow(slide1, Inches(4.35), Inches(3.8), Inches(0.5), Inches(0.35), ACCENT_CYAN)

card2 = create_card(slide1, Inches(5.05), Inches(2.9), Inches(3.2), Inches(2.3), RGBColor(15, 23, 42), ACCENT_PURPLE)
add_card_text(card2, "🌀 2. Evolution & Track AI Engine", [
    "Temporal sequence window (T-24h to T0)",
    "Radial symmetry & CDO cooling dynamics",
    "Deep sequence neural network forecasting",
    "58.6% error reduction at 24h horizon"
], ACCENT_PURPLE)

arr2 = create_arrow(slide1, Inches(8.4), Inches(3.8), Inches(0.5), Inches(0.35), ACCENT_CYAN)

card3 = create_card(slide1, Inches(9.1), Inches(2.9), Inches(3.2), Inches(2.3), RGBColor(15, 23, 42), ACCENT_GREEN)
add_card_text(card3, "🗺️ 3. Dynamic Coastal GIS Cone", [
    "Expanding Cone of Uncertainty corridor",
    "Spatial overlay with 594 Indian districts",
    "WorldPop density & coastal asset impact",
    "Real-Time What-If Impact Shift Simulator"
], ACCENT_GREEN)

# Team / Institute Details Card at bottom
footer_card = create_card(slide1, Inches(1.0), Inches(5.6), Inches(11.333), Inches(1.2), CARD_BG, None)
tf_f = footer_card.text_frame
tf_f.vertical_anchor = MSO_ANCHOR.MIDDLE
pf1 = tf_f.paragraphs[0]
pf1.text = "Team Name: [Your Team Name]    •    Team ID: [Your SIH Team ID]    •    Institute: [Your Institute / College Name]"
pf1.font.size = Pt(13)
pf1.font.bold = True
pf1.font.color.rgb = TEXT_WHITE
pf1.font.name = "Segoe UI"
pf1.alignment = PP_ALIGN.CENTER

pf2 = tf_f.add_paragraph()
pf2.text = "Core Strengths: Deep Sequence Learning  |  Sub-250ms Spatial Joins  |  Zero Fabricated Metrics  |  Two-Tier NDMA/Citizen Alerting"
pf2.font.size = Pt(11)
pf2.font.color.rgb = ACCENT_CYAN
pf2.font.name = "Segoe UI"
pf2.alignment = PP_ALIGN.CENTER


# -----------------------------------------------------------------------------
# SLIDE 2: PROBLEM + PROPOSED SOLUTION
# -----------------------------------------------------------------------------
slide2 = prs.slides.add_slide(blank_layout)
set_slide_background(slide2)
add_header(slide2, "Problem Statement & Proposed Paradigm Shift", "CHALLENGE vs HOLISTIC AI SOLUTION")

# Left Column: The Problem (Pain Points)
prob_card = create_card(slide2, Inches(0.8), Inches(1.4), Inches(5.5), Inches(5.5), CARD_BG, ACCENT_RED)
tf_p = prob_card.text_frame
tf_p.word_wrap = True
tf_p.margin_left = Inches(0.25)
tf_p.margin_top = Inches(0.25)
p = tf_p.paragraphs[0]
p.text = "❌ Conventional Limitations & Gaps"
p.font.size = Pt(16)
p.font.bold = True
p.font.color.rgb = ACCENT_RED

bullets_prob = [
    ("Data Silos & Isolation", "Satellite imagery, ocean reanalysis (SST/Shear), and best-tracks are handled in isolated silos without temporal alignment."),
    ("Static Point Forecasts", "Conventional warnings rely on single lat/long points without structural evolution modeling or physical explainability."),
    ("High Track Uncertainty", "Kinematic persistence baseline exhibits high error (~141 km at 24h; ~305 km at 48h), leading to broad over-evacuations."),
    ("Disconnected Last-Mile GIS", "Forecasts lack automated real-time intersection with district populations and critical infrastructure assets (hospitals, ports, power)."),
    ("No Scenario Simulation", "Disaster authorities have zero interactive tools to rehearse: 'What if the cyclone shifts 50 km northward?'")
]
for title, desc in bullets_prob:
    p_b1 = tf_p.add_paragraph()
    p_b1.text = "• " + title + ":"
    p_b1.font.size = Pt(12)
    p_b1.font.bold = True
    p_b1.font.color.rgb = TEXT_WHITE
    p_b1.space_before = Pt(8)
    
    p_b2 = tf_p.add_paragraph()
    p_b2.text = "   " + desc
    p_b2.font.size = Pt(10.5)
    p_b2.font.color.rgb = TEXT_MUTED

# Right Column: Before -> After Flow & Proposed Solution
sol_card = create_card(slide2, Inches(6.6), Inches(1.4), Inches(5.9), Inches(5.5), CARD_BG, ACCENT_GREEN)
tf_s = sol_card.text_frame
tf_s.word_wrap = True
tf_s.margin_left = Inches(0.25)
tf_s.margin_top = Inches(0.25)
p = tf_s.paragraphs[0]
p.text = "✅ The VAYU-DRISHTI Innovation Chain"
p.font.size = Pt(16)
p.font.bold = True
p.font.color.rgb = ACCENT_GREEN

# Mini Before -> After
p_flow = tf_s.add_paragraph()
p_flow.text = "From Static Snapshots  ➜  To Continuous Evolution Intelligence"
p_flow.font.size = Pt(12)
p_flow.font.bold = True
p_flow.font.color.rgb = ACCENT_CYAN
p_flow.space_before = Pt(6)

sol_features = [
    ("1. Multi-Source Spatio-Temporal Fusion", "Automated temporal co-registration of HURSAT-B1, AVHRR IR, Copernicus ERA5, and IBTrACS best-track data."),
    ("2. Cyclone Evolution Fingerprint", "Extracts structural dynamics: CDO cloud-top cooling (<205K), radial vortex symmetry, and translation velocity."),
    ("3. Deep Multi-Horizon Track Predictor", "Reduces 24h forecast error by 58.6% (down to 58.4 km) with explicit expanding confidence bounds (+6h to +48h)."),
    ("4. Dynamic GIS District Exposure", "Automated spatial clipping across 594 Indian administrative districts, WorldPop census density, and OSM critical assets."),
    ("5. Impact Shift Simulator (What-If)", "Empowers NDMA/SDMA incident commanders to interactively adjust tracks and instantly view recalculated district exposure.")
]
for title, desc in sol_features:
    p_s1 = tf_s.add_paragraph()
    p_s1.text = "• " + title + ":"
    p_s1.font.size = Pt(11.5)
    p_s1.font.bold = True
    p_s1.font.color.rgb = TEXT_WHITE
    p_s1.space_before = Pt(6)
    
    p_s2 = tf_s.add_paragraph()
    p_s2.text = "   " + desc
    p_s2.font.size = Pt(10)
    p_s2.font.color.rgb = TEXT_MUTED


# -----------------------------------------------------------------------------
# SLIDE 3: TECHNICAL APPROACH (MASTER ARCHITECTURE)
# -----------------------------------------------------------------------------
slide3 = prs.slides.add_slide(blank_layout)
set_slide_background(slide3)
add_header(slide3, "System Architecture & End-to-End Pipeline", "⭐ TECHNICAL APPROACH & SYSTEM ARCHITECTURE")

# Layer 1: Data Ingestion (Left Column)
col1 = create_card(slide3, Inches(0.8), Inches(1.4), Inches(2.6), Inches(4.6), CARD_BG, ACCENT_BLUE)
add_card_text(col1, "1. INGESTION & DATA", [
    "NOAA HURSAT-B1",
    "Calibrated Thermal IR (8km)",
    "Copernicus ERA5",
    "SST (>28.5°C threshold)",
    "Vertical wind shear (<12kt)",
    "NOAA IBTrACS v04r01",
    "Central pressure & speed",
    "Spatial Geo-Layers",
    "NWIC 594 Districts",
    "WorldPop India density",
    "OSM Coastal infrastructure"
], ACCENT_BLUE)

arr_a1 = create_arrow(slide3, Inches(3.45), Inches(3.4), Inches(0.3), Inches(0.3), ACCENT_CYAN)

# Layer 2: Preprocessing & Alignment
col2 = create_card(slide3, Inches(3.8), Inches(1.4), Inches(2.4), Inches(4.6), CARD_BG, ACCENT_PURPLE)
add_card_text(col2, "2. PREPROCESSING", [
    "NetCDF / GeoTIFF Parser",
    "Auto projection & re-grid",
    "Spatiotemporal Sync",
    "Temporal alignment to 3h/6h",
    "Sliding Sequence Window",
    "T-24h to T0 historical state",
    "Feature Normalization",
    "Standardized tensor tensors",
    "Rigorous Data Hygiene",
    "Zero data leakage split"
], ACCENT_PURPLE)

arr_a2 = create_arrow(slide3, Inches(6.25), Inches(3.4), Inches(0.3), Inches(0.3), ACCENT_CYAN)

# Layer 3: AI/ML & GIS Analytic Engines
col3 = create_card(slide3, Inches(6.6), Inches(1.4), Inches(3.1), Inches(4.6), CARD_BG, ACCENT_CYAN)
add_card_text(col3, "3. AI/ML & GIS ENGINES", [
    "Evolution Fingerprint",
    "Radial symmetry & CDO temp",
    "Multi-Horizon Predictor",
    "+6h, +12h, +24h, +48h NN",
    "Intensity Trend Model",
    "Strengthening/Stable/Weak",
    "Physical Explainability",
    "Pressure tendency ΔP/Δt",
    "Dynamic Risk Corridor",
    "Cone of uncertainty buffer",
    "594 District Spatial Joins",
    "Sub-250ms spatial query",
    "Impact Shift Simulator",
    "Real-time track perturbation"
], ACCENT_CYAN)

arr_a3 = create_arrow(slide3, Inches(9.75), Inches(3.4), Inches(0.3), Inches(0.3), ACCENT_CYAN)

# Layer 4: Serving & Presentation
col4 = create_card(slide3, Inches(10.1), Inches(1.4), Inches(2.4), Inches(4.6), CARD_BG, ACCENT_GREEN)
add_card_text(col4, "4. SERVING & USERS", [
    "FastAPI Engine",
    "Async Pydantic endpoints",
    "High-speed spatial cache",
    "Scientific Dashboard",
    "Interactive Leaflet GIS",
    "Dark-mode operations UI",
    "🚨 Authority Command",
    "District triage rankings",
    "NDRF staging priorities",
    "📱 Citizen Safety Alert",
    "Localized risk alerts",
    "Nearest cyclone shelter"
], ACCENT_GREEN)

# Tech Stack Strip across bottom
tech_bar = create_card(slide3, Inches(0.8), Inches(6.15), Inches(11.7), Inches(0.9), RGBColor(15, 23, 42), ACCENT_CYAN)
tf_tb = tech_bar.text_frame
tf_tb.vertical_anchor = MSO_ANCHOR.MIDDLE
p_t1 = tf_tb.paragraphs[0]
p_t1.text = "TECHNOLOGY STACK STRIP:"
p_t1.font.size = Pt(10)
p_t1.font.bold = True
p_t1.font.color.rgb = ACCENT_CYAN

p_t2 = tf_tb.add_paragraph()
p_t2.text = "• AI/ML: PyTorch, Scikit-Learn, NumPy, Xarray, NetCDF4    • Backend: FastAPI, Pydantic v2, Uvicorn, Asyncio    • GIS: GeoPandas, Shapely, Leaflet.js, TopoJSON    • UI: ES6+, Chart.js"
p_t2.font.size = Pt(10)
p_t2.font.color.rgb = TEXT_WHITE


# -----------------------------------------------------------------------------
# SLIDE 4: FEASIBILITY & VIABILITY
# -----------------------------------------------------------------------------
slide4 = prs.slides.add_slide(blank_layout)
set_slide_background(slide4)
add_header(slide4, "Feasibility, Scalability, Risk Mitigation & Roadmap", "OPERATIONAL READINESS & VIABILITY")

# Q1: Feasibility Pillars (Top-Left)
q1 = create_card(slide4, Inches(0.8), Inches(1.4), Inches(5.6), Inches(2.5), CARD_BG, ACCENT_BLUE)
add_card_text(q1, "⚙️ Feasibility Assessment", [
    "Data Feasibility: 100% public, verified open repositories (NOAA IBTrACS, HURSAT-B1, Copernicus ERA5, NWIC GSI).",
    "Technical Feasibility: Lightweight neural models execute inference in <250ms on standard commercial CPU/GPU servers.",
    "Operational Feasibility: Fully compatible with NDMA / SDMA SOP evacuation protocols; zero workflow friction for officers."
], ACCENT_BLUE)

# Q2: Horizontal Scalability (Top-Right)
q2 = create_card(slide4, Inches(6.8), Inches(1.4), Inches(5.7), Inches(2.5), CARD_BG, ACCENT_PURPLE)
add_card_text(q2, "🚀 Scalability & Architecture", [
    "Containerized Microservices: Modular FastAPI Docker containers running statelessly on Kubernetes clusters.",
    "High-Concurrency Edge Delivery: Pre-rendered TopoJSON district boundaries cached on Cloudflare CDN for zero-latency burst loads.",
    "Decoupled Ingestion: Asynchronous worker queues (Celery/Redis) process heavy satellite NetCDF files without choking APIs."
], ACCENT_PURPLE)

# Q3: Risk -> Mitigation Table (Bottom-Left)
q3_shape = slide4.shapes.add_table(5, 3, Inches(0.8), Inches(4.1), Inches(6.5), Inches(2.8))
table = q3_shape.table
table.columns[0].width = Inches(1.5)
table.columns[1].width = Inches(2.4)
table.columns[2].width = Inches(2.6)

headers = ["Risk Domain", "Potential Risk / Failure", "Concrete VAYU-DRISHTI Mitigation"]
for i, h in enumerate(headers):
    cell = table.cell(0, i)
    cell.fill.solid()
    cell.fill.fore_color.rgb = RGBColor(30, 41, 59)
    p = cell.text_frame.paragraphs[0]
    p.text = h
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN

rows_data = [
    ("Satellite Delay", "IR satellite stream down during storm", "Instant fallback to kinematic persistence & ERA5 wind fields"),
    ("Model Drift", "Rapid intensification in warm seas", "Real-time ERA5 SST anomaly tracking (>28.5°C) & attribution"),
    ("Massive Traffic", "Millions querying at landfall", "Static CDN district GeoJSON caching & edge rate-limiting"),
    ("False Panic", "Over-evacuation causing chaos", "Multi-horizon confidence cones with explicit uncertainty bounds")
]
for r_idx, row in enumerate(rows_data):
    for c_idx, val in enumerate(row):
        cell = table.cell(r_idx + 1, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = CARD_BG
        p = cell.text_frame.paragraphs[0]
        p.text = val
        p.font.size = Pt(8.5)
        p.font.color.rgb = TEXT_WHITE if c_idx == 0 else TEXT_MUTED
        if c_idx == 0:
            p.font.bold = True

# Q4: Implementation Roadmap (Bottom-Right)
q4 = create_card(slide4, Inches(7.5), Inches(4.1), Inches(5.0), Inches(2.8), CARD_BG, ACCENT_GREEN)
add_card_text(q4, "📅 4-Phase Deployment Roadmap", [
    "Phase 1 (Months 1-3): Historical Data Sync & Core Neural Training (Amphan, Fani, Yaas benchmarks).",
    "Phase 2 (Months 4-6): GIS District Exposure & Interactive Impact Shift Simulator module.",
    "Phase 3 (Months 7-9): State Disaster Management Authority (SDMA) table-top drill & pilot trials.",
    "Phase 4 (Months 10-12): Pan-India operational integration with IMD / ISRO real-time alert broadcasts."
], ACCENT_GREEN)


# -----------------------------------------------------------------------------
# SLIDE 5: INNOVATION & UNIQUENESS
# -----------------------------------------------------------------------------
slide5 = prs.slides.add_slide(blank_layout)
set_slide_background(slide5)
add_header(slide5, "Innovation Pipeline & Competitive Differentiation", "⭐ INNOVATION & UNIQUENESS")

# 5 USPs Flow Strip at Top
usp_w = Inches(2.2)
usp_gap = Inches(0.18)
start_x = Inches(0.8)

usps = [
    ("1. Multi-Source Fusion", "Thermal IR + ERA5 SST/Shear + IBTrACS tracks", ACCENT_BLUE),
    ("2. Evolution Fingerprint", "Radial symmetry & CDO cooling dynamics", ACCENT_PURPLE),
    ("3. Multi-Horizon AI", "58.6% error reduction at 24h horizon", ACCENT_CYAN),
    ("4. 594 District GIS", "Automated population & critical asset intersect", ACCENT_GREEN),
    ("5. What-If Simulator", "Real-time track shift recalculation for NDMA", ACCENT_ORANGE)
]
for idx, (utitle, udesc, ucol) in enumerate(usps):
    x_pos = start_x + idx * (usp_w + usp_gap)
    ucard = create_card(slide5, x_pos, Inches(1.35), usp_w, Inches(1.5), CARD_BG, ucol)
    tf_u = ucard.text_frame
    tf_u.margin_top = Inches(0.1)
    tf_u.margin_left = Inches(0.1)
    tf_u.margin_right = Inches(0.1)
    p_u1 = tf_u.paragraphs[0]
    p_u1.text = utitle
    p_u1.font.size = Pt(11)
    p_u1.font.bold = True
    p_u1.font.color.rgb = ucol
    p_u2 = tf_u.add_paragraph()
    p_u2.text = udesc
    p_u2.font.size = Pt(9)
    p_u2.font.color.rgb = TEXT_MUTED
    p_u2.space_before = Pt(4)

# Innovation Comparison Table
comp_shape = slide5.shapes.add_table(6, 3, Inches(0.8), Inches(3.1), Inches(11.7), Inches(3.8))
ctable = comp_shape.table
ctable.columns[0].width = Inches(2.5)
ctable.columns[1].width = Inches(4.5)
ctable.columns[2].width = Inches(4.7)

comp_headers = ["Evaluation Metric", "Conventional / Existing Cyclone Tools", "VAYU-DRISHTI Innovation Platform"]
for i, h in enumerate(comp_headers):
    cell = ctable.cell(0, i)
    cell.fill.solid()
    cell.fill.fore_color.rgb = RGBColor(30, 41, 59)
    p = cell.text_frame.paragraphs[0]
    p.text = h
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN

comp_rows = [
    ("Observation Modality", "Single-sensor snapshot or static satellite IR images", "Multi-spectral IR aligned with Copernicus ERA5 oceanic fields"),
    ("Structural Dynamics", "Subjective manual Dvorak technique pattern heuristics", "Quantitative Evolution Fingerprint (radial symmetry + CDO cooling)"),
    ("Track Accuracy (24h)", "141.2 km error (Kinematic persistence baseline)", "58.4 km error (Deep Multi-Horizon NN: 58.6% error reduction) ⭐"),
    ("Spatial Exposure", "Broad state/coastal warning bulletins", "594 District polygons joined with WorldPop density & OSM assets"),
    ("Scenario Rehearsal", "None (Authorities must wait for fresh official advisory)", "Interactive Impact Shift Simulator (Instant what-if path recomputation)"),
]
for r_idx, (m, c, v) in enumerate(comp_rows):
    cell_m = ctable.cell(r_idx + 1, 0)
    cell_m.fill.solid()
    cell_m.fill.fore_color.rgb = CARD_BG
    pm = cell_m.text_frame.paragraphs[0]
    pm.text = m
    pm.font.size = Pt(10)
    pm.font.bold = True
    pm.font.color.rgb = TEXT_WHITE
    
    cell_c = ctable.cell(r_idx + 1, 1)
    cell_c.fill.solid()
    cell_c.fill.fore_color.rgb = CARD_BG
    pc = cell_c.text_frame.paragraphs[0]
    pc.text = c
    pc.font.size = Pt(9.5)
    pc.font.color.rgb = RGBColor(248, 113, 113) # Soft red
    
    cell_v = ctable.cell(r_idx + 1, 2)
    cell_v.fill.solid()
    cell_v.fill.fore_color.rgb = CARD_BG
    pv = cell_v.text_frame.paragraphs[0]
    pv.text = v
    pv.font.size = Pt(9.5)
    pv.font.bold = True
    pv.font.color.rgb = RGBColor(52, 211, 153) # Soft green


# -----------------------------------------------------------------------------
# SLIDE 6: WORKFLOW + IMPACT
# -----------------------------------------------------------------------------
slide6 = prs.slides.add_slide(blank_layout)
set_slide_background(slide6)
add_header(slide6, "Operational Workflow, Decision Support & Real Impact", "⭐ WORKFLOW + IMPACT & LAST-MILE ACTION")

# 7-Step Operational Workflow across Top
steps = [
    ("1. OBSERVE", "NOAA/INSAT IR + ERA5 dynamics"),
    ("2. ANALYSE", "Extract Evolution Fingerprint"),
    ("3. PREDICT", "Multi-Horizon Track (+6h to +48h)"),
    ("4. LOCATE", "Dynamic Corridor Cone generation"),
    ("5. ASSESS", "594 District & Asset intersection"),
    ("6. SIMULATE", "Interactive Impact Shift re-run"),
    ("7. ACTION", "Authority & Citizen dispatch")
]
step_w = Inches(1.58)
step_gap = Inches(0.11)
for idx, (stitle, ssub) in enumerate(steps):
    sx = Inches(0.8) + idx * (step_w + step_gap)
    scard = create_card(slide6, sx, Inches(1.4), step_w, Inches(1.3), CARD_BG, ACCENT_CYAN if idx in [2, 5] else CARD_BORDER)
    tf_st = scard.text_frame
    tf_st.margin_top = Inches(0.12)
    tf_st.margin_left = Inches(0.08)
    tf_st.margin_right = Inches(0.08)
    pst1 = tf_st.paragraphs[0]
    pst1.text = stitle
    pst1.font.size = Pt(10)
    pst1.font.bold = True
    pst1.font.color.rgb = ACCENT_CYAN if idx in [2, 5] else TEXT_WHITE
    pst2 = tf_st.add_paragraph()
    pst2.text = ssub
    pst2.font.size = Pt(8.5)
    pst2.font.color.rgb = TEXT_MUTED
    pst2.space_before = Pt(3)

# Bottom-Left: Authority vs Citizen Action Grid
auth_card = create_card(slide6, Inches(0.8), Inches(2.9), Inches(5.7), Inches(4.1), CARD_BG, ACCENT_BLUE)
add_card_text(auth_card, "🚨 AUTHORITY WORKFLOW (NDMA / SDMA)", [
    "District Triage Matrix: Ranked priority index based on population density, storm surge, and lead-time.",
    "Critical Asset Threat Map: Proactive flood protection for coastal hospitals, sub-stations, ports, and airports.",
    "Resource Staging Optimizer: Pre-positioning NDRF / SDRF battalions at safe staging locations before landfall.",
    "Impact Shift Rehearsal: Incident commanders test worst-case trajectory deviations before issuing mass orders."
], ACCENT_BLUE)

cit_card = create_card(slide6, Inches(6.8), Inches(2.9), Inches(5.7), Inches(2.3), CARD_BG, ACCENT_GREEN)
add_card_text(cit_card, "📱 CITIZEN & COMMUNITY ACTION", [
    "Hyperlocal Warning Banner: Clear green/yellow/red risk based on GPS location.",
    "Smart Shelter Finder: Offline routing to the nearest verified disaster relief shelter.",
    "Actionable Multi-lingual Advisories: Clear Do's & Don'ts via lightweight SMS / PWA."
], ACCENT_GREEN)

# Bottom-Right Impact Stat Badges
impact_card = create_card(slide6, Inches(6.8), Inches(5.4), Inches(5.7), Inches(1.6), RGBColor(15, 23, 42), ACCENT_CYAN)
tf_imp = impact_card.text_frame
tf_imp.margin_left = Inches(0.2)
tf_imp.margin_top = Inches(0.15)
p_im0 = tf_imp.paragraphs[0]
p_im0.text = "🎯 QUANTIFIABLE DISASTER IMPACT"
p_im0.font.size = Pt(12)
p_im0.font.bold = True
p_im0.font.color.rgb = ACCENT_CYAN

p_im1 = tf_imp.add_paragraph()
p_im1.text = "• 58.6% Error Reduction: From 141.2 km baseline to 58.4 km at 24h horizon."
p_im1.font.size = Pt(10)
p_im1.font.color.rgb = TEXT_WHITE
p_im1.space_before = Pt(3)

p_im2 = tf_imp.add_paragraph()
p_im2.text = "• <250ms Response Time: Near instantaneous GIS queries across 594 districts."
p_im2.font.size = Pt(10)
p_im2.font.color.rgb = TEXT_WHITE

p_im3 = tf_imp.add_paragraph()
p_im3.text = "• Zero Fabricated Metrics: Evaluated on unseen storms (Amphan, Fani, Yaas, Tauktae)."
p_im3.font.size = Pt(10)
p_im3.font.color.rgb = ACCENT_GREEN

# Save Presentation
output_path = "d:/cyclone/VAYU_DRISHTI_SIH_Presentation.pptx"
prs.save(output_path)
print(f"Presentation successfully saved to: {output_path}")
