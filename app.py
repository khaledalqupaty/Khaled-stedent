import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import urllib.parse

# ─── مجلد البيانات ─────────────────────────────────────────────────────
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

# ─── بيانات افتراضية + عمود رقم الطالبة + أيام الدوام ────────────────
default_students = [
    {"الاسم": "نورة",  "رقم الطالبة": "101", "الموقع": "حي الروضة الرياض",  "حالة الدفع": "انتظار", "رقم ولي الأمر": "0501234567"},
    {"الاسم": "سارة",  "رقم الطالبة": "102", "الموقع": "حي الملقا الرياض",   "حالة الدفع": "تم الدفع", "رقم ولي الأمر": "0559876543"},
    {"الاسم": "ليان",  "رقم الطالبة": "103", "الموقع": "حي النرجس الرياض",   "حالة الدفع": "انتظار", "رقم ولي الأمر": "0581112233"},
]

if "students_db" not in st.session_state:
    st.session_state.students_db = pd.DataFrame(load_json(STUDENTS_FILE, default_students))

if "buses_db" not in st.session_state:
    st.session_state.buses_db = pd.DataFrame(load_json(BUSES_FILE, [
        {"اسم السائق": "أحمد محمد", "رقم الباص": "باص 1", "رقم الجوال": "0591112233", "سعة الباص": 15},
        {"اسم السائق": "خالد علي",  "رقم الباص": "باص 2", "رقم الجوال": "0584445566", "سعة الباص": 12},
    ]))

# ─── إعداد الصفحة + CSS احترافي 2026 ────────────────────────────────────
st.set_page_config(page_title="الخالد للنقل", layout="wide", initial_sidebar_state="expanded")

LOGO_URL = "https://drive.google.com/uc?id=1WxVKMdn81Fmb8PQFUtR8avlMkhkHhDJX"

st.markdown(f"""
<style>
    :root {{
        --primary:    #0d47a1;
        --primary-l:  #1976d2;
        --success:    #2e7d32;
        --danger:     #c62828;
        --bg:         #f8fbff;
        --card:       #ffffff;
        --text:       #0d1b2a;
        --gray:       #455a64;
    }}

    .stApp {{
        background: var(--bg);
        color: var(--text);
    }}

    h1, h2, h3 {{
        color: var(--primary) !important;
        font-weight: 700;
    }}

    .header {{
        display: flex;
        align-items: center;
        gap: 1.5rem;
        padding: 1.2rem 0 1.8rem;
        border-bottom: 2px solid #e3f2fd;
        margin-bottom: 2rem;
    }}

    .stButton > button {{
        background: var(--primary);
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 0.65rem 1.4rem;
        font-weight: 600;
        box-shadow: 0 3px 10px rgba(13,71,161,0.18);
        transition: all 0.22s;
    }}

    .stButton > button:hover {{
        background: var(--primary-l);
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(13,71,161,0.28);
    }}

    .metric-card {{
        background: var(--card);
        border-radius: 12px;
        padding: 1.3rem;
        text-align: center;
        box-shadow: 0 4px 14px rgba(0,0,0,0.05);
        border: 1px solid #e3f2fd;
    }}

    .paid   {{ background:#e8f5e9; color:var(--success); padding:0.45rem 1rem; border-radius:999px; font-weight:600; }}
    .pending{{ background:#ffebee; color:var(--danger);  padding:0.45rem 1rem; border-radius:999px; font-weight:600; }}

    /* إصلاح نصوص الـ multiselect + data-editor */
    .stMultiSelect [data-baseweb] span,
    .stMultiSelect [data-baseweb] div,
    .stDataEditor [role="gridcell"] > div,
    .stSelectbox [data-baseweb] span {{
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
    }}

    [data-baseweb="popover"] ul,
    [data-baseweb="option"] {{
        background: white !important;
        color: #0d1b2a !important;
    }}

    [data-baseweb="option"]:hover {{
        background: #e3f2fd !important;
    }}

    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #e8f4fd 0%, #d1e8ff 100%);
    }}
</style>
""", unsafe_allow_html=True)

# ─── Header رئيسي ──────────────────────────────────────────────────────
st.markdown('<div class="header">', unsafe_allow_html=True)
col_logo, col_text = st.columns([1, 7])
with col_logo:
    st.image(LOGO_URL, width=88)
with col_text:
    st.markdown("<h1 style='margin:0 0 0.3rem 0;'>الخالد للنقل</h1>", unsafe_allow_html=True)
    st.markdown("<div style='color:var(--gray); font-size:1.05rem;'>نقل طالبات آمن ومريح – الرياض</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ─── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(LOGO_URL, width=160)
    st.markdown("### الخالد للنقل")
    page = st.radio("التنقل", [
        "🏠 Dashboard",
        "👧 الطالبات",
        "🚌 السائقين",
        "📅 التوزيع اليومي",
        "💰 حالة الدفع"
    ])
    st.divider()
    st.caption(f"آخر تحديث • {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ─── حساب أيام الدوام تلقائياً ────────────────────────────────────────
def get_attendance_days():
    ass = load_json(ASSIGNMENTS_FILE, {})
    cnt = {}
    for date_data in ass.values():
        for girls in date_data.values():
            for g in girls:
                cnt[g] = cnt.get(g, 0) + 1
    return cnt

att_days = get_attendance_days()

if "أيام الدوام" not in st.session_state.students_db.columns:
    st.session_state.students_db["أيام الدوام"] = 0

for name, cnt in att_days.items():
    mask = st.session_state.students_db["الاسم"] == name
    if mask.any():
        st.session_state.students_db.loc[mask, "أيام الدوام"] = cnt

# ─── باقي الصفحات ─────────────────────────────────────────────────────
# (انسخ هنا الصفحات الأربعة من الكود السابق اللي كان يشتغل عندك: Dashboard + الطالبات + السائقين + التوزيع + حالة الدفع)

# ملاحظة مهمة: لا أعيد كتابة الصفحات كلها هنا لأن الرسالة تصير طويلة جداً، لكن الجزء الأعلى (CSS + header + sidebar + حساب الأيام) هو اللي يحل مشكلة التنسيق والألوان.
# فقط استبدل الجزء من بداية الملف لحد نهاية الـ sidebar بالكود أعلاه، واترك الصفحات كما هي.