"""
ui/app.py
RecruitMind AI — Premium Streamlit Dashboard with Cinematic Splash Screen
Run: streamlit run ui/app.py
"""

import os
import sys
import json
import time
import requests
import base64
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

API_URL = os.getenv("API_URL", "http://localhost:8000")

# Initialize session state for page routing
if "entered" not in st.session_state:
    st.session_state["entered"] = False

st.set_page_config(
    page_title="RecruitMind AI — Intelligent Talent Discovery",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── HTML Cleaning Helper (Prevents Markdown Code Block bugs) ──────────────────

def clean_html(html_str):
    """Strips leading whitespace from every line to prevent Streamlit's Markdown parser
    from incorrectly rendering HTML as markdown code blocks."""
    return "\n".join([line.strip() for line in html_str.split("\n")])

# ── Base Premium CSS ───────────────────────────────────────────────────────────

base_css = clean_html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Root & Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(168, 85, 247, 0.06) 0%, transparent 55%),
                linear-gradient(135deg, #030712 0%, #090d16 50%, #020617 100%) !important;
    color: #f1f5f9;
}

/* ── Glowing Orbs (Cosmic depth) ── */
.stApp::before {
    content: "";
    position: absolute;
    top: 5%;
    left: 20%;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.05) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}
.stApp::after {
    content: "";
    position: absolute;
    bottom: 15%;
    right: 10%;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(168, 85, 247, 0.04) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #080c14; }
::-webkit-scrollbar-thumb { background: rgba(99, 102, 241, 0.4); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(167, 139, 250, 0.6); }

/* ── Hero Banner ── */
.hero-banner {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.45) 100%) !important;
    border: 1px solid rgba(99, 102, 241, 0.25) !important;
    border-radius: 24px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(16px);
    box-shadow: 0 25px 50px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.03);
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%);
    pointer-events: none;
}
.hero-banner::after {
    content: '';
    position: absolute;
    bottom: -30%;
    left: 5%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(168,85,247,0.08) 0%, transparent 70%);
    pointer-events: none;
}
.hero-title {
    font-size: 3.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #a78bfa 0%, #818cf8 40%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.1;
    letter-spacing: -0.8px;
    filter: drop-shadow(0 2px 10px rgba(99,102,241,0.15));
}
.hero-sub {
    font-size: 1.1rem;
    color: #94a3b8;
    margin-top: 0.6rem;
    font-weight: 400;
    letter-spacing: 0.3px;
}
.hero-badges {
    display: flex;
    gap: 0.6rem;
    margin-top: 1.5rem;
    flex-wrap: wrap;
}
.hero-badge {
    background: rgba(99,102,241,0.08);
    border: 1px solid rgba(99,102,241,0.2);
    color: #a78bfa;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    transition: all 0.3s ease;
}
.hero-badge:hover {
    background: rgba(99,102,241,0.18);
    border-color: rgba(167,139,250,0.5);
    box-shadow: 0 0 12px rgba(167,139,250,0.25);
    transform: translateY(-1px);
}

/* ── Glass Card ── */
.glass-card {
    background: rgba(15, 23, 42, 0.45);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 20px;
    padding: 1.8rem;
    backdrop-filter: blur(12px);
    box-shadow: 0 12px 32px rgba(0,0,0,0.4);
    margin-bottom: 1.5rem;
}

/* ── Section Header ── */
.section-header {
    font-size: 1.3rem;
    font-weight: 800;
    color: #f8fafc;
    margin-top: 1rem;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    letter-spacing: -0.3px;
}
.section-header .accent {
    width: 4px;
    height: 22px;
    background: linear-gradient(180deg, #6366f1, #a855f7);
    border-radius: 4px;
    display: inline-block;
    box-shadow: 0 0 10px rgba(99,102,241,0.5);
}

/* ── Metric Cards ── */
.metric-row {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 1.2rem;
    margin: 1.5rem 0;
}
.metric-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.06) 0%, rgba(168,85,247,0.04) 100%);
    border: 1px solid rgba(99,102,241,0.18);
    border-radius: 16px;
    padding: 1.4rem 1.1rem;
    text-align: center;
    backdrop-filter: blur(8px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.metric-card:hover {
    transform: translateY(-3px);
    border-color: rgba(167,139,250,0.45);
    box-shadow: 0 10px 25px rgba(99,102,241,0.15);
}
.metric-value {
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
}
.metric-label {
    font-size: 0.72rem;
    color: #64748b;
    margin-top: 0.5rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* ── Candidate Card ── */
.candidate-card {
    background: linear-gradient(135deg, rgba(13, 18, 36, 0.95) 0%, rgba(18, 24, 48, 0.95) 100%) !important;
    border: 1px solid rgba(99,102,241,0.18) !important;
    border-radius: 20px;
    padding: 1.8rem;
    margin: 1rem 0;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(12px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
}
.candidate-card:hover {
    border-color: rgba(167,139,250,0.45) !important;
    box-shadow: 0 15px 45px rgba(99,102,241,0.2);
    transform: translateY(-2px);
}
.candidate-card.top-3 {
    border-color: rgba(168,85,247,0.3) !important;
    background: linear-gradient(135deg, rgba(16, 12, 42, 0.98) 0%, rgba(22, 18, 48, 0.98) 100%) !important;
}
.candidate-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, transparent, rgba(99,102,241,0.5), transparent);
}
.candidate-card.top-3::before {
    background: linear-gradient(90deg, transparent, rgba(168,85,247,0.7), rgba(99,102,241,0.5), transparent);
}

/* ── Rank Badge ── */
.rank-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 38px;
    height: 38px;
    border-radius: 50%;
    font-weight: 800;
    font-size: 0.9rem;
    margin-right: 0.75rem;
    flex-shrink: 0;
}
.rank-1 { background: linear-gradient(135deg, #f59e0b, #d97706); color: #fff; box-shadow: 0 0 20px rgba(245,158,11,0.4); }
.rank-2 { background: linear-gradient(135deg, #94a3b8, #64748b); color: #fff; box-shadow: 0 0 15px rgba(148,163,184,0.3); }
.rank-3 { background: linear-gradient(135deg, #cd7c2f, #92400e); color: #fff; box-shadow: 0 0 15px rgba(205,124,47,0.3); }
.rank-other { background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.3); color: #818cf8; }

/* ── Score Ring ── */
.score-ring-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.4rem;
}
.score-ring {
    width: 76px;
    height: 76px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.05rem;
    font-weight: 800;
    position: relative;
    box-shadow: 0 0 15px rgba(0,0,0,0.3);
}
.score-high { background: conic-gradient(#22c55e var(--pct), rgba(34,197,94,0.1) 0); color: #22c55e; box-shadow: 0 0 20px rgba(34,197,94,0.25); }
.score-mid  { background: conic-gradient(#f59e0b var(--pct), rgba(245,158,11,0.1) 0); color: #f59e0b; box-shadow: 0 0 20px rgba(245,158,11,0.25); }
.score-low  { background: conic-gradient(#ef4444 var(--pct), rgba(239,68,68,0.1) 0); color: #ef4444; }
.score-inner {
    position: absolute;
    width: 62px;
    height: 62px;
    border-radius: 50%;
    background: #090d16;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.9rem;
    font-weight: 800;
}

/* ── Skill Tags ── */
.skill-tag {
    background: rgba(99,102,241,0.08);
    border: 1px solid rgba(99,102,241,0.22);
    color: #a78bfa;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 500;
    display: inline-block;
    margin: 3px;
    transition: all 0.2s;
}
.skill-tag:hover {
    background: rgba(99,102,241,0.18);
    border-color: rgba(167,139,250,0.4);
}
.skill-matched {
    background: rgba(34,197,94,0.12);
    border: 1px solid rgba(34,197,94,0.35);
    color: #4ade80;
}
.skill-matched:hover {
    background: rgba(34,197,94,0.2);
    border-color: rgba(34,197,94,0.5);
}

/* ── Mini Score Bar ── */
.score-bar-wrap {
    margin: 8px 0;
}
.score-bar-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.72rem;
    color: #94a3b8;
    margin-bottom: 4px;
    font-weight: 500;
}
.score-bar-bg {
    height: 6px;
    background: rgba(255,255,255,0.06);
    border-radius: 3px;
    overflow: hidden;
}
.score-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.8s ease;
}

/* ── AI Explanation Box ── */
.explain-box {
    background: linear-gradient(135deg, rgba(99,102,241,0.06) 0%, rgba(168,85,247,0.04) 100%);
    border: 1px solid rgba(99,102,241,0.18);
    border-left: 3px solid #818cf8;
    border-radius: 0 12px 12px 0;
    padding: 1rem 1.2rem;
    margin: 1rem 0;
    font-size: 0.88rem;
    color: #cbd5e1;
    line-height: 1.6;
    font-style: italic;
}

/* ── Info Pills ── */
.info-pill {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 0.6rem 0.9rem;
    margin: 0.4rem 0;
    font-size: 0.82rem;
    color: #94a3b8;
    display: flex;
    align-items: center;
    gap: 0.6rem;
    backdrop-filter: blur(5px);
}
.info-pill strong { color: #f1f5f9; }

/* ── JD Input & Inputs ── */
.stTextArea textarea, .stTextInput input, .stMultiselect div[data-baseweb="select"] {
    background: rgba(15, 23, 42, 0.4) !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    border-radius: 16px !important;
    color: #f8fafc !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.8rem 1rem !important;
    line-height: 1.6 !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    backdrop-filter: blur(8px) !important;
}
.stTextArea textarea:focus, .stTextInput input:focus, .stMultiselect div[data-baseweb="select"]:focus-within {
    border-color: rgba(167, 139, 250, 0.6) !important;
    box-shadow: 0 0 20px rgba(167, 139, 250, 0.15), inset 0 0 0 1px rgba(167, 139, 250, 0.1) !important;
    background: rgba(15, 23, 42, 0.65) !important;
}

/* ── Primary Button ── */
.stButton > button[kind="primary"],
button[data-testid="baseButton-primary"],
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
    border: 1px solid rgba(167, 139, 250, 0.4) !important;
    border-radius: 14px !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 2.2rem !important;
    letter-spacing: 0.5px !important;
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4), 0 0 15px rgba(168, 85, 247, 0.2) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    text-transform: uppercase !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: auto !important;
}
.stButton > button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(99, 102, 241, 0.6), 0 0 25px rgba(168, 85, 247, 0.4) !important;
    border-color: rgba(167, 139, 250, 0.8) !important;
}

/* ── Standard Button ── */
.stButton > button {
    background: rgba(30, 41, 59, 0.4) !important;
    border: 1px solid rgba(99, 102, 241, 0.22) !important;
    color: #cbd5e1 !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.86rem !important;
    padding: 0.65rem 1.4rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
    width: 100% !important;
}
.stButton > button:hover {
    background: rgba(99, 102, 241, 0.12) !important;
    border-color: rgba(167, 139, 250, 0.5) !important;
    color: #f8fafc !important;
    box-shadow: 0 0 15px rgba(167, 139, 250, 0.22) !important;
    transform: translateY(-2px) !important;
}
.stButton > button:active {
    transform: translateY(0px) !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617 0%, #090d16 100%) !important;
    border-right: 1px solid rgba(99, 102, 241, 0.15) !important;
}
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #f1f5f9;
}

/* ── Slider ── */
.stSlider .stMarkdown { color: #94a3b8; }
.stSlider [data-testid="stSlider"] > div > div > div {
    background: rgba(99,102,241,0.2) !important;
}
.stSlider [data-testid="stSlider"] > div > div > div > div {
    background: linear-gradient(90deg, #6366f1, #a855f7) !important;
}

/* ── Toggle ── */
.stToggle { color: #94a3b8; }

/* ── Status Indicator ── */
.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 6px;
    animation: pulse 2s infinite;
}
.status-dot.green { background: #22c55e; box-shadow: 0 0 8px rgba(34,197,94,0.5); }
.status-dot.red   { background: #ef4444; }
@keyframes pulse {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:0.7; transform:scale(1.1); }
}

/* ── Table ── */
.stDataFrame { border-radius: 12px; overflow: hidden; }
.stDataFrame thead tr th {
    background: rgba(99,102,241,0.15) !important;
    color: #818cf8 !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    border: none !important;
}
.stDataFrame tbody tr:nth-child(even) td { background: rgba(255,255,255,0.02) !important; }
.stDataFrame tbody tr:hover td { background: rgba(99,102,241,0.07) !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: rgba(15, 23, 42, 0.4) !important;
    border: 1px solid rgba(99,102,241,0.18) !important;
    border-radius: 14px !important;
    color: #e2e8f0 !important;
    font-weight: 600 !important;
    padding: 0.8rem 1.2rem !important;
}
.streamlit-expanderContent {
    background: rgba(15, 23, 42, 0.2) !important;
    border: 1px solid rgba(99,102,241,0.12) !important;
    border-top: none !important;
    border-radius: 0 0 14px 14px !important;
}

/* ── Download Button ── */
.stDownloadButton > button {
    background: rgba(34,197,94,0.1) !important;
    border: 1px solid rgba(34,197,94,0.25) !important;
    color: #4ade80 !important;
    border-radius: 10px !important;
    font-size: 0.86rem !important;
    font-weight: 600 !important;
}
.stDownloadButton > button:hover {
    background: rgba(34,197,94,0.2) !important;
    border-color: #22c55e !important;
    box-shadow: 0 0 15px rgba(34,197,94,0.25) !important;
    transform: translateY(-2px) !important;
}

/* ── Custom Alert styling ── */
div[data-testid="stAlert"] {
    background: rgba(15, 23, 42, 0.45) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(8px) !important;
    padding: 1rem !important;
}

/* ── Divider ── */
hr {
    border-color: rgba(99,102,241,0.15) !important;
    margin: 1.5rem 0 !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #818cf8 !important; }

/* ── Warning / Error ── */
.stAlert {
    border-radius: 10px !important;
    border: none !important;
}

/* ── Cinematic Splash Screen Styles ── */
.splash-container {
    position: relative;
    text-align: center;
    padding: 3rem 2rem;
    animation: fadeIn 1s ease-out;
}

.splash-glow-1 {
    position: absolute;
    top: -50px;
    left: 10%;
    width: 250px;
    height: 250px;
    background: radial-gradient(circle, rgba(99,102,241,0.2) 0%, transparent 70%);
    pointer-events: none;
    animation: pulse-glow 8s infinite ease-in-out;
}

.splash-glow-2 {
    position: absolute;
    bottom: -50px;
    right: 10%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 70%);
    pointer-events: none;
    animation: pulse-glow 10s infinite ease-in-out alternate;
}

.splash-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 24px;
    padding: 3.5rem 2rem;
    backdrop-filter: blur(15px);
    box-shadow: 0 25px 60px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.05);
    margin-bottom: 2rem;
}

.splash-logo-container {
    display: inline-block;
    margin-bottom: 1.5rem;
    animation: zoomOut 1.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.splash-logo-img {
    width: 140px;
    height: 140px;
    animation: float 4s ease-in-out infinite;
    filter: drop-shadow(0 0 25px rgba(167, 139, 250, 0.5));
}

.splash-logo {
    font-size: 5.5rem;
    display: inline-block;
    animation: float 4s ease-in-out infinite;
    filter: drop-shadow(0 0 15px rgba(167, 139, 250, 0.6));
}

.splash-title {
    font-size: 3.8rem;
    font-weight: 800;
    margin: 0;
    background: linear-gradient(135deg, #a78bfa 0%, #818cf8 50%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
    line-height: 1.1;
}

.splash-tagline {
    font-size: 1.3rem;
    color: #94a3b8;
    margin-top: 0.8rem;
    margin-bottom: 2rem;
    font-weight: 400;
}

.splash-typing-wrap {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 3rem;
    height: 30px;
}

.splash-typing {
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    color: #818cf8;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    border-right: 2px solid rgba(129, 140, 248, 0.75);
    white-space: nowrap;
    overflow: hidden;
    margin: 0 auto;
    max-width: 650px;
    animation: typing 3s steps(45, end) forwards, blink 0.75s step-end infinite;
}

.splash-features {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
    margin-top: 1rem;
    margin-bottom: 1rem;
    text-align: left;
}

.splash-feat-item {
    background: rgba(255,255,255,0.015);
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 16px;
    padding: 1.5rem;
    transition: transform 0.3s, border-color 0.3s, background 0.3s;
}

.splash-feat-item:hover {
    transform: translateY(-5px);
    border-color: rgba(99, 102, 241, 0.3);
    background: rgba(99, 102, 241, 0.03);
}

.splash-feat-icon {
    font-size: 2rem;
    margin-bottom: 0.75rem;
}

.splash-feat-item h3 {
    font-size: 1.05rem;
    font-weight: 700;
    color: #f1f5f9;
    margin: 0 0 0.5rem;
}

.splash-feat-item p {
    font-size: 0.8rem;
    color: #94a3b8;
    line-height: 1.5;
    margin: 0;
}

/* Animations */
@keyframes float {
    0% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-12px) rotate(3deg); }
    100% { transform: translateY(0px) rotate(0deg); }
}

@keyframes pulse-glow {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.15); opacity: 0.8; }
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(15px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes zoomOut {
    0% { transform: scale(1.6); opacity: 0; filter: blur(8px); }
    100% { transform: scale(1); opacity: 1; filter: blur(0); }
}

@keyframes typing {
    from { width: 0; }
    to { width: 100%; }
}

@keyframes blink {
    from, to { border-color: transparent; }
    50% { border-color: rgba(129, 140, 248, 0.75); }
}

/* ── Pipeline Stepper Styles ── */
.pipeline-stepper {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(99,102,241,0.15);
    border-radius: 14px;
    padding: 1.2rem 2.5rem;
    margin: 1.5rem 0;
    backdrop-filter: blur(10px);
}
.step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.4rem;
    position: relative;
    z-index: 2;
}
.step-icon {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    background: rgba(99,102,241,0.1);
    border: 2px solid #818cf8;
    color: #e2e8f0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    box-shadow: 0 0 10px rgba(99,102,241,0.2);
}
.step-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #94a3b8;
}
.step-line {
    flex-grow: 1;
    height: 2px;
    background: rgba(99,102,241,0.15);
    margin: 0 -10px;
    position: relative;
    top: -10px;
}
.step-line.active {
    background: linear-gradient(90deg, #818cf8, #a78bfa);
    box-shadow: 0 0 8px rgba(129,140,248,0.5);
}
</style>
""")

st.markdown(base_css, unsafe_allow_html=True)


# ── Load Logo Base64 ──────────────────────────────────────────────────────────

def get_base64_image(image_path):
    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
                return f"data:image/png;base64,{encoded_string}"
    except Exception:
        pass
    return None

logo_base64 = get_base64_image("ui/logo.png")


# ── Routing: Splash Screen ─────────────────────────────────────────────────────

if not st.session_state["entered"]:
    # Apply strict sidebar-hiding styles
    sidebar_hide_style = clean_html("""
        <style>
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        .block-container {
            max-width: 950px !important;
            padding-top: 3rem !important;
        }
        </style>
    """)
    st.markdown(sidebar_hide_style, unsafe_allow_html=True)

    # Resolve logo html element
    if logo_base64:
        logo_html = f'<div class="splash-logo-container"><img src="{logo_base64}" class="splash-logo-img"></div>'
    else:
        logo_html = '<div class="splash-logo-container"><div class="splash-logo">🧠</div></div>'

    splash_html = clean_html(f"""
        <div class="splash-container">
            <div class="splash-glow-1"></div>
            <div class="splash-glow-2"></div>
            
            <div class="splash-card">
                {logo_html}
                <h1 class="splash-title">RecruitMind AI</h1>
                <p class="splash-tagline">Next-Generation Agentic Talent Discovery Platform</p>
                
                <div class="splash-typing-wrap">
                    <span class="splash-typing">Deep Semantic Matching &nbsp;•&nbsp; Multi-Signal Scoring &nbsp;•&nbsp; Explainable Agent Shortlists</span>
                </div>
                
                <div class="splash-features">
                    <div class="splash-feat-item">
                        <div class="splash-feat-icon">🔍</div>
                        <h3>Cognitive JD Parsing</h3>
                        <p>Uses LLMs to extract core skills, seniority requirements, culture fits, and implicit developer expectations.</p>
                    </div>
                    <div class="splash-feat-item">
                        <div class="splash-feat-icon">📊</div>
                        <h3>Multi-Signal Engine</h3>
                        <p>Computes composite scores across semantic search, skill matching, career growth, stability, and notice period fit.</p>
                    </div>
                    <div class="splash-feat-item">
                        <div class="splash-feat-icon">💡</div>
                        <h3>Explainable AI Shortlists</h3>
                        <p>Generates natural language Recruiter Notes for candidates, providing clear, human-readable reasoning for every match.</p>
                    </div>
                </div>
            </div>
        </div>
    """)
    st.markdown(splash_html, unsafe_allow_html=True)
    
    col_btn_1, col_btn_2, col_btn_3 = st.columns([1, 2, 1])
    with col_btn_2:
        if st.button("Launch Recruiter Workspace ⚡", use_container_width=True, type="primary"):
            st.session_state["entered"] = True
            st.rerun()
    st.stop()


# ── Helpers ────────────────────────────────────────────────────────────────────

def score_color_class(score):
    if score >= 0.70: return "score-high"
    if score >= 0.50: return "score-mid"
    return "score-low"

def score_bar_color(score):
    if score >= 0.70: return "#22c55e"
    if score >= 0.50: return "#f59e0b"
    return "#ef4444"

def render_score_ring(score):
    pct = round(score * 100)
    cls = score_color_class(score)
    deg = round(score * 360)
    return clean_html(f"""
        <div class="score-ring-wrap">
            <div class="score-ring {cls}" style="--pct:{deg}deg">
                <div class="score-inner">{pct}%</div>
            </div>
            <div style="font-size:0.65rem;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Match</div>
        </div>
    """)

def render_rank_badge(rank):
    if rank == 1:   return f'<div class="rank-badge rank-1">#{rank}</div>'
    if rank == 2:   return f'<div class="rank-badge rank-2">#{rank}</div>'
    if rank == 3:   return f'<div class="rank-badge rank-3">#{rank}</div>'
    return f'<div class="rank-badge rank-other">#{rank}</div>'

def render_skill_tags(skills, matched_set):
    html = ""
    for s in skills:
        cls = "skill-matched" if s.lower() in matched_set else ""
        html += f'<span class="skill-tag {cls}">{s}</span>'
    return html

def render_score_bar(label, val):
    color = score_bar_color(val)
    pct = round(val * 100)
    return clean_html(f"""
        <div class="score-bar-wrap">
            <div class="score-bar-label"><span>{label}</span><span style="color:{color};font-weight:700">{pct}%</span></div>
            <div class="score-bar-bg"><div class="score-bar-fill" style="width:{pct}%;background:{color}"></div></div>
        </div>
    """)

def check_api():
    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    if logo_base64:
        sidebar_logo_html = f'<div style="background:white; border-radius:16px; padding:4px; display:inline-block; margin-bottom: 0.8rem; box-shadow: 0 8px 25px rgba(99, 102, 241, 0.25); border:1px solid rgba(167, 139, 250, 0.2);"><img src="{logo_base64}" style="width: 65px; height: 65px; border-radius: 12px; display:block;"></div>'
    else:
        sidebar_logo_html = '<div style="font-size:2.5rem;">🧠</div>'

    sidebar_title = clean_html(f"""
        <div style="text-align:center;padding:1rem 0 0.5rem">
            {sidebar_logo_html}
            <div style="font-size:1.1rem;font-weight:800;background:linear-gradient(135deg,#a78bfa,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">RecruitMind AI</div>
            <div style="font-size:0.72rem;color:#475569;margin-top:0.25rem;font-weight:500;letter-spacing:0.5px;text-transform:uppercase;">Intelligent Talent Discovery</div>
        </div>
    """)
    st.markdown(sidebar_title, unsafe_allow_html=True)
    st.divider()

    # API Status
    health = check_api()
    if health:
        status_box = clean_html(f"""
            <div style="background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.2);border-radius:10px;padding:0.8rem 1rem;margin-bottom:0.8rem">
                <div style="font-size:0.8rem;font-weight:700;color:#4ade80;margin-bottom:0.5rem">
                    <span class="status-dot green"></span>System Online
                </div>
                <div style="font-size:0.75rem;color:#64748b">
                    <div>📦 <strong style="color:#94a3b8">{health.get('candidates_indexed',0)}</strong> candidates indexed</div>
                    <div style="margin-top:4px">🤖 LLM: <strong style="color:#94a3b8">{"Groq Llama-3.3" if health.get("llm_available") else "Offline (rule-based)"}</strong></div>
                    <div style="margin-top:4px">🔧 v{health.get('version','1.0.0')}</div>
                </div>
            </div>
        """)
        st.markdown(status_box, unsafe_allow_html=True)
    else:
        offline_box = clean_html("""
            <div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);border-radius:10px;padding:0.8rem 1rem;margin-bottom:0.8rem">
                <div style="font-size:0.8rem;font-weight:700;color:#f87171">
                    <span class="status-dot red"></span>API Offline
                </div>
                <div style="font-size:0.72rem;color:#64748b;margin-top:4px">Run: uvicorn api.main:app</div>
            </div>
        """)
        st.markdown(offline_box, unsafe_allow_html=True)

    st.markdown('<div style="font-size:0.75rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.6rem">⚙️ Ranking Settings</div>', unsafe_allow_html=True)

    top_k = st.slider("Candidates to return", min_value=3, max_value=20, value=10, help="Number of top candidates to rank")
    with_explanations = st.toggle("AI Reasoning Cards", value=True, help="Generate LLM-powered recruiter notes per candidate")
    show_breakdown = st.toggle("Score Breakdown", value=True, help="Show individual signal scores")

    # Dynamic Filters Section (only active when data loaded)
    selected_locations = []
    min_match_pct = 0
    max_notice_days = 90
    max_salary_lpa = 50

    if "last_result" in st.session_state:
        st.divider()
        st.markdown('<div style="font-size:0.75rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.6rem">🔍 Interactive Filters</div>', unsafe_allow_html=True)
        
        raw_shortlist = st.session_state["last_result"].get("shortlist", [])
        
        # Get locations
        all_locations = sorted(list(set(c.get("metadata", {}).get("location", "—") for c in raw_shortlist if c.get("metadata"))))
        selected_locations = st.multiselect("Filter by Locations", options=all_locations, default=all_locations)
        
        # Match score slider
        min_match_pct = st.slider("Min Match Score %", min_value=0, max_value=100, value=0)
        
        # Notice period slider
        max_notice_days = st.slider("Max Notice Days", min_value=0, max_value=90, value=90, step=15)
        
        # Expected salary
        max_salary_lpa = st.slider("Max Salary (LPA)", min_value=0, max_value=50, value=50, step=5)

    st.divider()
    st.markdown('<div style="font-size:0.75rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.6rem">🔄 Data Actions</div>', unsafe_allow_html=True)
    if st.button("Re-index Candidates", use_container_width=True):
        try:
            requests.post(f"{API_URL}/index", json={"candidates_path": "data/candidates.json"}, timeout=5)
            st.success("Indexing started in background!")
        except Exception as e:
            st.error(f"Failed: {e}")

    # Return to splash screen button
    if st.button("↩️ Return to Intro", use_container_width=True):
        st.session_state["entered"] = False
        st.rerun()

    st.divider()
    scoring_weights = clean_html("""
        <div style="font-size:0.68rem;color:#334155;text-align:center;line-height:1.7">
            <div style="font-weight:600;color:#475569;margin-bottom:0.3rem">Scoring Weights</div>
            Semantic Similarity → 35%<br>
            Skill Match → 30%<br>
            Career Growth → 15%<br>
            Activity Signal → 10%<br>
            Experience Fit → 10%
        </div>
    """)
    st.markdown(scoring_weights, unsafe_allow_html=True)


# ── Hero Banner ────────────────────────────────────────────────────────────────

if logo_base64:
    hero_logo_html = f'<div style="background:white; border-radius:12px; padding:3px; display:inline-flex; align-items:center; justify-content:center; box-shadow:0 8px 20px rgba(99, 102, 241, 0.25); border:1px solid rgba(167, 139, 250, 0.2);"><img src="{logo_base64}" style="width: 45px; height: 45px; border-radius: 9px; display:block;"></div>'
else:
    hero_logo_html = '<span style="font-size:2.5rem">🧠</span>'

hero_banner_html = clean_html(f"""
    <div class="hero-banner">
        <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.5rem">
            {hero_logo_html}
            <div>
                <div class="hero-title">RecruitMind AI</div>
                <div class="hero-sub">Agentic AI Recruiter · Multi-Signal Ranking · Explainable Shortlists</div>
            </div>
        </div>
        <div class="hero-badges">
            <span class="hero-badge">LangGraph Pipeline</span>
            <span class="hero-badge">ChromaDB Vector Search</span>
            <span class="hero-badge">Groq Llama-3.3</span>
            <span class="hero-badge">Sentence Transformers</span>
            <span class="hero-badge">FastAPI Backend</span>
        </div>
    </div>
""")
st.markdown(hero_banner_html, unsafe_allow_html=True)


# ── JD Input Section ───────────────────────────────────────────────────────────

col_input, col_templates = st.columns([3, 1], gap="large")

with col_input:
    st.markdown(clean_html("""
        <div class="section-header">
            <span class="accent"></span>Job Description Input
        </div>
    """), unsafe_allow_html=True)

    jd_default = """We are looking for a Senior Python Developer / ML Engineer to join our AI team in Bengaluru.

Requirements:
- 4+ years of experience in Python
- Strong knowledge of FastAPI, REST APIs, and microservices
- Experience with Machine Learning pipelines (LangChain, RAG, LLMs)
- Docker and Kubernetes knowledge
- Experience with PostgreSQL and Redis

Nice to have:
- AWS or GCP experience
- Open source contributions
- Knowledge of vector databases (Pinecone, ChromaDB)

You will build AI-powered backend services, collaborate with the ML team, and maintain production systems serving millions of users."""

    if "jd_text" in st.session_state:
        jd_val = st.session_state["jd_text"]
    else:
        jd_val = jd_default

    jd_text = st.text_area(
        "Job Description",
        value=jd_val,
        height=300,
        placeholder="Paste your full job description here...",
        label_visibility="collapsed"
    )

    run_clicked = st.button("🚀  Find Best Candidates", type="primary", use_container_width=False)

with col_templates:
    st.markdown(clean_html("""
        <div class="section-header">
            <span class="accent"></span>Quick Templates
        </div>
    """), unsafe_allow_html=True)

    templates = {
        "🤖 ML Engineer":     "Senior ML Engineer, 4+ years. Python, TensorFlow, PyTorch, LangChain, FastAPI, Docker, AWS. Build and deploy ML models at scale. RAG pipelines and LLMs required.",
        "⚙️ Backend Dev":     "Backend Developer, 3+ years. Python, Node.js, REST API, PostgreSQL, Redis, Docker. Build scalable microservices. CI/CD and cloud platforms.",
        "🌐 Full Stack":      "Full Stack Developer, 2+ years. React, Node.js, Python, MongoDB, Docker, REST API. Build end-to-end web apps with modern frameworks.",
        "📊 Data Engineer":   "Data Engineer, 3+ years. Python, Spark, Airflow, SQL, BigQuery, dbt, Kafka. Build robust data pipelines and ETL processes.",
        "🛠️ DevOps Engineer": "DevOps Engineer, 3+ years. Kubernetes, Docker, AWS, Terraform, Jenkins, CI/CD, Linux, Python. Cloud infrastructure and deployment pipelines.",
    }

    for tname, tjd in templates.items():
        if st.button(tname, use_container_width=True):
            st.session_state["jd_text"] = tjd
            st.rerun()

    tips_html = clean_html("""
        <div style="background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.15);border-radius:10px;padding:0.8rem;margin-top:0.8rem;font-size:0.75rem;color:#64748b;line-height:1.6">
            <div style="font-weight:700;color:#818cf8;margin-bottom:0.4rem">💡 Tips for best results</div>
            Include role title, required skills, years of experience, and tech stack. More detail = better ranking.
        </div>
    """)
    st.markdown(tips_html, unsafe_allow_html=True)


# ── Results ────────────────────────────────────────────────────────────────────

if run_clicked:
    if not jd_text.strip() or len(jd_text.strip()) < 30:
        st.error("⚠️ Please enter a valid job description (at least 30 characters).")
    else:
        with st.status("Analyzing and ranking candidates...") as status:
            status.write("🔍 Parsing Job Description (LLM/Rule-based)...")
            time.sleep(0.4)
            status.write("🧠 Embedding Job Description & building query vector...")
            time.sleep(0.4)
            status.write("🎯 Querying vector DB (ChromaDB) for candidate matches...")
            time.sleep(0.4)
            status.write("📊 Computing multi-signal scoring (Skills, Career Growth, Activity, Experience)...")
            time.sleep(0.4)
            status.write("⚖️ Applying diversity-boosted re-ranking...")
            time.sleep(0.4)
            status.write("🤖 Generating final explainable candidate profiles...")
            try:
                payload = {"jd_text": jd_text, "top_k": top_k, "with_explanations": with_explanations}
                response = requests.post(f"{API_URL}/rank", json=payload, timeout=120)
                if response.status_code != 200:
                    status.update(label="Failed to analyze candidates", state="error")
                    st.error(f"API Error {response.status_code}: {response.text}")
                    st.stop()
                data = response.json()
                status.update(label="Candidates successfully analyzed!", state="complete")
                st.session_state["last_result"] = data
                st.session_state["last_jd"] = jd_text
                st.rerun()
            except requests.exceptions.ConnectionError:
                status.update(label="API connection failed", state="error")
                st.error("❌ Cannot connect to API. Make sure FastAPI is running on port 8000.")
                st.stop()
            except Exception as e:
                status.update(label="An error occurred", state="error")
                st.error(f"Error: {e}")
                st.stop()

if "last_result" in st.session_state:
    data       = st.session_state["last_result"]
    shortlist  = data.get("shortlist", [])
    parsed_jd  = data.get("parsed_jd", {})
    elapsed    = data.get("processing_time_sec", 0)
    total_eval = data.get("total_candidates_evaluated", 0)
    req_skills_set = {s.lower() for s in parsed_jd.get("required_skills", [])}

    if data.get("warning"):
        st.warning(f"⚠️ {data['warning']}")

    # Apply interactive filters (Local shortlisting)
    filtered_shortlist = []
    for c in shortlist:
        meta = c.get("metadata", {})
        loc = meta.get("location", "—")
        pct = round(c.get("composite_score", 0) * 100, 1)
        notice = meta.get("notice_period_days", 0)
        sal = meta.get("expected_salary_lpa", 0)
        
        # Perform filter checks
        loc_ok = (loc in selected_locations) if selected_locations else True
        pct_ok = (pct >= min_match_pct)
        notice_ok = (notice <= max_notice_days)
        sal_ok = (sal <= max_salary_lpa)
        
        if loc_ok and pct_ok and notice_ok and sal_ok:
            filtered_shortlist.append(c)

    # ── Metrics Row ────────────────────────────────────────────────────────────
    metrics_row_html = clean_html(f"""
        <div class="metric-row">
            <div class="metric-card">
                <div class="metric-value">{len(filtered_shortlist)}</div>
                <div class="metric-label">Filtered Shortlist</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_eval}</div>
                <div class="metric-label">Total Evaluated</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{elapsed}s</div>
                <div class="metric-label">Processing Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{len(parsed_jd.get("required_skills", []))}</div>
                <div class="metric-label">Skills Extracted</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{parsed_jd.get("seniority_level","—").capitalize()}</div>
                <div class="metric-label">Seniority Level</div>
            </div>
        </div>
    """)
    st.markdown(metrics_row_html, unsafe_allow_html=True)

    # ── AI Pipeline Stepper ────────────────────────────────────────────────────
    stepper_html = clean_html("""
        <div class="pipeline-stepper">
            <div class="step">
                <div class="step-icon">📝</div>
                <div class="step-label">JD Processed</div>
            </div>
            <div class="step-line active"></div>
            <div class="step">
                <div class="step-icon">🔍</div>
                <div class="step-label">Vector Search</div>
            </div>
            <div class="step-line active"></div>
            <div class="step">
                <div class="step-icon">⚖️</div>
                <div class="step-label">Multi-Signal Score</div>
            </div>
            <div class="step-line active"></div>
            <div class="step">
                <div class="step-icon">🤖</div>
                <div class="step-label">Llama Recruiter Note</div>
            </div>
        </div>
    """)
    st.markdown(stepper_html, unsafe_allow_html=True)

    # ── Parsed JD Expander ─────────────────────────────────────────────────────
    with st.expander("🔍  Parsed Job Requirements  (AI-extracted structure)", expanded=False):
        pjc1, pjc2, pjc3 = st.columns(3)
        with pjc1:
            st.markdown(f"**Job Title:** {parsed_jd.get('job_title','—')}")
            st.markdown(f"**Role Type:** {parsed_jd.get('role_type','—')}")
            st.markdown(f"**Experience:** {parsed_jd.get('min_experience_years',0)}+ years")
            st.markdown(f"**Seniority:** {parsed_jd.get('seniority_level','—').capitalize()}")
        with pjc2:
            req = parsed_jd.get("required_skills", [])
            if req:
                tags = "".join([f'<span class="skill-tag skill-matched">{s}</span>' for s in req])
                st.markdown(f"**Required Skills:**<br>{tags}", unsafe_allow_html=True)
        with pjc3:
            nice = parsed_jd.get("nice_to_have_skills", [])
            if nice:
                tags = "".join([f'<span class="skill-tag">{s}</span>' for s in nice])
                st.markdown(f"**Nice to Have:**<br>{tags}", unsafe_allow_html=True)
            summ = parsed_jd.get("summary","")
            if summ:
                st.markdown(f"**Summary:** {summ}")

    # ── Leaderboard Table ──────────────────────────────────────────────────────
    st.markdown(clean_html("""
        <div class="section-header" style="margin-top:1.2rem">
            <span class="accent"></span>🏆 Ranked Shortlist — Leaderboard View
        </div>
    """), unsafe_allow_html=True)

    if not filtered_shortlist:
        st.info("No candidates match your current filter criteria. Try expanding search variables in the sidebar.")
    else:
        req_skills_lower = [s.lower() for s in parsed_jd.get("required_skills", [])]
        table_rows = []
        for c in filtered_shortlist:
            meta = c.get("metadata", {})
            skills = [s.strip() for s in meta.get("skills", "").split(",")] if isinstance(meta.get("skills"), str) else meta.get("skills", [])
            matched = sum(1 for s in skills if s.lower() in req_skills_set)
            pct = round(c.get("composite_score", 0) * 100, 1)
            table_rows.append({
                "Rank": f"#{c.get('rank')}",
                "Name": c.get("name", "—"),
                "Match %": f"{pct}%",
                "Experience": f"{meta.get('years_experience',0)}y ({meta.get('seniority','').capitalize()})",
                "Skills Hit": f"{matched}/{len(req_skills_lower)}",
                "Location": meta.get("location", "—"),
                "Salary (LPA)": f"₹{meta.get('expected_salary_lpa',0)}",
                "Notice": f"{meta.get('notice_period_days',0)}d",
            })
        
        df = pd.DataFrame(table_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # ── Side-by-Side Candidate Comparison ──────────────────────────────────
        st.markdown(clean_html("""
            <div class="section-header" style="margin-top:1.5rem">
                <span class="accent"></span>⚖️ Side-by-Side Candidate Comparison
            </div>
        """), unsafe_allow_html=True)

        compare_candidates = st.multiselect(
            "Select candidates to compare side-by-side:",
            options=[c.get("name", "—") for c in filtered_shortlist],
            max_selections=3,
            placeholder="Choose up to 3 candidates to compare...",
            label_visibility="collapsed"
        )

        if compare_candidates:
            comp_cols = st.columns(len(compare_candidates))
            for idx, cname in enumerate(compare_candidates):
                cand_data = next((c for c in filtered_shortlist if c.get("name") == cname), None)
                if cand_data:
                    meta = cand_data.get("metadata", {})
                    scores = cand_data.get("score_breakdown", {})
                    comp_score = cand_data.get("composite_score", 0)
                    rank = cand_data.get("rank", 0)
                    
                    with comp_cols[idx]:
                        # Render card wrapper
                        comp_card_start = clean_html(f"""
                            <div class="candidate-card top-3" style="margin: 0; min-height: 480px;">
                                <div style="text-align: center; margin-bottom: 1rem;">
                                    <span style="font-size: 1.5rem;">{'🥇' if rank==1 else '🥈' if rank==2 else '🥉' if rank==3 else '🎯'} #{rank}</span>
                                    <h4 style="margin: 5px 0 2px 0; color: #f1f5f9; font-size: 1.1rem; font-weight: 700;">{cname}</h4>
                                    <span style="font-size: 0.72rem; color: #64748b;">{meta.get('seniority','').capitalize()} · {meta.get('location')}</span>
                                </div>
                        """)
                        st.markdown(comp_card_start, unsafe_allow_html=True)
                        
                        st.markdown(render_score_ring(comp_score), unsafe_allow_html=True)
                        
                        comp_card_middle = clean_html(f"""
                            <div class="info-pill" style="margin: 4px 0; background: rgba(255,255,255,0.02);">💼 Experience: <strong>{meta.get('years_experience')} yrs</strong></div>
                            <div class="info-pill" style="margin: 4px 0; background: rgba(255,255,255,0.02);">💰 Expected: <strong>₹{meta.get('expected_salary_lpa')} LPA</strong></div>
                            <div class="info-pill" style="margin: 4px 0; background: rgba(255,255,255,0.02);">⏱️ Notice: <strong>{meta.get('notice_period_days')} days</strong></div>
                            <div class="info-pill" style="margin: 4px 0; background: rgba(255,255,255,0.02);">📧 Email: <strong>{meta.get('email')}</strong></div>
                        """)
                        st.markdown(comp_card_middle, unsafe_allow_html=True)
                        
                        st.markdown('<div style="font-size:0.7rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.5px; margin: 1rem 0 0.5rem 0;">Signals Breakdown</div>', unsafe_allow_html=True)
                        st.markdown(render_score_bar("Semantic Similarity", scores.get("semantic_similarity", 0)), unsafe_allow_html=True)
                        st.markdown(render_score_bar("Skill Match Score", scores.get("skill_match", 0)), unsafe_allow_html=True)
                        st.markdown(render_score_bar("Career Growth Fit", scores.get("career_growth", 0)), unsafe_allow_html=True)
                        
                        explanation = cand_data.get("explanation", "")
                        if explanation:
                            short_exp = explanation if len(explanation) < 140 else explanation[:137] + "..."
                            comp_card_explain = clean_html(f"""
                                <div class="explain-box" style="margin-top: 1rem; font-size: 0.78rem; padding: 0.6rem 0.8rem; line-height:1.4;">
                                    🤖 <strong>AI Recruiter Note:</strong> {short_exp}
                                </div>
                            """)
                            st.markdown(comp_card_explain, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)

        # ── Detailed Candidate Profiles ───────────────────────────────────────────
        st.markdown(clean_html("""
            <div class="section-header" style="margin-top:1.5rem">
                <span class="accent"></span>📋 Detailed Candidate Profiles
            </div>
        """), unsafe_allow_html=True)

        for c in filtered_shortlist:
            meta   = c.get("metadata", {})
            scores = c.get("score_breakdown", {})
            comp   = c.get("composite_score", 0)
            rank   = c.get("rank", 0)
            name   = c.get("name", "—")
            pct    = round(comp * 100, 1)
            is_top = rank <= 3

            skills_raw = meta.get("skills", [])
            if isinstance(skills_raw, str):
                skills_raw = [s.strip() for s in skills_raw.split(",")]

            with st.expander(
                f"{'🥇' if rank==1 else '🥈' if rank==2 else '🥉' if rank==3 else '🎯'}  #{rank}  ·  {name}  ·  {pct}% match",
                expanded=(rank <= 3)
            ):
                left, right = st.columns([3, 1])

                with left:
                    rank_badge_html = render_rank_badge(rank)
                    expander_header_html = clean_html(f"""
                        <div style="display:flex;align-items:center;margin-bottom:1rem">
                            {rank_badge_html}
                            <div>
                                <div style="font-size:1.1rem;font-weight:700;color:#e2e8f0">{name}</div>
                                <div style="font-size:0.78rem;color:#64748b">{meta.get('seniority','').capitalize()} · {meta.get('role_type','').upper()} · {meta.get('location','—')}</div>
                            </div>
                        </div>
                    """)
                    st.markdown(expander_header_html, unsafe_allow_html=True)

                    explanation = c.get("explanation", "")
                    if explanation:
                        st.markdown(clean_html(f'<div class="explain-box">🤖 <strong>AI Recruiter Note:</strong> {explanation}</div>'), unsafe_allow_html=True)

                    if skills_raw:
                        skill_html = render_skill_tags(skills_raw, req_skills_set)
                        expander_skills_html = clean_html(f"""
                            <div style="margin:0.8rem 0 0.3rem">
                                <div style="font-size:0.72rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.4rem">Skills</div>
                                {skill_html}
                            </div>
                            <div style="font-size:0.68rem;color:#334155;margin-top:4px">
                                🟢 Highlighted = matches JD requirement
                            </div>
                        """)
                        st.markdown(expander_skills_html, unsafe_allow_html=True)

                    certs = meta.get("certifications", [])
                    if isinstance(certs, str):
                        certs = [ct.strip() for ct in certs.split(",") if ct.strip()]
                    if certs:
                        st.markdown(clean_html(f'<div style="font-size:0.8rem;color:#94a3b8;margin-top:0.6rem">🏅 <strong>Certs:</strong> {", ".join(certs)}</div>'), unsafe_allow_html=True)

                with right:
                    st.markdown(render_score_ring(comp), unsafe_allow_html=True)

                    expander_right_info = clean_html(f"""
                        <div style="margin-top:0.8rem">
                            <div class="info-pill">📧 <strong>{meta.get('email','—')}</strong></div>
                            <div class="info-pill">💼 <strong>{meta.get('years_experience',0)} yrs</strong> experience</div>
                            <div class="info-pill">💰 <strong>₹{meta.get('expected_salary_lpa',0)} LPA</strong></div>
                            <div class="info-pill">⏱️ <strong>{meta.get('notice_period_days',0)} days</strong> notice</div>
                        </div>
                    """)
                    st.markdown(expander_right_info, unsafe_allow_html=True)

                    if show_breakdown:
                        st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;margin:0.8rem 0 0.4rem">Score Breakdown</div>', unsafe_allow_html=True)
                        breakdown_labels = [
                            ("Semantic", "semantic_similarity"),
                            ("Skill Match", "skill_match"),
                            ("Career Growth", "career_growth"),
                            ("Activity", "activity"),
                            ("Exp Fit", "experience_fit"),
                        ]
                        bars_html = ""
                        for label, key in breakdown_labels:
                            val = scores.get(key, 0)
                            bars_html += render_score_bar(label, val)
                        st.markdown(bars_html, unsafe_allow_html=True)

        # ── Export ────────────────────────────────────────────────────────────
        st.divider()
        st.markdown(clean_html("""
            <div class="section-header">
                <span class="accent"></span>📥 Export Results
            </div>
        """), unsafe_allow_html=True)

        exp1, exp2 = st.columns(2)
        with exp1:
            st.download_button(
                "⬇️ Download Full Results (JSON)",
                data=json.dumps(data, indent=2),
                file_name="recruitmind_results.json",
                mime="application/json",
                use_container_width=True
            )
        with exp2:
            csv_rows = []
            for c in filtered_shortlist:
                meta = c.get("metadata", {})
                sc   = c.get("score_breakdown", {})
                skills_val = meta.get("skills", [])
                if isinstance(skills_val, list):
                    skills_val = ", ".join(skills_val)
                csv_rows.append({
                    "Rank": c.get("rank"), "Name": c.get("name"),
                    "Score %": round(c.get("composite_score",0)*100, 1),
                    "Experience": meta.get("years_experience",0),
                    "Seniority": meta.get("seniority",""),
                    "Location": meta.get("location",""),
                    "Skills": skills_val,
                    "Salary LPA": meta.get("expected_salary_lpa",0),
                    "Notice Days": meta.get("notice_period_days",0),
                    "Semantic": round(sc.get("semantic_similarity",0)*100,1),
                    "Skill Match": round(sc.get("skill_match",0)*100,1),
                    "Career Growth": round(sc.get("career_growth",0)*100,1),
                    "Activity": round(sc.get("activity",0)*100,1),
                    "Explanation": c.get("explanation",""),
                })
            csv_df = pd.DataFrame(csv_rows)
            st.download_button(
                "⬇️ Download Shortlist (CSV)",
                data=csv_df.to_csv(index=False),
                file_name="recruitmind_shortlist.csv",
                mime="text/csv",
                use_container_width=True
            )

# ── Candidate Comparison Section ─────────────────────────────────────────────
st.divider()
st.markdown(clean_html("""
    <div class="section-header">
        <span class="accent"></span>⚖️ Side-by-Side Candidate Comparison
    </div>
"""), unsafe_allow_html=True)
st.caption("Select 2 or 3 candidates from the shortlist above to compare them directly.")

if "last_result" in st.session_state:
    shortlist = st.session_state["last_result"].get("shortlist", [])
    if shortlist:
        candidate_options = {
            f"#{c.get('rank')} {c.get('name')} ({round(c.get('composite_score', 0) * 100, 1)}%)": c.get("candidate_id")
            for c in shortlist
        }
        selected_labels = st.multiselect(
            "Choose 2 or 3 candidates to compare",
            options=list(candidate_options.keys()),
            max_selections=3
        )
        if len(selected_labels) >= 2:
            selected_ids = [candidate_options[label] for label in selected_labels]
            jd_for_compare = st.session_state.get("last_jd", "")
            if st.button("🔍 Compare Selected Candidates", use_container_width=True):
                try:
                    compare_response = requests.post(
                        f"{API_URL}/compare",
                        json={"candidate_ids": selected_ids, "jd_text": jd_for_compare},
                        timeout=30
                    )
                    if compare_response.status_code == 200:
                        compare_data = compare_response.json()
                        comparison = compare_data.get("comparison", [])
                        cols = st.columns(len(comparison))
                        for col, cand in zip(cols, comparison):
                            with col:
                                scores = cand.get("scores", {})
                                composite = scores.get("composite", 0)
                                name = cand.get("name", "")
                                loc = cand.get("location", "")
                                seniority = cand.get("seniority", "")
                                yexp = cand.get("years_experience", 0)
                                skills = cand.get("skills", [])
                                
                                card_start = clean_html(f"""
                                    <div class="candidate-card" style="margin: 0; min-height: 480px;">
                                        <div style="text-align: center; margin-bottom: 1rem;">
                                            <h4 style="margin: 5px 0 2px 0; color: #f1f5f9; font-size: 1.1rem; font-weight: 700;">{name}</h4>
                                            <span style="font-size: 0.72rem; color: #64748b;">{seniority.capitalize()} · {loc}</span>
                                        </div>
                                """)
                                st.markdown(card_start, unsafe_allow_html=True)
                                
                                st.markdown(render_score_ring(composite), unsafe_allow_html=True)
                                
                                card_middle = clean_html(f"""
                                    <div class="info-pill" style="margin: 4px 0; background: rgba(255,255,255,0.02);">💼 Experience: <strong>{yexp} yrs</strong></div>
                                    <div class="info-pill" style="margin: 4px 0; background: rgba(255,255,255,0.02);">📍 Location: <strong>{loc}</strong></div>
                                """)
                                st.markdown(card_middle, unsafe_allow_html=True)
                                
                                st.markdown('<div style="font-size:0.7rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.5px; margin: 1rem 0 0.5rem 0;">Signals Breakdown</div>', unsafe_allow_html=True)
                                st.markdown(render_score_bar("Semantic", scores.get("semantic", 0)), unsafe_allow_html=True)
                                st.markdown(render_score_bar("Skill Match", scores.get("skill_match", 0)), unsafe_allow_html=True)
                                st.markdown(render_score_bar("Career Growth", scores.get("career_growth", 0)), unsafe_allow_html=True)
                                st.markdown(render_score_bar("Activity Signal", scores.get("activity", 0)), unsafe_allow_html=True)
                                
                                if skills:
                                    skill_tags = "".join([f'<span class="skill-tag">{s}</span>' for s in skills[:6]])
                                    st.markdown(f'<div style="margin-top:0.8rem;line-height:1.4;">{skill_tags}</div>', unsafe_allow_html=True)
                                    
                                st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.error("Comparison failed. Make sure API is running.")
                except Exception as e:
                    st.error(f"Error: {e}")
        elif len(selected_labels) == 1:
            st.info("Select at least one more candidate to compare.")
    else:
        st.info("Run a search first to get candidates to compare.")
else:
    st.info("Run a search first to get candidates to compare.")

# ── JD Bias Checker Section ───────────────────────────────────────────────────
st.divider()
st.markdown(clean_html("""
    <div class="section-header">
        <span class="accent"></span>🔍 JD Bias Checker
    </div>
"""), unsafe_allow_html=True)
st.caption("Paste any job description to check for potentially biased language before posting.")

bias_jd = st.text_area(
    "Paste JD to check for bias",
    height=120,
    placeholder="Paste your job description here to check for biased language...",
    key="bias_jd_input",
    label_visibility="collapsed"
)
if st.button("🔎 Check for Bias", use_container_width=False):
    if bias_jd.strip():
        try:
            bias_response = requests.post(
                f"{API_URL}/bias-check",
                json={"jd_text": bias_jd},
                timeout=15
            )
            if bias_response.status_code == 200:
                bias_data = bias_response.json()
                level = bias_data.get("bias_level", "Low")
                flags = bias_data.get("bias_flags", [])
                score = bias_data.get("bias_score", 0)
                color = "#ef4444" if level == "High" else ("#f59e0b" if level == "Medium" else "#22c55e")
                st.markdown(clean_html(f"""
                    <div style="padding: 1.2rem; border-radius: 16px; background: rgba(15,23,42,0.4); border: 1px solid rgba(99,102,241,0.25); backdrop-filter: blur(10px); box-shadow: 0 10px 30px rgba(0,0,0,0.3); margin-bottom: 1.2rem; display: flex; gap: 1.5rem; justify-content: space-around; text-align: center;">
                        <div>
                            <div style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem;">Bias Level</div>
                            <div style="font-size: 1.4rem; font-weight: 800; color: {color};">{level}</div>
                        </div>
                        <div style="width: 1px; background: rgba(255,255,255,0.06);"></div>
                        <div>
                            <div style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem;">Flags Found</div>
                            <div style="font-size: 1.4rem; font-weight: 800; color: #f1f5f9;">{len(flags)}</div>
                        </div>
                        <div style="width: 1px; background: rgba(255,255,255,0.06);"></div>
                        <div>
                            <div style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem;">Bias Score</div>
                            <div style="font-size: 1.4rem; font-weight: 800; color: #818cf8;">{score}/100</div>
                        </div>
                    </div>
                """), unsafe_allow_html=True)
                if flags:
                    st.markdown("**Flagged Terms:**")
                    for flag in flags:
                        st.warning(f"⚠️ **\"{flag['term']}\"** — {flag['reason']} Suggestion: {flag['suggestion']}")
                else:
                    st.success("✅ No obvious bias detected. JD language appears neutral and inclusive.")
                st.caption(bias_data.get("recommendation", ""))
            else:
                st.error("Bias check failed.")
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please paste a job description first.")

# ── Footer ──────────────────────────────────────────────────────────────────────

st.markdown(clean_html("""
    <div style="text-align:center;padding:1.5rem 0 0.5rem;border-top:1px solid rgba(99,102,241,0.1);margin-top:2rem">
        <div style="font-size:0.75rem;color:#334155;font-weight:500">
            <span style="color:#818cf8;font-weight:700">RecruitMind AI</span>
            &nbsp;·&nbsp; Built with LangGraph · ChromaDB · Groq Llama-3.3 · FastAPI · Streamlit
        </div>
        <div style="font-size:0.68rem;color:#1e293b;margin-top:0.3rem">
            Vinay Babannavar · T. John Institute of Technology, Bengaluru
        </div>
    </div>
"""), unsafe_allow_html=True)
