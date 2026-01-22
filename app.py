import streamlit as st
import pandas as pd

# --- بيانات تجريبية ---
def load_data():
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

# تحميل البيانات
load_data()

# --- الصفحة الرئيسية ---
st.set_page_config(page_title="التطبيق", layout="wide")
st.title("الصفحة الرئيسية")
st.write("هذه الصفحة الرئيسية للتطبيق")

# عرض بيانات الطالبات
st.subheader("قائمة الطالبات")
st.dataframe(st.session_state.students_db)

# عرض بيانات السائقين
st.subheader("قائمة السائقين")
st.dataframe(st.session_state.buses_db)

# القائمة الجانبية
with st.sidebar:
    st.header("القائمة الرئيسية")
    st.write("اختر الصفحة من هنا:")
    st.write("- الصفحة الرئيسية")
    st.write("- لوحة التحكم")