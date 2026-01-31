# -*- coding: utf-8 -*-
"""
نظام الخالد الذكي للنقل المدرسي - الإصدار الاحترافي (Pro Edition)
معدل ليعمل على Streamlit Cloud: اتصال جديد في كل عملية + /tmp
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
st.markdown("""... (نفس الـ CSS السابق بدون تغيير) ...""", unsafe_allow_html=True)

# ─── مسار قاعدة البيانات ──────────────────────────────────────────────────────
def get_db_path():
    return pathlib.Path("/tmp/alkhaled_pro.db")

# ─── دوال الاتصال والاستعلامات (اتصال جديد كل مرة) ──────────────────────────
def init_db():
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS students (...)""")  # نفس التعريف السابق
    cur.execute("""CREATE TABLE IF NOT EXISTS drivers (...)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS trips (...)""")

    if not cur.execute("SELECT 1 FROM students LIMIT 1").fetchone():
        # بيانات تجريبية (نفس السابق)
        cur.executemany("INSERT INTO students VALUES (...) ", students_seed)
        cur.executemany("INSERT INTO drivers VALUES (...) ", drivers_seed)

    conn.commit()
    conn.close()

# نفذ الإنشاء مرة واحدة عند بداية التطبيق
init_db()

def run_query(query, params=None):
    conn = sqlite3.connect(get_db_path())
    try:
        with conn:
            if params:
                conn.execute(query, params)
            else:
                conn.execute(query)
        return True
    except sqlite3.IntegrityError:
        st.error("خطأ: قيمة مكررة")
        return False
    except Exception as e:
        st.error(f"خطأ في التنفيذ: {str(e)}")
        return False
    finally:
        conn.close()

def get_df(query, params=None):
    conn = sqlite3.connect(get_db_path())
    try:
        return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        st.error(f"خطأ في القراءة: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()

# ─── باقي الكود (القائمة الجانبية، لوحة القيادة، الطالبات، إلخ) ──────────────
# استخدم run_query و get_df في كل مكان بدل conn مباشرة

# مثال في إضافة طالبة:
if submitted:
    success = run_query(
        """
        INSERT INTO students 
        (name, sid, phone, district, lat, lon, fees_total, fees_paid, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, sid, phone, dist, lat, lon, fees, 0.0, 'نشط')
    )
    # ... باقي الكود

# مثال في عرض الجدول:
df = get_df(q)

# ─── باقي الأقسام ──────────────────────────────────────────────────────────────
# (السائقين، الخريطة، التوزيع، الإعدادات) نفسها، لكن باستخدام get_df و run_query