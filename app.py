import streamlit as st
import pandas as pd
import urllib.parse

# ==========================
# إعداد البيانات التجريبية
# ==========================
if 'students_db' not in st.session_state:
    st.session_state.students_db = pd.DataFrame([
        {"الاسم": "نورة", "الموقع": "حي الروضة", "حالة الدفع": "انتظار", "رقم التواصل": "050xxx"},
        {"الاسم": "سارة", "الموقع": "حي الملقا", "حالة الدفع": "تم الدفع", "رقم التواصل": "055xxx"}
    ])

if 'buses_db' not in st.session_state:
    st.session_state.buses_db = pd.DataFrame([
        {"اسم السائق": "أحمد", "رقم الجوال": "059xxx"},
        {"اسم السائق": "محمد", "رقم الجوال": "058xxx"}
    ])

if 'assignments' not in st.session_state:
    st.session_state.assignments = {}

# ==========================
# إعداد الصفحة
# ==========================
st.set_page_config(
    page_title="Bus Management Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* تحسين الخطوط والألوان */
body { font-family: 'Arial', sans-serif; }
h1 { color: #2F4F4F; }
.stButton>button { background-color: #4CAF50; color: white; border-radius: 8px; }
.stButton>button:hover { background-color: #45a049; }
</style>
""", unsafe_allow_html=True)

st.title("🚍 تطبيق إدارة الباصات")
st.markdown("إدارة الطالبات، السائقين والتوزيع اليومي بسهولة من الهاتف")

# ==========================
# القائمة الجانبية
# ==========================
with st.sidebar:
    st.header("🗂 القائمة الرئيسية")
    page = st.radio("اختر الصفحة:", ["🏠 الصفحة الرئيسية", "⚙️ لوحة التحكم"])

# ==========================
# الصفحة الرئيسية
# ==========================
if page == "🏠 الصفحة الرئيسية":
    st.subheader("📋 جدول الطالبات")
    edited_df = st.data_editor(
        st.session_state.students_db,
        use_container_width=True,
        num_rows="dynamic"
    )
    if st.button("💾 حفظ تعديلات الطالبات"):
        st.session_state.students_db = edited_df
        st.success("تم تحديث حالة الدفع!")

    st.subheader("🚌 جدول السائقين")
    st.dataframe(st.session_state.buses_db, use_container_width=True)

    st.subheader("🚐 توزيع الطالبات على السائقين")
    driver_name = st.selectbox("اختر السائق", st.session_state.buses_db["اسم السائق"])
    assigned_students = st.multiselect(
        "اختر الطالبات لهذا السائق",
        st.session_state.students_db["الاسم"],
        default=st.session_state.assignments.get(driver_name, [])
    )
    if st.button(f"✅ اعتماد التوزيع لـ {driver_name}"):
        st.session_state.assignments[driver_name] = assigned_students
        st.success(f"تم تثبيت قائمة الطالبات لـ {driver_name}")

    st.subheader("📊 ملخص التوزيع الحالي")
    for driver, names in st.session_state.assignments.items():
        if names:
            st.text(f"🚐 {driver}: {', '.join(names)}")

    st.subheader("📍 مواقع الطالبات")
    for _, student in st.session_state.students_db.iterrows():
        st.write(f"👩 {student['الاسم']}")
        if st.button(f"🗺 فتح موقع {student['الاسم']}", key=student['الاسم']):
            url = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(student["الموقع"])
            st.markdown(f"[اضغط هنا للانتقال إلى الخريطة]({url})")

# ==========================
# لوحة التحكم (للمستقبل)
# ==========================
else:
    st.subheader("⚙️ لوحة التحكم")
    st.write("هنا يمكن إضافة مزيد من الأدوات المستقبلية، مثل تقارير الدفع، تنبيهات السائقين، وإحصائيات الرحلات.")