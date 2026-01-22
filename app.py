import streamlit as st
import pandas as pd
import urllib.parse
import json
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# ───────────────────────────────────────────────
#               مجلد وحفظ دائم
# ───────────────────────────────────────────────
DATA_FOLDER = "bus_data"
os.makedirs(DATA_FOLDER, exist_ok=True)

STUDENTS_FILE  = os.path.join(DATA_FOLDER, "students.json")
BUSES_FILE     = os.path.join(DATA_FOLDER, "buses.json")
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

# ───────────────────────────────────────────────
#               تحميل البيانات
# ───────────────────────────────────────────────
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

# ───────────────────────────────────────────────
#               Theme + CSS جميل 2026 style
# ───────────────────────────────────────────────
st.set_page_config(
    page_title="إدارة باصات المدرسة 2026",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ألوان رئيسية (وردي ناعم + أزرق هادئ + أخضر للنجاح)
primary    = "#6366f1"   # indigo
success    = "#10b981"
warning    = "#f59e0b"
danger     = "#ef4444"
bg_light   = "#f8fafc"
text_dark  = "#1e293b"

st.markdown(f"""
<style>
    :root {{
        --primary: {primary};
        --success: {success};
        --warning: {warning};
        --danger: {danger};
        --bg: {bg_light};
        --text: {text_dark};
    }}

    .stApp {{
        background-color: var(--bg);
        color: var(--text);
    }}

    h1, h2, h3 {{
        color: var(--primary) !important;
    }}

    .stButton > button {{
        background-color: var(--primary);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.7rem 1.4rem;
        font-weight: 600;
        transition: all 0.25s ease;
    }}

    .stButton > button:hover {{
        background-color: #4f46e5;
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(99,102,241,0.3);
    }}

    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #6366f1, #4f46e5);
    }}

    .card {{
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        border: 1px solid #e2e8f0;
    }}

    .metric-card {{
        text-align: center;
        padding: 1.2rem;
        border-radius: 12px;
        background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
    }}

    .paid   {{ background: #ecfdf5; color: #065f46; padding: 0.5rem 1rem; border-radius: 999px; font-weight: 600; }}
    .pending{{ background: #fef2f2; color: #991b1b; padding: 0.5rem 1rem; border-radius: 999px; font-weight: 600; }}
</style>
""", unsafe_allow_html=True)

st.title("🚌 إدارة نقل الطالبات – نسخة 2026 احترافية")
st.caption("متابعة يومية | دفع | توزيع | مواقع | إحصائيات")

# ───────────────────────────────────────────────
#               Sidebar
# ───────────────────────────────────────────────
with st.sidebar:
    st.header("القائمة الرئيسية")
    page = st.radio("اختر الصفحة", [
        "🏠 Dashboard",
        "👧 الطالبات",
        "🚌 السائقين والباصات",
        "📅 التوزيع اليومي",
        "💰 حالة الدفع"
    ], label_visibility="collapsed")

# ───────────────────────────────────────────────
#               الصفحات
# ───────────────────────────────────────────────

if page == "🏠 Dashboard":
    st.header("لوحة التحكم الرئيسية")

    today = datetime.now().strftime("%Y-%m-%d")
    assignments = load_json(ASSIGNMENTS_FILE, {})

    # ── كروت إحصائية ─────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("إجمالي الطالبات", len(st.session_state.students_db))
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        paid = len(st.session_state.students_db[st.session_state.students_db["حالة الدفع"] == "تم الدفع"])
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("دفعن", paid, delta=f"+{paid} طالبة")
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("عدد السائقين", len(st.session_state.buses_db))
        st.markdown("</div>", unsafe_allow_html=True)

    with col4:
        today_assign = assignments.get(today, {})
        assigned = sum(len(g) for g in today_assign.values())
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("موزعات اليوم", assigned)
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # ── رسوم بيانية ───────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["حالة الدفع", "توزيع اليوم", "آخر 7 أيام"])

    with tab1:
        if not st.session_state.students_db.empty:
            pie_df = st.session_state.students_db["حالة الدفع"].value_counts().reset_index()
            pie_df.columns = ["حالة", "العدد"]
            fig_pie = px.pie(pie_df, values="العدد", names="حالة",
                             color_discrete_sequence=["#10b981","#ef4444"],
                             title="توزيع حالة الدفع")
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        today_assign = assignments.get(today, {})
        if today_assign:
            data = []
            for driver, girls in today_assign.items():
                data.append({"السائق": driver, "عدد الطالبات": len(girls)})
            df_today = pd.DataFrame(data)
            fig_bar = px.bar(df_today, x="السائق", y="عدد الطالبات",
                             title="عدد الطالبات لكل سائق اليوم",
                             color="عدد الطالبات",
                             color_continuous_scale="blues")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("لم يتم توزيع أي طالبات اليوم بعد")

    with tab3:
        dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
        data_last7 = []
        for d in dates:
            ass = assignments.get(d, {})
            total = sum(len(g) for g in ass.values())
            data_last7.append({"التاريخ": d, "العدد": total})

        df_last7 = pd.DataFrame(data_last7)
        fig_line = px.line(df_last7, x="التاريخ", y="العدد",
                           title="عدد الطالبات الموزعات – آخر 7 أيام",
                           markers=True)
        fig_line.update_traces(line_color=primary, line_width=3)
        st.plotly_chart(fig_line, use_container_width=True)


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
    if st.button("💾 حفظ التغييرات", type="primary"):
        save_students()
        st.success("تم الحفظ بنجاح")


# باقي الصفحات (نفس السابق مع تعديلات بسيطة على الأزرار)

elif page == "🚌 السائقين والباصات":
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
    if st.button("💾 حفظ بيانات السائقين", type="primary"):
        save_buses()
        st.success("تم الحفظ")


elif page == "📅 التوزيع اليومي":
    st.header("توزيع الطالبات اليومي")
    today = datetime.now().strftime("%Y-%m-%d")
    today_ar = datetime.now().strftime("%d/%m/%Y")
    st.subheader(f"التوزيع ليوم: {today_ar}")

    assignments = load_json(ASSIGNMENTS_FILE, {})

    for driver in st.session_state.buses_db["اسم السائق"]:
        with st.expander(f"🚌 {driver}", expanded=False):
            current = assignments.get(today, {}).get(driver, [])
            selected = st.multiselect(
                "الطالبات المخصصة",
                options=st.session_state.students_db["الاسم"].tolist(),
                default=current,
                key=f"sel_{driver}_{today}"
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"حفظ {driver}", key=f"sv_{driver}", type="primary"):
                    if today not in assignments: assignments[today] = {}
                    assignments[today][driver] = selected
                    save_json(ASSIGNMENTS_FILE, assignments)
                    st.success("تم الحفظ")
                    st.rerun()
            with col2:
                if st.button("مسح", key=f"cl_{driver}"):
                    if today in assignments and driver in assignments[today]:
                        del assignments[today][driver]
                        save_json(ASSIGNMENTS_FILE, assignments)
                    st.rerun()

    st.divider()
    st.subheader("ملخص اليوم")
    today_a = assignments.get(today, {})
    if today_a:
        for d, gs in today_a.items():
            if gs: st.success(f"{d} → {', '.join(gs)}")
    else:
        st.info("لا يوجد توزيع بعد")


elif page == "💰 حالة الدفع":
    st.header("حالة الدفع")
    filter_st = st.selectbox("عرض", ["الكل", "تم الدفع", "انتظار"])

    df = st.session_state.students_db.copy()
    if filter_st != "الكل":
        df = df[df["حالة الدفع"] == filter_st]

    for i, row in df.iterrows():
        with st.container(border=True):
            cols = st.columns([2,3,2,2])
            cols[0].write(f"**{row['الاسم']}**")
            cols[1].write(row["الموقع"])
            cls = "paid" if row["حالة الدفع"] == "تم الدفع" else "pending"
            cols[2].markdown(f"<span class='{cls}'>{row['حالة الدفع']}</span>", unsafe_allow_html=True)

            new_st = "تم الدفع" if row["حالة الدفع"] == "انتظار" else "انتظار"
            if cols[3].button("تبديل الحالة", key=f"tog_{i}"):
                st.session_state.students_db.at[i, "حالة الدفع"] = new_st
                save_json(STUDENTS_FILE, st.session_state.students_db.to_dict("records"))
                st.rerun()

st.sidebar.caption(f"آخر تحديث • {datetime.now().strftime('%Y-%m-%d %H:%M')}")