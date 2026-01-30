# -*- coding: utf-8 -*-
"""
نظام الخالد الذكي للنقل المدرسي - الإصدار الاحترافي (Pro Edition)
معدل: إضافة حقل نسخ الموقع + استخراج إحداثيات تلقائي + إصلاحات سابقة
"""
import streamlit as st
import pandas as pd
import sqlite3
import pathlib
import datetime
import io
import random
import re
import altair as alt
import folium
from streamlit_folium import st_folium

# ─── إعدادات الصفحة ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="نظام الخالد برو",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── التصميم (CSS) ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Almarai:wght@300;400;700;800&display=swap');
    :root {
        --primary: #2563eb; --secondary: #1e40af; --bg: #f8fafc; --card: #ffffff;
        --text: #0f172a; --success: #10b981; --warning: #f59e0b; --danger: #ef4444;
    }
    html, body, [class*="css"] { font-family: 'Almarai', sans-serif; }
    .stApp { background-color: var(--bg); }
    .kpi-card {
        background: var(--card); border-radius: 16px; padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border-right: 5px solid var(--primary);
        transition: transform 0.2s;
    }
    .kpi-card:hover { transform: translateY(-5px); }
    .kpi-title { color: #64748b; font-size: 0.9rem; font-weight: 700; margin-bottom: 5px; }
    .kpi-value { color: var(--text); font-size: 1.8rem; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# ─── قاعدة البيانات ────────────────────────────────────────────────────────────
@st.cache_resource
def get_connection():
    db_path = pathlib.Path("alkhaled_pro.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, sid TEXT UNIQUE NOT NULL, phone TEXT,
            district TEXT, lat REAL, lon REAL,
            fees_total REAL DEFAULT 5000, fees_paid REAL DEFAULT 0,
            status TEXT DEFAULT 'نشط'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, bus_no TEXT UNIQUE,
            phone TEXT, capacity INTEGER, route_area TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            trip_date TEXT, driver_id INTEGER, student_id INTEGER,
            trip_type TEXT DEFAULT 'go',
            PRIMARY KEY(trip_date, driver_id, student_id, trip_type)
        )
    """)

    if not cur.execute("SELECT 1 FROM students LIMIT 1").fetchone():
        students_seed = [
            ("نورة فهد", "101", "0501111111", "الملقا",   24.810, 46.610, 5000, 5000, "نشط"),
            ("سارة أحمد", "102", "0502222222", "النرجس",  24.830, 46.650, 5000, 2500, "نشط"),
            ("ليان خالد", "103", "0503333333", "الياسمين",24.820, 46.630, 5000,    0, "نشط"),
            ("ريم محمد", "104", "0504444444", "العارض",   24.850, 46.660, 5000, 5000, "نشط"),
        ]
        cur.executemany("INSERT INTO students VALUES (NULL,?,?,?,?,?,?,?,?)", students_seed)

        drivers_seed = [
            ("أبو عبدالله", "BUS-01", "0590000001", 15, "شمال الرياض"),
            ("أبو صالح",    "BUS-02", "0590000002", 12, "وسط الرياض"),
        ]
        cur.executemany("INSERT INTO drivers VALUES (NULL,?,?,?,?,?)", drivers_seed)

    conn.commit()
    return conn

conn = get_connection()

# ─── دوال مساعدة ────────────────────────────────────────────────────────────────
def run_query(query, params=None):
    try:
        with conn:
            if params:
                conn.execute(query, params)
            else:
                conn.execute(query)
        st.cache_data.clear()
        return True
    except sqlite3.IntegrityError:
        st.error("خطأ: قيمة مكررة (رقم الملف أو رقم الحافلة)")
        return False
    except Exception as e:
        st.error(f"خطأ في قاعدة البيانات: {str(e)}")
        return False

def get_df(query, params=None):
    return pd.read_sql_query(query, conn, params=params)

# ─── القائمة الجانبية ──────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063823.png", width=80)
    st.markdown("### 🚌 الخالد للنقل")
    st.markdown("---")

    menu = st.radio(
        "القائمة الرئيسية",
        ["📊 لوحة القيادة", "👩‍🎓 الطالبات والرسوم", "🚍 السائقين والحافلات",
         "📍 الخريطة الذكية", "🗓️ التوزيع اليومي", "⚙️ الإعدادات"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.info("💡 يمكنك نسخ الموقع من Google Maps مباشرة في صفحة إضافة طالبة")

# ─── 1. لوحة القيادة ────────────────────────────────────────────────────────────
if menu == "📊 لوحة القيادة":
    st.title("📊 مركز التحكم والعمليات")
    df_stu = get_df("SELECT * FROM students")
    df_drv = get_df("SELECT * FROM drivers")

    total = df_stu["fees_total"].sum()
    collected = df_stu["fees_paid"].sum()
    pending = total - collected

    cols = st.columns(4)
    cols[0].markdown(f'<div class="kpi-card"><div class="kpi-title">عدد الطالبات</div><div class="kpi-value">{len(df_stu)}</div></div>', unsafe_allow_html=True)
    cols[1].markdown(f'<div class="kpi-card" style="border-color:var(--success)"><div class="kpi-title">إجمالي التحصيل</div><div class="kpi-value">{collected:,.0f} ر.س</div></div>', unsafe_allow_html=True)
    cols[2].markdown(f'<div class="kpi-card" style="border-color:var(--warning)"><div class="kpi-title">المتبقي</div><div class="kpi-value">{pending:,.0f} ر.س</div></div>', unsafe_allow_html=True)
    cols[3].markdown(f'<div class="kpi-card" style="border-color:var(--secondary)"><div class="kpi-title">عدد الحافلات</div><div class="kpi-value">{len(df_drv)}</div></div>', unsafe_allow_html=True)

# ─── 2. الطالبات والرسوم ───────────────────────────────────────────────────────
elif menu == "👩‍🎓 الطالبات والرسوم":
    st.title("👩‍🎓 إدارة الطالبات والرسوم")

    col1, col2 = st.columns([3,1])
    with col1:
        search = st.text_input("🔍 بحث (الاسم أو رقم الملف)", "")
    with col2:
        st.write("")
        st.write("")
        if st.button("➕ إضافة طالبة جديدة", type="primary"):
            st.session_state.show_add_form = True

    if st.session_state.get("show_add_form", False):
        with st.form("add_student"):
            st.subheader("إضافة طالبة جديدة")
            c1,c2,c3 = st.columns(3)
            name   = c1.text_input("الاسم الرباعي *")
            sid    = c2.text_input("رقم الملف / الهوية *")
            phone  = c3.text_input("رقم الجوال")

            c4,c5 = st.columns(2)
            dist   = c4.text_input("الحي السكني")
            fees   = c5.number_input("الرسوم السنوية", min_value=0, value=5000)

            # ─── حقل نسخ الموقع ──────────────────────────────────────────────
            location_text = st.text_area(
                "انسخ الموقع هنا (من Google Maps)",
                placeholder="مثال:\n24.7139, 46.6753\nأو 24.7139° N, 46.6753° E\nأو https://maps.app.goo.gl/...\nأو انسخ من شريط العنوان",
                height=100,
                help="انسخ أي نص يحتوي على الإحداثيات — النظام سيحاول قراءتها تلقائيًا"
            )

            lat = None
            lon = None

            if location_text.strip():
                # محاولة استخراج الإحداثيات بعدة أنماط شائعة
                patterns = [
                    r'([+-]?\d{1,3}\.\d{4,8})\s*[,; \n]\s*([+-]?\d{1,3}\.\d{4,8})',
                    r'(\d{1,3}\.\d+)\s*°?\s*[NS]?\s*[,; \n]\s*(\d{1,3}\.\d+)\s*°?\s*[EW]?',
                    r'@([\d\.-]+),([\d\.-]+)',
                ]

                for pat in patterns:
                    match = re.search(pat, location_text)
                    if match:
                        try:
                            lat = float(match.group(1))
                            lon = float(match.group(2))
                            if 20 < lat < 30 and 40 < lon < 55:  # نطاق الرياض تقريبًا
                                st.success(f"تم قراءة الموقع: {lat:.6f}, {lon:.6f}")
                                break
                        except:
                            continue

            # fallback إذا ما نجح الاستخراج
            if lat is None or lon is None:
                if location_text.strip():
                    st.warning("لم يتم التعرف على إحداثيات صحيحة → تم استخدام موقع افتراضي")
                lat = 24.7139 + random.uniform(-0.12, 0.12)
                lon = 46.6753 + random.uniform(-0.12, 0.12)

            submitted = st.form_submit_button("حفظ الطالبة", type="primary")

            if submitted:
                if not name or not sid:
                    st.error("الاسم ورقم الملف مطلوبان")
                else:
                    success = run_query(
                        "INSERT INTO students (name, sid, phone, district, lat, lon, fees_total) VALUES (?,?,?,?,?,?,?)",
                        (name, sid, phone, dist, lat, lon, fees)
                    )
                    if success:
                        st.success("تمت إضافة الطالبة بنجاح")
                        st.session_state.show_add_form = False
                        st.rerun()

    # باقي كود صفحة الطالبات (البحث، الجدول، التعديل، التصدير) ...
    # (يمكنك نسخه من النسخة السابقة إذا لم يتغير)

# باقي الأقسام (لوحة القيادة، السائقين، الخريطة، التوزيع، الإعدادات) تبقى كما هي
# للاختصار لم أكررها هنا، لكنها موجودة في النسخة الكاملة السابقة

# ─── الخريطة ────────────────────────────────────────────────────────────────
elif menu == "📍 الخريطة الذكية":
    st.title("📍 الخريطة الذكية")
    df_map = get_df("SELECT name, district, lat, lon, fees_paid, fees_total FROM students WHERE lat IS NOT NULL AND lon IS NOT NULL")

    if df_map.empty:
        st.info("لا توجد إحداثيات لعرضها على الخريطة بعد")
    else:
        m = folium.Map(location=[24.7139, 46.6753], zoom_start=11, tiles="CartoDB positron")

        for _, row in df_map.iterrows():
            color = "green" if row["fees_paid"] >= row["fees_total"] else "red"
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=f"<b>{row['name']}</b><br>الحي: {row['district']}<br>المدفوع: {row['fees_paid']}",
                icon=folium.Icon(color=color, icon="female", prefix="fa")
            ).add_to(m)

        st_folium(m, width="100%", height=600)

# ─── باقي الأقسام (السائقين، التوزيع، الإعدادات) ──────────────────────────────
# ... (انسخها من النسخة السابقة إذا أردت)

st.caption("نظام الخالد برو © 2025–2026 | تم التحديث: يناير 2026")