# FILE: app.py | OWNER: #1 | VERSION: 1 | BASE: 0 | DATE: 2026-10-24
# CHANGES: v1 แยกจากไฟล์ v0 (app.py v0: ตั้งค่าหน้า + ลำดับตามข้อ 8 หน้าล็อกอินย้ายไป auth.py)
"""Korvian: ไฟล์หลัก (จุดเริ่มต้นของแอป)

ลำดับตามจุดเชื่อมข้อ 8 ของเอกสารกลาง
"""
import os

import streamlit as st
from PIL import Image

import auth
import finance_data
import health
import page_money
import page_summary
import sidebar
import study

# ไอคอนแท็บเบราว์เซอร์ (ถ้าหาไฟล์ไม่เจอ ใช้อิโมจิแทน)
try:
    _icon = Image.open(os.path.join(os.path.dirname(__file__), "korvian_icon.png"))
except Exception:
    _icon = "🌀"

# 1) ต้องเป็นคำสั่ง Streamlit คำสั่งแรกของแอป
st.set_page_config(
    page_title="Korvian",
    page_icon=_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(
    "<style>[data-testid='stMainBlockContainer'], .block-container "
    "{ padding-bottom: 4rem !important; }</style>",
    unsafe_allow_html=True
)

# เมนูแต่ละอันไปที่ฟังก์ชันไหน (key ต้องตรงกับ MENU_ITEMS ใน sidebar.py)
PAGES = {
    "summary": page_summary.render,
    "money": page_money.render,
    "health": health.render,
    "study": study.render,
}

# 2) คืนสถานะล็อกอิน (สร้าง CookieController + restore_login + set_session)
auth.restore_session()

# 3) ยังไม่ล็อกอิน ห้ามแสดงส่วนเกมด้านล่าง
if "user_id" not in st.session_state:
    auth.render_login()
    st.stop()

# 4) ตั้งค่า session_state: balance, goal, item_name
try:
    finance_data.init_player_state(st.session_state["user_id"])
except Exception as e:
    st.error(f"โหลดข้อมูลไม่สำเร็จ: {e}")
    st.stop()

# 5) sidebar (เมนู + กล่องบัญชี) คืน key ของหน้า  6) แสดงหน้านั้น
page = sidebar.render()
PAGES[page]()
