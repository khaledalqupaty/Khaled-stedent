# -*- coding: utf-8 -*-
"""
نظام الخالد الذكي للنقل المدرسي - الإصدار الاحترافي المتكامل (Pro Max)
"""
import streamlit as st
import pandas as pd
import sqlite3
import pathlib
import datetime
import io
import random
import altair as alt
import folium
from streamlit_folium import st_folium

# -------------------- إعدادات الصفحة --------------------
st.set_page_config(
    page_title="نظام الخالد برو",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- التصميم الاحترافي (CSS) --------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Almarai:wght@300;400;700;800&display=swap');

    :root {
        --primary-color: #2563eb;
        --secondary-color: #1e40af;
        --bg-color: #f8fafc;
        --card-bg: #ffffff;
        --text-color: #0f172a;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
    }

    html, body, [class*="css"] { font-family: 'Almarai', sans-serif; }
    .stApp { background-color: var(--bg-color); }

    /* البطاقات */
    .kpi-card {
        background: var(--card-bg);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-right: 5px solid var(--primary-color);
        transition: transform 0.2s;
    }
    .kpi-card:hover { transform: translateY(-5px); }
    .kpi-title { color: #64748b; font-size: 0.9rem; font-weight: 700; }
    .kpi-value { color: var(--text-color); font-size: 1.8rem; font-weight: 800; }

    /* تخصيص الجداول */
    .stDataFrame { border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] { background-color: #1e293b; }
    [data-testid="stSidebar"] * { color: #f1f5f9 !important; }
    
    /* رسالة امتلاء الباص */
    .bus-full { color: #ef4444; font-weight: bold; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# -------------------- قاعدة البيانات --------------------
@st.cache_resource
def get_connection():
    db_path = pathlib.Path("alkhaled_pro_v2.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    
    # الجداول
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sid TEXT UNIQUE,
            phone TEXT,
            district TEXT,
            lat REAL,
            lon REAL,
            fees_total REAL DEFAULT 5000,
            fees_paid REAL DEFAULT 0,
            status TEXT DEFAULT 'نشط'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            bus_no TEXT,
            phone TEXT,
            capacity INTEGER,
            route_area TEXT
        )
    """)
    # جدول الرحلات (التوزيع اليومي)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            trip_date TEXT,
            driver_id INTEGER,
            student_id INTEGER,
            trip_type TEXT DEFAULT 'go',
            PRIMARY KEY(trip_date, driver_id, student_id)
        )
    """)
    
    # بيانات أولية للتجربة
    if not cursor.execute("SELECT 1 FROM students").fetchone():
        students_data = [
            ("نورة فهد", "101", "0501111111", "الملقا", 24.810, 46.610, 5000, 5000, "نشط"),
            ("سارة أحمد", "102", "0502222222", "النرجس", 24.830, 46.650, 5000, 2500, "نشط"),
            ("ليان خالد", "103", "0503333333", "الياسمين", 24.820, 46.630, 5000, 0, "نشط"),
        ]
        cursor.executemany("INSERT INTO students (name, sid, phone, district, lat, lon, fees_total, fees_paid, status) VALUES (?,?,?,?,?,?,?,?,?)", students_data)
        
        drivers_data = [
            ("أبو عبدالله", "BUS-01", "0590000001", 15, "شمال الرياض"),
            ("أبو صالح", "BUS-02", "0590000002", 12, "وسط الرياض"),
        ]
        cursor.executemany("INSERT INTO drivers (name, bus_no, phone, capacity, route_area) VALUES (?,?,?,?,?)", drivers_data)
        
    conn.commit()
    return conn

conn = get_connection()

# -------------------- دوال مساعدة --------------------
def get_df(query, params=None):
    return pd.read_sql(query, conn, params=params)

def execute_query(query, params):
    try:
        with conn:
            conn.execute(query, params)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
        return False

# دالة لحفظ التوزيع اليومي
def save_daily_distribution(date_str, driver_id, selected_student_ids):
    try:
        with conn:
            # 1. حذف التوزيع السابق لهذا السائق في هذا اليوم لتجنب التكرار
            conn.execute("DELETE FROM trips WHERE trip_date = ? AND driver_id = ?", (date_str, driver_id))
            
            # 2. إضافة التوزيع الجديد
            if selected_student_ids:
                data = [(date_str, driver_id, s_id) for s_id in selected_student_ids]
                conn.executemany("INSERT INTO trips (trip_date, driver_id, student_id) VALUES (?,?,?)", data)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"خطأ في الحفظ: {e}")
        return False

# -------------------- القائمة الجانبية --------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063823.png", width=80)
    st.markdown("### 🚌 الخالد برو")
    st.markdown("---")
    
    menu = st.radio(
        "القائمة الرئيسية",
        ["📊 لوحة القيادة", "📅 التوزيع اليومي", "👩‍🎓 الطالبات والحضور", "🚍 السائقين", "📍 الخريطة", "⚙️ الإعدادات"],
        label_visibility="collapsed"
    )
    st.markdown("---")

# -------------------- 1. لوحة القيادة --------------------
if menu == "📊 لوحة القيادة":
    st.title("📊 مركز العمليات")
    
    # جلب البيانات المحدثة
    # لاحظ هنا: قمنا بدمج عدد أيام الحضور في استعلام الطالبات
    df_stu = get_df("""
        SELECT s.*, 
        (SELECT COUNT(*) FROM trips t WHERE t.student_id = s.id) as attendance_days 
        FROM students s
    """)
    df_drv = get_df("SELECT * FROM drivers")
    
    # حسابات سريعة
    total_fees = df_stu['fees_total'].sum()
    paid_fees = df_stu['fees_paid'].sum()
    active_students = len(df_stu[df_stu['attendance_days'] > 0])
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">إجمالي الطالبات</div><div class="kpi-value">{len(df_stu)}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-card" style="border-color:var(--success)"><div class="kpi-title">نسبة التحصيل</div><div class="kpi-value">{(paid_fees/total_fees*100 if total_fees else 0):.1f}%</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi-card" style="border-color:var(--warning)"><div class="kpi-title">الطالبات النشطات (حضور)</div><div class="kpi-value">{active_students}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="kpi-card" style="border-color:var(--secondary-color)"><div class="kpi-title">عدد السائقين</div><div class="kpi-value">{len(df_drv)}</div></div>', unsafe_allow_html=True)

    st.markdown("### 📈 نشاط الأسبوع")
    # رسم بياني بسيط للحضور (وهمي للتوضيح)
    chart_data = pd.DataFrame({'Day': ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس'], 'Attendance': [45, 48, 47, 46, 40]})
    c = alt.Chart(chart_data).mark_area(opacity=0.3, color='#2563eb').encode(x='Day', y='Attendance').properties(height=250)
    st.altair_chart(c, use_container_width=True)

# -------------------- 2. التوزيع اليومي (الميزة الجديدة) --------------------
elif menu == "📅 التوزيع اليومي":
    st.title("📅 توزيع الطالبات اليومي")
    st.caption("قم باختيار التاريخ والسائق، ثم حدد الطالبات للصعود للحافلة.")
    
    # 1. اختيار التاريخ
    selected_date = st.date_input("تاريخ الرحلة", datetime.date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    
    # 2. عرض السائقين في كروت
    drivers = get_df("SELECT * FROM drivers")
    students = get_df("SELECT * FROM students WHERE status='نشط'") # فقط الطالبات النشطات
    
    if drivers.empty:
        st.warning("الرجاء إضافة سائقين أولاً من قائمة السائقين.")
    
    # تقسيم العرض لعمودين
    row1 = st.columns(2)
    row2 = st.columns(2)
    cols = row1 + row2 # قائمة مسطحة للأعمدة
    
    for idx, driver in drivers.iterrows():
        # استخدام الأعمدة بالتناوب
        with cols[idx % 4]: 
            with st.container(border=True):
                st.markdown(f"#### 🚌 {driver['name']}")
                st.caption(f"الحافلة: {driver['bus_no']} | السعة: {driver['capacity']}")
                
                # جلب الطالبات المسجلات لهذا السائق في هذا اليوم
                current_trip = get_df("SELECT student_id FROM trips WHERE trip_date=? AND driver_id=?", (date_str, driver['id']))
                existing_ids = current_trip['student_id'].tolist()
                
                # قائمة الاختيار
                selected_students = st.multiselect(
                    f"تسجيل الحضور ({driver['name']})",
                    options=students['id'].tolist(),
                    format_func=lambda x: students[students['id']==x]['name'].values[0],
                    default=existing_ids,
                    key=f"driver_{driver['id']}"
                )
                
                # التحقق من السعة
                count = len(selected_students)
                if count > driver['capacity']:
                    st.markdown(f"<span class='bus-full'>⚠️ تن
