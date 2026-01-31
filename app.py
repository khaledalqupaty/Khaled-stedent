# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import sqlite3
import pathlib
import datetime
import altair as alt
import folium
from streamlit_folium import st_folium

# --- 1. إعدادات الصفحة (تنسيق الجوال) ---
st.set_page_config(
    page_title="نظام الخالد Pro",
    page_icon="🚌",
    layout="centered", # لجعل المحتوى في المنتصف وسهل القراءة
    initial_sidebar_state="collapsed"
)

# --- 2. محرك التنسيق (CSS) لإصلاح التشوه ومنع تداخل العناصر ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Almarai:wght@400;700&display=swap');
    
    /* ضبط الخط والاتجاه */
    html, body, [class*="css"] { 
        font-family: 'Almarai', sans-serif; 
        direction: rtl; 
        text-align: right; 
    }

    /* منع تداخل الأعمدة في الشاشات الصغيرة */
    [data-testid="column"] { 
        min-width: 100% !important; 
        margin-bottom: 15px; 
    }

    /* تصميم بطاقات الـ KPI بشكل احترافي */
    .mobile-card {
        background: white;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-right: 5px solid #2563eb;
        margin-bottom: 10px;
    }
    .card-label { color: #64748b; font-size: 0.85rem; font-weight: bold; }
    .card-value { color: #1e293b; font-size: 1.5rem; font-weight: 800; }

    /* تحسين شكل التبويبات */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f5f9;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. إدارة قاعدة البيانات ---
DB_PATH = "alkhaled_final.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, phone TEXT, district TEXT,
            lat REAL, lon REAL, fees_total REAL, fees_paid REAL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, bus_no TEXT, phone TEXT, capacity INTEGER
        )""")
        # إضافة بيانات تجريبية إذا كانت القاعدة فارغة
        if conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
            conn.execute("INSERT INTO students (name, phone, district, lat, lon, fees_total, fees_paid) VALUES (?,?,?,?,?,?,?)",
                       ("نورة أحمد", "0501112222", "النرجس", 24.83, 46.65, 5000, 3500))
            conn.execute("INSERT INTO drivers (name, bus_no, phone, capacity) VALUES (?,?,?,?)",
                       ("أبو محمد", "أ ب ج 123", "0590000001", 15))

init_db()

def get_data(query):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn)

def execute_query(query, params):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(query, params)
        conn.commit()

# --- 4. واجهة التطبيق الرئيسية ---

st.title("🚌 نظام الخالد الذكي")

# استخدام التبويبات كقائمة تنقل رئيسية سهلة للمس
main_tab, student_tab, driver_tab, map_tab = st.tabs(["📊 الرئيسية", "👩‍🎓 الطالبات", "🚍 السائقين", "📍 الخريطة"])

# --- تبويب الرئيسية ---
with main_tab:
    df_s = get_data("SELECT * FROM students")
    total_students = len(df_s)
    total_paid = df_s['fees_paid'].sum()
    total_remain = df_s['fees_total'].sum() - total_paid

    # بطاقات الأداء (تظهر تحت بعضها في الجوال بفضل الـ CSS)
    st.markdown(f"""
    <div class="mobile-card">
        <div class="card-label">عدد الطالبات</div>
        <div class="card-value">{total_students}</div>
    </div>
    <div class="mobile-card" style="border-right-color: #10b981;">
        <div class="card-label">إجمالي المحصل</div>
        <div class="card-value">{total_paid:,.0f} ريال</div>
    </div>
    """, unsafe_allow_html=True)

    # الرسم البياني (تم تصغيره ليناسب الشاشة)
    st.subheader("📊 ملخص الرسوم")
    chart_data = pd.DataFrame({
        "الفئة": ["المحصل", "المتبقي"],
        "المبلغ": [total_paid, total_remain]
    })
    
    donut = alt.Chart(chart_data).mark_arc(innerRadius=50, outerRadius=80).encode(
        theta=alt.Theta(field="المبلغ", type="quantitative"),
        color=alt.Color(field="الفئة", type="nominal", scale=alt.Scale(range=['#10b981', '#ef4444']), legend=alt.Legend(orient="bottom"))
    ).properties(height=250)
    
    st.altair_chart(donut, use_container_width=True)

# --- تبويب الطالبات ---
with student_tab:
    st.subheader("إدارة الطالبات")
    
    with st.expander("➕ إضافة طالبة جديدة"):
        with st.form("stu_form"):
            name = st.text_input("الاسم")
            phone = st.text_input("الجوال")
            dist = st.selectbox("الحي", ["النرجس", "الملقا", "الياسمين", "العارض"])
            f_total = st.number_input("إجمالي الرسوم", value=5000)
            f_paid = st.number_input("المدفوع حالياً", value=0)
            if st.form_submit_button("حفظ"):
                execute_query("INSERT INTO students (name, phone, district, fees_total, fees_paid) VALUES (?,?,?,?,?)",
                             (name, phone, dist, f_total, f_paid))
                st.success("تمت الإضافة!")
                st.rerun()

    df_display = get_data("SELECT name, district, fees_paid FROM students")
    st.dataframe(df_display, use_container_width=True, hide_index=True)

# --- تبويب السائقين ---
with driver_tab:
    st.subheader("قائمة السائقين")
    df_d = get_data("SELECT name, bus_no, phone FROM drivers")
    
    for _, row in df_d.iterrows():
        with st.container():
            st.markdown(f"""
            <div style="background:#f8fafc; padding:10px; border-radius:10px; margin-bottom:10px; border:1px solid #e2e8f0;">
                <b>👤 {row['name']}</b><br>
                🚌 حافلة: {row['bus_no']} <br>
                📞 {row['phone']}
            </div>
            """, unsafe_allow_html=True)
            # زر واتساب مباشر
            wa_url = f"https://wa.me/966{row['phone'][1:]}"
            st.link_button(f"تواصل مع {row['name']}", wa_url)

# --- تبويب الخريطة ---
with map_tab:
    st.subheader("مواقع الطالبات")
    df_map = get_data("SELECT name, lat, lon FROM students WHERE lat IS NOT NULL")
    
    if not df_map.empty:
        m = folium.Map(location=[24.7136, 46.6753], zoom_start=11)
        for _, row in df_map.iterrows():
            folium.Marker([row['lat'], row['lon']], popup=row['name']).add_to(m)
        st_folium(m, width="100%", height=350)
    else:
        st.info("لا توجد إحداثيات لعرضها")

# --- تذييل الصفحة ---
st.divider()
st.caption("نظام الخالد Pro | نسخة الجوال المستقرة 2026")
