import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import urllib.parse

# ───────────────────────────────────────────────
# مجلد البيانات + دوال الحفظ / التحميل
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

# ───────────────────────────────────────────────
# البيانات الافتراضية (أضفنا عمود "رقم الطالبة" كمثال)
# ───────────────────────────────────────────────
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

# ───────────────────────────────────────────────
# إعداد الصفحة + ستايل
# ───────────────────────────────────────────────
st.set_page_config(page_title="الخالد للنقل", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    :root { --primary: #1976d2; --success: #388e3c; --danger: #d32f2f; --bg: #f8fafc; --text: #0f172a; }
    .stApp { background-color: var(--bg); }
    h1, h2, h3 { color: var(--primary) !important; }
    .stButton > button { background: linear-gradient(135deg, var(--primary), #42a5f5); color: white !important; border-radius: 10px; box-shadow: 0 4px 12px rgba(25,118,210,0.25); transition: all 0.25s; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(25,118,210,0.4); }
    .paid   {background:#e8f5e9; color:var(--success); padding:0.5rem 1rem; border-radius:999px; font-weight:600;}
    .pending{background:#ffebee; color:var(--danger); padding:0.5rem 1rem; border-radius:999px; font-weight:600;}
    .stMultiSelect [data-baseweb="select"] span, .stMultiSelect [data-baseweb="tag"] span, .stMultiSelect [data-baseweb="option"] span { color: #0f172a !important; }
    [data-baseweb="popover"] ul, [data-baseweb="option"] { background-color: white !important; color: #111 !important; }
    [data-baseweb="option"]:hover { background-color: #e3f2fd !important; }
    [data-testid="stSidebar"] { background: linear-gradient(to bottom, #e3f2fd, #bbdefb); }
</style>
""", unsafe_allow_html=True)

# شعار + عنوان
LOGO_URL = "https://drive.google.com/uc?id=1WxVKMdn81Fmb8PQFUtR8avlMkhkHhDJX"  # غيّر إذا ما اشتغل

col1, col2 = st.columns([1, 5])
with col1:
    st.image(LOGO_URL, width=140)
with col2:
    st.title("الخالد للنقل")
    st.subheader("إدارة نقل الطالبات")

# ───────────────────────────────────────────────
# Sidebar
# ───────────────────────────────────────────────
with st.sidebar:
    st.image(LOGO_URL, width=180)
    st.header("الخالد للنقل")
    page = st.radio("الصفحات", ["Dashboard", "الطالبات", "السائقين", "التوزيع اليومي", "حالة الدفع"])
    st.divider()
    st.caption(f"آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ───────────────────────────────────────────────
# حساب عدد أيام الدوام لكل طالبة
# ───────────────────────────────────────────────
def calculate_attendance_days():
    assignments = load_json(ASSIGNMENTS_FILE, {})
    attendance = {}
    for date, drivers_dict in assignments.items():
        for driver, girls in drivers_dict.items():
            for girl in girls:
                attendance[girl] = attendance.get(girl, 0) + 1
    return attendance

attendance_days = calculate_attendance_days()

# إضافة/تحديث العمود في students_db
if "أيام الدوام" not in st.session_state.students_db.columns:
    st.session_state.students_db["أيام الدوام"] = 0

for name in st.session_state.students_db["الاسم"]:
    days = attendance_days.get(name, 0)
    idx = st.session_state.students_db[st.session_state.students_db["الاسم"] == name].index[0]
    st.session_state.students_db.at[idx, "أيام الدوام"] = days

# ───────────────────────────────────────────────
# الصفحات
# ───────────────────────────────────────────────

if page == "Dashboard":
    st.header("نظرة عامة")
    today = datetime.now().strftime("%Y-%m-%d")
    assignments = load_json(ASSIGNMENTS_FILE, {})
    today_assign = assignments.get(today, {})

    cols = st.columns(4)
    cols[0].metric("الطالبات", len(st.session_state.students_db))
    cols[1].metric("دفعن", len(st.session_state.students_db[st.session_state.students_db["حالة الدفع"] == "تم الدفع"]))
    cols[2].metric("السائقين", len(st.session_state.buses_db))
    cols[3].metric("موزعات اليوم", sum(len(v) for v in today_assign.values()))

    if today_assign:
        df_chart = pd.DataFrame([{"سائق": k, "عدد": len(v)} for k,v in today_assign.items()])
        st.bar_chart(df_chart.set_index("سائق"))

elif page == "الطالبات":
    st.header("إدارة الطالبات")

    def save_students():
        save_json(STUDENTS_FILE, st.session_state.students_db.to_dict("records"))

    # رابط خرائط جوجل لكل موقع
    def make_map_link(location):
        if pd.isna(location) or not location.strip():
            return ""
        encoded = urllib.parse.quote(location.strip())
        return f"https://www.google.com/maps/search/?api=1&query={encoded}"

    # نسخة معدلة للعرض مع روابط
    display_df = st.session_state.students_db.copy()
    display_df["خريطة"] = display_df["الموقع"].apply(make_map_link)

    edited = st.data_editor(
        display_df,
        num_rows="dynamic",
        use_container_width=True,
        key="students_ed",
        on_change=save_students,
        column_config={
            "خريطة": st.column_config.LinkColumn(
                "خريطة",
                help="اضغط لفتح الموقع في جوجل مابس",
                display_text="فتح الخريطة",
                disabled=True
            ),
            "أيام الدوام": st.column_config.NumberColumn(
                "أيام الدوام",
                min_value=0,
                disabled=True
            )
        }
    )

    if st.button("حفظ التغييرات", type="primary"):
        save_students()
        st.success("تم الحفظ")
        st.rerun()

elif page == "السائقين":
    st.header("إدارة السائقين")
    def save_buses():
        save_json(BUSES_FILE, st.session_state.buses_db.to_dict("records"))

    st.data_editor(
        st.session_state.buses_db,
        num_rows="dynamic",
        use_container_width=True,
        key="buses_ed",
        on_change=save_buses
    )
    if st.button("حفظ", type="primary"):
        save_buses()
        st.rerun()

elif page == "التوزيع اليومي":
    st.header("توزيع اليوم")
    today = datetime.now().strftime("%Y-%m-%d")

    assignments = load_json(ASSIGNMENTS_FILE, {})

    # عرض الطالبات مع رقم + اسم
    student_options = [
        f"{row['الاسم']} ({row['رقم الطالبة']})"
        for _, row in st.session_state.students_db.iterrows()
    ]

    student_name_map = {f"{row['الاسم']} ({row['رقم الطالبة']})": row['الاسم']
                         for _, row in st.session_state.students_db.iterrows()}

    for driver in st.session_state.buses_db["اسم السائق"]:
        bus = st.session_state.buses_db.query("`اسم السائق` == @driver")["رقم الباص"].iloc[0]
        with st.expander(f"{driver} – {bus}", expanded=False):
            current_labels = assignments.get(today, {}).get(driver, [])
            current_names = [student_name_map.get(label, label) for label in current_labels]

            selected_labels = st.multiselect(
                "اختر الطالبات",
                options=student_options,
                default=[f"{n} ({st.session_state.students_db[st.session_state.students_db['الاسم']==n]['رقم الطالبة'].iloc[0]})" for n in current_names],
                key=f"ms_{driver}_{today}"
            )

            selected_names = [student_name_map.get(label, label.split(" (")[0]) for label in selected_labels]

            c1, c2 = st.columns(2)
            if c1.button("حفظ", key=f"sv_{driver}", type="primary"):
                if today not in assignments: assignments[today] = {}
                assignments[today][driver] = selected_names
                save_json(ASSIGNMENTS_FILE, assignments)
                st.success("تم")
                st.rerun()

            if c2.button("مسح", key=f"cl_{driver}"):
                if today in assignments and driver in assignments[today]:
                    del assignments[today][driver]
                    save_json(ASSIGNMENTS_FILE, assignments)
                st.rerun()

    st.divider()
    st.subheader("ملخص اليوم")
    today_a = assignments.get(today, {})
    if today_a:
        for d, gs in today_a.items():
            if gs:
                st.info(f"{d} → {', '.join(gs)}")
    else:
        st.info("لا توزيع اليوم")

elif page == "حالة الدفع":
    st.header("حالة الدفع")
    flt = st.selectbox("فلتر", ["الكل", "تم الدفع", "انتظار"])

    df = st.session_state.students_db.copy()
    if flt != "الكل":
        df = df[df["حالة الدفع"] == flt]

    for i, r in df.iterrows():
        cols = st.columns([2,3,2,2])
        cols[0].write(f"**{r['الاسم']}** ({r['رقم الطالبة']})")
        cols[1].write(r["الموقع"])
        cls = "paid" if r["حالة الدفع"] == "تم الدفع" else "pending"
        cols[2].markdown(f"<div class='{cls}'>{r['حالة الدفع']}</div>", unsafe_allow_html=True)

        newv = "تم الدفع" if r["حالة الدفع"] == "انتظار" else "انتظار"
        if cols[3].button("تبديل", key=f"tg_{i}"):
            st.session_state.students_db.at[i, "حالة الدفع"] = newv
            save_json(STUDENTS_FILE, st.session_state.students_db.to_dict("records"))
            st.rerun()

st.sidebar.caption("الخالد للنقل © 2026")