# -*- coding: utf-8 -*-
"""
الخالد للنقل – نسخة ثابتة وسهلة
"""
import streamlit as st
import pandas as pd
import sqlite3, pathlib, datetime, io

# تهيئة الصفحة
st.set_page_config(page_title="الخالد للنقل", layout="wide")

# تهيئة قاعدة البيانات
@st.cache_resource
def init_db():
    DB_FILE = pathlib.Path("bus_data/db.sqlite")
    DB_FILE.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            sid TEXT,
            loc TEXT,
            phone TEXT,
            status TEXT DEFAULT 'انتظار'
        )
    """)
    conn.commit()
    return conn

conn = init_db()

# عرض بسيط
st.title("الخالد للنقل")
st.write("اختبار الاتصال بقاعدة البيانات")

# جلب البيانات
df = pd.read_sql("SELECT * FROM students", conn)
st.dataframe(df)

# نموذج إضافة
with st.form("add_student"):
    name = st.text_input("الاسم")
    sid = st.text_input("رقم الطالبة")
    loc = st.text_input("الموقع")
    submitted = st.form_submit_button("إضافة")
    if submitted:
        conn.execute("INSERT INTO students(name, sid, loc) VALUES(?,?,?)", (name, sid, loc))
        conn.commit()
        st.success("تمت الإضافة")
        st.rerun()
