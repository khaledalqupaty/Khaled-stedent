# -*- coding: utf-8 -*-
"""
نظام الخالد الذكي للنقل المدرسي - الإصدار الاحترافي (Pro Edition)
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

# -------------------- إعدادات الصفحة --------------------
st.set_page_config(
    page_title="نظام الخالد برو",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- التصميم الاحترافي (CSS) --------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Almarai:wght@300;400;700;800&display=swap');

    :root {
        --primary-color: #2563eb;
        --secondary-color: #1e40af;
        --bg-color: #f8fafc;
        --card-bg: #ffffff;
        --text-color: #0f172a;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
    }

    /* تعيين الخط العام */
    html, body, [class*="css"] {
        font-family: 'Almarai', sans-serif;
    }

    /* خلفية التطبيق */
    .stApp {
        background-color: var(--bg-color);
    }

    /* البطاقات الإحصائية */
    .kpi-card {
        background: var(--card-bg);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border-right: 5px solid var(--primary-color);
        transition: transform 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
    }
    .kpi-title {
        color: #64748b;
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .kpi-value {
        color: var(--text-color);
        font-size: 1.8rem;
        font-weight: 800;
    }

    /* تخصيص الجداول */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
    }

    /* تخصيص القائمة الجانبية */
    [data-testid="stSidebar"] {
        background-color: #1e293b;
    }
    [data-testid="stSidebar"] * {
        color: #f1f5f9 !important;
    }
    
    /* أزرار الحالة */
    .status-badge {
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 700;
    }
    .status-paid { background-color: #d1fae5; color: #065f46; }
    .status-pending { background-color: #fee2e2; color: #991b1b; }
    .status-waiting { background-color: #fef3c7; color: #92400e; }

</style>
""", unsafe_allow_html=True)

# -------------------- إدارة قاعدة البيانات --------------------
@st.cache_resource
def get_connection():
    # إنشاء اتصال بقاعدة البيانات
    db_path = pathlib.Path("alkhaled_pro.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    
    # إنشاء الجداول إذا لم تكن موجودة
    cursor = conn.cursor()
    
    # جدول الطالبات (تم إضافة إحداثيات ورسوم)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sid TEXT UNIQUE,
            phone TEXT,
            district TEXT,
            lat REAL,
            lon REAL,
            fees_total REAL DEFAULT 5000,
            fees_paid REAL DEFAULT 0,
            status TEXT DEFAULT 'نشط'
        )
    """)
    
    # جدول السائقين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            bus_no TEXT,
            phone TEXT,
            capacity INTEGER,
            route_area TEXT
        )
    """)
    
    # جدول التوزيع اليومي
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            trip_date TEXT,
            driver_id INTEGER,
            student_id INTEGER,
            trip_type TEXT DEFAULT 'go',
            PRIMARY KEY(trip_date, driver_id, student_id, trip_type)
        )
    """)
    
    # بيانات تجريبية أولية (Seed Data)
    if not cursor.execute("SELECT 1 FROM students").fetchone():
        students_data = [
            ("نورة فهد", "101", "0501111111", "الملقا", 24.810, 46.610, 5000, 5000, "نشط"),
            ("سارة أحمد", "102", "0502222222", "النرجس", 24.830, 46.650, 5000, 2500, "نشط"),
            ("ليان خالد", "103", "0503333333", "الياسمين", 24.820, 46.630, 5000, 0, "نشط"),
            ("ريم محمد", "104", "0504444444", "العارض", 24.850, 46.660, 5000, 5000, "نشط"),
        ]
        cursor.executemany("INSERT INTO students (name, sid, phone, district, lat, lon, fees_total, fees_paid, status) VALUES (?,?,?,?,?,?,?,?,?)", students_data)
        
        drivers_data = [
            ("أبو عبدالله", "BUS-01", "0590000001", 15, "شمال الرياض"),
            ("أبو صالح", "BUS-02", "0590000002", 12, "وسط الرياض"),
        ]
        cursor.executemany("INSERT INTO drivers (name, bus_no, phone, capacity, route_area) VALUES (?,?,?,?,?)", drivers_data)
        
    conn.commit()
    return conn

conn = get_connection()

# -------------------- دوال مساعدة (Business Logic) --------------------
def get_df(query, params=None):
    return pd.read_sql(query, conn, params=params)

def execute_query(query, params):
    try:
        with conn:
            conn.execute(query, params)
        st.cache_data.clear() # مسح الكاش لتحديث البيانات
        return True
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
        return False

# -------------------- القائمة الجانبية الاحترافية --------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063823.png", width=80)
    st.markdown("### 🚌 الخالد للنقل")
    st.markdown("---")
    
    menu = st.radio(
        "القائمة الرئيسية",
        ["📊 لوحة القيادة", "👩‍🎓 الطالبات والرسوم", "🚍 السائقين والحافلات", "📍 الخريطة الذكية", "⚙️ الإعدادات"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.info("💡 نصيحة: يمكنك تحميل بيانات الطالبات كملف Excel من صفحة الطالبات.")

# -------------------- 1. لوحة القيادة (Dashboard) --------------------
if menu == "📊 لوحة القيادة":
    st.title("📊 مركز التحكم والعمليات")
    st.markdown("نظرة عامة على سير العمل والأداء المالي")
    
    # إحصائيات علوية
    df_stu = get_df("SELECT * FROM students")
    df_drv = get_df("SELECT * FROM drivers")
    
    total_fees = df_stu['fees_total'].sum()
    collected_fees = df_stu['fees_paid'].sum()
    pending_fees = total_fees - collected_fees
    collection_rate = (collected_fees / total_fees * 100) if total_fees > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">عدد الطالبات</div>
            <div class="kpi-value">{len(df_stu)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="kpi-card" style="border-color: var(--success);">
            <div class="kpi-title">إجمالي التحصيلات</div>
            <div class="kpi-value">{collected_fees:,.0f} ريال</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card" style="border-color: var(--warning);">
            <div class="kpi-title">المبالغ المتبقية</div>
            <div class="kpi-value">{pending_fees:,.0f} ريال</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div class="kpi-card" style="border-color: var(--secondary-color);">
            <div class="kpi-title">أسطول الحافلات</div>
            <div class="kpi-value">{len(df_drv)}</div>
        </div>
        """, unsafe_allow_html=True)

    # الرسوم البيانية
    st.markdown("### 📈 التحليل المالي والتشغيلي")
    c1, c2 = st.columns([2, 1])
    
    with c1:
        # رسم بياني لتوزيع الطالبات حسب الحي
        chart_data = df_stu.groupby('district').size().reset_index(name='count')
        bar_chart = alt.Chart(chart_data).mark_bar(cornerRadiusTopLeft=10, cornerRadiusTopRight=10).encode(
            x=alt.X('district', sort='-y', title='الحي'),
            y=alt.Y('count', title='عدد الطالبات'),
            color=alt.Color('district', legend=None),
            tooltip=['district', 'count']
        ).properties(height=300, title="توزيع الطالبات حسب الأحياء")
        st.altair_chart(bar_chart, use_container_width=True)
        
    with c2:
        # رسم بياني دائري لحالة الدفع
        # تصنيف البيانات
        paid_full = len(df_stu[df_stu['fees_paid'] >= df_stu['fees_total']])
        partial = len(df_stu[(df_stu['fees_paid'] > 0) & (df_stu['fees_paid'] < df_stu['fees_total'])])
        unpaid = len(df_stu[df_stu['fees_paid'] == 0])
        
        pie_data = pd.DataFrame({
            'Category': ['مدفوع بالكامل', 'جزئي', 'غير مدفوع'],
            'Value': [paid_full, partial, unpaid]
        })
        
        pie_chart = alt.Chart(pie_data).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Value", type="quantitative"),
            color=alt.Color(field="Category", type="nominal", scale=alt.Scale(domain=['مدفوع بالكامل', 'جزئي', 'غير مدفوع'], range=['#10b981', '#f59e0b', '#ef4444'])),
            tooltip=['Category', 'Value']
        ).properties(height=300, title="حالة الرسوم الدراسية")
        st.altair_chart(pie_chart, use_container_width=True)

# -------------------- 2. الطالبات والرسوم --------------------
elif menu == "👩‍🎓 الطالبات والرسوم":
    st.title("👩‍🎓 إدارة الطالبات والرسوم")
    
    # شريط أدوات علوي
    tc1, tc2 = st.columns([3, 1])
    with tc1:
        search_term = st.text_input("🔍 بحث عن طالبة (الاسم أو الهوية)", placeholder="اكتب للبحث...")
    with tc2:
        st.write("") # Spacer
        st.write("")
        add_btn = st.button("➕ إضافة طالبة جديدة", type="primary")

    # نموذج إضافة طالبة
    if add_btn:
        with st.form("new_student_form"):
            st.write("بيانات الطالبة الجديدة")
            c1, c2, c3 = st.columns(3)
            n_name = c1.text_input("الاسم الرباعي")
            n_sid = c2.text_input("رقم الهوية/الطالب")
            n_phone = c3.text_input("رقم الجوال")
            
            c4, c5 = st.columns(2)
            n_district = c4.text_input("الحي السكني")
            n_fees = c5.number_input("الرسوم السنوية", value=5000)
            
            submitted = st.form_submit_button("حفظ البيانات")
            if submitted and n_name:
                # محاكاة احداثيات عشوائية حول الرياض للإضافة السريعة
                lat = 24.7136 + (random.random() - 0.5) * 0.2
                lon = 46.6753 + (random.random() - 0.5) * 0.2
                
                success = execute_query(
                    "INSERT INTO students (name, sid, phone, district, lat, lon, fees_total) VALUES (?,?,?,?,?,?,?)",
                    (n_name, n_sid, n_phone, n_district, lat, lon, n_fees)
                )
                if success: st.toast("تمت إضافة الطالبة بنجاح", icon="✅")

    # عرض الجدول القابل للتعديل
    query = "SELECT * FROM students"
    if search_term:
        query += f" WHERE name LIKE '%{search_term}%' OR sid LIKE '%{search_term}%'"
    
    df = get_df(query)
    
    # تنسيق العرض: حساب المتبقي ونسبة السداد
    df['المتبقي'] = df['fees_total'] - df['fees_paid']
    df['نسبة السداد'] = (df['fees_paid'] / df['fees_total']).apply(lambda x: f"{x:.0%}")
    
    # واجهة التعديل
    edited_df = st.data_editor(
        df,
        column_config={
            "id": None, # إخفاء
            "lat": None,
            "lon": None,
            "name": "اسم الطالبة",
            "sid": "رقم الملف",
            "fees_paid": st.column_config.ProgressColumn("المدفوع", min_value=0, max_value=5000, format="%f ريال"),
            "fees_total": st.column_config.NumberColumn("الرسوم", format="%d ريال"),
            "status": st.column_config.SelectboxColumn("الحالة", options=["نشط", "متوقف", "خريج"]),
        },
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
        key="student_editor"
    )

    # حفظ التعديلات
    if not df.equals(edited_df):
        # هنا يتم حفظ التغييرات (مثال مبسط، في التطبيق الفعلي يجب مقارنة الصفوف)
        # لإغراض التبسيط سنقوم بتحديث كامل للقيم المعدلة بناء على الـ ID
        for index, row in edited_df.iterrows():
            conn.execute("""
                UPDATE students SET name=?, phone=?, district=?, fees_paid=?, status=? WHERE id=?
            """, (row['name'], row['phone'], row['district'], row['fees_paid'], row['status'], row['id']))
        conn.commit()
        st.toast("تم حفظ التعديلات بنجاح", icon="💾")

    # تصدير البيانات
    st.markdown("### 📥 تصدير")
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        edited_df.to_excel(writer, sheet_name='Students', index=False)
        # تنسيق الاتجاه من اليمين لليسار في اكسل
        workbook = writer.book
        worksheet = writer.sheets['Students']
        worksheet.right_to_left()
        
    st.download_button(
        label="تحميل ملف Excel",
        data=excel_buffer.getvalue(),
        file_name="students_report.xlsx",
        mime="application/vnd.ms-excel",
        help="تصدير القائمة كاملة بتنسيق متوافق مع اللغة العربية"
    )

# -------------------- 3. السائقين والحافلات --------------------
elif menu == "🚍 السائقين والحافلات":
    st.title("🚍 إدارة الأسطول")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### إضافة سائق / حافلة")
        with st.form("add_driver"):
            d_name = st.text_input("اسم السائق")
            d_bus = st.text_input("رقم اللوحة/الباص")
            d_cap = st.number_input("سعة الركاب", 10, 50, 15)
            d_phone = st.text_input("رقم التواصل")
            d_area = st.selectbox("منطقة المسار", ["شمال الرياض", "شرق الرياض", "غرب الرياض", "جنوب الرياض", "وسط الرياض"])
            
            if st.form_submit_button("إضافة"):
                execute_query("INSERT INTO drivers (name, bus_no, phone, capacity, route_area) VALUES (?,?,?,?,?)",
                              (d_name, d_bus, d_phone, d_cap, d_area))
                st.success("تمت الإضافة")

    with col2:
        st.markdown("#### قائمة السائقين")
        drivers = get_df("SELECT * FROM drivers")
        
        for _, d in drivers.iterrows():
            with st.expander(f"🚌 {d['name']} | {d['bus_no']}"):
                c1, c2, c3 = st.columns(3)
                c1.metric("السعة", d['capacity'])
                c2.metric("المنطقة", d['route_area'])
                c3.write(f"📞 {d['phone']}")
                
                # عرض توزيع اليوم (محاكاة)
                st.info(f"عدد الطالبات المسجلات لهذا الباص: {random.randint(5, d['capacity'])}")

# -------------------- 4. الخريطة الذكية --------------------
elif menu == "📍 الخريطة الذكية":
    st.title("📍 التوزيع الجغرافي للطالبات")
    
    df_map = get_df("SELECT name, district, lat, lon, fees_paid, fees_total FROM students")
    
    # خريطة تفاعلية
    m = folium.Map(location=[24.7136, 46.6753], zoom_start=11, tiles="Cartodb Positron")
    
    for _, row in df_map.iterrows():
        # تحديد لون الايقونة بناء على الدفع
        color = "green" if row['fees_paid'] >= row['fees_total'] else "red"
        
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=folium.Popup(f"<b>{row['name']}</b><br>الحي: {row['district']}<br>المدفوع: {row['fees_paid']}", max_width=200),
            icon=folium.Icon(color=color, icon="user", prefix="fa")
        ).add_to(m)
    
    st_folium(m, width="100%", height=500)
    
    st.caption("🟢 الأخضر: تم السداد بالكامل | 🔴 الأحمر: توجد مبالغ مستحقة")

# -------------------- 5. الإعدادات --------------------
elif menu == "⚙️ الإعدادات":
    st.title("⚙️ إعدادات النظام")
    
    st.subheader("النسخ الاحتياطي")
    if st.button("💾 إنشاء نسخة احتياطية من قاعدة البيانات"):
        with open("alkhaled_pro.db", "rb") as f:
            st.download_button("تحميل ملف DB", f, file_name=f"backup_{datetime.date.today()}.db")
            
    st.subheader("إعدادات عامة")
    st.checkbox("تفعيل الوضع الليلي التلقائي", value=True)
    st.checkbox("إرسال تنبيهات SMS عند تأخر الدفع")

