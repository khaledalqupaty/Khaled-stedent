# -*- coding: utf-8 -*-
"""
نظام الخالد الذكي للنقل المدرسي - الإصدار الاحترافي (Pro Edition)
النسخة الشاملة المجمعة حتى يناير 2026
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

# ─── مسار قاعدة البيانات (مهم جدًا للسحابة) ────────────────────────────────
DB_PATH = pathlib.Path("/tmp/alkhaled_pro.db")

# ─── تهيئة قاعدة البيانات مرة واحدة فقط ─────────────────────────────────────
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

    # بيانات أولية إذا كانت الجداول فارغة
    if not cur.execute("SELECT 1 FROM students LIMIT 1").fetchone():
        students_seed = [
            ("نورة فهد", "101", "0501111111", "الملقا", 24.810, 46.610, 5000, 5000, "نشط"),
            ("سارة أحمد", "102", "0502222222", "النرجس", 24.830, 46.650, 5000, 2500, "نشط"),
            ("ليان خالد", "103", "0503333333", "الياسمين", 24.820, 46.630, 5000, 0, "نشط"),
            ("ريم محمد", "104", "0504444444", "العارض", 24.850, 46.660, 5000, 5000, "نشط"),
        ]
        cur.executemany("INSERT INTO students VALUES (NULL,?,?,?,?,?,?,?,?)", students_seed)

        drivers_seed = [
            ("أبو عبدالله", "BUS-01", "0590000001", 15, "شمال الرياض"),
            ("أبو صالح", "BUS-02", "0590000002", 12, "وسط الرياض"),
        ]
        cur.executemany("INSERT INTO drivers VALUES (NULL,?,?,?,?,?)", drivers_seed)

    conn.commit()
    conn.close()
    st.session_state.db_initialized = True

# ─── دوال التعامل مع قاعدة البيانات (اتصال جديد كل مرة) ─────────────────────
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
    st.info("💡 يمكنك نسخ الموقع من Google Maps في صفحة إضافة طالبة")

# ─── 1. لوحة القيادة ────────────────────────────────────────────────────────────
if menu == "📊 لوحة القيادة":
    st.title("📊 مركز التحكم والعمليات")
    df_stu = get_df("SELECT * FROM students")
    df_drv = get_df("SELECT * FROM drivers")

    total = df_stu["fees_total"].sum() if not df_stu.empty else 0
    collected = df_stu["fees_paid"].sum() if not df_stu.empty else 0
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

            location_text = st.text_area(
                "انسخ الموقع هنا (من Google Maps)",
                placeholder="مثال:\n24.7139, 46.6753\nأو 24.7139° N, 46.6753° E",
                height=100
            )

            lat = None
            lon = None

            if location_text.strip():
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
                            if 20 < lat < 30 and 40 < lon < 55:
                                st.success(f"تم قراءة: {lat:.6f}, {lon:.6f}")
                                break
                        except:
                            continue

            if lat is None or lon is None:
                if location_text.strip():
                    st.warning("لم يتم قراءة إحداثيات → موقع تقريبي")
                lat = 24.7139 + random.uniform(-0.12, 0.12)
                lon = 46.6753 + random.uniform(-0.12, 0.12)

            submitted = st.form_submit_button("حفظ الطالبة", type="primary")

            if submitted:
                if not name or not sid:
                    st.error("الاسم ورقم الملف مطلوبان")
                else:
                    success = run_query(
                        """
                        INSERT INTO students 
                        (name, sid, phone, district, lat, lon, fees_total, fees_paid, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (name, sid, phone, dist, lat, lon, fees, 0.0, 'نشط')
                    )
                    if success:
                        st.success("تمت الإضافة")
                        st.session_state.show_add_form = False
                        st.rerun()

    # عرض الجدول + أيام الدوام
    q = "SELECT * FROM students"
    if search:
        q += f" WHERE name LIKE '%{search}%' OR sid LIKE '%{search}%'"

    df = get_df(q)

    attendance = get_df("SELECT student_id, COUNT(DISTINCT trip_date) as days_count FROM trips GROUP BY student_id")
    attendance["student_id"] = pd.to_numeric(attendance["student_id"], errors='coerce').astype('Int64')

    df = df.merge(attendance, left_on="id", right_on="student_id", how="left")
    df["أيام الدوام"] = df["days_count"].fillna(0).astype(int)
    df = df.drop(columns=["student_id", "days_count"], errors="ignore")

    df["المتبقي"] = df["fees_total"] - df["fees_paid"]
    df["نسبة السداد"] = (df["fees_paid"] / df["fees_total"].replace(0,1)).clip(0,1).map(lambda x: f"{x:.0%}")

    edited = st.data_editor(
        df,
        column_config={
            "id": None, "lat": None, "lon": None,
            "name": "الاسم", "sid": "رقم الملف", "phone": "الجوال",
            "district": "الحي",
            "fees_paid": st.column_config.NumberColumn("المدفوع", format="%d ر.س"),
            "fees_total": st.column_config.NumberColumn("الرسوم", format="%d ر.س"),
            "أيام الدوام": st.column_config.NumberColumn("أيام الدوام", disabled=True, format="%d يوم"),
            "status": st.column_config.SelectboxColumn("الحالة", options=["نشط","متوقف","خريج"]),
            "المتبقي": None, "نسبة السداد": None
        },
        hide_index=True,
        use_container_width=True,
        key="stu_editor"
    )

    # حفظ التعديلات
    if "stu_editor" in st.session_state and st.session_state.stu_editor.get("edited_rows"):
        for idx, changes in st.session_state.stu_editor["edited_rows"].items():
            student_id = df.iloc[idx]["id"]
            sets = ", ".join(f"{k}=?" for k in changes)
            vals = list(changes.values()) + [student_id]
            run_query(f"UPDATE students SET {sets} WHERE id=?", vals)
        st.toast("تم حفظ التعديلات", icon="💾")
        st.rerun()

    # تصدير
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        df.to_excel(w, index=False)
        w.sheets["Sheet1"].right_to_left = True
    st.download_button("📥 تحميل Excel", buf.getvalue(), "الطالبات.xlsx")

# ─── 3. السائقين والحافلات ─────────────────────────────────────────────────────
elif menu == "🚍 السائقين والحافلات":
    st.title("🚍 إدارة الأسطول والسائقين")

    col_form, col_list = st.columns([1, 2.5])

    with col_form:
        st.subheader("إضافة سائق / حافلة")
        with st.form("add_driver"):
            d_name  = st.text_input("اسم السائق")
            d_bus   = st.text_input("رقم الحافلة")
            d_phone = st.text_input("رقم الجوال")
            d_cap   = st.number_input("سعة الحافلة", 8, 60, 15)
            d_area  = st.selectbox("المنطقة", ["شمال الرياض","وسط الرياض","شرق الرياض","غرب الرياض","جنوب الرياض"])

            if st.form_submit_button("إضافة"):
                run_query(
                    "INSERT INTO drivers (name, bus_no, phone, capacity, route_area) VALUES (?,?,?,?,?)",
                    (d_name, d_bus, d_phone, d_cap, d_area)
                )
                st.success("تمت الإضافة")

    with col_list:
        st.subheader("قائمة السائقين")
        dfd = get_df("SELECT * FROM drivers")
        for _, r in dfd.iterrows():
            with st.expander(f"{r['name']} - {r['bus_no']}"):
                st.metric("السعة", r["capacity"])
                st.write(f"المنطقة: {r['route_area']}")
                st.write(f"جوال: {r['phone']}")

# ─── 4. الخريطة الذكية ───────────────────────────────────────────────────────────
elif menu == "📍 الخريطة الذكية":
    st.title("📍 الخريطة الذكية")
    df_map = get_df("SELECT name, district, lat, lon, fees_paid, fees_total FROM students WHERE lat IS NOT NULL AND lon IS NOT NULL")

    if df_map.empty:
        st.info("لا توجد إحداثيات لعرضها بعد")
    else:
        m = folium.Map(location=[24.7139, 46.6753], zoom_start=11, tiles="CartoDB positron")
        for _, row in df_map.iterrows():
            color = "green" if row["fees_paid"] >= row["fees_total"] else "red"
            folium.Marker(
                [row["lat"], row["lon"]],
                popup=f"<b>{row['name']}</b><br>{row['district']}",
                icon=folium.Icon(color=color, icon="user", prefix="fa")
            ).add_to(m)
        st_folium(m, width="100%", height=500)

# ─── 5. التوزيع اليومي ──────────────────────────────────────────────────────────
elif menu == "🗓️ التوزيع اليومي":
    st.title("🗓️ التوزيع اليومي")
    st.write("(أضف هنا الكود الخاص بالتوزيع اليومي إذا كنت تريد إعادته من النسخ السابقة)")

# ─── 6. الإعدادات ───────────────────────────────────────────────────────────────
elif menu == "⚙️ الإعدادات":
    st.title("⚙️ الإعدادات")
    if st.button("نسخ احتياطي"):
        with open(DB_PATH, "rb") as f:
            st.download_button("تحميل قاعدة البيانات", f, file_name=f"backup_{datetime.date.today()}.db")

st.caption("نظام الخالد برو © 2025–2026 | تم التصحيح للسحابة")