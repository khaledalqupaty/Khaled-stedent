import streamlit as st
import pandas as pd

# ضبط إعدادات الصفحة
st.set_page_config(
    page_title="نظام إدارة نقل الطالبات",
    page_icon="🚌",
    layout="wide"
)

st.title("🚌 نظام إدارة حافلات وسائقين النقل")

# القائمة الجانبية للتنقل
menu = ["لوحة التحكم", "إدارة السائقين", "إدارة الطالبات والمسارات", "التقارير اليومية"]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

# 1. لوحة التحكم
if choice == "لوحة التحكم":
    st.subheader("ملخص العمليات اليومية")
    
    col1, col2, col3 = st.columns(3)
    col1.metric(label="إجمالي السائقين", value="3")
    col2.metric(label="إجمالي الحافلات (H1)", value="3")
    col3.metric(label="الوجهات الرئيسية", value="الكلية التقنية - ديراب")
    
    st.markdown("---")
    st.write("### حالة الجولات اليومية")
    status_df = pd.DataFrame({
        "السائق": ["السائق 1", "السائق 2", "السائق 3"],
        "المسار / المنطقة": ["شمال الرياض", "شرق الرياض", "وسط الرياض"],
        "حالة الجولة": ["مكتملة", "قيد التنفيذ", "جاهز"]
    })
    st.dataframe(status_df, use_container_width=True)

# 2. إدارة السائقين
elif choice == "إدارة السائقين":
    st.subheader("إدارة بيانات السائقين والحافلات")
    
    with st.form("add_driver_form"):
        st.write("إضافة سائق جديد")
        driver_name = st.text_input("اسم السائق")
        phone = st.text_input("رقم التواصل")
        plate_no = st.text_input("رقم لوحة الحافلة (H1)")
        submitted = st.form_submit_button("حفظ البيانات")
        
        if submitted:
            st.success(f"تم حفظ بيانات السائق {driver_name} بنجاح!")

# 3. إدارة الطالبات والمسارات
elif choice == "إدارة الطالبات والمسارات":
    st.subheader("سجل الطالبات والمسارات")
    st.info("يمكنك تنظيم اشتراكات ومواقع الطالبات حسب الأحياء والمسارات.")

# 4. التقارير
elif choice == "التقارير اليومية":
    st.subheader("التقارير والسجلات")
    st.write("متابعة الحضور والغياب واشتراكات النقل.")
