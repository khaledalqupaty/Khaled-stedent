# -*- coding: utf-8 -*-
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

# --- إعدادات الصفحة ---
st.set_page_config(page_title="الخالد برو", page_icon="🚌", layout="wide")

# --- تنسيق الواجهة CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Almarai:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Almarai', sans-serif; text-align: right; }
    .stMetric { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# --- قاعدة البيانات ---
@st.cache_resource
def init_db():
    conn = sqlite3.connect("alkhaled_v3.db", check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sid TEXT, phone TEXT, district TEXT, fees_total REAL, fees_paid REAL, status TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS drivers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, bus_no TEXT, capacity INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS trips (date TEXT, driver_id INTEGER, student_id INTEGER, PRIMARY KEY(date, driver_id, student_id))")
    conn.commit()
    return conn

conn = init_db()

# --- القائمة الجانبية ---
with st.sidebar:
    st.title("🚌 نظام الخالد")
    menu = st.radio("القائمة", ["📊 الإحصائيات", "📅 التوزيع اليومي", "👩‍🎓 إدارة الطالبات", "🚍 إدارة السائقين"])

# --- 1. الإحصائيات ---
if menu == "📊 الإحصائيات":
    st.header("📊 لوحة التحكم")
    df_stu = pd.read_sql("SELECT * FROM students", conn)
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي الطالبات", len(df_stu))
    c2.metric("إجمالي التحصيل", f"{df_stu['fees_paid'].sum() if not df_stu.empty else 0} ريال")
    
    if not df_stu.empty:
        chart = alt.Chart(df_stu).mark_bar().encode(x='district', y='count()', color='district')
        st.altair_chart(chart, use_container_width=True)

# --- 2. التوزيع اليومي ---
elif menu == "📅 التوزيع اليومي":
    st.header("📅 التوزيع اليومي للحافلات")
    date_str = st.date_input("اختر التاريخ", datetime.date.today()).strftime("%Y-%m-%d")
    
    drivers = pd.read_sql("SELECT * FROM drivers", conn)
    students = pd.read_sql("SELECT * FROM students WHERE status='نشط'", conn)
    
    for _, drv in drivers.iterrows():
        with st.expander(f"باص: {drv['name']} ({drv['bus_no']})"):
            # جلب الطلاب الموزعين مسبقاً لهذا اليوم
            current = pd.read_sql(f"SELECT student_id FROM trips WHERE date='{date_str}' AND driver_id={drv['id']}", conn)
            defaults = current['student_id'].tolist()
            
            selected = st.multiselect(f"اختر طالبات {drv['name']}", options=students['id'].tolist(), 
                                     format_func=lambda x: students[students['id']==x]['name'].values[0],
                                     default=defaults, key=f"drv_{drv['id']}")
            
            if st.button("حفظ التوزيع", key=f"btn_{drv['id']}"):
                conn.execute(f"DELETE FROM trips WHERE date='{date_str}' AND driver_id={drv['id']}")
                for s_id in selected:
                    conn.execute("INSERT INTO trips (date, driver_id, student_id) VALUES (?,?,?)", (date_str, drv['id'], s_id))
                conn.commit()
                st.success("تم الحفظ!")

# --- 3. إدارة الطالبات ---
elif menu == "👩‍🎓 إدارة الطالبات":
    st.header("👩‍🎓 بيانات الطالبات")
    
    with st.expander("➕ إضافة طالبة جديدة"):
        with st.form("add_stu"):
            name = st.text_input("الاسم")
            sid = st.text_input("الهوية")
            dist = st.text_input("الحي")
            fees = st.number_input("الرسوم", value=5000)
            if st.form_submit_button("إضافة"):
                conn.execute("INSERT INTO students (name, sid, district, fees_total, fees_paid, status) VALUES (?,?,?,?,?,?)", 
                             (name, sid, dist, fees, 0, 'نشط'))
                conn.commit()
                st.rerun()

    df = pd.read_sql("SELECT s.*, (SELECT COUNT(*) FROM trips t WHERE t.student_id = s.id) as days FROM students s", conn)
    st.data_editor(df, use_container_width=True, hide_index=True)

# --- 4. إدارة السائقين ---
elif menu == "🚍 إدارة السائقين":
    st.header("🚍 بيانات السائقين")
    with st.form("add_drv"):
        d_name = st.text_input("اسم السائق")
        d_bus = st.text_input("رقم الباص")
        d_cap = st.number_input("السعة", value=15)
        if st.form_submit_button("إضافة سائق"):
            conn.execute("INSERT INTO drivers (name, bus_no, capacity) VALUES (?,?,?)", (d_name, d_bus, d_cap))
            conn.commit()
            st.rerun()
            
    df_drv = pd.read_sql("SELECT * FROM drivers", conn)
    st.data_editor(df_drv, use_container_width=True, hide_index=True)
