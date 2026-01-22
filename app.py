import streamlit as st

# إعداد الصفحة
st.set_page_config(page_title="التطبيق", layout="wide")

# محتوى الصفحة الرئيسية
st.title("الصفحة الرئيسية")
st.write("هذه الصفحة الرئيسية للتطبيق")

# القائمة الجانبية (تأكد من ظهورها)
with st.sidebar:
    st.header("القائمة الرئيسية")
    st.write("اختر الصفحة من هنا:")
    st.write("- الصفحة الرئيسية")
    st.write("- لوحة التحكم")