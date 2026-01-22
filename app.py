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