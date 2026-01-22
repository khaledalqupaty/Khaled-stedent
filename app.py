import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# ───────────────────────────────────────────────
# مجلد البيانات + دوال الحفظ / التحميل
# ───────────────────────────────────────────────
DATA_FOLDER = "bus_data"
os.makedirs(DATA_FOLDER, exist_ok=True)

STUDENTS_FILE = os.path.join(DATA_FOLDER, "students.json")
BUSES_FILE    = os.path.join(DATA_FOLDER, "buses.json")
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
# البيانات الافتراضية
# ───────────────────────────────────────────────
if "students_db" not in st.session_state:
    st.session_state.students_db = pd.DataFrame(load_json(STUDENTS_FILE, [
        {"الاسم": "نورة",  "الموقع": "حي الروضة الرياض",  "حالة الدفع": "انتظار",  "رقم ولي الأمر": "0501234567"},
        {"الاسم": "سارة",  "الموقع": "حي الملقا الرياض",   "حالة الدفع": "تم الدفع",  "رقم ولي الأمر": "0559876543"},
        {"الاسم": "ليان",  "الموقع": "حي النرجس الرياض",   "حالة الدفع": "انتظار",  "رقم ولي الأمر": "0581112233"},
    ]))

if "buses_db" not in st.session_state:
    st.session_state.buses_db = pd.DataFrame(load_json(BUSES_FILE, [
        {"اسم السائق": "أحمد محمد", "رقم الباص": "باص 1", "رقم الجوال": "0591112233", "سعة الباص": 15},
        {"اسم السائق": "خالد علي",  "رقم الباص": "باص 2", "رقم الجوال": "0584445566", "سعة الباص": 12},
    ]))

# ───────────────────────────────────────────────
# إعداد الصفحة + ستايل عصري 2025/2026
# ───────────────────────────────────────────────
st.set_page_config(
    page_title="إدارة باصات المدرسة",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    :root {
        --primary: #1976d2;
        --primary-dark: #1565c0;
        --success: #388e3c;
        --danger: #d32f2f;
        --bg: #f5faff;
        --card: white;
        --text: #1a237e;
    }

    .stApp {
        background-color: var(--bg);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    h1, h2, h3 {
        color: var(--primary) !important;
    }

    /* أزرار عصرية */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary), #42a5f5);
        color: white !important;
        border: none;
        border-radius: 10px;
        padding: 0.7rem 1.2rem;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(25,118,210,0.25);
        transition: all 0.25s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(25,118,210,0.35);
        background: linear-gradient(135deg, #1565c0, #1976d2);
    }

    /* كروت Dashboard */
    .metric-card {
        background: var(--card);
        border-radius: 12px;
        padding: 1.4rem;
        text-align: center;
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
        border: 1px solid #e3f2fd;
        transition: transform 0.2s;
    }

    .metric-card:hover {
        transform: translateY(-4px);
    }

    /* حالة الدفع */
    .paid   {background: #e8f5e9; color: var(--success); padding: 0.5rem 1rem; border-radius: 999px; font-weight: 600;}
    .pending{background: #ffebee; color: var(--danger);  padding: 0.5rem 1rem; border-radius: 999px; font-weight: 600;}

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(to bottom, #e3f2fd, #bbdefb);
        border-radius: 0 16px 16px 0;
    }

    /* تحسين الـ expander */
    .stExpander {
        border-radius: 10px;
        border: 1px solid #bbdefb;
        margin-bottom: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚌 إدارة نقل الطالبات – نسخة احترافية")

# ───────────────────────────────────────────────
# الشريط الجانبي
# ───────────────────────────────────────────────
with st.sidebar:
    st.header("التنقل")
    page = st.radio("اختر الصفحة", [
        "📊 Dashboard",
        "👧 الطالبات",
        "🚌 السائقين",
        "📅 التوزيع اليومي",
        "💰 حالة الدفع"
    ], label_visibility="collapsed")

    st.divider()
    st.caption(f"آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ───────────────────────────────────────────────
# Dashboard – مع كروت تفاعلية
# ───────────────────────────────────────────────
if page == "📊 Dashboard":
    st.header("نظرة عامة اليوم")

    today = datetime.now().strftime("%Y-%m-%d")
    assignments = load_json(ASSIGNMENTS_FILE, {})
    today_assign = assignments.get(today, {})

    total_students = len(st.session_state.students_db)
    paid = len(st.session_state.students_db[st.session_state.students_db["حالة الدفع"] == "تم الدفع"])
    drivers = len(st.session_state.buses_db)
    assigned_today = sum(len(girls) for girls in today_assign.values())

    cols = st.columns(4)
    metrics = [
        ("الطالبات الكلي", total_students, "👧"),
        ("دفعن", paid, "💸"),
        ("السائقين", drivers, "🚌"),
        ("موزعات اليوم", assigned_today, "🚀")
    ]

    for col, (label, value, emoji) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 2.4rem; margin-bottom: 0.3rem;">{emoji}</div>
                <div style="font-size: 2.1rem; font-weight: bold; color: var(--primary);">{value}</div>
                <div style="color: #555; font-size: 1rem;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    if today_assign:
        st.subheader("توزيع الطالبات اليوم")
        chart_data = [{"سائق": driver, "عدد": len(girls)} for driver, girls in today_assign.items()]
        df_chart = pd.DataFrame(chart_data)
        st.bar_chart(df_chart.set_index("سائق"), height=260, use_container_width=True)
    else:
        st.info("لم يتم تسجيل أي توزيع لهذا اليوم بعد")

# ───────────────────────────────────────────────
# باقي الصفحات (باقي الكود كما هو مع تحسينات بسيطة)
# ───────────────────────────────────────────────

elif page == "👧 الطالبات":
    st.header("إدارة الطالبات")

    def save_students():
        save_json(STUDENTS_FILE, st.session_state.students_db.to_dict("records"))

    st.data_editor(
        st.session_state.students_db,
        num_rows="dynamic",
        use_container_width=True,
        key="students_editor",
        on_change=save_students
    )

    if st.button("💾 حفظ التعديلات", type="primary"):
        save_students()
        st.success("تم الحفظ بنجاح!")
        st.rerun()

elif page == "🚌 السائقين":
    st.header("إدارة السائقين والباصات")

    def save_buses():
        save_json(BUSES_FILE, st.session_state.buses_db.to_dict("records"))

    st.data_editor(
        st.session_state.buses_db,
        num_rows="dynamic",
        use_container_width=True,
        key="buses_editor",
        on_change=save_buses
    )

    if st.button("💾 حفظ التعديلات", type="primary"):
        save_buses()
        st.success("تم الحفظ!")
        st.rerun()

elif page == "📅 التوزيع اليومي":
    st.header("توزيع الطالبات اليومي")
    today = datetime.now().strftime("%Y-%m-%d")
    st.caption(f"التاريخ: {datetime.now().strftime('%d/%m/%Y')}")

    assignments = load_json(ASSIGNMENTS_FILE, {})

    for driver in st.session_state.buses_db["اسم السائق"]:
        bus = st.session_state.buses_db[st.session_state.buses_db["اسم السائق"] == driver]["رقم الباص"].values[0]
        with st.expander(f"🚌 {driver} – {bus}", expanded=False):
            current = assignments.get(today, {}).get(driver, [])
            selected = st.multiselect(
                "اختر الطالبات",
                st.session_state.students_db["الاسم"].tolist(),
                default=current,
                key=f"select_{driver}_{today}"
            )

            c1, c2 = st.columns(2)
            if c1.button("حفظ التوزيع", key=f"save_{driver}", type="primary"):
                if today not in assignments:
                    assignments[today] = {}
                assignments[today][driver] = selected
                save_json(ASSIGNMENTS_FILE, assignments)
                st.success("تم حفظ التوزيع")
                st.rerun()

            if c2.button("مسح", key=f"clear_{driver}"):
                if today in assignments and driver in assignments[today]:
                    del assignments[today][driver]
                    save_json(ASSIGNMENTS_FILE, assignments)
                st.rerun()

elif page == "💰 حالة الدفع":
    st.header("متابعة حالة الدفع")

    filter_status = st.selectbox("عرض", ["الكل", "تم الدفع", "انتظار"])

    df = st.session_state.students_db
    if filter_status != "الكل":
        df = df[df["حالة الدفع"] == filter_status]

    for idx, row in df.iterrows():
        cols = st.columns([3, 4, 2, 2])
        cols[0].write(f"**{row['الاسم']}**")
        cols[1].write(row["الموقع"])

        cls = "paid" if row["حالة الدفع"] == "تم الدفع" else "pending"
        cols[2].markdown(f"<div class='{cls}'>{row['حالة الدفع']}</div>", unsafe_allow_html=True)

        new_status = "تم الدفع" if row["حالة الدفع"] == "انتظار" else "انتظار"
        if cols[3].button("تبديل", key=f"toggle_{idx}"):
            st.session_state.students_db.at[idx, "حالة الدفع"] = new_status
            save_json(STUDENTS_FILE, st.session_state.students_db.to_dict("records"))
            st.success("تم التحديث")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("تطبيق نقل الطالبات – خالد القباطي © 2026")