import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import urllib.parse

# ───────────────────────────────────────────────
# مجلد البيانات وحفظ دائم
# ───────────────────────────────────────────────
DATA_FOLDER = "bus_data"
os.makedirs(DATA_FOLDER, exist_ok=True)

STUDENTS_FILE    = os.path.join(DATA_FOLDER, "students.json")
BUSES_FILE       = os.path.join(DATA_FOLDER, "buses.json")
ASSIGNMENTS_FILE = os.path.join(DATA_FOLDER, "daily_assignments.json")

def load_json(path, default=[]):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_students():
    data = load_json(STUDENTS_FILE, [
        {"الاسم": "نورة",  "رقم الطالبة": "101", "الموقع": "حي الروضة الرياض",  "حالة الدفع": "انتظار", "رقم ولي الأمر": "0501234567"},
        {"الاسم": "سارة",  "رقم الطالبة": "102", "الموقع": "حي الملقا الرياض",   "حالة الدفع": "تم الدفع", "رقم ولي الأمر": "0559876543"},
        {"الاسم": "ليان",  "رقم الطالبة": "103", "الموقع": "حي النرجس الرياض",   "حالة الدفع": "انتظار", "رقم ولي الأمر": "0581112233"},
    ])
    return pd.DataFrame(data)

def load_buses():
    data = load_json(BUSES_FILE, [
        {"اسم السائق": "أحمد محمد", "رقم الباص": "باص 1", "رقم الجوال": "0591112233", "سعة الباص": 15},
        {"اسم السائق": "خالد علي",  "رقم الباص": "باص 2", "رقم الجوال": "0584445566", "سعة الباص": 12},
    ])
    return pd.DataFrame(data)

# تحميل البيانات في session_state (فقط مرة واحدة أو عند إعادة التحميل)
if "students_db" not in st.session_state:
    st.session_state.students_db = load_students()

if "buses_db" not in st.session_state:
    st.session_state.buses_db = load_buses()

# ───────────────────────────────────────────────
# إعداد الصفحة + ستايل احترافي
# ───────────────────────────────────────────────
st.set_page_config(page_title="الخالد للنقل", layout="wide", initial_sidebar_state="expanded")

LOGO_URL = "https://drive.google.com/uc?id=1WxVKMdn81Fmb8PQFUtR8avlMkhkHhDJX"

st.markdown("""
<style>
    :root {
        --primary: #0d47a1;
        --primary-light: #1976d2;
        --success: #2e7d32;
        --danger: #c62828;
        --bg: #f9fcff;
        --card: #ffffff;
        --text: #0d1b2a;
        --gray: #546e7a;
    }
    .stApp { background: var(--bg); color: var(--text); }
    h1, h2, h3 { color: var(--primary) !important; }
    .stButton > button { background: var(--primary); color: white !important; border-radius: 8px; padding: 0.6rem 1.3rem; font-weight: 600; box-shadow: 0 3px 10px rgba(13,71,161,0.2); }
    .stButton > button:hover { background: var(--primary-light); box-shadow: 0 6px 15px rgba(13,71,161,0.3); }
    .metric-card { background: var(--card); border-radius: 10px; padding: 1.2rem; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.06); border: 1px solid #e3f2fd; }
    .paid   {background:#e8f5e9; color:var(--success); padding:0.5rem 1rem; border-radius:999px;}
    .pending{background:#ffebee; color:var(--danger);  padding:0.5rem 1rem; border-radius:999px;}
    .stMultiSelect div, .stDataEditor div, .stSelectbox div { color: var(--text) !important; }
    [data-baseweb="option"], [data-baseweb="select"] span { color: #111 !important; }
    [data-testid="stSidebar"] { background: linear-gradient(to bottom, #0d47a1 0%, #1565c0 100%) !important; color: white !important; }
    [data-testid="stSidebar"] .stRadio > div > label { color: white !important; padding: 0.8rem 1rem; border-radius: 8px; }
    [data-testid="stSidebar"] .stRadio > div > label:hover { background: rgba(255,255,255,0.15); }
    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] { background: rgba(255,255,255,0.25); font-weight: bold; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] div, [data-testid="stSidebar"] span { color: white !important; }
</style>
""", unsafe_allow_html=True)

# Header
col_logo, col_text = st.columns([1, 6])
with col_logo:
    st.image(LOGO_URL, width=90)
with col_text:
    st.title("الخالد للنقل")
    st.caption("نقل طالبات آمن ومريح – الرياض")

# Sidebar
with st.sidebar:
    st.image(LOGO_URL, width=140)
    st.header("الخالد للنقل")
    page = st.radio("", [
        "🏠 Dashboard",
        "👧 الطالبات",
        "🚌 السائقين",
        "📅 التوزيع اليومي",
        "💰 حالة الدفع"
    ], label_visibility="collapsed")
    st.divider()
    st.caption(f"آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ─── حساب أيام الدوام تلقائياً ────────────────────────────────────────
assignments = load_json(ASSIGNMENTS_FILE, {})
attendance = {}
for date_data in assignments.values():
    for girls in date_data.values():
        for girl in girls:
            attendance[girl] = attendance.get(girl, 0) + 1

st.session_state.students_db["أيام الدوام"] = st.session_state.students_db["الاسم"].map(attendance).fillna(0).astype(int)

# ─── الصفحات مع حفظ تلقائي + إعادة تحميل فوري ──────────────────────

if page == "🏠 Dashboard":
    st.header("نظرة عامة اليوم")
    today = datetime.now().strftime("%Y-%m-%d")
    today_assign = assignments.get(today, {})

    cols = st.columns(4)
    cols[0].markdown(f'<div class="metric-card"><div style="font-size:2.2rem;">{len(st.session_state.students_db)}</div><div>عدد الطالبات</div></div>', unsafe_allow_html=True)
    paid = len(st.session_state.students_db[st.session_state.students_db["حالة الدفع"] == "تم الدفع"])
    cols[1].markdown(f'<div class="metric-card"><div style="font-size:2.2rem;">{paid}</div><div>دفعن</div></div>', unsafe_allow_html=True)
    cols[2].markdown(f'<div class="metric-card"><div style="font-size:2.2rem;">{len(st.session_state.buses_db)}</div><div>السائقين</div></div>', unsafe_allow_html=True)
    cols[3].markdown(f'<div class="metric-card"><div style="font-size:2.2rem;">{sum(len(v) for v in today_assign.values())}</div><div>موزعات اليوم</div></div>', unsafe_allow_html=True)

    st.divider()
    if today_assign:
        chart_df = pd.DataFrame([{"سائق": d, "عدد": len(g)} for d, g in today_assign.items()])
        st.subheader("توزيع اليوم")
        st.bar_chart(chart_df.set_index("سائق"))

elif page == "👧 الطالبات":
    st.header("إدارة الطالبات")

    def auto_save_students():
        save_json(STUDENTS_FILE, st.session_state.students_db.to_dict("records"))
        # إعادة تحميل البيانات فوراً للتأكد من التحديث
        st.session_state.students_db = load_students()
        st.rerun()

    def map_link(loc):
        if pd.isna(loc) or not loc.strip(): return ""
        return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(loc)}"

    display_df = st.session_state.students_db.copy()
    display_df["خريطة"] = display_df["الموقع"].apply(map_link)

    st.data_editor(
        display_df,
        num_rows="dynamic",
        use_container_width=True,
        key="students_ed",
        on_change=auto_save_students,
        column_config={
            "خريطة": st.column_config.LinkColumn("خريطة", display_text="🗺 فتح"),
            "أيام الدوام": st.column_config.NumberColumn(disabled=True)
        }
    )
    st.caption("يتم الحفظ تلقائياً بعد كل تعديل")

elif page == "🚌 السائقين":
    st.header("إدارة السائقين والباصات")

    def auto_save_buses():
        save_json(BUSES_FILE, st.session_state.buses_db.to_dict("records"))
        st.session_state.buses_db = load_buses()
        st.rerun()

    st.data_editor(
        st.session_state.buses_db,
        num_rows="dynamic",
        use_container_width=True,
        key="buses_ed",
        on_change=auto_save_buses
    )
    st.caption("يتم الحفظ تلقائياً")

elif page == "📅 التوزيع اليومي":
    st.header("توزيع الطالبات اليومي")
    today = datetime.now().strftime("%Y-%m-%d")
    st.caption(f"التاريخ: {datetime.now().strftime('%d/%m/%Y')}")

    assignments = load_json(ASSIGNMENTS_FILE, {})

    student_options = [f"{row['الاسم']} ({row['رقم الطالبة']})" for _, row in st.session_state.students_db.iterrows()]
    student_name_map = {opt: opt.split(" (")[0] for opt in student_options}

    def auto_save_assignment(driver):
        selected_labels = st.session_state[f"ms_{driver}_{today}"]
        selected_names = [student_name_map[label] for label in selected_labels]

        if today not in assignments:
            assignments[today] = {}
        assignments[today][driver] = selected_names

        save_json(ASSIGNMENTS_FILE, assignments)
        st.toast(f"تم حفظ توزيع {driver}", icon="💾")
        st.rerun()

    for driver in st.session_state.buses_db["اسم السائق"]:
        bus = st.session_state.buses_db[st.session_state.buses_db["اسم السائق"] == driver]["رقم الباص"].values[0]
        with st.expander(f"🚌 {driver} – {bus}", expanded=False):
            current_labels = [
                f"{name} ({st.session_state.students_db[st.session_state.students_db['الاسم']==name]['رقم الطالبة'].iloc[0]})"
                for name in assignments.get(today, {}).get(driver, [])
            ]

            st.multiselect(
                "اختر الطالبات",
                options=student_options,
                default=current_labels,
                key=f"ms_{driver}_{today}",
                on_change=lambda d=driver: auto_save_assignment(d)
            )

    st.divider()
    st.subheader("ملخص اليوم")
    today_a = assignments.get(today, {})
    if today_a:
        for d, gs in today_a.items():
            st.info(f"{d} → {', '.join(gs)}")
    else:
        st.info("لا يوجد توزيع بعد")

elif page == "💰 حالة الدفع":
    st.header("متابعة حالة الدفع")

    filter_status = st.selectbox("عرض", ["الكل", "تم الدفع", "انتظار"])

    df = st.session_state.students_db
    if filter_status != "الكل":
        df = df[df["حالة الدفع"] == filter_status]

    for idx, row in df.iterrows():
        cols = st.columns([3, 4, 2, 2])
        cols[0].write(f"**{row['الاسم']}** ({row['رقم الطالبة']})")
        cols[1].write(row["الموقع"])
        cls = "paid" if row["حالة الدفع"] == "تم الدفع" else "pending"
        cols[2].markdown(f"<div class='{cls}'>{row['حالة الدفع']}</div>", unsafe_allow_html=True)

        new_status = "تم الدفع" if row["حالة الدفع"] == "انتظار" else "انتظار"
        if cols[3].button("تبديل", key=f"toggle_{idx}"):
            st.session_state.students_db.at[idx, "حالة الدفع"] = new_status
            save_json(STUDENTS_FILE, st.session_state.students_db.to_dict("records"))
            st.success("تم التحديث")
            st.rerun()

st.sidebar.caption("الخالد للنقل © 2026")