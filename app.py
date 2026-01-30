# -*- coding: utf-8 -*-
"""
الخالد للنقل – الإصدار النهائي الاحترافي
تصميم متجاوب + ألوان حالة الدفع + خطوط أنيقة
"""
import streamlit as st
import pandas as pd
import sqlite3, pathlib, datetime, io
import folium
from fpdf import FPDF

st.set_page_config(page_title="الخالد للنقل", layout="wide", initial_sidebar_state="expanded")

# -------------------- ستايل احترافي متجاوب --------------------
st.markdown("""
<style>
/* استيراد خط Tajawal من Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');

:root{
  --primary:#0d47a1;
  --primary-light:#1976d2;
  --success:#2e7d32;
  --danger:#c62828;
  --bg:#f5f7fa;
  --card:#ffffff;
  --text:#0d1b2a;
  --shadow:0 4px 20px rgba(0,0,0,.08);
  --transition:all .3s ease;
}

.stApp{background:var(--bg);font-family:'Tajawal',sans-serif;color:var(--text);}
h1,h2,h3{color:var(--primary)!important;text-align:right;font-weight:700;}

/* أزرار احترافية */
.stButton>button{
  width:100%;
  background:linear-gradient(135deg,var(--primary),var(--primary-light));
  color:white!important;
  border:none;
  border-radius:12px;
  padding:.75rem 1.5rem;
  font-weight:700;
  font-size:1.05rem;
  box-shadow:var(--shadow);
  transition:var(--transition);
}
.stButton>button:hover{
  transform:translateY(-2px);
  box-shadow:0 6px 25px rgba(13,71,161,.3);
}

/* كروت الإحصائيات */
.metric-card{
  background:var(--card);
  border-radius:16px;
  padding:1.5rem;
  text-align:center;
  box-shadow:var(--shadow);
  transition:var(--transition);
}
.metric-card:hover{transform:translateY(-4px);}
.metric-card h3{font-size:2.2rem;margin-bottom:.5rem;}

/* ألوان حالة الدفع */
.status-paid{
  background:linear-gradient(135deg,#43a047,#66bb6a);
  color:#fff;
  padding:.4rem 1rem;
  border-radius:999px;
  font-weight:700;
  box-shadow:0 2px 8px rgba(67,160,71,.3);
}
.status-pending{
  background:linear-gradient(135deg,#e53935,#ef5350);
  color:#fff;
  padding:.4rem 1rem;
  border-radius:999px;
  font-weight:700;
  box-shadow:0 2px 8px rgba(229,57,53,.3);
}

/* شريط جانبي أنيق */
[data-testid="stSidebar"]{
  background:linear-gradient(180deg,var(--primary),#1565c0)!important;
  color:white!important;
  box-shadow:var(--shadow);
}
[data-testid="stSidebar"] .stRadio>div>label{
  color:white!important;
  padding:.9rem 1.1rem;
  border-radius:12px;
  margin:4px 0;
  transition:var(--transition);
}
[data-testid="stSidebar"] .stRadio>div>label:hover{background:rgba(255,255,255,.15);}
[data-testid="stSidebar"] .stRadio>div>label[data-checked="true"]{
  background:rgba(255,255,255,.25);
  font-weight:700;
  box-shadow:0 2px 10px rgba(0,0,0,.1);
}

/* جداول أنيقة */
table{width:100%;border-collapse:collapse;margin-top:1rem;}
th,td{padding:.75rem;border:1px solid #e3f2fd;text-align:center;}
th{background:#e3f2fd;color:var(--primary);font-weight:700;}
.stDataFrame{border-radius:12px;overflow:hidden;box-shadow:var(--shadow);}

/* تصدير أنيق */
.exports{display:flex;gap:1rem;margin-top:1rem;}
.exports button{
  background:linear-gradient(135deg,#2e7d32,#4caf50);
  color:white;
  border:none;
  padding:.6rem 1.2rem;
  border-radius:10px;
  font-weight:700;
  box-shadow:0 3px 10px rgba(46,125,50,.3);
  transition:var(--transition);
}
.exports button:hover{transform:translateY(-2px);box-shadow:0 5px 15px rgba(46,125,50,.4);}
</style>
""", unsafe_allow_html=True)

# -------------------- قاعدة البيانات --------------------
@st.cache_resource
def init_db():
    DB_FILE = pathlib.Path("bus_data/db.sqlite")
    DB_FILE.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        sid TEXT UNIQUE NOT NULL,
        loc TEXT,
        phone TEXT,
        status TEXT DEFAULT 'انتظار'
    );
    CREATE TABLE IF NOT EXISTS drivers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        bus_no TEXT,
        phone TEXT,
        capacity INTEGER DEFAULT 14
    );
    CREATE TABLE IF NOT EXISTS assignments(
        date TEXT,
        driver_id INTEGER,
        student_id INTEGER,
        PRIMARY KEY(date, driver_id, student_id)
    );
    """)
    if not conn.execute("SELECT 1 FROM students").fetchone():
        conn.executemany("INSERT INTO students(name,sid,loc,phone,status) VALUES(?,?,?,?,?)",
                         [("نورة","101","حي الروضة","0501234567","انتظار"),
                          ("سارة","102","حي الملقا","0559876543","تم الدفع"),
                          ("ليان","103","حي النرجس","0581112233","انتظار")])
    if not conn.execute("SELECT 1 FROM drivers").fetchone():
        conn.executemany("INSERT INTO drivers(name,bus_no,phone,capacity) VALUES(?,?,?,?)",
                         [("أحمد محمد","باص 1","0591112233",15),
                          ("خالد علي","باص 2","0584445566",12)])
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
    pdf.set_font('Arial', size=16)
    # عنوان بالإنجليزي مؤقت لتجنب مشاكل الترميز
    pdf.cell(0, 10, title.encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
    pdf.ln(4)
    pdf.set_font('Arial', size=10)
    cols = df.columns
    for c in cols:
        pdf.cell(40, 8, str(c).encode('latin-1', 'replace').decode('latin-1'), border=1)
    pdf.ln()
    for _, row in df.iterrows():
        for c in cols:
            txt = str(row[c]).encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(40, 8, txt, border=1)
        pdf.ln()
    byte = io.BytesIO()
    pdf.output(byte)
    return byte.getvalue()

# -------------------- التنقل --------------------
today = datetime.date.today().isoformat()
with st.sidebar:
    st.image("https://drive.google.com/uc?id=1WxVKMdn81Fmb8PQFUtR8avlMkhkHhDJX", width=110)
    menu = st.radio("", ["🏠 Dashboard", "👧 إدارة الطالبات", "🚌 إدارة السائقين",
                         "📅 التوزيع اليومي", "📊 تقارير", "🗺 الخريطة"], label_visibility="collapsed")
    st.divider()
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
    
    # عرض مخصص مع ألوان الحالة
    for _, row in df.iterrows():
        status_class = "status-paid" if row["status"] == "تم الدفع" else "status-pending"
        col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
        col1.write(f"**{row['name']}**")
        col2.write(row['sid'])
        col3.write(row['loc'])
        col4.markdown(f'<span class="{status_class}">{row["status"]}</span>', unsafe_allow_html=True)
    
    # تعديل البيانات
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="stu_ed")
    if not edited.equals(df):
        save_students(conn, edited)
        st.toast("✅ تم حفظ الطالبات", icon="✨")
    
    # أزرار تصدير أنيقة
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📥 Excel", to_excel(edited), "students.xlsx", help="تحميل كملف Excel")
    with c2:
        st.download_button("📄 PDF", to_pdf(edited, "Students Report"), "students.pdf", help="تحميل كملف PDF")

# -------------------- إدارة السائقين --------------------
elif menu == "🚌 إدارة السائقين":
    st.header("إدارة السائقين")
    df = get_drivers(conn)
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="drv_ed")
    if not edited.equals(df):
        save_drivers(conn, edited)
        st.toast("✅ تم حفظ السائقين", icon="✨")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📥 Excel", to_excel(edited), "drivers.xlsx", help="تحميل كملف Excel")
    with c2:
        st.download_button("📄 PDF", to_pdf(edited, "Drivers Report"), "drivers.pdf", help="تحميل كملف PDF")

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
                st.toast("✅ تم حفظ التوزيع", icon="✨")

# -------------------- تقارير --------------------
elif menu == "📊 تقارير":
    st.header("تقارير")
    stu = get_students(conn)
    stu["days"] = stu.id.apply(lambda x: attendance_days(conn, x))
    
    # عرض البيانات مع ألوان الحالة
    for _, row in stu.iterrows():
        status_class = "status-paid" if row["status"] == "تم الدفع" else "status-pending"
        col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 1])
        col1.write(f"**{row['name']}**")
        col2.write(row['sid'])
        col3.write(row['loc'])
        col4.write(row['days'])
        col5.markdown(f'<span class="{status_class}">{row["status"]}</span>', unsafe_allow_html=True)
    
    # أزرار تصدير أنيقة
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📊 Excel كامل", to_excel(stu), "full_report.xlsx", help="تحميل تقرير Excel كامل")
    with c2:
        st.download_button("📄 PDF كامل", to_pdf(stu, "Full Report"), "full_report.pdf", help="تحميل تقرير PDF كامل")

# -------------------- الخريطة التفاعلية --------------------
elif menu == "🗺 الخريطة":
    st.header("مواقع الطالبات")
    stu = get_students(conn)
    if stu.empty:
        st.info("لا توجد بيانات")
        st.stop()
    lat, lon = 24.7136, 46.6753
    m = folium.Map(location=[lat, lon], zoom_start=11)
    for _, r in stu.iterrows():
        if r["loc"]:
            folium.Marker(
                location=[lat, lon],
                popup=f"{r['name']} ({r['sid']})",
                tooltip=r["loc"]
            ).add_to(m)
    st.components.v1.html(m._repr_html_(), height=500)
