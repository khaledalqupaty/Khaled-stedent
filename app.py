import streamlit as st
import pandas as pd

# إعدادات الصفحة
st.set_page_config(page_title="نظام إدارة حافلات الطالبات", layout="wide")

# --- محاكاة قاعدة البيانات (يمكن ربطها بـ Google Sheets أو SQL لاحقاً) ---
if 'students' not in st.session_state:
    st.session_state.students = pd.DataFrame(columns=["الاسم", "الموقع", "حالة الدفع", "رقم التواصل"])
if 'buses' not in st.session_state:
    st.session_state.buses = pd.DataFrame(columns=["رقم الباص", "اسم السائق", "رقم الجوال"])
if 'daily_schedule' not in st.session_state:
    st.session_state.daily_schedule = {}

# --- القائمة الجانبية للتنقل ---
st.sidebar.title("🚌 نظام الحافلات الذكي")
user_role = st.sidebar.radio("دخول بصفتي:", ["مدير النظام", "سائق"])

# ------------------- قسم مدير النظام -------------------
if user_role == "مدير النظام":
    st.title("🛠 لوحة تحكم الإدارة")
    
    tab1, tab2, tab3, tab4 = st.tabs(["👥 إدخال الطالبات", "🚌 إعداد الباصات", "📅 التوزيع اليومي", "💰 متابعة الدفع"])

    with tab1:
        st.subheader("إضافة طالبة جديدة")
        with st.form("student_form"):
            name = st.text_input("اسم الطالبة")
            loc = st.text_input("رابط الموقع (Google Maps)")
            payment = st.selectbox("حالة الدفع", ["تم الدفع", "انتظار", "متأخر"])
            contact = st.text_input("رقم التواصل")
            if st.form_submit_button("حفظ البيانات"):
                new_data = pd.DataFrame([[name, loc, payment, contact]], columns=st.session_state.students.columns)
                st.session_state.students = pd.concat([st.session_state.students, new_data], ignore_index=True)
                st.success("تمت الإضافة بنجاح!")
        st.dataframe(st.session_state.students, use_container_width=True)

    with tab2:
        st.subheader("إدارة الباصات والسائقين")
        with st.form("bus_form"):
            b_id = st.text_input("رقم أو لوحة الباص")
            driver = st.text_input("اسم السائق")
            d_phone = st.text_input("جوال السائق")
            if st.form_submit_button("إضافة باص"):
                new_bus = pd.DataFrame([[b_id, driver, d_phone]], columns=st.session_state.buses.columns)
                st.session_state.buses = pd.concat([st.session_state.buses, new_bus], ignore_index=True)
        st.dataframe(st.session_state.buses, use_container_width=True)

    with tab3:
        st.subheader("التوزيع اليومي للمداومات")
        if st.session_state.students.empty or st.session_state.buses.empty:
            st.warning("يرجى إضافة طالبات وباصات أولاً.")
        else:
            selected_date = st.date_input("اختر التاريخ")
            selected_bus = st.selectbox("اختر الباص/السائق", st.session_state.buses["اسم السائق"])
            selected_students = st.multiselect("اختر الطالبات المداومات اليوم", st.session_state.students["الاسم"])
            
            if st.button("اعتماد توزيع اليوم"):
                st.session_state.daily_schedule[selected_bus] = selected_students
                st.success(f"تم تخصيص {len(selected_students)} طالبات للسائق {selected_bus}")

    with tab4:
        st.subheader("سجل المدفوعات")
        st.table(st.session_state.students[["الاسم", "حالة الدفع"]])

# ------------------- قسم السائق -------------------
else:
    st.title("📱 واجهة السائق")
    driver_name = st.selectbox("اختر اسمك (السائق)", st.session_state.buses["اسم السائق"] if not st.session_state.buses.empty else ["لا يوجد سائقين"])
    
    if driver_name in st.session_state.daily_schedule:
        st.info(f"مرحباً {driver_name}، إليك قائمة الطالبات لليوم:")
        students_list = st.session_state.daily_schedule[driver_name]
        
        # عرض بيانات الطالبات المخصصات لهذا السائق فقط
        display_data = st.session_state.students[st.session_state.students["الاسم"].isin(students_list)]
        for index, row in display_data.iterrows():
            with st.expander(f"📍 الطالبة: {row['الاسم']}"):
                st.write(f"**الموقع:** {row['الموقع']}")
                st.write(f"**التواصل:** {row['رقم التواصل']}")
                st.link_button("فتح الخريطة", f"{row['الموقع']}")
    else:
        st.warning("لا يوجد توزيع مخصص لك اليوم بعد.")
