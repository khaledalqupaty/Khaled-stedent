import streamlit as st
import pandas as pd

# --- بيانات تجريبية ---
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

# --- إعداد الصفحة ---
st.set_page_config(page_title="التطبيق", layout="wide")

# --- الصفحة الرئيسية ---
st.title("الصفحة الرئيسية")
st.write("هذه الصفحة الرئيسية للتطبيق")

# --- القائمة الجانبية ---
with st.sidebar:
    st.header("القائمة الرئيسية")
    st.write("اختر الصفحة من هنا:")
    st.write("- الصفحة الرئيسية")
    st.write("- لوحة التحكم")

# --- جدول الطالبات مع إمكانية تعديل ---
st.subheader("قائمة الطالبات")
edited_df = st.data_editor(
    st.session_state.students_db,
    use_container_width=True,
    num_rows="dynamic"
)
if st.button("حفظ تعديلات الطالبات"):
    st.session_state.students_db = edited_df
    st.success("تم تحديث حالة الدفع!")

# --- جدول السائقين للعرض فقط ---
st.subheader("قائمة السائقين")
st.dataframe(st.session_state.buses_db, use_container_width=True)