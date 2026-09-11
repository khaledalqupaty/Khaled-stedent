# -*- coding: utf-8 -*-
"""
🚌 نظام تشغيل نقل الطالبات اليومي — الإصدار 3.0
الفكرة: توزيع الطالبات على السيارات صباح كل يوم + إرسال المواقع للسائق واتساب
• إدارة الطالبات مع مواقع Google Maps وإحداثيات GPS
• إدارة السائقين والمركبات
• شاشة توزيع يومية (سحب/تحديد متعدد) مع ترتيب تلقائي جغرافي (أقرب مسار)
• إرسال واتساب بنقرة واحدة عبر wa.me (بدون API مدفوع)
• أرشيف الرحلات + عدد الركاب لكل سيارة
التشغيل: streamlit run school_dispatch_v3.py
"""
import os
import math
import urllib.parse
import pandas as pd
import streamlit as st
from datetime import date

DATA_DIR = "data_v3"
FILES = {
    "students": ("students.csv", ["الطالبة", "رقم ولي الأمر", "رقم المنزل",
                                   "رابط الموقع", "خط العرض", "خط الطول", "ملاحظات", "نشطة"]),
    "drivers":  ("drivers.csv",  ["السائق", "رقم الجوال (واتساب)"]),
    "vehicles": ("vehicles.csv", ["المركبة", "اللوحة", "السعة"]),
    "trips":    ("trips.csv",    ["التاريخ", "المركبة", "السائق", "الطالبة",
                                  "الترتيب", "خط العرض", "خط الطول", "حالة الركوب"]),
}


def init_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    for fname, cols in FILES.values():
        p = os.path.join(DATA_DIR, fname)
        if not os.path.exists(p):
            pd.DataFrame(columns=cols).to_csv(p, index=False, encoding="utf-8-sig")


def load_df(key):
    p = os.path.join(DATA_DIR, FILES[key][0])
    if not os.path.exists(p):
        return pd.DataFrame(columns=FILES[key][1])
    df = pd.read_csv(p, encoding="utf-8-sig")
    for c in FILES[key][1]:
        if c not in df.columns:
            df[c] = ""
    # منع مشاكل الأنواع عند الإدخال النصي في أعمدة رقمية فارغة
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].astype("object")
    return df[FILES[key][1]]


def save_df(key, df):
    df.to_csv(os.path.join(DATA_DIR, FILES[key][0]), index=False, encoding="utf-8-sig")


def parse_coords(link):
    """استخراج الإحداثيات من رابط Google Maps (أي صيغة شائعة)."""
    link = str(link).strip()
    try:
        if "?q=" in link:
            q = link.split("?q=")[1].split("&")[0]
            lat, lon = q.split(",")[:2]
            return float(lat), float(lon)
        if "/@" in link:
            part = link.split("@")[1].split(",")
            return float(part[0]), float(part[1])
    except Exception:
        pass
    return None, None


def haversine(a, b):
    R = 6371.0
    la1, lo1, la2, lo2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def order_route(coords, start=None):
    """ترتيب نقاط التوقف بالجشع (أقرب جار) بدءًا من المدرسة أو أول نقطة."""
    pts = list(coords.items())
    if not pts:
        return []
    if start is None:
        # نقطة البداية = أقصى نقطة جنوبًا غربًا (ناحية وسط المدينة غالبًا)
        start = (min(p[1][0] for p in pts), min(p[1][1] for p in pts))
    remaining = pts[:]
    ordered = []
    cur = start
    while remaining:
        nxt = min(remaining, key=lambda p: haversine(cur, p[1]))
        ordered.append(nxt[0])
        cur = nxt[1]
        remaining.remove(nxt)
    return ordered


init_data()

st.set_page_config(page_title="نظام تشغيل نقل الطالبات", page_icon="🚌",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
    html, body, [class*="css"], .stMarkdown, label, input, select, textarea {
        font-family: 'Tajawal', sans-serif !important; direction: rtl; text-align: right; }
    .hero { background: linear-gradient(135deg, #065f46 0%, #059669 55%, #10b981 100%);
        padding: 24px 32px; border-radius: 18px; margin-bottom: 18px;
        box-shadow: 0 10px 30px rgba(5,150,105,.28); }
    .hero-title { color: #fff; font-size: 1.8rem; font-weight: 800; }
    .hero-sub { color: #d1fae5; font-size: .95rem; margin-top: 6px; }
    .section-title { font-size: 1.15rem; font-weight: 800; color: #065f46;
        border-right: 5px solid #10b981; padding-right: 12px; margin: 18px 0 10px; }
    div[data-testid="stMetric"] { background: #fff; border: 1px solid #e5e7eb;
        border-radius: 14px; padding: 12px 18px; box-shadow: 0 2px 10px rgba(0,0,0,.05); }
    div[data-testid="stMetricValue"] { color: #065f46; font-weight: 800; }
    .stButton > button { border-radius: 10px; font-weight: 700; border: none;
        background: linear-gradient(135deg, #059669, #10b981); color: #fff;
        box-shadow: 0 3px 10px rgba(5,150,105,.3); }
    .wa-btn a { display: inline-block; background: #25d366; color: #fff !important;
        font-weight: 800; padding: .6rem 1.6rem; border-radius: 12px; text-decoration: none; }
</style>
""", unsafe_allow_html=True)


def section_title(t):
    st.markdown(f'<div class="section-title">{t}</div>', unsafe_allow_html=True)


st.markdown("""
<div class="hero">
    <div class="hero-title">🚌 نظام تشغيل نقل الطالبات اليومي</div>
    <div class="hero-sub">الإصدار 3.0 &nbsp;•&nbsp; توزيع صباحي على السيارات &nbsp;•&nbsp; ترتيب أقرب مسار تلقائي &nbsp;•&nbsp; إرسال واتساب للسائق &nbsp;•&nbsp; أرشيف الرحلات</div>
</div>
""", unsafe_allow_html=True)

menu = ["🚐 التوزيع الصباحي", "👩‍🎓 الطالبات والمواقع", "🧑‍✈️ السائقون", "🚗 المركبات", "🗂️ أرشيف الرحلات"]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)
st.sidebar.markdown("""
<div style="background:#fff;border-radius:12px;padding:14px;border:1px solid #d1fae5;">
<b style="color:#065f46;">💡 طريقة العمل اليومية</b><br>
١) أضف الطالبات مع روابط مواقعها<br>
٢) في «التوزيع الصباحي» حدد من ركبت كل سيارة<br>
٣) اضغط «إرسال للسائق» — يفتح واتساب بالمسار مرتبًا جاهزًا للإرسال
</div>
""", unsafe_allow_html=True)


# ============================================================
#  1) التوزيع الصباحي
# ============================================================
if choice == "🚐 التوزيع الصباحي":
    students_df = load_df("students")
    active = students_df[students_df["نشطة"].astype(str) == "نعم"] if not students_df.empty else students_df
    drivers_df = load_df("drivers")
    vehicles_df = load_df("vehicles")
    trips_df = load_df("trips")

    if active.empty or vehicles_df.empty:
        st.warning("⚠️ أضف طالبات (بمواقعها) ومركبات أولًا من القوائم الجانبية.")
    else:
        trip_date = str(st.date_input("📅 تاريخ الرحلة", value=date.today()))
        assigned_today = set(trips_df[trips_df["التاريخ"] == trip_date]["الطالبة"].tolist()) if not trips_df.empty else set()

        section_title("🚐 توزيع الطالبات على المركبات")
        st.caption("حدد الطالبات لكل مركبة ثم اضغط «تثبيت التوزيع» — يُرتب المسار تلقائيًا بالأقرب جغرافيًا.")

        col_a, col_b = st.columns([2, 1])
        with col_b:
            section_title("👥 الطالبات المتاحات")
            st.caption(f"المتبقي بدون تخصيص: {len(set(active['الطالبة']) - assigned_today)}")
            st.dataframe(active[["الطالبة"]], use_container_width=True, hide_index=True)

        with col_a:
            assignments = {}
            for _, veh in vehicles_df.iterrows():
                cap = int(pd.to_numeric(pd.Series([veh["السعة"]]), errors="coerce")[0] or 0)
                drv_list = drivers_df["السائق"].tolist() if not drivers_df.empty else []
                with st.expander(f"🚗 {veh['المركبة']} — {veh['اللوحة']}", expanded=True):
                    c1, c2 = st.columns(2)
                    drv = c1.selectbox("السائق", drv_list, key=f"drv_{veh['المركبة']}") if drv_list else c1.text_input("السائق", key=f"drv_{veh['المركبة']}")
                    already = sorted(set(active["الطالبة"]) & assigned_today)
                    picked = c2.multiselect("الركاب", sorted(active["الطالبة"].tolist()),
                                            default=already, key=f"pick_{veh['المركبة']}")
                    if cap and len(picked) > cap:
                        st.error(f"⚠️ عدد الركاب ({len(picked)}) يتجاوز السعة ({cap})")
                    if picked:
                        sub = active[active["الطالبة"].isin(picked)][["الطالبة", "خط العرض", "خط الطول"]]
                        coords = {r["الطالبة"]: (float(r["خط العرض"]), float(r["خط الطول"]))
                                  for _, r in sub.iterrows()
                                  if pd.notna(pd.to_numeric(pd.Series([r["خط العرض"]]), errors="coerce")[0])}
                        if len(coords) == len(picked):
                            ordered = order_route(coords)
                            st.success("🔢 الترتيب المقترح: " + " ← ".join(ordered))
                            phone = ""
                            m = drivers_df[drivers_df["السائق"] == drv]
                            if not m.empty:
                                phone = str(m.iloc[0]["رقم الجوال (واتساب)"]).replace("+", "").replace(" ", "")
                            if phone:
                                lines = [f"🚌 رحلة {trip_date} — {veh['المركبة']}", ""]
                                for i, nme in enumerate(ordered, 1):
                                    link = active[active["الطالبة"] == nme]["رابط الموقع"].iloc[0]
                                    lines.append(f"{i}- {nme}")
                                    lines.append(str(link))
                                wa = "https://wa.me/" + phone + "?text=" + urllib.parse.quote("\n".join(lines))
                                st.markdown(f'<div class="wa-btn"><a href="{wa}" target="_blank">📲 إرسال المسار للسائق واتساب</a></div>', unsafe_allow_html=True)
                            else:
                                st.caption("أضف رقم جوال السائق لتفعيل زر واتساب.")
                        else:
                            st.info("بعض الركاب بدون إحداثيات — أكمل مواقعهم ليتم الترتيب التلقائي.")
                    assignments[veh["المركبة"]] = (veh, drv, picked)

            if st.button("💾 تثبيت التوزيع وأرشفة الرحلة"):
                trips_df = trips_df[trips_df["التاريخ"] != trip_date] if not trips_df.empty else trips_df
                rows = []
                for veh_name, (veh, drv, picked) in assignments.items():
                    if not picked:
                        continue
                    sub = active[active["الطالبة"].isin(picked)][["الطالبة", "خط العرض", "خط الطول"]]
                    coords = {r["الطالبة"]: (float(r["خط العرض"]), float(r["خط الطول"])) for _, r in sub.iterrows()
                              if pd.notna(pd.to_numeric(pd.Series([r["خط العرض"]]), errors="coerce")[0])}
                    ordered = order_route(coords) if len(coords) == len(picked) else picked
                    for i, nme in enumerate(ordered, 1):
                        lat = coords.get(nme, (None, None))[0]
                        lon = coords.get(nme, (None, None))[1]
                        rows.append([trip_date, veh_name, drv, nme, i, lat, lon, "على المتن"])
                trips_df = pd.concat([trips_df, pd.DataFrame(rows, columns=FILES["trips"][1])], ignore_index=True)
                save_df("trips", trips_df)
                st.success(f"✅ تم أرشفة رحلة {trip_date} — {len(rows)} رحلة طالبة.")
                st.rerun()


# ============================================================
#  2) الطالبات والمواقع
# ============================================================
elif choice == "👩‍🎓 الطالبات والمواقع":
    students_df = load_df("students")
    section_title("👩‍🎓 سجل الطالبات والمواقع")
    t1, t2 = st.tabs(["➕ إضافة طالبة", "📋 القائمة والبحث"])

    with t1:
        with st.form("add_student", clear_on_submit=True):
            name = st.text_input("اسم الطالبة *")
            c1, c2 = st.columns(2)
            parent = c1.text_input("رقم ولي الأمر")
            home = c2.text_input("رقم المنزل")
            link = st.text_input("🔗 رابط الموقع (Google Maps — شارك الموقع ثم انسخ الرابط)", 
                                 placeholder="https://maps.google.com/?q=24.71,46.67")
            notes = st.text_input("ملاحظات (مثال: تُستلم من البوابة الشرقية)")
            if st.form_submit_button("💾 حفظ"):
                if not name:
                    st.error("الاسم إلزامي.")
                elif not students_df.empty and name in students_df["الطالبة"].astype(str).values:
                    st.warning("الطالبة مسجلة مسبقًا.")
                else:
                    lat, lon = parse_coords(link)
                    if lat is None:
                        st.warning("⚠️ تعذر استخراج الإحداثيات من الرابط — سيظل الترتيب اليدوي. تأكد أن الرابط يحتوي ?q=خط_العرض,خط_الطول")
                    students_df.loc[len(students_df)] = [name, parent, home, link,
                                                         lat if lat is not None else "", lon if lon is not None else "", notes, "نعم"]
                    save_df("students", students_df)
                    st.success(f"✅ تم حفظ {name}" + ("" if lat is not None else " (بدون إحداثيات)"))
                    st.rerun()

    with t2:
        if students_df.empty:
            st.info("لا توجد طالبات.")
        else:
            q = st.text_input("🔍 بحث")
            view = students_df
            if q:
                view = view[view["الطالبة"].astype(str).str.contains(q, na=False)]
            st.dataframe(view, use_container_width=True, hide_index=True)
            sel = st.selectbox("اختر طالبة", students_df["الطالبة"].tolist())
            c1, c2 = st.columns(2)
            if c1.button("🚫 إيقاف/تفعيل"):
                cur = students_df.loc[students_df["الطالبة"] == sel, "نشطة"].iloc[0]
                students_df.loc[students_df["الطالبة"] == sel, "نشطة"] = "لا" if cur == "نعم" else "نعم"
                save_df("students", students_df)
                st.rerun()
            if c2.button("🗑️ حذف"):
                save_df("students", students_df[students_df["الطالبة"] != sel])
                st.success("✅ تم الحذف.")
                st.rerun()


# ============================================================
#  3) السائقون
# ============================================================
elif choice == "🧑‍✈️ السائقون":
    drivers_df = load_df("drivers")
    section_title("🧑‍✈️ سجل السائقين")
    with st.form("add_driver", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("اسم السائق *")
        phone = c2.text_input("رقم الجوال مع كود الدولة (واتساب) *", placeholder="9665xxxxxxxx")
        if st.form_submit_button("💾 حفظ"):
            if name and phone:
                drivers_df.loc[len(drivers_df)] = [name, phone]
                save_df("drivers", drivers_df)
                st.success(f"✅ تم حفظ {name}")
                st.rerun()
            else:
                st.error("الاسم والجوال إلزاميان.")
    if not drivers_df.empty:
        st.dataframe(drivers_df, use_container_width=True, hide_index=True)
        sel = st.selectbox("حذف سائق", drivers_df["السائق"].tolist())
        if st.button("🗑️ حذف السائق"):
            save_df("drivers", drivers_df[drivers_df["السائق"] != sel])
            st.rerun()


# ============================================================
#  4) المركبات
# ============================================================
elif choice == "🚗 المركبات":
    vehicles_df = load_df("vehicles")
    section_title("🚗 سجل المركبات")
    with st.form("add_veh", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("اسم المركبة *", placeholder="حافلة ١")
        plate = c2.text_input("اللوحة")
        cap = c3.number_input("السعة", min_value=1, max_value=80, value=15)
        if st.form_submit_button("💾 حفظ"):
            if name:
                vehicles_df.loc[len(vehicles_df)] = [name, plate, cap]
                save_df("vehicles", vehicles_df)
                st.success(f"✅ تم حفظ {name}")
                st.rerun()
            else:
                st.error("اسم المركبة إلزامي.")
    if not vehicles_df.empty:
        st.dataframe(vehicles_df, use_container_width=True, hide_index=True)
        sel = st.selectbox("حذف مركبة", vehicles_df["المركبة"].tolist())
        if st.button("🗑️ حذف المركبة"):
            save_df("vehicles", vehicles_df[vehicles_df["المركبة"] != sel])
            st.rerun()


# ============================================================
#  5) أرشيف الرحلات
# ============================================================
elif choice == "🗂️ أرشيف الرحلات":
    trips_df = load_df("trips")
    section_title("🗂️ أرشيف الرحلات — من ركب مع أي سائق ومتى")
    if trips_df.empty:
        st.info("لا توجد رحلات مؤرشفة.")
    else:
        dates = sorted(trips_df["التاريخ"].unique().tolist(), reverse=True)
        d = st.selectbox("التاريخ", dates)
        day = trips_df[trips_df["التاريخ"] == d]
        c1, c2, c3 = st.columns(3)
        c1.metric("🚐 المركبات", day["المركبة"].nunique())
        c2.metric("👩‍🎓 الطالبات المنقولات", len(day))
        c3.metric("🧑‍✈️ السائقون", day["السائق"].nunique())
        st.dataframe(day.sort_values(["المركبة", "الترتيب"]), use_container_width=True, hide_index=True)
        for veh, grp in day.groupby("المركبة"):
            st.download_button(f"⬇️ تصدير رحلة {veh} — {d}",
                               grp.to_csv(index=False).encode("utf-8-sig"),
                               f"trip_{d}_{veh}.csv", "text/csv")

st.markdown('<div style="color:#9ca3af;font-size:.8rem;text-align:center;margin-top:40px;">🚌 نظام تشغيل نقل الطالبات — الإصدار 3.0</div>', unsafe_allow_html=True)
