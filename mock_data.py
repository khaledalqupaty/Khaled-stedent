# mock_data.py
# يمكن تشغيله مرة واحدة لملء بيانات اضافية

import sqlite3, pathlib

DB_FILE = pathlib.Path("bus_data/db.sqlite")
conn = sqlite3.connect(DB_FILE, check_same_thread=False)

# طالبات إضافية
students_add = [
    ("ريم","104","حي الياسمين","0566666666","انتظار"),
    ("نورا","105","حي الربيع","0577777777","تم الدفع"),
    ("جوري","106","حي النخيل","0588888888","انتظار"),
]

# سائقون إضافيون
drivers_add = [
    ("فهد خالد","باص 3","0555555555",18),
    ("سعيد أحمد","باص 4","0544444444",16),
]

conn.executemany("INSERT OR IGNORE INTO students(name,sid,loc,phone,status) VALUES(?,?,?,?,?)", students_add)
conn.executemany("INSERT OR IGNORE INTO drivers(name,bus_no,phone,capacity) VALUES(?,?,?,?)", drivers_add)
conn.commit()
print("✅ تمت إضافة البيانات الإضافية")
