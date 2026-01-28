# dashboard.py
# يمكن استيراده داخل app.py أو تشغيله standalone لعرض تقارير سريعة

import streamlit as st
import pandas as pd
import sqlite3, pathlib, datetime

DB_FILE = pathlib.Path("bus_data/db.sqlite")
conn   = sqlite3.connect(DB_FILE, check_same_thread=False)

# بيانات سريعة
today   = datetime.date.today().isoformat()
students= pd.read_sql("SELECT * FROM students", conn)
drivers = pd.read_sql("SELECT * FROM drivers", conn)
assign  = pd.read_sql("SELECT * FROM assignments WHERE date=?", conn, params=(today,))

st.title("Dashboard – الخالد للنقل")
c1,c2,c3,c4=st.columns(4)
c1.metric("الطالبات", len(students))
c2.metric("تم الدفع", len(students[students.status=="تم الدفع"]))
c3.metric("السائقين", len(drivers))
c4.metric("موزعات اليوم", len(assign))

if len(assign):
    ch=assign.groupby("driver_id").size()
    st.bar_chart(ch)
