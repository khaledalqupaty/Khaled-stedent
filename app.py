import streamlit as st
import pandas as pd

# إعداد الصفحة
st.set_config = st.set_page_config(page_title="Bus Management Pro", layout="wide")

# --- إدارة البيانات في الذاكرة (للتجربة قبل ربط قاعدة البيانات) ---
if 'students_db' not in st.session_state:
    st.session_state.students_db = pd.DataFrame([
        {"الاسم": "نورة", "الموقع": "حي الروضة", "حالة الدفع": "انتظار", "رقم التواصل": "050xxx"},
        {"الاسم": "سارة", "الموقع": "حي الملقا", "حالة الدفع": "تم الدفع", "رقم التواصل": "055xxx"}
    ])

if 'buses_db' not in st.session_state:
    st.session_state.buses_db = pd.DataFrame([
        {"رقم الباص": "1", "اسم السائق": "أحمد", "رقم الجوال": "059xxx"},
        {"رقم الباص": "2", "اسم السائق": "محمد", "رقم الجوال": "058xxx"}
    ])

if 'assignments' not in st.session_state:
    st.session_state.assignments = {} # قاموس لحفظ توزيع كل سائق بشكل مستقل

# --- القائمة الجانبية ---
with st.sidebar:
    st.header("🗂 القائمة الرئيسية")
    role = st.selectbox("نوع الدخول", ["⚙️ مدير النظام", "🚐 واجهة السائق"])
    st.divider()
    st.info("ملاحظة: البيانات حالياً تجريبية وتختفي عند تحديث المتصفح. لثباتها نحتاج ربط Google Sheets.")

# ------------------- نظام مدير النظام -------------------
if role == "⚙️ مدير النظام":
    st.title("إدارة العمليات اليومية")
    
    tab1, tab2, tab3 = st.tabs(["👥 الطالبات والدفع", "📅 التوزيع اليومي", "🚌 أسطول الباصات"])

    with tab1:
        st.subheader("إدارة بيانات الطالبات")
        # إضافة طالبة
        with st.expander("➕ إضافة طالبة جديدة"):
            with st.form("add_student"):
                c1, c2 = st.columns(2)
                name = c1.text_input("الاسم")
                loc = c2.text_input("الموقع (رابط)")
                phone = c1.text_input("الجوال")
                pay = c2.selectbox("الحالة المالية", ["تم الدفع", "انتظار", "متأخر"])
                if st.form_submit_button("حفظ"):
                    new_row = {"الاسم": name, "الموقع": loc, "حالة الدفع": pay, "رقم التواصل": phone}
                    st.session_state.students_db = pd.concat([st.session_state.students_db, pd.DataFrame([new_row])], ignore_index=True)
                    st.rerun()

        # عرض وتعديل حالة الدفع
        st.write("### قائمة الطالبات")
        edited_df = st.data_editor(st.session_state.students_db, use_container_width=True, num_rows="dynamic")
        if st.button("حفظ التعديلات في الجدول"):
            st.session_state.students_db = edited_df
            st.success("تم تحديث البيانات وحالة الدفع!")

    with tab2:
        st.subheader("توزيع الباصات (اليوم)")
        col_a, col_b = st.columns([1, 2])
        
        with col_a:
            driver_to_assign = st.selectbox("اختر السائق", st.session_state.buses_db["اسم السائق"])
            selected_st = st.multiselect("اختر الطالبات له", st.session_state.students_db["الاسم"], 
                                         default=st.session_state.assignments.get(driver_to_assign, []))
            
            if st.button("اعتماد التوزيع لهذا السائق"):
                st.session_state.assignments[driver_to_assign] = selected_st
                st.success(f"تم تثبيت قائمة {driver_to_assign}")

        with col_b:
            st.write("### الملخص الحالي")
            for driver, names in st.session_state.assignments.items():
                if names:
                    st.text(f"🚐 {driver}: {', '.join(names)}")

    with tab3:
        st.subheader("بيانات السائقين")
        st.data_editor(st.session_state.buses_db, use_container_width=True, num_rows="dynamic")

# ------------------- نظام السائق -------------------
else:
    st.title("مرحباً بك أيها السائق")
    my_name = st.selectbox("اختر اسمك لعرض جدولك", ["اختر اسمك"] + list(st.session_state.buses_db["اسم السائق"]))
    
    if my_name != "اختر اسمك":
        my_list = st.session_state.assignments.get(my_name, [])
        if my_list:
            st.success(f"لديك {len(my_list)} طالبات اليوم:")
            for student in my_list:
                # جلب بيانات الطالبة من قاعدة البيانات
                s_info = st.session_state.students_db[st.session_state.students_db["الاسم"] == student].iloc[0]
                with st.expander(f"📍 {student}"):
                    st.write(f"🏠 الموقع: {s_info['الموقع']}")
                    st.write(f"📞 التواصل: {s_info['رقم التواصل']}")
                    if st.button(f"فتح الخريطة لـ {student}", key=student):
                        st.info("سيتم فتح جوجل ماب...")
        else:
            st.warning("لا يوجد طالبات مخصصات لك حالياً.")
