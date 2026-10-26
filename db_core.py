# FILE: db_core.py | OWNER: #1 | VERSION: 1 | BASE: 0 | DATE: 2026-10-24
# CHANGES: v1 แยกจากไฟล์ v0 (db.py: admin_client -> get_service_client, user_client -> get_client)
"""Korvian: ตัวเชื่อม Supabase (ที่เดียวที่แตะ st.secrets และ create_client)

สำคัญ: ห้ามเก็บ client ของผู้ใช้ไว้ในตัวแปรระดับไฟล์ (module level) และห้ามใช้
st.cache_resource กับ get_client() ไฟล์ที่ถูก import แล้วจะถูกใช้ร่วมกันทุกผู้ใช้
จึงเก็บใน st.session_state (แยกตามผู้ใช้) เท่านั้น
ไฟล์นี้ห้าม import ไฟล์อื่นของโปรเจกต์
"""
import streamlit as st
from supabase import create_client


@st.cache_resource
def get_service_client():
    """service role: ไม่มี session ผู้ใช้ติดอยู่ จึงใช้ร่วมกันได้อย่างปลอดภัย
    ใช้ได้เฉพาะ auth.py"""
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_SERVICE_ROLE_KEY"],
    )


def get_client():
    """client ของผู้ใช้ เก็บแยกตาม session ของแต่ละคน
    ไม่ set_session ที่นี่ (set_session ทำที่ auth.restore_session() เท่านั้น)"""
    if "sb_client" not in st.session_state:
        st.session_state["sb_client"] = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"],
        )
    return st.session_state["sb_client"]
