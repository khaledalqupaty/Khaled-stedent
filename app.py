import streamlit as st
import pandas as pd
import json
import os
import urllib.parse
from datetime import datetime

# ─── إعداد المجلد ودوال الحفظ ────────────────────────────────────────
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

# ─── البيانات الافتراضية ──────────────────────────────────────────────
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

# ─── إعداد الصفحة + ستايل ────────────────────────────────────────────
st.set_page_config(page_title="إدارة باصات المدرسة", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stButton>button {background:#1e88e5; color:white; border-radius:8px; font-weight:bold;}
    .stButton>button:hover {background:#1565c0;}
    .paid   {background:#e8f5e9; color:#2e7d32; padding:6px; border-radius:6px; text-align:center;}
    .pending{background:#ffebee; color:#c62828; padding:6px; border-radius:6px; text-align:center;}
    [data-testid="stSidebar"] {background:#e3f2fd;}
</style>
""", unsafe_allow_html=True)

st.title("🚌 إدارة باصات المدرسة")

# ─── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("التنقل")
    page = st.radio("", [
        "📊 Dashboard",
        "👧 الطالبات",
        "🚌 السائقين",
        "📅 التوزيع اليومي",
        "💰 الدفع"
    ])
    st.divider()
    st.caption(f"آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ─── Dashboard ──────────────────────────────────────────────────────────
if page == "📊 Dashboard":
    st.header("نظرة عامة اليوم")
    today = datetime.now().strftime("%Y-%m-%d")
    ass = load_json(ASSIGNMENTS_FILE, {})
    today_ass = ass.get(today, {})

    cols = st.columns(4)
    cols[0].metric("الطالبات", len(st.session_state.students_db))
    cols[1].metric("دفعن", len(st.session_state.students_db.query("`حالة الدفع` == 'تم الدفع'")))
    cols[2].metric("السائقين", len(st.session_state.buses_db))
    cols[3].metric("موزعات اليوم", sum(len(v) for v in today_ass.values()))

    st.divider()
    if today_ass:
        df_chart = pd.DataFrame([{"سائق": k, "عدد": len(v)} for k,v in today_ass.items()])
        st.subheader("توزيع اليوم")
        st.bar_chart(df_chart.set_index("سائق"), height=240)
    else:
        st.info("لم يُسجل توزيع اليوم بعد")

# ─── الطالبات ──────────────────────────────────────────────────────────
elif page == "👧 الطالبات":
    st.header("إدارة الطالبات")

    def on_students_change():
        save_json(STUDENTS_FILE, st.session_state.students_db.to_dict("records"))

    st.data_editor(
        st.session_state.students_db,
        num_rows="dynamic",
        use_container_width=True,
        key="students_ed",
        on_change=on_students_change
    )

    if st.button("💾 حفظ يدوي", type="primary"):
        on_students_change()
        st.success("تم الحفظ")
        st.rerun()

# ─── السائقين ──────────────────────────────────────────────────────────
elif page == "🚌 السائقين":
    st.header("إدارة السائقين والباصات")

    def on_buses_change():
        save_json(BUSES_FILE, st.session_state.buses_db.to_dict("records"))

    st.data_editor(
        st.session_state.buses_db,
        num_rows="dynamic",
        use_container_width=True,
        key="buses_ed",
        on_change=on_buses_change
    )

    if st.button("💾 حفظ", type="primary"):
        on_buses_change()
        st.success("تم الحفظ")
        st.rerun()

# ─── التوزيع اليومي ────────────────────────────────────────────────────
elif page == "📅 التوزيع اليومي":
    st.header("توزيع اليوم")
    today = datetime.now().strftime("%Y-%m-%d")
    today_str = datetime.now().strftime("%d/%m/%Y")
    st.caption(f"التاريخ: {today_str}")

    ass = load_json(ASSIGNMENTS_FILE, {})

    for driver in st.session_state.buses_db["اسم السائق"]:
        bus = st.session_state.buses_db.query("`اسم السائق` == @driver")["رقم الباص"].iloc[0]
        with st.expander(f"{driver} – {bus}", expanded=False):
            selected = st.multiselect(
                "الطالبات",
                st.session_state.students_db["الاسم"].tolist(),
                default=ass.get(today, {}).get(driver, []),
                key=f"ms_{driver}_{today}"
            )

            c1, c2 = st.columns(2)
            if c1.button("حفظ", key=f"sv_{driver}", type="primary"):
                if today not in ass: ass[today] = {}
                ass[today][driver] = selected
                save_json(ASSIGNMENTS_FILE, ass)
                st.success("تم الحفظ")
                st.rerun()

            if c2.button("مسح", key=f"cl_{driver}"):
                if today in ass and driver in ass[today]:
                    del ass[today][driver]
                    save_json(ASSIGNMENTS_FILE, ass)
                st.rerun()

# ─── حالة الدفع ────────────────────────────────────────────────────────
elif page == "💰 الدفع":
    st.header("حالة الدفع")

    flt = st.selectbox("الحالة", ["الكل", "تم الدفع", "انتظار"])

    df = st.session_state.students_db
    if flt != "الكل":
        df = df[df["حالة الدفع"] == flt]

    for i, r in df.iterrows():
        cols = st.columns([3,4,2,2])
        cols[0].write(f"**{r['الاسم']}**")
        cols[1].write(r["الموقع"])
        cls = "paid" if r["حالة الدفع"] == "تم الدفع" else "pending"
        cols[2].markdown(f"<div class='{cls}'>{r['حالة الدفع']}</div>", unsafe_allow_html=True)

        new_val = "تم الدفع" if r["حالة الدفع"] == "انتظار" else "انتظار"
        if cols[3].button("تبديل", key=f"tg_{i}"):
            st.session_state.students_db.at[i, "حالة الدفع"] = new_val
            save_json(STUDENTS_FILE, st.session_state.students_db.to_dict("records"))
            st.rerun()