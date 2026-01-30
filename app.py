# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import sqlite3
import datetime
import io
import random
import altair as alt
import folium
from streamlit_folium import st_folium

# --- الإعدادات الأساسية ---
st.set_page_config(page_title="الخالد للنقل الذكي", page_icon="🚌", layout="wide")

# --- التصميم الاحترافي CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Almarai:wght@400;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Almarai', sans-serif;
        direction: rtl;
        text-align: right;
    }
    
    .main { background-color: #f8fafc; }
    
    /* كروت الإحصائيات */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-right: 6px solid #2563eb;
        margin-bottom: 10px;
    }
    
    .metric-title { color: #64748b; font-size: 0.9rem; font-weight: bold; }
    .metric-value { color: #1e293b; font-size: 1.7rem; font-weight: 800; }

    /* تحسين القائمة الجانبية */
    section[data-testid="stSidebar"] { background-color: #0f172a !important; }
    section[data-testid="stSidebar"] * { color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- إدارة قاعدة البيانات ---
@st.cache_resource
def get_db():
    conn = sqlite3.connect("alkhaled_pro_final.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, sid TEXT, phone TEXT, district TEXT,
            fees_total REAL DEFAULT 5000, fees_paid REAL DEFAULT 0, status TEXT DEFAULT 'نشط'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, bus_no TEXT, phone TEXT, capacity INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            date TEXT, driver_id INTEGER, student_id INTEGER,
            PRIMARY KEY(date, driver_id, student_id)
        )
    """)
    conn.commit()
    return conn

conn = get_db()

# --- القائمة الجانبية ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center;'>🚌 الخالد PRO</h1>", unsafe_allow_html=True)
    st.markdown("---")
    menu = st.radio("انتقل إلى:", 
                   ["📊 لوحة التحكم", "📅 التوزيع اليومي", "👩‍🎓 إدارة الطالبات", "🚍 إدارة السائقين", "📍 الخريطة الذكية"])

# --- 1. لوحة التحكم ---
if menu == "📊 لوحة التحكم":
    st.title("📊 نظام الرقابة والعمليات")
    
    df_stu = pd.read_sql("SELECT * FROM students", conn)
    df_drv = pd.read_sql("SELECT * FROM drivers", conn)
    
    # صف المؤشرات
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="metric-card"><div class="metric-title">إجمالي الطالبات</div><div class="metric-value">{}</div></div>'.format(len(df_stu)), unsafe_allow_html=True)
    with c2:
        paid = df_stu['fees_paid'].sum() if not df_stu.empty else 0
        st.markdown('<div class="metric-card" style="border-color:#10b981"><div class="metric-title">التحصيلات المالية</div><div class="metric-value">{} ريال</div></div>'.format(int(paid)), unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="metric-card" style="border-color:#f59e0b"><div class="metric-title">عدد الحافلات</div><div class="metric-value">{}</div></div>'.format(len(df_drv)), unsafe_allow_html=True)
    with c4:
        active = pd.read_sql("SELECT COUNT(DISTINCT student_id) as count FROM trips WHERE date = ?", conn, params=(datetime.date.today().isoformat(),))
        st.markdown('<div class="metric-card" style="border-color:#6366f1"><div class="metric-title">الحضور اليوم</div><div class="metric-value">{}</div></div>'.format(active.iloc[0]['count']), unsafe_allow_html=True)

    st.markdown("---")
    # رسوم بيانية
    if not df_stu.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            chart = alt.Chart(df_stu).mark_bar(cornerRadiusTopLeft=10, cornerRadiusTopRight=10, color='#2563eb').encode(
                x=alt.X('district:N', title='الحي'),
                y=alt.Y('count():Q', title='عدد الطالبات')
            ).properties(title="توزيع الطالبات حسب الأحياء", height=300)
            st.altair_chart(chart, use_container_width=True)
        with col_b:
            # حالة الرسوم
            df_stu['payment_status'] = df_stu.apply(lambda x: 'خالص' if x['fees_paid'] >= x['fees_total'] else 'متبقي', axis=1)
            pie = alt.Chart(df_stu).mark_arc(innerRadius=50).encode(
                theta="count():Q", color=alt.Color("payment_status:N", scale=alt.Scale(range=['#10b981', '#ef4444']))
            ).properties(title="نسبة سداد الرسوم")
            st.altair_chart(pie, use_container_width=True)

# --- 2. التوزيع اليومي (الميزة المطلوبة) ---
elif menu == "📅 التوزيع اليومي":
    st.title("📅 التوزيع اليومي وتسجيل الحضور")
    sel_date = st.date_input("تاريخ اليوم", datetime.date.today())
    date_str = sel_date.isoformat()
    
    drv_df = pd.read_sql("SELECT * FROM drivers", conn)
    stu_df = pd.read_sql("SELECT id, name FROM students WHERE status='نشط'", conn)
    
    if drv_df.empty:
        st.warning("يرجى إضافة سائقين أولاً.")
    else:
        # عرض السائقين في شبكة
        cols = st.columns(2)
        for i, drv in drv_df.iterrows():
            with cols[i % 2]:
                with st.container(border=True):
                    st.subheader(f"🚍 {drv['name']}")
                    st.caption(f"الباص: {drv['bus_no']} | السعة: {drv['capacity']}")
                    
                    # الطلاب المسجلين حالياً
                    curr_ids = pd.read_sql("SELECT student_id FROM trips WHERE date=? AND driver_id=?", 
                                         conn, params=(date_str, drv['id']))['student_id'].tolist()
                    
                    selected = st.multiselect(f"تحديد الطالبات ({drv['name']})", 
                                             options=stu_df['id'].tolist(),
                                             format_func=lambda x: stu_df[stu_df['id']==x]['name'].values[0],
                                             default=curr_ids, key=f"sel_{drv['id']}")
                    
                    if st.button("تحديث التوزيع", key=f"btn_{drv['id']}"):
                        with conn:
                            conn.execute("DELETE FROM trips WHERE date=? AND driver_id=?", (date_str, drv['id']))
                            for sid in selected:
                                conn.execute("INSERT INTO trips (date, driver_id, student_id) VALUES (?,?,?)", (date_str, drv['id'], sid))
                        st.success(f"تم تحديث باص {drv['name']}")

# --- 3. إدارة الطالبات ---
elif menu == "👩‍🎓 إدارة الطالبات":
    st.title("👩‍🎓 سجل الطالبات")
    
    with st.expander("➕ إضافة طالبة جديدة"):
        with st.form("stu_form"):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("الاسم الرباعي")
            sid = c2.text_input("رقم الهوية")
            dist = c3.text_input("الحي")
            if st.form_submit_button("حفظ الطالبة"):
                conn.execute("INSERT INTO students (name, sid, district) VALUES (?,?,?)", (name, sid, dist))
                conn.commit()
                st.rerun()

    # الاستعلام المطور لحساب أيام الحضور
    df = pd.read_sql("""
        SELECT s.id, s.name, s.sid, s.district, s.fees_total, s.fees_paid, s.status,
        (SELECT COUNT(*) FROM trips t WHERE t.student_id = s.id) as days
        FROM students s
    """, conn)
    
    edited = st.data_editor(df, column_config={
        "id": None,
        "days": st.column_config.NumberColumn("أيام الدوام", format="%d يوم"),
        "fees_paid": st.column_config.ProgressColumn("السداد", min_value=0, max_value=5000),
        "status": st.column_config.SelectboxColumn("الحالة", options=["نشط", "موقف"])
    }, use_container_width=True, hide_index=True)
    
    if st.button("حفظ التعديلات"):
        for _, r in edited.iterrows():
            conn.execute("UPDATE students SET name=?, fees_paid=?, status=? WHERE id=?", (r['name'], r['fees_paid'], r['status'], r['id']))
        conn.commit()
        st.toast("تم الحفظ")

# --- 4. إدارة السائقين (تعديل مباشر) ---
elif menu == "🚍 إدارة السائقين":
    st.title("🚍 سجل السائقين والحافلات")
    
    with st.expander("➕ إضافة سائق جديد"):
        with st.form("drv_form"):
            c1, c2, c3 = st.columns(3)
            dn = c1.text_input("اسم السائق")
            db = c2.text_input("لوحة الباص")
            dc = c3.number_input("السعة", value=15)
            if st.form_submit_button("إضافة"):
                conn.execute("INSERT INTO drivers (name, bus_no, capacity) VALUES (?,?,?)", (dn, db, dc))
                conn.commit()
                st.rerun()

    df_drv = pd.read_sql("SELECT * FROM drivers", conn)
    edited_drv = st.data_editor(df_drv, use_container_width=True, hide_index=True, key="drv_edit")
    
    if st.button("تحديث بيانات السائقين"):
        for _, r in edited_drv.iterrows():
            conn.execute("UPDATE drivers SET name=?, bus_no=?, capacity=? WHERE id=?", (r['name'], r['bus_no'], r['capacity'], r['id']))
        conn.commit()
        st.toast("تم التحديث")

# --- 5. الخريطة ---
elif menu == "📍 الخريطة الذكية":
    st.title("📍 خريطة المواقع")
    # محاكاة خريطة (تحتاج لإحداثيات حقيقية لتعمل بدقة)
    m = folium.Map(location=[24.7136, 46.6753], zoom_start=11)
    st_folium(m, width="100%", height=500)
