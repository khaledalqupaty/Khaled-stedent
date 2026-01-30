# -*- coding: utf-8 -*-
"""
نظام الخالد الذكي للنقل المدرسي - الإصدار الاحترافي (Pro Edition)
مع إضافة التوزيع اليومي - النسخة المجمعة والمصححة
"""
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
        --primary: #2563eb;
        --secondary: #1e40af;
        --bg: #f8fafc;
        --card: #ffffff;
        --text: #0f172a;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
    }

    html, body, [class*="css"] { font-family: 'Almarai', sans-serif; }
    .stApp { background-color: var(--bg); }

    .kpi-card {
        background: var(--card);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        border-right: 5px solid var(--primary);
        transition: transform 0.2s;
    }
    .kpi-card:hover { transform: translateY(-5px); }

    .kpi-title { color: #64748b; font-size: 0.9rem; font-weight: 700; margin-bottom: 5px; }
    .kpi-value { color: var(--text); font-size: 1.8rem; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# ─── قاعدة البيانات ────────────────────────────────────────────────────────────
@st.cache_resource
def get_connection():
    db_path = pathlib.Path("alkhaled_pro.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
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

    # بيانات تجريبية أولية
    if not cur.execute("SELECT 1 FROM students LIMIT 1").fetchone():
        students_seed = [
            ("نورة فهد", "101", "0501111111", "الملقا",   24.810, 46.610, 5000, 5000, "نشط"),
            ("سارة أحمد", "102", "0502222222", "النرجس",  24.830, 46.650, 5000, 2500, "نشط"),
            ("ليان خالد", "103", "0503333333", "الياسمين",24.820, 46.630, 5000,    0, "نشط"),
            ("ريم محمد", "104", "0504444444", "العارض",   24.850, 46.660, 5000, 5000, "نشط"),
        ]
        cur.executemany("INSERT INTO students VALUES (NULL,?,?,?,?,?,?,?,?)", students_seed)

        drivers_seed = [
            ("أبو عبدالله", "BUS-01", "0590000001", 15, "شمال الرياض"),
            ("أبو صالح",    "BUS-02", "0590000002", 12, "وسط الرياض"),
        ]
        cur.executemany("INSERT INTO drivers VALUES (NULL,?,?,?,?,?)", drivers_seed)

    conn.commit()
    return conn

conn = get_connection()

# ─── دوال مساعدة ────────────────────────────────────────────────────────────────
def run_query(query, params=None):
    try:
        with conn:
            if params:
                conn.execute(query, params)
            else:
                conn.execute(query)
        st.cache_data.clear()
        return True
    except sqlite3.IntegrityError:
        st.error("خطأ: قيمة مكررة (رقم الملف / رقم الباص)")
        return False
    except Exception as e:
        st.error(f"خطأ في قاعدة البيانات: {e}")
        return False

def get_df(query, params=None):
    return pd.read_sql_query(query, conn, params=params)

# ─── القائمة الجانبية ──────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063823.png", width=80)
    st.markdown("### 🚌 الخالد للنقل")
    st.markdown("---")

    menu = st.radio(
        "القائمة الرئيسية",
        [
            "📊 لوحة القيادة",
            "👩‍🎓 الطالبات والرسوم",
            "🚍 السائقين والحافلات",
            "📍 الخريطة الذكية",
            "🗓️ التوزيع اليومي",
            "⚙️ الإعدادات"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.info("💡 نصيحة: يمكنك تصدير البيانات كـ Excel من صفحة الطالبات")

# ─── 1. لوحة القيادة ────────────────────────────────────────────────────────────
if menu == "📊 لوحة القيادة":
    st.title("📊 مركز التحكم والعمليات")

    df_stu = get_df("SELECT * FROM students")
    df_drv = get_df("SELECT * FROM drivers")

    total_fees    = df_stu["fees_total"].sum()
    collected     = df_stu["fees_paid"].sum()
    pending       = total_fees - collected
    collection_pct = (collected / total_fees * 100) if total_fees > 0 else 0

    cols = st.columns(4)
    cols[0].markdown(f'<div class="kpi-card"><div class="kpi-title">عدد الطالبات</div><div class="kpi-value">{len(df_stu)}</div></div>', unsafe_allow_html=True)
    cols[1].markdown(f'<div class="kpi-card" style="border-color:var(--success)"><div class="kpi-title">إجمالي التحصيل</div><div class="kpi-value">{collected:,.0f} ر.س</div></div>', unsafe_allow_html=True)
    cols[2].markdown(f'<div class="kpi-card" style="border-color:var(--warning)"><div class="kpi-title">المتبقي</div><div class="kpi-value">{pending:,.0f} ر.س</div></div>', unsafe_allow_html=True)
    cols[3].markdown(f'<div class="kpi-card" style="border-color:var(--secondary)"><div class="kpi-title">عدد الحافلات</div><div class="kpi-value">{len(df_drv)}</div></div>', unsafe_allow_html=True)

    st.markdown("### توزيع الطالبات حسب الحي")
    chart_data = df_stu.groupby("district").size().reset_index(name="count")
    bar = alt.Chart(chart_data).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(
        x=alt.X("district", sort="-y"),
        y="count",
        color="district",
        tooltip=["district", "count"]
    ).properties(height=320)
    st.altair_chart(bar, use_container_width=True)

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

            if st.form_submit_button("حفظ"):
                if not name or not sid:
                    st.error("الاسم ورقم الملف مطلوبان")
                else:
                    lat = 24.7136 + random.uniform(-0.18, 0.18)
                    lon = 46.6753 + random.uniform(-0.18, 0.18)
                    if run_query(
                        "INSERT INTO students (name,sid,phone,district,lat,lon,fees_total) VALUES (?,?,?,?,?,?,?)",
                        (name, sid, phone, dist, lat, lon, fees)
                    ):
                        st.success("تمت الإضافة")
                        st.session_state.show_add_form = False
                        st.rerun()

    q = "SELECT * FROM students"
    if search:
        q += f" WHERE name LIKE '%{search}%' OR sid LIKE '%{search}%'"

    df = get_df(q)
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
            "status": st.column_config.SelectboxColumn("الحالة", options=["نشط","متوقف","خريج"]),
            "المتبقي": None, "نسبة السداد": None
        },
        hide_index=True,
        use_container_width=True,
        key="stu_editor"
    )

    if "stu_editor" in st.session_state and st.session_state.stu_editor["edited_rows"]:
        for idx, changes in st.session_state.stu_editor["edited_rows"].items():
            sid = df.iloc[idx]["id"]
            sets = ", ".join(f"{k}=?" for k in changes)
            vals = list(changes.values()) + [sid]
            run_query(f"UPDATE students SET {sets} WHERE id=?", vals)
        st.toast("تم الحفظ", icon="💾")
        st.rerun()

    # تصدير
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        df.to_excel(w, index=False)
        w.sheets["Sheet1"].right_to_left = True
    st.download_button("📥 Excel", buf.getvalue(), "الطالبات.xlsx")

# ─── 3. السائقين والحافلات ─────────────────────────────────────────────────────
elif menu == "🚍 السائقين والحافلات":
    st.title("🚍 إدارة الأسطول")

    col1, col2 = st.columns([1,2])

    with col1:
        with st.form("add_driver"):
            st.subheader("إضافة سائق / حافلة")
            dname = st.text_input("اسم السائق")
            bus   = st.text_input("رقم اللوحة")
            cap   = st.number_input("السعة", 8, 60, 15)
            phone = st.text_input("رقم الجوال")
            area  = st.selectbox("المنطقة", ["شمال الرياض","وسط الرياض","شرق الرياض","غرب الرياض","جنوب الرياض"])

            if st.form_submit_button("إضافة"):
                run_query("INSERT INTO drivers (name,bus_no,phone,capacity,route_area) VALUES (?,?,?,?,?)",
                          (dname, bus, phone, cap, area))
                st.success("تمت الإضافة")

    with col2:
        st.subheader("قائمة السائقين")
        dfd = get_df("SELECT * FROM drivers")
        for _, r in dfd.iterrows():
            with st.expander(f"🚌 {r['name']}  •  {r['bus_no']}"):
                c1,c2,c3 = st.columns(3)
                c1.metric("السعة", r["capacity"])
                c2.metric("المنطقة", r["route_area"])
                c3.write(f"📞 {r['phone']}")

# ─── 4. الخريطة الذكية ───────────────────────────────────────────────────────────
elif menu == "📍 الخريطة الذكية":
    st.title("📍 التوزيع الجغرافي")

    dfm = get_df("SELECT name, district, lat, lon, fees_paid, fees_total FROM students")

    m = folium.Map(location=[24.7136, 46.6753], zoom_start=11, tiles="CartoDB positron")

    for _, row in dfm.iterrows():
        color = "green" if row["fees_paid"] >= row["fees_total"] else "red"
        folium.Marker(
            [row["lat"], row["lon"]],
            popup=f"<b>{row['name']}</b><br>{row['district']}<br>مدفوع: {row['fees_paid']}",
            icon=folium.Icon(color=color, icon="user", prefix="fa")
        ).add_to(m)

    st_folium(m, width="100%", height=520)
    st.caption("🟢 مدفوع كامل  •  🔴 باقي مستحقات")

# ─── 5. التوزيع اليومي ──────────────────────────────────────────────────────────
elif menu == "🗓️ التوزيع اليومي":
    st.title("🗓️ التوزيع اليومي للطالبات")

    sel_date = st.date_input("التاريخ", datetime.date.today())
    date_str = sel_date.strftime("%Y-%m-%d")

    students = get_df("SELECT id, name, sid, district FROM students WHERE status='نشط'")
    drivers  = get_df("SELECT id, name, bus_no, capacity, route_area FROM drivers")

    if students.empty or drivers.empty:
        st.warning("تحتاج طالبات نشطات وسائقين مسجلين لعرض التوزيع")
    else:
        # التوزيع الحالي
        st.subheader(f"التوزيع في {date_str}")
        curr = get_df("""
            SELECT d.name, d.bus_no, COUNT(t.student_id) cnt,
                   GROUP_CONCAT(s.name, '، ') students
            FROM trips t
            JOIN drivers d ON t.driver_id = d.id
            JOIN students s ON t.student_id = s.id
            WHERE t.trip_date = ? AND t.trip_type='go'
            GROUP BY t.driver_id
        """, (date_str,))

        if not curr.empty:
            for _, r in curr.iterrows():
                with st.expander(f"{r['name']} • {r['bus_no']}  ({r['cnt']} طالبة)"):
                    st.write(r["students"] or "—")
        else:
            st.info("لا يوجد توزيع بعد لهذا اليوم")

        # نموذج التوزيع
        st.subheader("إضافة توزيع جديد")

        assigned = get_df("SELECT student_id FROM trips WHERE trip_date=? AND trip_type='go'",
                          (date_str,))["student_id"].tolist()

        avail = students[~students["id"].isin(assigned)]

        with st.form("assign_form"):
            col_d, col_s = st.columns([1,3])

            with col_d:
                drv_dict = {f"{r['name']} • {r['bus_no']} (سعة {r['capacity']})": r["id"] for _,r in drivers.iterrows()}
                sel_drv = st.selectbox("اختر السائق", options=list(drv_dict.keys()), index=None)

            with col_s:
                if sel_drv:
                    drv_id = drv_dict[sel_drv]
                    curr_cnt = get_df("SELECT COUNT(*) c FROM trips WHERE trip_date=? AND driver_id=?",
                                      (date_str, drv_id)).iloc[0]["c"]
                    remain = drivers[drivers["id"]==drv_id]["capacity"].iloc[0] - curr_cnt

                    sel_stu = st.multiselect(
                        f"اختر الطالبات  (متبقي {remain} مقعد)",
                        options=avail["name"].tolist(),
                        max_selections=max(0, remain)
                    )

            if st.form_submit_button("توزيع المختارات", type="primary"):
                if not sel_drv:
                    st.error("اختر سائقاً")
                elif not sel_stu:
                    st.warning("اختر طالبة واحدة على الأقل")
                else:
                    cnt = 0
                    for nm in sel_stu:
                        sid = avail[avail["name"]==nm]["id"].iloc[0]
                        if not conn.execute(
                            "SELECT 1 FROM trips WHERE trip_date=? AND driver_id=? AND student_id=?",
                            (date_str, drv_id, sid)
                        ).fetchone():
                            run_query(
                                "INSERT INTO trips (trip_date, driver_id, student_id, trip_type) VALUES (?,?,?,?)",
                                (date_str, drv_id, sid, "go")
                            )
                            cnt += 1
                    if cnt:
                        st.success(f"تم توزيع {cnt} طالبة")
                        st.rerun()
                    else:
                        st.info("جميعهن موزعات مسبقاً")

# ─── 6. الإعدادات ───────────────────────────────────────────────────────────────
elif menu == "⚙️ الإعدادات":
    st.title("⚙️ الإعدادات")

    if st.button("📦 نسخة احتياطية"):
        with open("alkhaled_pro.db", "rb") as f:
            st.download_button(
                "تحميل قاعدة البيانات",
                f,
                file_name=f"backup_{datetime.date.today()}.db"
            )

    st.checkbox("تفعيل الوضع الليلي التلقائي", value=True)
    st.checkbox("إرسال تنبيهات SMS للتأخير في الدفع", value=False)

st.caption("الخالد برو © 2025–2026")