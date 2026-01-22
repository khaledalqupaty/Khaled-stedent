import streamlit as st
from data.mock_data import load_data  # تأكد أن المسار صحيح

st.set_page_config(page_title="التطبيق", layout="wide")

# تحميل البيانات
load_data()

# الصفحة الرئيسية
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