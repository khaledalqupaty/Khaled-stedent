import streamlit as st
import pandas as pd
import json
import os
import urllib.parse
from datetime import datetime

# ==========================
# إعداد مجلد البيانات وحفظ دائم
# ==========================
DATA_FOLDER = "bus_data"
os.makedirs(DATA_FOLDER, exist_ok=True)

STUDENTS_FILE = os.path.join(DATA_FOLDER, "students.json")
BUSES_FILE = os.path.join(DATA_FOLDER, "buses.json")
ASSIGNMENTS_FILE = os.path.join(DATA_FOLDER, "daily_assignments.json")

def load_json(file_path, default=[]):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==========================
# بيانات الطلاب والسائقين الافتراضية
# ==========================
default_students = [
    {"الاسم": "نورة",  "الموقع": "حي الروضة الرياض",  "حالة الدفع": "انتظار",  "رقم ولي الأمر": "0501234567"},
    {"الاسم": "سارة",  "الموقع": "حي الملقا الرياض",   "حالة الدفع": "تم الدفع",  "رقم ولي الأمر": "0559876543"},
    {"الاسم": "ليان",  "الموقع": "حي النرجس الرياض",   "حالة الدفع": "انتظار",  "رقم ولي الأمر": "0581112233"},
]

default_buses = [
    {"اسم السائق": "أحمد محمد", "رقم الباص": "باص 1", "رقم الجوال": "0591112233", "سعة الباص": 15},
    {"اسم السائق": "خالد علي",  "رقم الباص": "باص 2", "رقم الجوال": "0584445566", "سعة الباص": 12},
]

if "students_db" not in st.session_state:
    st.session_state.students_db = pd.DataFrame(load_json(STUDENTS_FILE, default_students))

if "buses_db" not in st.session_state:
    st.session_state.buses_db = pd.DataFrame(load_json(BUSES_FILE, default_buses))

# ==========================
# إعداد الصفحة
# ==========================
st.set_page_config(
    page_title="إدارة باصات المدرسة 2026",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================
# ستايل احترافي (ألوان، خلفيات، أزرار)
# ==========================
st.markdown("""
<style>
/* الخطوط والألوان */
body { font-family: 'Arial', sans-serif; background-color:#f7f9fc; }
h1, h2, h3 { color: #1F4E79; font-weight:bold; }
.stMarkdown h1 { color:#1F4E79; }

/* الأزرار */
.stButton>button { 
    background-color: #1F77B4; color: white; height:3em; width:100%; border-radius:10px; font-size:18px; font-weight:bold;
    box-shadow: 1px 1px 5px rgba(0,0,0,0.2);
}
.stButton>button:hover { background-color:#0f5c91; }

/* حالة الدفع */
.paid   {background-color:#d4edda; color:#155724; padding:6px; border-radius:6px; text-align:center; font-weight:bold;}
.pending{background-color:#f8d7da; color:#721c24; padding:6px; border-radius:6px; text-align:center; font-weight:bold;}

/* تمييز الجداول */
[data-testid="stDataFrame"] {border-radius:10px; box-shadow: 1px 1px 5px rgba(0,0,0,0.1);}

/* Sidebar */
[data-testid="stSidebar"] {background-color:#e1f0ff; border-radius:10px; padding:15px;}
</style>
""", unsafe_allow_html=True)

st.title("🚌 إدارة باصات المدرسة – نسخة احترافية")
st.caption("نسخة حديثة مع ألوان جذابة وأزرار واضحة")

# ==========================
# الشريط الجانبي
# ==========================
with st.sidebar:
    st.header("القائمة الرئيسية")
    page = st.radio("اختر الصفحة", [
        "📊 Dashboard",
        "👧 الطالبات",
        "🚌 السائقين والباصات",
        "📅 التوزيع اليومي",
        "💰 حالة الدفع"
    ])
    st.sidebar.markdown("---")
    st.sidebar.caption(f"آخر تحديث: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ==========================
# الصفحة: Dashboard
# ==========================
if page == "📊 Dashboard":
    st.header("📊 Dashboard اليومي")

    today = datetime.now().strftime("%Y-%m-%d")
    assignments = load_json(ASSIGNMENTS_FILE, {})
    today_assign = assignments.get(today, {})

    total_students = len(st.session_state.students_db)
    paid_students = len(st.session_state.students_db[st.session_state.students_db["حالة الدفع"]=="تم الدفع"])
    total_drivers = len(st.session_state.buses_db)
    assigned_today = sum(len(girls) for girls in today_assign.values())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("عدد الطالبات", total_students)
    col2.metric("دفعن", paid_students)
    col3.metric("عدد السائقين", total_drivers)
    col4.metric("موزعات اليوم", assigned_today)

    st.divider()
    st.subheader("📊 توزيع الطالبات اليوم")
    if today_assign:
        chart_data = pd.DataFrame([
            {"سائق": driver, "عدد الطالبات": len(girls)}
            for driver, girls in today_assign.items()
        ])
        st.bar_chart(chart_data.set_index("سائق"))
    else:
        st.info("لم يتم توزيع أي طالبات بعد لهذا اليوم")

# ==========================
# الصفحة: الطالبات
# ==========================
elif page == "👧 الطالبات":
    st.header("إدارة الطالبات")

    def save_students():
        save_json(STUDENTS_FILE, st.session_state.students_db.to_dict("records"))

    edited = st.data_editor(
        st.session_state.students_db,
        num_rows="dynamic",
        use_container_width=True,
        key="students_editor",
        on_change=save_students
    )

    if st.button("💾 حفظ التغييرات يدوياً", type="primary"):
        st.session_state.students_db = edited.copy()
        save_students()
        st.success("تم حفظ بيانات الطالبات")
        st.rerun()

# ==========================
# الصفحة: السائقين والباصات
# ==========================
elif page == "🚌 السائقين والباصات":
    st.header("إدارة السائقين والباصات")

    def save_buses():
        save_json(BUSES_FILE, st.session_state.buses_db.to_dict("records"))

    edited_buses = st.data_editor(
        st.session_state.buses_db,
        num_rows="dynamic",
        use_container_width=True,
        key="buses_editor",
        on_change=save_buses
    )

    if st.button("💾 حفظ بيانات السائقين", type="primary"):
        st.session_state.buses_db = edited_buses.copy()
        save_buses()
        st.success("تم الحفظ")
        st.rerun()

# ==========================
# الصفحة: التوزيع اليومي
# ==========================
elif page == "📅 التوزيع اليومي":
    st.header("توزيع الطالبات اليومي")
    today = datetime.now().strftime("%Y-%m-%d")
    today_ar = datetime.now().strftime("%d/%m/%Y")
    st.subheader(f"التوزيع ليوم: {today_ar}")

    assignments = load_json(ASSIGNMENTS_FILE, {})

    for driver in st.session_state.buses_db["اسم السائق"]:
        bus_number = st.session_state.buses_db[st.session_state.buses_db["اسم السائق"]==driver]["رقم الباص"].values[0]
        with st.expander(f"🚌 {driver} – {bus_number}", expanded=True):
            current_girls = assignments.get(today, {}).get(driver, [])
            selected = st.multiselect(
                "اختر الطالبات",
                options=st.session_state.students_db["الاسم"].tolist(),
                default=current_girls,
                key=f"select_{driver}_{today}"
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"💾 حفظ توزيع {driver}", key=f"save_{driver}", type="primary"):
                    if today not in assignments:
                        assignments[today] = {}
                    assignments[today][driver] = selected
                    save_json(ASSIGNMENTS_FILE, assignments)
                    st.success(f"تم حفظ توزيع {driver}")
                    st.rerun()

            with col2:
                if st.button(f"🗑 مسح التوزيع", key=f"clear_{driver}"):
                    if today in assignments and driver in assignments[today]:
                        del assignments[today][driver]
                        if not assignments[today]:
                            del assignments[today]
                    save_json(ASSIGNMENTS_FILE, assignments)
                    st.warning(f"تم مسح توزيع {driver}")
                    st.rerun()

# ==========================
# الصفحة: حالة الدفع
# ==========================
elif page == "💰 حالة الدفع":
    st.header("متابعة حالة الدفع")

    status_filter = st.selectbox("فلتر حسب الحالة", ["الكل", "تم الدفع", "انتظار"])
    df = st.session_state.students_db.copy()
    if status_filter != "الكل":
        df = df[df["حالة الدفع"] == status_filter]

    for idx, row in df.iterrows():
        cols = st.columns([2, 3, 2, 2])
        cols[0].write(f"**{row['الاسم']}**")
        cols[1].write(row["الموقع"])

        status_class = "paid" if row["حالة الدفع"]=="تم الدفع" else "pending"
        cols[2].markdown(f"<div class='{status_class}'>{row['حالة الدفع']}</div>", unsafe_allow_html=True)

        new_status = "تم الدفع" if row["حالة الدفع"]=="انتظار" else "انتظار"
        if cols[3].button("🔄 تبديل", key=f"toggle_{idx}", use_container_width=True):
            st.session_state.students_db.loc[idx, "حالة الدفع"] = new_status
            save_json(STUDENTS_FILE, st.session_state.students_db.to_dict("records"))
            st.success("تم تحديث الحالة")
            st.rerun()