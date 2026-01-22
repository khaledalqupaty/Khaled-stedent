import streamlit as st

# إعداد الصفحة
st.set_page_config(page_title="التطبيق", layout="wide")

# محتوى الصفحة الرئيسية
st.title("الصفحة الرئيسية")
st.write("هذه الصفحة الرئيسية للتطبيق")

# اختياري: رابط سريع للصفحة الثانوية
st.markdown("---")
st.write("انتقل إلى صفحة لوحة التحكم في القائمة الجانبية.")