# -*- coding: utf-8 -*-
"""
🚌 نظام إدارة نقل الطالبات الاحترافي — الإصدار 2.0
جديد في هذا الإصدار:
  • ترحيل تلقائي للملفات القديمة (إضافة الأعمدة الجديدة دون فقدان البيانات)
  • أرقام فواتير تلقائية (INV-2026-09-00001) — عدّاد مستقل لكل شهر
  • سجل حركات مالي كامل (transactions.csv) مع طريقة الدفع
  • منع الدفع الزائد + بطاقات metrics في شاشة الدفع
  • كشف حساب كامل لكل طالبة (فواتير + حركات)
  • بحث فوري عن الطالبات + نسبة إشغال الحافلات (مُصلحة)
  • إصلاح حذف الحضور (لم يعد يمسح مسارات أخرى من نفس اليوم)
التشغيل: streamlit run school_transport_pro_v2.py
"""
import os
import numpy as np
import pandas as pd
import streamlit as st
from datetime import date

# ============================================================
#  الإعدادات العامة وقاعدة البيانات (CSV)
# ============================================================
DATA_DIR = "data"
FILES = {
    "buses":        ("buses.csv",        ["لوحة الحافلة", "نوع الحافلة", "السعة", "الحالة", "تاريخ الإضافة"]),
    "drivers":      ("drivers.csv",      ["السائق", "رقم التواصل", "الهوية/الرخصة", "اللوحة المخصصة", "تاريخ الإضافة"]),
    "routes":       ("routes.csv",       ["المسار", "المنطقة", "السائق", "اللوحة", "وقت الانطلاق", "ملاحظات"]),
    "students":     ("students.csv",     ["الطالبة", "رقم التواصل", "اسم ولي الأمر", "الحي / موقع الاستلام", "المسار", "اللوحة", "الاشتراك الشهري", "تاريخ الالتحاق", "الحالة"]),
    "attendance":   ("attendance.csv",   ["التاريخ", "الطالبة", "المسار", "الحالة"]),
    "payments":     ("payments.csv",     ["رقم الفاتورة", "الشهر", "الطالبة", "المبلغ المطلوب", "المدفوع", "المتبقي", "حالة الدفع", "تاريخ آخر دفعة", "ملاحظات"]),
    "transactions": ("transactions.csv", ["التاريخ", "الشهر", "الطالبة", "المبلغ", "طريقة الدفع", "ملاحظات"]),
}
PAY_METHODS = ["نقدي", "تحويل بنكي", "مدى", "STC Pay"]
STATUSES = ["حاضرة", "غائبة", "معتذرة"]


def init_data():
    """إنشاء الملفات الناقصة + ترحيل الملفات القديمة تلقائيًا."""
    os.makedirs(DATA_DIR, exist_ok=True)
    for fname, cols in FILES.values():
        path = os.path.join(DATA_DIR, fname)
        if not os.path.exists(path):
            pd.DataFrame(columns=cols).to_csv(path, index=False, encoding="utf-8-sig")
            continue
        df = pd.read_csv(path, encoding="utf-8-sig")
        changed = False

        # إعادة تسمية الأعمدة القديمة
        if fname == FILES["drivers"][0] and "اللوحة الم assigned" in df.columns and "اللوحة المخصصة" not in df.columns:
            df = df.rename(columns={"اللوحة الم assigned": "اللوحة المخصصة"})
            changed = True

        # إضافة الأعمدة الناقصة
        for c in cols:
            if c not in df.columns:
                df[c] = ""
                changed = True

        # ترحيل: ترقيم الفواتير القديمة فاقدة الأرقام
        if fname == FILES["payments"][0] and not df.empty:
            mask = df["رقم الفاتورة"].astype(str).str.strip().isin(["", "nan", "None"])
            if mask.any():
                counters = {}
                for idx in df[mask].index:
                    m = str(df.at[idx, "الشهر"])
                    counters[m] = counters.get(m, 0) + 1
                    df.at[idx, "رقم الفاتورة"] = f"INV-{m}-{counters[m]:05d}"
                changed = True

        # ترتيب الأعمدة حسب التعريف الحالي
        df = df[cols]
        if changed:
            df.to_csv(path, index=False, encoding="utf-8-sig")


def load_df(key):
    path = os.path.join(DATA_DIR, FILES[key][0])
    if not os.path.exists(path):
        return pd.DataFrame(columns=FILES[key][1])
    df = pd.read_csv(path, encoding="utf-8-sig")
    if key == "payments":
        for col in ["المبلغ المطلوب", "المدفوع", "المتبقي"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if key == "transactions":
        if "المبلغ" in df.columns:
            df["المبلغ"] = pd.to_numeric(df["المبلغ"], errors="coerce").fillna(0)
    return df


def save_df(key, df):
    df.to_csv(os.path.join(DATA_DIR, FILES[key][0]), index=False, encoding="utf-8-sig")


def money(x):
    try:
        return f"{float(x):,.0f} ر.س"
    except Exception:
        return "0 ر.س"


def next_invoice_id(pay_df, month):
    """رقم فاتورة تالٍ داخل الشهر — لا يتكرر حتى بعد حذف فواتير."""
    pref = f"INV-{month}-"
    seqs = (pay_df["رقم الفاتورة"].astype(str)
            .str.replace(pref, "", regex=False)
            .pipe(pd.to_numeric, errors="coerce"))
    seq = seqs.max()
    return f"{pref}{(int(seq) if pd.notna(seq) else 0) + 1:05d}"


init_data()

# ============================================================
#  إعدادات الصفحة والتنسيق
# ============================================================
st.set_page_config(page_title="نظام إدارة نقل الطالبات الاحترافي", page_icon="🚌", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; }
    .success-card  { background: #dff5e8; padding: 15px; border-radius: 12px; }
    .warning-card  { background: #fff3cd; padding: 15px; border-radius: 12px; }
    .danger-card   { background: #f8d7da; padding: 15px; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

st.title("🚌 نظام إدارة نقل الطالبات الاحترافي")
st.caption("الإصدار 2.0 — فواتير مرقّمة • سجل مالي • كشوف حسابات • إشغال الحافلات")

menu = [
    "📊 لوحة التحكم",
    "🚌 إدارة الحافلات",
    "🧑‍✈️ إدارة السائقين",
    "🗺️ إدارة المسارات",
    "👩‍🎓 إدارة الطالبات",
    "✅ الحضور اليومي",
    "💳 الاشتراكات الشهرية",
    "📈 التقارير الشاملة",
]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)


# ============================================================
#  1) لوحة التحكم
# ============================================================
if choice == "📊 لوحة التحكم":
    st.subheader("📊 ملخص العمليات")
    buses_df, drivers_df = load_df("buses"), load_df("drivers")
    routes_df, students_df = load_df("routes"), load_df("students")
    att_df, pay_df = load_df("attendance"), load_df("payments")

    active_students = students_df[students_df["الحالة"] == "نشطة"] if not students_df.empty else students_df
    today = str(date.today())
    today_att = att_df[att_df["التاريخ"] == today] if not att_df.empty else pd.DataFrame()

    cur_month = date.today().strftime("%Y-%m")
    month_pay = pay_df[pay_df["الشهر"] == cur_month] if not pay_df.empty else pd.DataFrame()
    required = float(month_pay["المبلغ المطلوب"].sum()) if not month_pay.empty else 0
    paid_amt = float(month_pay["المدفوع"].sum()) if not month_pay.empty else 0
    remaining = required - paid_amt
    rate = round(paid_amt / required * 100, 1) if required else 0

    row = st.columns(4)
    row[0].metric("🚌 الحافلات", len(buses_df))
    row[1].metric("🧑‍✈️ السائقون", len(drivers_df))
    row[2].metric("🗺️ المسارات", len(routes_df))
    row[3].metric("👩‍🎓 الطالبات النشطات", len(active_students))

    row = st.columns(4)
    row[0].metric("💰 مستحقات الشهر", money(required))
    row[1].metric("✅ المحصّل", money(paid_amt))
    row[2].metric("⏳ المتبقي", money(max(remaining, 0)))
    row[3].metric("📈 نسبة التحصيل", f"{rate}%")

    st.markdown("---")
    left, right = st.columns(2)

    with left:
        st.write("### 🗺️ حالة الجولات اليومية")
        if not routes_df.empty:
            disp = routes_df.copy()
            disp["عدد الطالبات"] = disp["المسار"].map(
                active_students.groupby("المسار").size() if not active_students.empty else {}
            ).fillna(0).astype(int)
            disp["حاضرات اليوم"] = disp["المسار"].map(
                today_att[today_att["الحالة"] == "حاضرة"].groupby("المسار").size() if not today_att.empty else {}
            ).fillna(0).astype(int)
            # نسبة الإشغال (مصححة: لا قسمة على صفر ولا inf)
            cap = disp["اللوحة"].map(buses_df.set_index("لوحة الحافلة")["السعة"]) if not buses_df.empty else pd.Series(np.nan, index=disp.index)
            disp["نسبة الإشغال %"] = (disp["عدد الطالبات"] / cap.replace(0, np.nan) * 100).fillna(0).round(1)
            st.dataframe(disp, use_container_width=True, hide_index=True)
        else:
            st.info("لم تُعرّف مسارات بعد.")

    with right:
        st.write("### ✅ حضور اليوم")
        if not today_att.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("🟢 حاضرات", len(today_att[today_att["الحالة"] == "حاضرة"]))
            c2.metric("🔴 غائبات", len(today_att[today_att["الحالة"] == "غائبة"]))
            c3.metric("🟡 معتذرات", len(today_att[today_att["الحالة"] == "معتذرة"]))
        else:
            st.info("لم يُسجّل حضور اليوم بعد.")

        st.write("### 💳 متأخرات السداد")
        if not month_pay.empty:
            late = month_pay[month_pay["حالة الدفع"] != "مدفوع"]
            st.metric("طالبات عليهن مستحقات", len(late))
            if not late.empty:
                st.dataframe(late[["رقم الفاتورة", "الطالبة", "المتبقي", "حالة الدفع"]], use_container_width=True, hide_index=True)
        else:
            st.info(f"لم تُولّد فواتير شهر {cur_month} بعد — من قائمة الاشتراكات.")


# ============================================================
#  2) إدارة الحافلات
# ============================================================
elif choice == "🚌 إدارة الحافلات":
    st.subheader("🚌 سجل الحافلات")
    buses_df = load_df("buses")
    t1, t2, t3 = st.tabs(["➕ إضافة حافلة", "✏️ تعديل", "🗑️ حذف"])

    with t1:
        with st.form("add_bus", clear_on_submit=True):
            c1, c2 = st.columns(2)
            plate = c1.text_input("رقم اللوحة (H1)")
            btype = c2.selectbox("نوع الحافلة", ["حافلة صغيرة", "حافلة متوسطة", "حافلة كبيرة", "فان", "أخرى"])
            cap = st.number_input("السعة (عدد المقاعد)", min_value=1, max_value=80, value=30)
            status = st.selectbox("حالة الحافلة", ["جاهزة", "في الصيانة", "خارج الخدمة"])
            if st.form_submit_button("💾 حفظ الحافلة"):
                if plate:
                    if not buses_df.empty and plate in buses_df["لوحة الحافلة"].values:
                        st.warning("هذه اللوحة مسجلة مسبقًا!")
                    else:
                        buses_df.loc[len(buses_df)] = [plate, btype, cap, status, str(date.today())]
                        save_df("buses", buses_df)
                        st.success(f"✅ تمت إضافة الحافلة {plate}.")
                        st.rerun()
                else:
                    st.error("رقم اللوحة إلزامي.")

    with t2:
        if buses_df.empty:
            st.info("لا توجد حافلات مسجلة.")
        else:
            sel = st.selectbox("اختر الحافلة", buses_df["لوحة الحافلة"].tolist())
            r = buses_df[buses_df["لوحة الحافلة"] == sel].iloc[0]
            with st.form("edit_bus"):
                c1, c2 = st.columns(2)
                opts = ["حافلة صغيرة", "حافلة متوسطة", "حافلة كبيرة", "فان", "أخرى"]
                bt = c1.selectbox("النوع", opts, index=opts.index(r["نوع الحافلة"]) if r["نوع الحافلة"] in opts else 4)
                cp = c2.number_input("السعة", min_value=1, max_value=80, value=int(r["السعة"]))
                st_opts = ["جاهزة", "في الصيانة", "خارج الخدمة"]
                stt = st.selectbox("الحالة", st_opts, index=st_opts.index(r["الحالة"]) if r["الحالة"] in st_opts else 0)
                if st.form_submit_button("✏️ تحديث"):
                    buses_df.loc[buses_df["لوحة الحافلة"] == sel, ["نوع الحافلة", "السعة", "الحالة"]] = [bt, cp, stt]
                    save_df("buses", buses_df)
                    st.success("✅ تم التحديث.")
                    st.rerun()

    with t3:
        if buses_df.empty:
            st.info("لا توجد حافلات مسجلة.")
        else:
            sel = st.selectbox("اختر حافلة للحذف", buses_df["لوحة الحافلة"].tolist(), key="del_bus")
            if st.button("🗑️ حذف الحافلة"):
                save_df("buses", buses_df[buses_df["لوحة الحافلة"] != sel])
                st.success("✅ تم الحذف.")
                st.rerun()

    st.markdown("---")
    st.write("### قائمة الحافلات")
    st.dataframe(buses_df, use_container_width=True, hide_index=True) if not buses_df.empty else st.info("لا توجد بيانات.")


# ============================================================
#  3) إدارة السائقين
# ============================================================
elif choice == "🧑‍✈️ إدارة السائقين":
    st.subheader("🧑‍✈️ سجل السائقين")
    drivers_df, buses_df = load_df("drivers"), load_df("buses")
    plates = buses_df["لوحة الحافلة"].tolist() if not buses_df.empty else []

    t1, t2, t3 = st.tabs(["➕ إضافة سائق", "✏️ تعديل", "🗑️ حذف"])

    with t1:
        with st.form("add_driver", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("اسم السائق")
            phone = c2.text_input("رقم التواصل")
            lic = st.text_input("رقم الهوية / الرخصة")
            plate = st.selectbox("الحافلة المخصصة", plates) if plates else st.text_input("رقم اللوحة")
            if st.form_submit_button("💾 حفظ السائق"):
                if name and phone:
                    drivers_df.loc[len(drivers_df)] = [name, phone, lic, plate, str(date.today())]
                    save_df("drivers", drivers_df)
                    st.success(f"✅ تم حفظ السائق {name}.")
                    st.rerun()
                else:
                    st.error("الاسم ورقم التواصل إلزاميان.")

    with t2:
        if drivers_df.empty:
            st.info("لا يوجد سائقون.")
        else:
            sel = st.selectbox("اختر السائق", drivers_df["السائق"].tolist(), key="ed_drv")
            r = drivers_df[drivers_df["السائق"] == sel].iloc[0]
            with st.form("edit_driver"):
                ph = st.text_input("رقم التواصل", value=str(r["رقم التواصل"]))
                lc = st.text_input("الهوية / الرخصة", value=str(r["الهوية/الرخصة"]))
                pl = (st.selectbox("الحافلة", plates,
                                   index=plates.index(r["اللوحة المخصصة"]) if r["اللوحة المخصصة"] in plates else 0)
                      if plates else st.text_input("اللوحة", value=str(r["اللوحة المخصصة"])))
                if st.form_submit_button("✏️ تحديث"):
                    drivers_df.loc[drivers_df["السائق"] == sel,
                                   ["رقم التواصل", "الهوية/الرخصة", "اللوحة المخصصة"]] = [ph, lc, pl]
                    save_df("drivers", drivers_df)
                    st.success("✅ تم التحديث.")
                    st.rerun()

    with t3:
        if drivers_df.empty:
            st.info("لا يوجد سائقون.")
        else:
            sel = st.selectbox("اختر سائقًا للحذف", drivers_df["السائق"].tolist(), key="del_drv")
            if st.button("🗑️ حذف السائق"):
                save_df("drivers", drivers_df[drivers_df["السائق"] != sel])
                st.success("✅ تم الحذف.")
                st.rerun()

    st.markdown("---")
    st.write("### قائمة السائقين")
    st.dataframe(drivers_df, use_container_width=True, hide_index=True) if not drivers_df.empty else st.info("لا توجد بيانات.")


# ============================================================
#  4) إدارة المسارات
# ============================================================
elif choice == "🗺️ إدارة المسارات":
    st.subheader("🗺️ المسارات والمناطق")
    routes_df, drivers_df, buses_df = load_df("routes"), load_df("drivers"), load_df("buses")
    drv_list = drivers_df["السائق"].tolist() if not drivers_df.empty else []
    plt_list = buses_df["لوحة الحافلة"].tolist() if not buses_df.empty else []

    with st.form("add_route", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        route = c1.text_input("اسم المسار")
        area = c2.text_input("المنطقة / الاتجاه")
        driver = c3.selectbox("السائق", drv_list) if drv_list else c3.text_input("السائق")
        plate = c4.selectbox("اللوحة", plt_list) if plt_list else c4.text_input("اللوحة")
        c5, c6 = st.columns(2)
        ttime = c5.text_input("وقت الانطلاق", placeholder="مثال: 6:30 صباحًا")
        notes = c6.text_input("ملاحظات")
        if st.form_submit_button("➕ إضافة مسار"):
            if route and area:
                routes_df.loc[len(routes_df)] = [route, area, driver, plate, ttime, notes]
                save_df("routes", routes_df)
                st.success(f"✅ تمت إضافة المسار {route}.")
                st.rerun()
            else:
                st.error("اسم المسار والمنطقة إلزاميان.")

    if not routes_df.empty:
        st.write("### المسارات المسجلة")
        st.dataframe(routes_df, use_container_width=True, hide_index=True)
        sel = st.selectbox("اختر مسارًا للحذف", routes_df["المسار"].tolist())
        if st.button("🗑️ حذف المسار"):
            save_df("routes", routes_df[routes_df["المسار"] != sel])
            st.success("✅ تم الحذف.")
            st.rerun()
    else:
        st.info("لا توجد مسارات بعد.")


# ============================================================
#  5) إدارة الطالبات
# ============================================================
elif choice == "👩‍🎓 إدارة الطالبات":
    st.subheader("👩‍🎓 سجل الطالبات")
    students_df, routes_df, buses_df = load_df("students"), load_df("routes"), load_df("buses")
    route_list = routes_df["المسار"].tolist() if not routes_df.empty else []
    plt_list = buses_df["لوحة الحافلة"].tolist() if not buses_df.empty else []

    t1, t2, t3 = st.tabs(["➕ إضافة طالبة", "✏️ تعديل / 🗑️ حذف", "📋 القائمة"])

    with t1:
        if not route_list:
            st.warning("⚠️ أضف مسارًا أولًا من قائمة المسارات.")
        with st.form("add_student", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("اسم الطالبة")
            phone = c2.text_input("رقم التواصل")
            parent = st.text_input("اسم ولي الأمر")
            area = st.text_input("الحي / موقع الاستلام")
            c3, c4 = st.columns(2)
            route = c3.selectbox("المسار", route_list) if route_list else c3.text_input("المسار")
            plate = c4.selectbox("الحافلة", plt_list) if plt_list else c4.text_input("اللوحة")
            sub = st.number_input("قيمة الاشتراك الشهري (ر.س)", min_value=0, value=200, step=10)
            if st.form_submit_button("💾 حفظ الطالبة"):
                if name and route:
                    students_df.loc[len(students_df)] = [name, phone, parent, area, route, plate, sub, str(date.today()), "نشطة"]
                    save_df("students", students_df)
                    st.success(f"✅ تم تسجيل الطالبة {name}.")
                    st.rerun()
                else:
                    st.error("اسم الطالبة والمسار إلزاميان.")

    with t2:
        if students_df.empty:
            st.info("لا توجد طالبات.")
        else:
            sel = st.selectbox("اختر الطالبة", students_df["الطالبة"].tolist())
            r = students_df[students_df["الطالبة"] == sel].iloc[0]
            with st.form("edit_student"):
                c1, c2 = st.columns(2)
                ph = c1.text_input("رقم التواصل", value=str(r["رقم التواصل"]))
                par = c2.text_input("ولي الأمر", value=str(r["اسم ولي الأمر"]))
                ar = st.text_input("الحي", value=str(r["الحي / موقع الاستلام"]))
                ro = (st.selectbox("المسار", route_list,
                                   index=route_list.index(r["المسار"]) if r["المسار"] in route_list else 0)
                      if route_list else st.text_input("المسار", value=str(r["المسار"])))
                pl = (st.selectbox("الحافلة", plt_list,
                                   index=plt_list.index(r["اللوحة"]) if r["اللوحة"] in plt_list else 0)
                      if plt_list else st.text_input("اللوحة", value=str(r["اللوحة"])))
                sb = st.number_input("الاشتراك الشهري", min_value=0, value=int(r["الاشتراك الشهري"]))
                stt = st.selectbox("الحالة", ["نشطة", "موقوفة"], index=0 if r["الحالة"] == "نشطة" else 1)
                cu, cd = st.columns(2)
                upd = cu.form_submit_button("✏️ تحديث")
                dele = cd.form_submit_button("🗑️ حذف الطالبة")
            if upd:
                students_df.loc[students_df["الطالبة"] == sel,
                                ["رقم التواصل", "اسم ولي الأمر", "الحي / موقع الاستلام", "المسار",
                                 "اللوحة", "الاشتراك الشهري", "الحالة"]] = [ph, par, ar, ro, pl, sb, stt]
                save_df("students", students_df)
                st.success("✅ تم التحديث.")
                st.rerun()
            if dele:
                save_df("students", students_df[students_df["الطالبة"] != sel])
                st.success("✅ تم الحذف.")
                st.rerun()

    with t3:
        if not students_df.empty:
            c1, c2 = st.columns(2)
            f = c1.multiselect("تصفية حسب المسار", students_df["المسار"].unique().tolist())
            search = c2.text_input("🔍 البحث عن طالبة")
            view_df = students_df
            if f:
                view_df = view_df[view_df["المسار"].isin(f)]
            if search:
                view_df = view_df[view_df["الطالبة"].astype(str).str.contains(search, case=False, na=False)]
            st.dataframe(view_df, use_container_width=True, hide_index=True)
        else:
            st.info("لا توجد بيانات.")


# ============================================================
#  6) الحضور اليومي
# ============================================================
elif choice == "✅ الحضور اليومي":
    st.subheader("✅ تسجيل حضور الجولة")
    students_df, att_df = load_df("students"), load_df("attendance")
    active = students_df[students_df["الحالة"] == "نشطة"] if not students_df.empty else students_df

    if active.empty:
        st.info("لا توجد طالبات نشطات — أضف طالبات أولًا.")
    else:
        att_date = st.date_input("تاريخ الجولة", value=date.today())
        route_filter = st.selectbox("المسار", ["الكل"] + sorted(active["المسار"].unique().tolist()))
        group = active if route_filter == "الكل" else active[active["المسار"] == route_filter]

        existing = att_df[att_df["التاريخ"] == str(att_date)] if not att_df.empty else pd.DataFrame()

        statuses = {}
        for _, r in group.iterrows():
            d = 0
            if not existing.empty:
                m = existing[existing["الطالبة"] == r["الطالبة"]]
                if not m.empty and m.iloc[0]["الحالة"] in STATUSES:
                    d = STATUSES.index(m.iloc[0]["الحالة"])
            statuses[r["الطالبة"]] = st.radio(
                f"**{r['الطالبة']}** — {r['المسار']}",
                STATUSES, index=d, horizontal=True,
                key=f"att_{att_date}_{r['الطالبة']}")

        if st.button("💾 حفظ سجل الحضور"):
            # إصلاح: نحذف فقط سجلات الطالبات المعروضات، لا كامل يوم كامل
            names = list(statuses.keys())
            att_df = att_df[~((att_df["التاريخ"] == str(att_date)) & (att_df["الطالبة"].isin(names)))] \
                if not att_df.empty else att_df
            new_rows = pd.DataFrame([{
                "التاريخ": str(att_date), "الطالبة": n,
                "المسار": group[group["الطالبة"] == n]["المسار"].iloc[0],
                "الحالة": s} for n, s in statuses.items()])
            att_df = pd.concat([att_df, new_rows], ignore_index=True)
            save_df("attendance", att_df)
            st.success("✅ تم حفظ سجل الحضور!")


# ============================================================
#  7) الاشتراكات الشهرية وحالة الدفع
# ============================================================
elif choice == "💳 الاشتراكات الشهرية":
    st.subheader("💳 الاشتراكات الشهرية وتتبع الدفع")
    students_df, pay_df = load_df("students"), load_df("payments")
    active = students_df[students_df["الحالة"] == "نشطة"] if not students_df.empty else students_df

    t1, t2, t3, t4 = st.tabs(["🧾 توليد فواتير الشهر", "💵 تسجيل دفعة", "📋 حالة الدفع", "🧾 كشف حساب طالبة"])

    with t1:
        cur_month = date.today().strftime("%Y-%m")
        month = st.text_input("شهر الفواتير (YYYY-MM)", value=cur_month)
        if st.button("🧾 توليد فواتير جميع الطالبات النشطات"):
            if active.empty:
                st.warning("لا توجد طالبات نشطات.")
            else:
                existing = pay_df[pay_df["الشهر"] == month]["الطالبة"].tolist() if not pay_df.empty else []
                added = 0
                for _, r in active.iterrows():
                    if r["الطالبة"] not in existing:
                        amt = float(r["الاشتراك الشهري"])
                        inv = next_invoice_id(pay_df, month)
                        pay_df.loc[len(pay_df)] = [inv, month, r["الطالبة"], amt, 0, amt, "غير مدفوع", "", ""]
                        added += 1
                save_df("payments", pay_df)
                st.success(f"✅ تم توليد {added} فاتورة لشهر {month}.")

    with t2:
        if pay_df.empty:
            st.info("لا توجد فواتير — ولّد فواتير أولًا.")
        else:
            month = st.selectbox("الشهر", sorted(pay_df["الشهر"].unique().tolist(), reverse=True), key="pay_month")
            unpaid = pay_df[(pay_df["الشهر"] == month) & (pay_df["حالة الدفع"] != "مدفوع")]
            if unpaid.empty:
                st.success("🎉 جميع الفواتير مدفوعة لهذا الشهر!")
            else:
                sel = st.selectbox("اختر الطالبة", unpaid["الطالبة"].tolist())
                r = unpaid[unpaid["الطالبة"] == sel].iloc[0]

                # بطاقات ملخص الفاتورة
                col1, col2, col3 = st.columns(3)
                col1.metric("💰 المطلوب", money(r["المبلغ المطلوب"]))
                col2.metric("✅ المدفوع", money(r["المدفوع"]))
                col3.metric("⏳ المتبقي", money(r["المتبقي"]))
                st.caption(f"🧾 رقم الفاتورة: `{r['رقم الفاتورة']}`")

                amt = st.number_input("مبلغ الدفعة (ر.س)", min_value=0.0, value=float(r["المتبقي"]), step=10.0)
                method = st.selectbox("طريقة الدفع", PAY_METHODS)
                note = st.text_input("ملاحظات", placeholder="دفعة جزئية / خصم / ...")

                if st.button("💵 تسجيل الدفعة"):
                    if amt <= 0:
                        st.error("⚠️ مبلغ الدفعة يجب أن يكون أكبر من صفر.")
                    elif amt > float(r["المتبقي"]):
                        st.warning("⚠️ لا يمكن دفع مبلغ أكبر من المتبقي.")
                    else:
                        new_paid = float(r["المدفوع"]) + amt
                        new_rem = float(r["المبلغ المطلوب"]) - new_paid
                        new_status = "مدفوع" if new_rem <= 0 else ("جزئي" if new_paid > 0 else "غير مدفوع")
                        pay_df.loc[(pay_df["الشهر"] == month) & (pay_df["الطالبة"] == sel) &
                                   (pay_df["رقم الفاتورة"] == r["رقم الفاتورة"]),
                                   ["المدفوع", "المتبقي", "حالة الدفع", "تاريخ آخر دفعة", "ملاحظات"]] = \
                            [new_paid, max(new_rem, 0), new_status, str(date.today()), note]
                        save_df("payments", pay_df)

                        # تسجيل الحركة في السجل المالي
                        trans_df = load_df("transactions")
                        trans_df.loc[len(trans_df)] = [str(date.today()), month, sel, amt, method, note]
                        save_df("transactions", trans_df)

                        st.success(f"✅ تم تسجيل دفعة بقيمة {money(amt)} ({method}) للطالبة {sel}.")
                        st.rerun()

    with t3:
        if pay_df.empty:
            st.info("لا توجد فواتير.")
        else:
            month = st.selectbox("الشهر", sorted(pay_df["الشهر"].unique().tolist(), reverse=True), key="view_month")
            view = pay_df[pay_df["الشهر"] == month].copy()
            c1, c2, c3 = st.columns(3)
            c1.metric("💰 إجمالي المطلوب", money(view["المبلغ المطلوب"].sum()))
            c2.metric("✅ المحصّل", money(view["المدفوع"].sum()))
            c3.metric("📈 نسبة التحصيل",
                      f"{round(view['المدفوع'].sum() / view['المبلغ المطلوب'].sum() * 100, 1) if view['المبلغ المطلوب'].sum() else 0}%")
            status_filter = st.multiselect("تصفية حسب حالة الدفع", ["مدفوع", "جزئي", "غير مدفوع"])
            if status_filter:
                view = view[view["حالة الدفع"].isin(status_filter)]
            st.dataframe(view, use_container_width=True, hide_index=True)

    with t4:
        if pay_df.empty:
            st.info("لا توجد فواتير.")
        else:
            sel = st.selectbox("اختر الطالبة", sorted(pay_df["الطالبة"].unique().tolist()), key="stmt_student")
            st.write(f"### 🧾 كشف حساب: {sel}")
            history = pay_df[pay_df["الطالبة"] == sel].sort_values("الشهر")
            if not history.empty:
                view = history[["رقم الفاتورة", "الشهر", "المبلغ المطلوب", "المدفوع", "المتبقي", "حالة الدفع", "تاريخ آخر دفعة"]].copy()
                st.dataframe(view, use_container_width=True, hide_index=True)
                tc1, tc2, tc3 = st.columns(3)
                tc1.metric("💰 إجمالي المطلوب", money(history["المبلغ المطلوب"].sum()))
                tc2.metric("✅ إجمالي المدفوع", money(history["المدفوع"].sum()))
                tc3.metric("⏳ الرصيد المتبقي", money(max(history["المتبقي"].sum(), 0)))
            else:
                st.info("لا توجد فواتير لهذه الطالبة.")

            trans_df = load_df("transactions")
            if not trans_df.empty:
                st.write("### 💵 سجل الحركات المالية")
                st.dataframe(trans_df[trans_df["الطالبة"] == sel].sort_values("التاريخ", ascending=False),
                             use_container_width=True, hide_index=True)


# ============================================================
#  8) التقارير الشاملة
# ============================================================
elif choice == "📈 التقارير الشاملة":
    st.subheader("📈 التقارير الشاملة")
    att_df, pay_df = load_df("attendance"), load_df("payments")

    tab1, tab2, tab3 = st.tabs(["💰 التقرير المالي", "✅ تقرير الحضور", "⬇️ تصدير البيانات"])

    with tab1:
        if pay_df.empty:
            st.info("لا توجد بيانات مالية.")
        else:
            st.write("### ملخص التحصيل الشهري")
            fin = pay_df.groupby("الشهر").agg(
                المطلوب=("المبلغ المطلوب", "sum"),
                المحصل=("المدفوع", "sum"),
                الفواتير=("الطالبة", "count"),
                المسددة=("حالة الدفع", lambda x: (x == "مدفوع").sum()),
            ).reset_index()
            fin["المتبقي"] = fin["المطلوب"] - fin["المحصل"]
            fin["نسبة التحصيل %"] = (fin["المحصل"] / fin["المطلوب"] * 100).round(1)
            st.dataframe(fin.sort_values("الشهر", ascending=False), use_container_width=True, hide_index=True)
            st.bar_chart(fin.set_index("الشهر")[["المحصل", "المتبقي"]])

            st.write("### أكثر الطالبات تأخرًا")
            late = pay_df[pay_df["حالة الدفع"] != "مدفوع"].groupby("الطالبة").agg(
                عدد_الأشهر_المتأخرة=("الشهر", "count"),
                إجمالي_المتبقي=("المتبقي", "sum")).reset_index().sort_values("إجمالي_المتبقي", ascending=False)
            st.dataframe(late, use_container_width=True, hide_index=True) if not late.empty else st.success("🎉 لا توجد متأخرات.")

    with tab2:
        if att_df.empty:
            st.info("لا توجد سجلات حضور.")
        else:
            att_df = att_df.copy()
            att_df["التاريخ"] = pd.to_datetime(att_df["التاريخ"])
            c1, c2 = st.columns(2)
            d1 = c1.date_input("من تاريخ", value=att_df["التاريخ"].min().date())
            d2 = c2.date_input("إلى تاريخ", value=att_df["التاريخ"].max().date())
            period = att_df[(att_df["التاريخ"] >= pd.Timestamp(d1)) & (att_df["التاريخ"] <= pd.Timestamp(d2))]

            st.write("### الحضور حسب المسار")
            st.dataframe(period.groupby(["المسار", "الحالة"]).size().unstack(fill_value=0), use_container_width=True)

            st.write("### نسبة الحضور لكل طالبة")
            per = period.groupby("الطالبة")["الحالة"].agg(
                حضور=lambda x: (x == "حاضرة").sum(),
                غياب=lambda x: (x == "غائبة").sum(),
                اعتذار=lambda x: (x == "معتذرة").sum()).reset_index()
            per["إجمالي"] = per["حضور"] + per["غياب"] + per["اعتذار"]
            per["نسبة الحضور %"] = (per["حضور"] / per["إجمالي"] * 100).round(1)
            st.dataframe(per.sort_values("نسبة الحضور %"), use_container_width=True, hide_index=True)

    with tab3:
        for key, label in [("buses", "الحافلات"), ("drivers", "السائقون"), ("routes", "المسارات"),
                           ("students", "الطالبات"), ("attendance", "الحضور"),
                           ("payments", "الاشتراكات"), ("transactions", "الحركات المالية")]:
            df = load_df(key)
            if not df.empty:
                st.download_button(f"⬇️ تصدير {label}", df.to_csv(index=False).encode("utf-8-sig"),
                                   f"{key}_report.csv", "text/csv")
