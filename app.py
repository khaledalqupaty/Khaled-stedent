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

def load_json(path, default=None):
    """تحميل JSON مع التحقق من وجود البيانات الفعلية"""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # التحقق أن البيانات ليست فارغة ولا null
                if data is not None and len(data) > 0:
                    return data
        except Exception as e:
            st.error(f"خطأ في قراءة {path}: {e}")
    return default

def save_json(path, data):
    """حفظ JSON مع التأكد من الكتابة الصحيحة"""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # التأكد من أن الملف كُتب فعلاً
        if os.path.exists(path):
            return True
    except Exception as e:
        st.error(f"خطأ في الحفظ {path}: {e}")
        return False

def initialize_data():
    """تهيئة البيانات الأولية مرة واحدة فقط"""
    
    # ─── الطالبات ───
    if "students_db" not in st.session_state:
        loaded = load_json(STUDENTS_FILE)
        if loaded is None:
            # البيانات الافتراضية فقط في أول مرة
            default_students = [
                {"الاسم": "نورة", "رقم الطالبة": "101", "الموقع": "حي الروضة الرياض", 
                 "حالة الدفع": "انتظار", "رقم ولي الأمر": "0501234567", "أيام الدوام": 0},
                {"الاسم": "سارة", "رقم الطالبة": "102", "الموقع": "حي الملقا الرياض", 
                 "حالة الدفع": "تم الدفع", "رقم ولي الأمر": "0559876543", "أيام الدوام": 0},
                {"الاسم": "ليان", "رقم الطالبة": "103", "الموقع": "حي النرجس الرياض", 
                 "حالة الدفع": "انتظار", "رقم ولي الأمر": "0581112233", "أيام الدوام": 0},
            ]
            st.session_state.students_db = pd.DataFrame(default_students)
            save_json(STUDENTS_FILE, default_students)
            st.info("✅ تم إنشاء بيانات الطالبات الأولية")
        else:
            st.session_state.students_db = pd.DataFrame(loaded)
            st.success(f"📂 تم تحميل {len(loaded)} طالبة من الملف")

    # ─── السائقين ───
    if "buses_db" not in st.session_state:
        loaded = load_json(BUSES_FILE)
        if loaded is None:
            default_buses = [
                {"اسم السائق": "أحمد محمد", "رقم الباص": "باص 1", 
                 "رقم الجوال": "0591112233", "سعة الباص": 15},
                {"اسم السائق": "خالد علي", "رقم الباص": "باص 2", 
                 "رقم الجوال": "0584445566", "سعة الباص": 12},
            ]
            st.session_state.buses_db = pd.DataFrame(default_buses)
            save_json(BUSES_FILE, default_buses)
            st.info("✅ تم إنشاء بيانات السائقين الأولية")
        else:
            st.session_state.buses_db = pd.DataFrame(loaded)
            st.success(f"📂 تم تحميل {len(loaded)} سائق من الملف")

    # ─── التوزيعات ───
    if "assignments" not in st.session_state:
        loaded = load_json(ASSIGNMENTS_FILE)
        if loaded is None:
            st.session_state.assignments = {}
            save_json(ASSIGNMENTS_FILE, {})
        else:
            st.session_state.assignments = loaded

# ─── تهيئة البيانات عند بدء التطبيق ───
initialize_data()

# ─── تحديث أيام الدوام ───
def update_attendance():
    attendance = {}
    for date_data in st.session_state.assignments.values():
        for girls in date_data.values():
            for girl in girls:
                attendance[girl] = attendance.get(girl, 0) + 1
    
    if "أيام الدوام" in st.session_state.students_db.columns:
        st.session_state.students_db["أيام الدوام"] = \
            st.session_state.students_db["الاسم"].map(attendance).fillna(0).astype(int)

update_attendance()

# ───────────────────────────────────────────────
# إعداد الصفحة + ستايل
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
    .stButton > button { 
        background: var(--primary); 
        color: white !important; 
        border-radius: 8px; 
        padding: 0.6rem 1.3rem; 
        font-weight: 600; 
        box-shadow: 0 3px 10px rgba(13,71,161,0.2); 
    }
    .stButton > button:hover { 
        background: var(--primary-light); 
        box-shadow: 0 6px 15px rgba(13,71,161,0.3); 
    }
    .metric-card { 
        background: var(--card); 
        border-radius: 10px; 
        padding: 1.2rem; 
        text-align: center; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.06); 
        border: 1px solid #e3f2fd; 
    }
    .paid   {background:#e8f5e9; color:var(--success); padding:0.5rem 1rem; border-radius:999px;}
    .pending{background:#ffebee; color:var(--danger);  padding:0.5rem 1rem; border-radius:999px;}
    .stMultiSelect div, .stDataEditor div, .stSelectbox div { color: var(--text) !important; }
    [data-baseweb="option"], [data-baseweb="select"] span { color: #111 !important; }
    [data-testid="stSidebar"] { 
        background: linear-gradient(to bottom, #0d47a1 0%, #1565c0 100%) !important; 
        color: white !important; 
    }
    [data-testid="stSidebar"] .stRadio > div > label { 
        color: white !important; 
        padding: 0.8rem 1rem; 
        border-radius: 8px; 
    }
    [data-testid="stSidebar"] .stRadio > div > label:hover { 
        background: rgba(255,255,255,0.15); 
    }
    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] { 
        background: rgba(255,255,255,0.25); 
        font-weight: bold; 
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] div, [data-testid="stSidebar"] span { 
        color: white !important; 
    }
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
    
    # زر حفظ يدوي للتأكد
    if st.button("💾 حفظ جميع البيانات", use_container_width=True):
        save_json(STUDENTS_FILE, st.session_state.students_db.to_dict("records"))
        save_json(BUSES_FILE, st.session_state.buses_db.to_dict("records"))
        save_json(ASSIGNMENTS_FILE, st.session_state.assignments)
        st.success("تم الحفظ اليدوي!")
    
    st.caption(f"آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ─── دوال الحفظ المحسّنة ───
def save_students():
    """حفظ طالبات مع رسالة تأكيد"""
    data = st.session_state.students_db.to_dict("records")
    if save_json(STUDENTS_FILE, data):
        st.toast("✅ تم حفظ بيانات الطالبات", icon="💾")

def save_buses():
    """حفظ سائقين مع رسالة تأكيد"""
    data = st.session_state.buses_db.to_dict("records")
    if save_json(BUSES_FILE, data):
        st.toast("✅ تم حفظ بيانات السائقين", icon="💾")

def save_assignments():
    """حفظ التوزيعات"""
    if save_json(ASSIGNMENTS_FILE, st.session_state.assignments):
        st.toast("✅ تم حفظ التوزيع", icon="💾")

# ─── الصفحات ───

if page == "🏠 Dashboard":
    st.header("نظرة عامة اليوم")
    today = datetime.now().strftime("%Y-%m-%d")
    today_assign = st.session_state.assignments.get(today, {})

    cols = st.columns(4)
    cols[0].markdown(
        f'<div class="metric-card"><div style="font-size:2.2rem;">{len(st.session_state.students_db)}</div>'
        f'<div>عدد الطالبات</div></div>', 
        unsafe_allow_html=True
    )
    paid = len(st.session_state.students_db[st.session_state.students_db["حالة الدفع"] == "تم الدفع"])
    cols[1].markdown(
        f'<div class="metric-card"><div style="font-size:2.2rem;">{paid}</div><div>دفعن</div></div>', 
        unsafe_allow_html=True
    )
    cols[2].markdown(
        f'<div class="metric-card"><div style="font-size:2.2rem;">{len(st.session_state.buses_db)}</div>'
        f'<div>السائقين</div></div>', 
        unsafe_allow_html=True
    )
    total_assigned = sum(len(v) for v in today_assign.values())
    cols[3].markdown(
        f'<div class="metric-card"><div style="font-size:2.2rem;">{total_assigned}</div>'
        f'<div>موزعات اليوم</div></div>', 
        unsafe_allow_html=True
    )

    st.divider()
    if today_assign:
        chart_df = pd.DataFrame([{"سائق": d, "عدد": len(g)} for d, g in today_assign.items()])
        st.subheader("توزيع اليوم")
        st.bar_chart(chart_df.set_index("سائق"))
    else:
        st.info("لا يوجد توزيع لليوم بعد")

elif page == "👧 الطالبات":
    st.header("إدارة الطالبات")

    def map_link(loc):
        if pd.isna(loc) or not str(loc).strip():
            return ""
        return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(str(loc))}"

    # نسخة للعرض فقط
    display_df = st.session_state.students_db.copy()
    display_df["خريطة"] = display_df["الموقع"].apply(map_link)

    edited = st.data_editor(
        display_df,
        num_rows="dynamic",
        use_container_width=True,
        key="students_editor",
        column_config={
            "خريطة": st.column_config.LinkColumn("خريطة", display_text="🗺 فتح"),
            "أيام الدوام": st.column_config.NumberColumn("أيام الدوام", disabled=True),
            "الاسم": st.column_config.TextColumn("الاسم", required=True),
            "رقم الطالبة": st.column_config.TextColumn("رقم الطالبة", required=True),
            "حالة الدفع": st.column_config.SelectColumn("حالة الدفع", options=["انتظار", "تم الدفع"]),
        }
    )
    
    # مقارنة وحفظ فقط عند التغيير الفعلي
    if not edited.equals(st.session_state.students_db):
        st.session_state.students_db = edited.copy()
        save_students()
        update_attendance()

    st.caption("💡 يتم الحفظ تلقائياً عند أي تعديل")

elif page == "🚌 السائقين":
    st.header("إدارة السائقين والباصات")

    edited = st.data_editor(
        st.session_state.buses_db,
        num_rows="dynamic",
        use_container_width=True,
        key="buses_editor",
        column_config={
            "اسم السائق": st.column_config.TextColumn("اسم السائق", required=True),
            "رقم الباص": st.column_config.TextColumn("رقم الباص", required=True),
            "رقم الجوال": st.column_config.TextColumn("رقم الجوال"),
            "سعة الباص": st.column_config.NumberColumn("سعة الباص", min_value=1),
        }
    )
    
    if not edited.equals(st.session_state.buses_db):
        st.session_state.buses_db = edited.copy()
        save_buses()

    st.caption("💡 يتم الحفظ تلقائياً عند أي تعديل")

elif page == "📅 التوزيع اليومي":
    st.header("توزيع الطالبات اليومي")
    today = datetime.now().strftime("%Y-%m-%d")
    st.caption(f"التاريخ: {datetime.now().strftime('%d/%m/%Y')}")

    student_options = [
        f"{row['الاسم']} ({row['رقم الطالبة']})" 
        for _, row in st.session_state.students_db.iterrows()
    ]
    student_name_map = {opt: opt.split(" (")[0] for opt in student_options}

    for _, driver_row in st.session_state.buses_db.iterrows():
        driver = driver_row["اسم السائق"]
        bus = driver_row["رقم الباص"]
        capacity = driver_row.get("سعة الباص", 15)
        
        with st.expander(f"🚌 {driver} – {bus} (السعة: {capacity})", expanded=False):
            
            # الطالبات المخصصة حالياً
            current_names = st.session_state.assignments.get(today, {}).get(driver, [])
            current_labels = [
                f"{name} ({st.session_state.students_db[st.session_state.students_db['الاسم']==name]['رقم الطالبة'].iloc[0]})"
                for name in current_names if name in st.session_state.students_db["الاسم"].values
            ]

            selected = st.multiselect(
                f"اختر الطالبات (الحد الأقصى: {capacity})",
                options=student_options,
                default=current_labels,
                key=f"assign_{driver}_{today}",
                help=f"لا يمكن اختيار أكثر من {capacity} طالبة"
            )

            # التحقق من السعة
            if len(selected) > capacity:
                st.error(f"⚠️ تجاوزت السعة! الحد الأقصى {capacity} طالبة")

            # حفظ التغييرات
            selected_names = [student_name_map[label] for label in selected]
            
            if selected_names != current_names:
                if today not in st.session_state.assignments:
                    st.session_state.assignments[today] = {}
                st.session_state.assignments[today][driver] = selected_names
                save_assignments()
                update_attendance()

    st.divider()
    st.subheader("ملخص اليوم")
    today_a = st.session_state.assignments.get(today, {})
    if today_a:
        for d, gs in today_a.items():
            st.info(f"{d} → {', '.join(gs) if gs else 'لا يوجد طالبات'}")
    else:
        st.info("لا يوجد توزيع بعد")

elif page == "💰 حالة الدفع":
    st.header("متابعة حالة الدفع")

    filter_status = st.selectbox("عرض", ["الكل", "تم الدفع", "انتظار"])

    df = st.session_state.students_db.copy()
    if filter_status != "الكل":
        df = df[df["حالة الدفع"] == filter_status]

    for idx, row in df.iterrows():
        cols = st.columns([3, 4, 2, 2])
        cols[0].write(f"**{row['الاسم']}** ({row['رقم الطالبة']})")
        cols[1].write(row["الموقع"])
        
        cls = "paid" if row["حالة الدفع"] == "تم الدفع" else "pending"
        cols[2].markdown(f"<div class='{cls}'>{row['حالة الدفع']}</div>", unsafe_allow_html=True)

        new_status = "تم الدفع" if row["حالة الدفع"] == "انتظار" else "انتظار"
        btn_text = "✅ تأكيد الدفع" if row["حالة الدفع"] == "انتظار" else "⏳ إلغاء الدفع"
        
        if cols[3].button(btn_text, key=f"pay_{idx}_{row['رقم الطالبة']}"):
            mask = st.session_state.students_db["رقم الطالبة"] == row["رقم الطالبة"]
            st.session_state.students_db.loc[mask, "حالة الدفع"] = new_status
            save_students()
            st.rerun()

st.sidebar.caption("الخالد للنقل © 2026")
