import streamlit as st
import pandas as pd

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
