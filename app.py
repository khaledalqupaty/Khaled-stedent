# -*- coding: utf-8 -*-
import subprocess
import sys

# تثبيت المكتبات المطلوبة تلقائياً
required = ['streamlit', 'pandas', 'folium', 'fpdf2', 'openpyxl']
for package in required:
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

# الآن استيراد المكتبات
import streamlit as st
import pandas as pd
import sqlite3, pathlib, datetime, io
