# -*- coding: utf-8 -*-
import subprocess
import sys

# تثبيت المكتبات المطلوبة تلقائياً
required = ['streamlit', 'pandas', 'folium', 'fpdf2', 'openpyxl']
for package in required:
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

# الآن استيراد المكتبات
import streamlit as st
import pandas as pd
import sqlite3, pathlib, datetime, io
# -*- coding: utf-8 -*-
"""
الخالد للنقل – الإصدار النهائي الكامل (جوال/لابتوب)
كل شيء مدمج: SQLite، خريطة، PDF/Excel، Toast، ستايل احترافي
"""
import streamlit as st
import pandas as pd
import sqlite3, pathlib, datetime, io, folium, urllib.parse
from fpdf import FPDF

# -------------------- إعداد الصفحة --------------------
st.set_page_config(
    page_title="الخالد للنقل",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- ستايل احترافي RTL --------------------
st.markdown("""
<style>
:root{
  --primary:#0d47a1;
  --primary-light:#1976d2;
  --success:#2e7d32;
  --danger:#c62828;
  --bg:#f9fcff;
  --card:#ffffff;
  --text:#0d1b2a;
  --gray:#546e7a;
}
.stApp{background:var(--bg);color:var(--text);}
h1,h2,h3{color:var(--primary)!important;text-align:right;}
.stButton>button{
  width:100%;
  background:var(--primary);
  color:white!important;
  border-radius:8px;
  padding:.6rem 1.3rem;
  font-weight:600;
  box-shadow:0 3px 10px rgba(13,71,161,.2);
}
.stButton>button:hover{background:var(--primary-light);}
.metric-card{
  background:var(--card);
  border-radius:10px;
  padding:1.2rem;
  text-align:center;
  box-shadow:0 4px 12px rgba(0,0,0,.06);
  border:1px solid #e3f2fd;
}
.paid{background:#e8f5e9;color:var(--success);padding:.4rem .8rem;border-radius:999px;}
.pending{background:#ffebee;color:var(--danger);padding:.4rem .8rem;border-radius:999px;}
[data-testid="stSidebar"]{
  background:linear-gradient(to bottom,var(--primary),#1565c0)!important;
  color:white!important;
}
[data-testid="stSidebar"] .stRadio>div>label{
  color:white!important;
  padding:.8rem 1rem;
  border-radius:8px;
}
[data-testid="stSidebar"] .stRadio>div>label:hover{background:rgba(255,255,255,.15);}
[data-testid="stSidebar"] .stRadio>div>label[data-checked="true"]{
  background:rgba(255,255,255,.25);
  font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

# -------------------- قاعدة البيانات --------------------
@st.cache_resource
def init_db():
    DB_FILE = pathlib.Path("bus_data/db.sqlite")
    DB_FILE.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.executescript("""
    PRAGMA foreign_keys = ON;
    CREATE TABLE IF NOT EXISTS students(
        id     INTEGER PRIMARY KEY AUTOINCREMENT,
        name   TEXT UNIQUE NOT NULL,
        sid    TEXT UNIQUE NOT NULL,
        loc    TEXT,
        phone  TEXT,
        status TEXT DEFAULT 'انتظار'
    );
    CREATE TABLE IF NOT EXISTS drivers(
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        name     TEXT UNIQUE NOT NULL,
        bus_no   TEXT,
        phone    TEXT,
        capacity INTEGER DEFAULT 14
    );
    CREATE TABLE IF NOT EXISTS assignments(
        date       TEXT,
        driver_id  INTEGER,
        student_id INTEGER,
        PRIMARY KEY(date, driver_id, student_id),
        FOREIGN KEY(driver_id)  REFERENCES drivers(id)  ON DELETE CASCADE,
        FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    """)
    # بيانات افتراضية (أول مرة فقط)
    if not conn.execute("SELECT 1 FROM students").fetchone():
        conn.executemany("""
            INSERT INTO students(name,sid,loc,phone,status)
            VALUES(?,?,?,?,?)
        """, [
            ("نورة", "101", "حي الروضة", "0501234567", "انتظار"),
            ("سارة", "102", "حي الملقا", "0559876543", "تم الدفع"),
            ("ليان", "103", "حي النرجس", "0581112233", "انتظار"),
        ])
    if not conn.execute("SELECT 1 FROM drivers").fetchone():
        conn.executemany("""
            INSERT INTO drivers(name,bus_no,phone,capacity)
            VALUES(?,?,?,?)
        """, [
            ("أحمد محمد", "باص 1", "0591112233", 15),
            ("خالد علي", "باص 2", "0584445566", 12),
        ])
    conn.commit()
    return conn

conn = init_db()

# -------------------- دوال CRUD --------------------
@st.cache_data(ttl=60)
def get_students(_conn):
    return pd.read_sql("SELECT * FROM students ORDER BY name", _conn)

@st.cache_data(ttl=60)
def get_drivers(_conn):
    return pd.read_sql("SELECT * FROM drivers ORDER BY name", _conn)

def save_students(_conn, df):
    df.to_sql("students", _conn, if_exists="replace", index=False)
    st.cache_data.clear()

def save_drivers(_conn, df):
    df.to_sql("drivers", _conn, if_exists="replace", index=False)
    st.cache_data.clear()

def get_assign(_conn, date):
    return pd.read_sql("""
        SELECT a.date, d.name driver, s.name student
        FROM assignments a
        JOIN drivers d ON d.id = a.driver_id
        JOIN students s ON s.id = a.student_id
        WHERE a.date = ?
    """, _conn, params=(date,))

def set_assign(_conn, date, driver_id, student_ids):
    with _conn:
        _conn.execute("DELETE FROM assignments WHERE date=? AND driver_id=?", (date, driver_id))
        _conn.executemany("INSERT INTO assignments(date,driver_id,student_id) VALUES(?,?,?)",
                         [(date, driver_id, sid) for sid in student_ids])
    st.cache_data.clear()

def attendance_days(_conn, student_id):
    return _conn.execute("SELECT COUNT(*) FROM assignments WHERE student_id=?", (student_id,)).fetchone()[0]

# -------------------- تصدير Excel & PDF --------------------
def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    return out.getvalue()

def to_pdf(df, title):
    pdf = FPDF()
    pdf.set_auto_page_break(True, 10)
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.cell(0, 10, title, ln=True, align="C")
    pdf.ln(4)
    pdf.set_font("Arial", size=10)
    cols = df.columns
    for c in cols:
        pdf.cell(40, 8, c, border=1)
    pdf.ln()
    for _, row in df.iterrows():
        for c in cols:
            pdf.cell(40, 8, str(row[c]), border=1)
        pdf.ln()
    byte = io.BytesIO()
    pdf.output(byte)
    return byte.getvalue()

# -------------------- شريط جانبي --------------------
today = datetime.date.today().isoformat()
with st.sidebar:
    st.image("https://drive.google.com/uc?id=1WxVKMdn81Fmb8PQFUtR8avlMkhkHhDJX", width=110)
    menu = st.radio("", ["🏠 Dashboard", "👧 إدارة الطالبات", "🚌 إدارة السائقين",
                         "📅 التوزيع اليومي", "📊 تقارير", "🗺 الخريطة"], label_visibility="collapsed")
    st.divider()
    if st.button("💾 حفظ يدوي"):
        st.success("تم الحفظ")
    st.caption(f"آخر تحديث: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")

# -------------------- Dashboard --------------------
if menu == "🏠 Dashboard":
    st.header("نظرة عامة")
    stu, drv = get_students(conn), get_drivers(conn)
    ass = get_assign(conn, today)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("الطالبات", len(stu))
    c2.metric("تم الدفع", len(stu[stu.status == "تم الدفع"]))
    c3.metric("السائقين", len(drv))
    c4.metric("موزعات اليوم", len(ass))
    if len(ass):
        ch = ass.groupby("driver").size()
        st.bar_chart(ch, color="#0d47a1")

# -------------------- إدارة الطالبات --------------------
elif menu == "👧 إدارة الطالبات":
    st.header("إدارة الطالبات")
    df = get_students(conn)
    # عرض + تعديل
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="stu_ed")
    if not edited.equals(df):
        save_students(conn, edited)
        st.toast("✅ تم حفظ الطالبات")
    # أزرار تصدير
    c1, c2 = st.columns(2)
    c1.download_button("📥 Excel", to_excel(edited), "students.xlsx")
    c2.download_button("📄 PDF", to_pdf(edited, "تقرير الطالبات"), "students.pdf")

# -------------------- إدارة السائقين --------------------
elif menu == "🚌 إدارة السائقين":
    st.header("إدارة السائقين")
    df = get_drivers(conn)
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="drv_ed")
    if not edited.equals(df):
        save_drivers(conn, edited)
        st.toast("✅ تم حفظ السائقين")
    c1, c2 = st.columns(2)
    c1.download_button("📥 Excel", to_excel(edited), "drivers.xlsx")
    c2.download_button("📄 PDF", to_pdf(edited, "تقرير السائقين"), "drivers.pdf")

# -------------------- التوزيع اليومي --------------------
elif menu == "📅 التوزيع اليومي":
    st.header(f"توزيع يوم: {today}")
    stu, drv = get_students(conn), get_drivers(conn)
    assigned = get_assign(conn, today)
    for _, d in drv.iterrows():
        with st.expander(f"🚌 {d['name']} – {d['bus_no']} (السعة {d['capacity']})"):
            prev = assigned[assigned.driver == d["name"]]["student"].tolist()
            options = stu["name"].tolist()
            sel = st.multiselect("اختر الطالبات", options, default=prev, key=f"assign_{d['id']}")
            if len(sel) > d["capacity"]:
                st.error(f"⚠️ تجاوزت السعة ({d['capacity']})")
            if st.button("حفظ التوزيع", key=f"save_{d['id']}"):
                ids = [int(stu[stu.name == s].id.iloc[0]) for s in sel]
                set_assign(conn, today, d["id"], ids)
                st.toast("تم الحفظ")

# -------------------- تقارير --------------------
elif menu == "📊 تقارير":
    st.header("تقارير")
    stu = get_students(conn)
    stu["days"] = stu.id.apply(lambda x: attendance_days(conn, x))
    c1, c2 = st.columns(2)
    c1.download_button("📊 Excel كامل", to_excel(stu), "full_report.xlsx")
    c2.download_button("📄 PDF كامل", to_pdf(stu, "تقرير شامل"), "full_report.pdf")
    st.dataframe(stu, use_container_width=True)

# -------------------- الخريطة التفاعلية --------------------
elif menu == "🗺 الخريطة":
    st.header("مواقع الطالبات")
    stu = get_students(conn)
    if stu.empty:
        st.info("لا توجد بيانات")
        st.stop()
    # مركز الخريطة (الرياض)
    lat, lon = 24.7136, 46.6753
    m = folium.Map(location=[lat, lon], zoom_start=11)
    for _, r in stu.iterrows():
        if r["loc"]:
            folium.Marker(
                location=[lat, lon],  # يمكن استبداله بنتيجة geocode حقيقية لاحقاً
                popup=f"{r['name']} ({r['sid']})",
                tooltip=r["loc"]
            ).add_to(m)
    st.components.v1.html(m._repr_html_(), height=500)
