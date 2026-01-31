# -*- coding: utf-8 -*-
"""
نظام الخالد الذكي للنقل المدرسي - نسخة الجوال الاحترافية (Mobile Pro)
تحديثات: تكامل واتساب + رسوم بيانية + إدارة كاملة للإضافة
"""
import streamlit as st
import pandas as pd
import sqlite3
import pathlib
import datetime
import altair as alt
import folium
from streamlit_folium import st_folium

# إعداد الصفحة لتناسب الجوال
st.set_page_config(
    page_title="الخالد برو",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="collapsed" # القائمة مغلقة تلقائياً للجوال
)

# --- CSS تحسينات بصرية للجوال ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Almarai:wght@300;400;700;800&display=swap');
    :root { --primary: #2563eb; --bg: #f8fafc; --card: #ffffff; }
    html, body, [class*="css"] { font-family: 'Almarai', sans-serif; direction: rtl; }
    
    /* تحسين البطاقات */
    .kpi-card { background: var(--card); border-radius: 12px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-right: 4px solid var(--primary); margin-bottom: 10px; }
    .kpi-title { color: #64748b; font-size: 0.8rem; font-weight: 700; }
    .kpi-value { color: #0f172a; font-size: 1.4rem; font-weight: 800; }
    
    /* تحسين الأزرار للجوال */
    div.stButton > button { width: 100%; border-radius: 10px; height: 50px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- إعداد قاعدة البيانات ---
DB_PATH = pathlib.Path("alkhaled_pro_v2.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, sid TEXT UNIQUE, phone TEXT,
        district TEXT, lat REAL, lon REAL,
        fees_total REAL, fees_paid REAL, status TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, bus_no TEXT UNIQUE, phone TEXT,
        capacity INTEGER, area TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS trips (
        trip_date TEXT, driver_id INTEGER, student_id INTEGER,
        trip_type TEXT, PRIMARY KEY(trip_date, driver_id, student_id, trip_type)
    )""")
    # بيانات أولية للتجربة
    if not c.execute("SELECT 1 FROM students LIMIT 1").fetchone():
        data = [("نورة فهد", "101", "0555555555", "الملقا", 24.81, 46.61, 5000, 5000, "نشط")]
        c.executemany("INSERT INTO students (name, sid, phone, district, lat, lon, fees_total, fees_paid, status) VALUES (?,?,?,?,?,?,?,?,?)", data)
    conn.commit()
    conn.close()

if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

def get_df(query, params=None):
    with sqlite3.connect(DB_PATH) as conn:
        try:
            return pd.read_sql_query(query, conn, params=params)
        except: return pd.DataFrame()

def run_query(query, params):
    with sqlite3.connect(DB_PATH) as conn:
        try:
            conn.execute(query, params)
            conn.commit()
            return True
        except Exception as e:
            st.error(f"خطأ: {e}")
            return False

# --- الواجهة الرئيسية ---
with st.sidebar:
    st.header("🚌 الخالد للنقل")
    selected = st.radio("القائمة", ["📊 لوحة القيادة", "👩‍🎓 الطالبات", "🚍 السائقين", "📍 الخريطة", "🗓️ التوزيع", "⚙️ الإعدادات"])
    st.divider()
    st.caption("📱 نسخة الجوال v2.0")

# --- الصفحات ---

if selected == "📊 لوحة القيادة":
    st.title("الرئيسية")
    df_s = get_df("SELECT * FROM students")
    
    # بطاقات الأداء
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">عدد الطالبات</div><div class="kpi-value">{len(df_s)}</div></div>', unsafe_allow_html=True)
    with col2:
        paid = df_s['fees_paid'].sum() if not df_s.empty else 0
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">التحصيل</div><div class="kpi-value">{paid/1000:.1f}k</div></div>', unsafe_allow_html=True)

    # رسم بياني للسداد
    if not df_s.empty:
        st.subheader("تحليل الرسوم")
        total_fees = df_s['fees_total'].sum()
        total_paid = df_s['fees_paid'].sum()
        remain = total_fees - total_paid
        
        chart_data = pd.DataFrame({
            'Category': ['تم التحصيل', 'المتبقي'],
            'Value': [total_paid, remain]
        })
        
        c = alt.Chart(chart_data).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Value", type="quantitative"),
            color=alt.Color(field="Category", type="nominal", scale=alt.Scale(range=['#10b981', '#ef4444']))
        )
        st.altair_chart(c, use_container_width=True)

elif selected == "👩‍🎓 الطالبات":
    st.title("إدارة الطالبات")
    tab1, tab2 = st.tabs(["📋 القائمة والواتس", "➕ طالبة جديدة"])
    
    with tab1:
        df = get_df("SELECT name, phone, district, fees_paid, fees_total FROM students")
        if not df.empty:
            # تحويل الرقم لرابط واتساب
            df['واتساب'] = "https://wa.me/966" + df['phone'].astype(str).str.lstrip('0')
            
            st.dataframe(
                df[['name', 'district', 'fees_paid', 'واتساب']],
                column_config={
                    "واتساب": st.column_config.LinkColumn("تواصل", display_text="💬"),
                    "fees_paid": st.column_config.ProgressColumn("المدفوع", min_value=0, max_value=5000, format="%d ريال")
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("لا توجد بيانات")

    with tab2:
        with st.form("add_student"):
            c1, c2 = st.columns(2)
            name = c1.text_input("الاسم الثلاثي")
            sid = c2.text_input("رقم الهوية/الملف")
            phone = st.text_input("الجوال (05xxxx)")
            district = st.selectbox("الحي", ["الملقا", "النرجس", "العارض", "الياسمين", "أخرى"])
            
            st.caption("📍 الموقع (اختياري - انسخ من جوجل ماب)")
            cl1, cl2 = st.columns(2)
            lat = cl1.number_input("Lat", value=24.0, format="%.4f")
            lon = cl2.number_input("Lon", value=46.0, format="%.4f")
            
            if st.form_submit_button("حفظ الطالبة"):
                if run_query("INSERT INTO students (name, sid, phone, district, lat, lon) VALUES (?,?,?,?,?,?)", 
                           (name, sid, phone, district, lat, lon)):
                    st.success("تم الحفظ!")
                    st.rerun()

elif selected == "🚍 السائقين":
    st.title("السائقين")
    tab1, tab2 = st.tabs(["📋 القائمة", "➕ سائق جديد"])
    
    with tab1:
        df = get_df("SELECT name, bus_no, phone, capacity FROM drivers")
        if not df.empty:
            df['واتساب'] = "https://wa.me/966" + df['phone'].astype(str).str.lstrip('0')
            st.dataframe(
                df,
                column_config={"واتساب": st.column_config.LinkColumn("تواصل", display_text="📞")},
                use_container_width=True, hide_index=True
            )
    
    with tab2:
        with st.form("add_driver"):
            d_name = st.text_input("اسم السائق")
            d_bus = st.text_input("رقم اللوحة")
            d_phone = st.text_input("الجوال")
            d_cap = st.number_input("السعة", 10, 50, 15)
            if st.form_submit_button("حفظ السائق"):
                if run_query("INSERT INTO drivers (name, bus_no, phone, capacity) VALUES (?,?,?,?)", 
                           (d_name, d_bus, d_phone, d_cap)):
                    st.success("تم الحفظ!")
                    st.rerun()

elif selected == "📍 الخريطة":
    st.title("المواقع")
    # عرض الخريطة بارتفاع مناسب للجوال
    df_map = get_df("SELECT name, lat, lon, district FROM students WHERE lat > 20")
    if not df_map.empty:
        m = folium.Map(location=[24.7136, 46.6753], zoom_start=11)
        for _, row in df_map.iterrows():
            folium.Marker(
                [row['lat'], row['lon']], 
                popup=row['name'],
                icon=folium.Icon(icon="user", color="blue")
            ).add_to(m)
        st_folium(m, width="100%", height=400) # ارتفاع مناسب للجوال
    else:
        st.warning("أضف طالبات مع إحداثيات صحيحة أولاً")

elif selected == "🗓️ التوزيع":
    st.title("التوزيع اليومي")
    date_pick = st.date_input("التاريخ", datetime.date.today())
    
    drivers = get_df("SELECT id, name, capacity FROM drivers")
    students = get_df("SELECT id, name FROM students WHERE status='نشط'")
    
    if not drivers.empty:
        # اختيار السائق
        d_list = {r['name']: r['id'] for _, r in drivers.iterrows()}
        s_driver = st.selectbox("السائق", list(d_list.keys()))
        driver_id = d_list[s_driver]
        
        # حساب السعة
        cap = drivers[drivers['id']==driver_id]['capacity'].iloc[0]
        used = get_df("SELECT COUNT(*) as c FROM trips WHERE trip_date=? AND driver_id=?", 
                    (str(date_pick), driver_id)).iloc[0]['c']
        
        st.progress(used/cap if cap > 0 else 0)
        st.caption(f"المقاعد: {used} / {cap}")
        
        # نموذج التوزيع
        with st.form("assign"):
            s_choices = st.multiselect("اختر الطالبات", students['name'].tolist())
            if st.form_submit_button("تأكيد التوزيع"):
                for s_name in s_choices:
                    sid = students[students['name']==s_name]['id'].iloc[0]
                    run_query("INSERT OR IGNORE INTO trips (trip_date, driver_id, student_id, trip_type) VALUES (?,?,?,?)",
                            (str(date_pick), driver_id, sid, "go"))
                st.success("تم التوزيع!")

elif selected == "⚙️ الإعدادات":
    st.title("الإعدادات")
    st.info("رقم الإصدار: Mobile Pro 2.1")
    if st.button("🗑️ حذف جميع البيانات (للبدء من جديد)"):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM students")
            conn.execute("DELETE FROM drivers")
            conn.execute("DELETE FROM trips")
        st.warning("تم تصفير النظام")
        st.rerun()
