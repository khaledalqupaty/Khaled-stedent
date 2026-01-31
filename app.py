# -*- coding: utf-8 -*-
"""
نظام الخالد الذكي للنقل المدرسي - الإصدار الاحترافي (Pro Edition)
معدل لـ Streamlit Cloud: init_db مرة واحدة فقط + اتصال جديد كل عملية
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
st.set_page_config(page_title="نظام الخالد برو", page_icon="🚌", layout="wide", initial_sidebar_state="expanded")

# ─── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Almarai:wght@300;400;700;800&display=swap');
    :root {
        --primary: #2563eb; --secondary: #1e40af; --bg: #f8fafc; --card: #ffffff;
        --text: #0f172a; --success: #10b981; --warning: #f59e0b; --danger: #ef4444;
    }
    html, body, [class*="css"] { font-family: 'Almarai', sans-serif; }
    .stApp { background-color: var(--bg); }
    .kpi-card { background: var(--card); border-radius: 16px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border-right: 5px solid var(--primary); transition: transform 0.2s; }
    .kpi-card:hover { transform: translateY(-5px); }
    .kpi-title { color: #64748b; font-size: 0.9rem; font-weight: 700; margin-bottom: 5px; }
    .kpi-value { color: var(--text); font-size: 1.8rem; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# ─── مسار قاعدة البيانات ──────────────────────────────────────────────────────
DB_PATH = pathlib.Path("/tmp/alkhaled_pro.db")

# ─── إنشاء قاعدة البيانات مرة واحدة فقط ──────────────────────────────────────
if "db_initialized" not in st.session_state:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sid TEXT UNIQUE NOT NULL,
            phone TEXT,
            district TEXT,
            lat REAL,
            lon REAL,
            fees_total REAL DEFAULT 5000,
            fees_paid REAL DEFAULT 0,
            status TEXT DEFAULT 'نشط'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            bus_no TEXT UNIQUE,
            phone TEXT,
            capacity INTEGER,
            route_area TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            trip_date TEXT,
            driver_id INTEGER,
            student_id INTEGER,
            trip_type TEXT DEFAULT 'go',
            PRIMARY KEY(trip_date, driver_id, student_id, trip_type)
        )
    """)

    if not cur.execute("SELECT 1 FROM students LIMIT 1").fetchone():
        students_seed = [
            ("نورة فهد", "101", "0501111111", "الملقا", 24.810, 46.610, 5000, 5000, "نشط"),
            ("سارة أحمد", "102", "0502222222", "النرجس", 24.830, 46.650, 5000, 2500, "نشط"),
            ("ليان خالد", "103", "0503333333", "الياسمين", 24.820, 46.630, 5000, 0, "نشط"),
            ("ريم محمد", "104", "0504444444", "العارض", 24.850, 46.660, 5000, 5000, "نشط"),
        ]
        cur.executemany("INSERT INTO students VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)", students_seed)

        drivers_seed = [
            ("أبو عبدالله", "BUS-01", "0590000001", 15, "شمال الرياض"),
            ("أبو صالح", "BUS-02", "0590000002", 12, "وسط الرياض"),
        ]
        cur.executemany("INSERT INTO drivers VALUES (NULL, ?, ?, ?, ?)", drivers_seed)

    conn.commit()
    conn.close()
    st.session_state.db_initialized = True

# ─── دوال مساعدة (اتصال جديد كل مرة) ─────────────────────────────────────────
def run_query(query, params=None):
    conn = sqlite3.connect(DB_PATH)
    try:
        with conn:
            if params:
                conn.execute(query, params)
            else:
                conn.execute(query)
        return True
    except sqlite3.IntegrityError:
        st.error("خطأ: قيمة مكررة (رقم الملف أو رقم الحافلة)")
        return False
    except Exception as e:
        st.error(f"خطأ في التنفيذ: {str(e)}")
        return False
    finally:
        conn.close()

def get_df(query, params=None):
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        st.error(f"خطأ في القراءة: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()

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
    st.info("💡 نصيحة: جرب إضافة طالبة جديدة وتحقق من الخريطة")

# ─── باقي الكود (لوحة القيادة، الطالبات، السائقين، الخريطة، التوزيع، الإعدادات) ──
# استخدم run_query و get_df في كل مكان

# مثال سريع لصفحة الطالبات (أكمل الباقي بنفس الطريقة)
if menu == "👩‍🎓 الطالبات والرسوم":
    st.title("👩‍🎓 إدارة الطالبات والرسوم")
    df = get_df("SELECT * FROM students")
    st.dataframe(df)

# ... أضف باقي الأقسام بنفس الأسلوب (استخدم get_df و run_query فقط)

st.caption("نظام الخالد برو © 2025–2026 | تم التصحيح للسحابة")