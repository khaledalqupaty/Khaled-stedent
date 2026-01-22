import streamlit as st
import pandas as pd

st.set_page_config(page_title="نظام إدارة الباصات", layout="wide")

# إنشاء ملف بيانات وهمي إذا لم يوجد
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["الاسم", "الحي", "السائق", "المبلغ", "الحالة"])

st.title("🚌 نظام إدارة باصاتك")

tab1, tab2, tab3 = st.tabs(["إدارة الطالبات", "توزيع السائقين", "المدفوعات"])

with tab1:
    st.subheader("تسجيل طالبة جديدة")
    with st.form("add_form"):
        name = st.text_input("اسم الطالبة")
        area = st.text_input("الحي")
        driver = st.selectbox("السائق", ["أبو محمد", "أبو فهد", "أبو علي"])
        price = st.number_input("المبلغ الشهري", value=500)
        if st.form_submit_button("حفظ"):
            new_data = pd.DataFrame([[name, area, driver, price, "غير مدفوع"]], columns=st.session_state.df.columns)
            st.session_state.df = pd.concat([st.session_state.df, new_data], ignore_index=True)
            st.success("تم الحفظ")

with tab2:
    st.subheader("قائمة التوزيع")
    st.dataframe(st.session_state.df, use_container_width=True)

with tab3:
    st.subheader("تحصيل المبالغ")
    for index, row in st.session_state.df.iterrows():
        col1, col2 = st.columns([3, 1])
        col1.write(f"الطالبة: {row['الاسم']} - المبلغ: {row['المبلغ']}")
        if col2.button(f"تم الدفع ✅", key=index):
            st.session_state.df.at[index, 'الحالة'] = "مدفوع"
            st.rerun()
