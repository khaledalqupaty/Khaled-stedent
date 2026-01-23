import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import urllib.parse

# ─── مجلد البيانات ────────────────────────────────────────────────
DATA_FOLDER = "bus_data"
os.makedirs(DATA_FOLDER, exist_ok=True)

STUDENTS_FILE    = os.path.join(DATA_FOLDER, "students.json")
BUSES_FILE       = os.path.join(DATA_FOLDER, "buses.json")
ASSIGNMENTS_FILE = os.path.join(DATA_FOLDER, "daily_assignments.json")

def load_json(path, default=[]):
    if os.path.exists(path):
        try: return json.load(open(path, "r", encoding="utf-8"))
        except: pass
    return default

def save_json(path, data):
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ─── البيانات الافتراضية ──────────────────────────────────────────
if "students_db" not in st.session_state:
    st.session_state.students_db = pd.DataFrame(load_json(STUDENTS_FILE, [
        {"الاسم": "نورة", "رقم الطالبة": "101", "الموقع": "حي الروضة الرياض", "حالة الدفع": "انتظار", "رقم ولي الأمر": "0501234567"},
        {"الاسم": "سارة", "رقم الطالبة": "102", "الموقع": "حي الملقا الرياض",  "حالة الدفع": "تم الدفع", "رقم ولي الأمر": "0559876543"},
        {"الاسم": "ليان", "رقم الطالبة": "103", "الموقع": "حي النرجس الرياض",  "حالة الدفع": "انتظار", "رقم ولي الأمر": "0581112233"},
    ]))

if "buses_db" not in st.session_state:
    st.session_state.buses_db = pd.DataFrame(load_json(BUSES_FILE, [
        {"اسم السائق": "أحمد محمد", "رقم الباص": "باص 1", "رقم الجوال": "0591112233", "سعة الباص": 15},
        {"اسم السائق": "خالد علي",  "رقم الباص": "باص 2", "رقم الجوال": "0584445566", "سعة الباص": 12},
    ]))

# ─── إعداد الصفحة + CSS نظيف ومنظم ────────────────────────────────
st.set_page_config(page_title="الخالد للنقل", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    :root {
        --primary: #1e88e5;
        --primary-dark: #1565c0;
        --bg: #f9fcff;
        --card-bg: #ffffff;
        --text: #0d47a1;
        --gray: #546e7a;
    }

    .stApp {
        background: var(--bg);
    }

    h1, h2, h3 {
        color: var(--primary) !important;
        font-weight: 600;
    }

    /* Header تنسيق */
    .main-header {
        display: flex;
        align-items: center;
        gap: 20px;
        padding: 1rem 0;
        border-bottom: 2px solid #e3f2fd;
        margin-bottom: 1.5rem;
    }

    /* أزرار */
    .stButton > button {
        background: var(--primary);
        color: white !important;
        border-radius: 8px;
        padding: 0.6rem 1.4rem;
        font-weight: 600;
        border: none;
        box-shadow: 0 3px 10px rgba(30,136,229,0.2);
        transition: all 0.2s;
    }

    .stButton > button:hover {
        background: var(--primary-dark);
        box-shadow: 0 6px 15px rgba(30,136,229,0.3);
    }

    /* كروت */
    .metric-card {
        background: var(--card-bg);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        border: 1px solid #e3f2fd;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(to bottom, #e8f4fd, #c5e1ff);
    }

    /* إصلاح النصوص في الـ widgets */
    .stMultiSelect [data-baseweb="select"] span,
    .stMultiSelect [data-baseweb="tag"] span,
    .stMultiSelect [data-baseweb="option"] span,
    .stDataEditor [role="gridcell"] div {
        color: #0d47a1 !important;
        background: transparent !important;
    }

    [data-baseweb="popover"] ul,
    [data-baseweb="option"] {
        background: white !important;
        color: #111 !important;
    }

    [data-baseweb="option"]:hover {
        background: #e3f2fd !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── Header رئيسي منظم ─────────────────────────────────────────────
logo_url = "https://drive.google.com/uc?id=1WxVKMdn81Fmb8PQFUtR8avlMkhkHhDJX"

st.markdown('<div class="main-header">', unsafe_allow_html=True)
col1, col2 = st.columns([1, 6])
with col1:
    st.image(logo_url, width=90)
with col2:
    st.markdown("<h1 style='margin:0;'>الخالد للنقل</h1>", unsafe_allow_html=True)
    st.caption("نقل طالبات آمن ومريح – الرياض")
st.markdown('</div>', unsafe_allow_html=True)

# ─── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.image(logo_url, width=160)
    st.markdown("### الخالد للنقل")
    page = st.radio("الصفحات", [
        "Dashboard",
        "الطالبات",
        "السائقين",
        "التوزيع اليومي",
        "حالة الدفع"
    ])
    st.divider()
    st.caption(f"آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

