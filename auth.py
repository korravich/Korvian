# FILE: auth.py | OWNER: #1 | VERSION: 1 | BASE: 0 | DATE: 2026-10-24
# CHANGES: v1 แยกจากไฟล์ v0 (db.py: store_login, save_persistent_session, restore_login, delete_saved_session, apply_session, clear_session_state; app.py: login_screen, _finish_login)
"""Korvian: ล็อกอิน / สมัครสมาชิก / คุกกี้ gq_session / คืนล็อกอิน / ออกจากระบบ

จุดเชื่อม: restore_session(), render_login(), logout()
ห้ามแตะ (เฉพาะ #1): คุกกี้ gq_session และ same_site="none", ตาราง user_sessions
"""
import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone

import streamlit as st
from streamlit_cookies_controller import CookieController

import db_core
import theme

COOKIE_NAME = "gq_session"
SESSION_DAYS = 30


def _controller():
    """CookieController ของรอบนี้ (สร้างใน restore_session ทุกรอบ)"""
    return st.session_state["auth_cookie_ctl"]


def clear_session_state():
    """ล้างทุกอย่างใน session (ใช้ตอนออกจากระบบ กันข้อมูลคนก่อนค้างอยู่)"""
    for key in list(st.session_state.keys()):
        try:
            del st.session_state[key]
        except Exception:
            pass


# ==========================================
# ล็อกอินและล็อกอินค้าง (คุกกี้ + ตาราง user_sessions)
# ==========================================

def store_login(result):
    """เก็บผลการล็อกอิน/สมัครสมาชิกลง session_state"""
    st.session_state["user_id"] = result.user.id
    st.session_state["user_email"] = result.user.email or ""
    st.session_state["access_token"] = result.session.access_token
    st.session_state["refresh_token"] = result.session.refresh_token


def save_persistent_session(cookie_controller, user_id, access_token, refresh_token):
    try:
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)

        db_core.get_service_client().table("user_sessions").insert({
            "user_id": user_id,
            "token_hash": token_hash,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires.isoformat(),
        }).execute()

        cookie_controller.set(
            COOKIE_NAME,
            token,
            max_age=SESSION_DAYS * 24 * 60 * 60,
            secure=True,
            same_site="none",
        )
    except Exception as e:
        st.error(f"บันทึก session ไม่สำเร็จ: {e}")


def _finish_login(cookie_controller, result):
    """เก็บผลล็อกอิน + จำการล็อกอินไว้ในคุกกี้ แล้วรีเฟรชหน้า"""
    store_login(result)
    save_persistent_session(
        cookie_controller,
        result.user.id,
        result.session.access_token,
        result.session.refresh_token
    )


def restore_login(cookie_controller):
    """ถ้ายังไม่ได้ล็อกอินแต่มีคุกกี้ ให้คืนสถานะล็อกอินและต่ออายุ token"""
    cookie_token = cookie_controller.get(COOKIE_NAME)
    if "user_id" in st.session_state or not cookie_token:
        return

    try:
        token_hash = hashlib.sha256(cookie_token.encode()).hexdigest()

        response = (
            db_core.get_service_client().table("user_sessions")
            .select("*")
            .eq("token_hash", token_hash)
            .gt("expires_at", datetime.now(timezone.utc).isoformat())
            .maybe_single()
            .execute()
        )
        saved = response.data if response else None
        if not saved:
            return

        # ใช้ refresh token ขอ token ชุดใหม่ แล้วเก็บทับลงตาราง
        refreshed = db_core.get_client().auth.refresh_session(saved["refresh_token"])
        if refreshed.session and refreshed.user:
            db_core.get_service_client().table("user_sessions").update({
                "access_token": refreshed.session.access_token,
                "refresh_token": refreshed.session.refresh_token,
            }).eq("token_hash", token_hash).execute()

            store_login(refreshed)
    except Exception:
        pass


def delete_saved_session(cookie_token):
    token_hash = hashlib.sha256(cookie_token.encode()).hexdigest()
    db_core.get_service_client().table("user_sessions") \
        .delete() \
        .eq("token_hash", token_hash) \
        .execute()


def apply_session():
    """ใส่ session ของผู้ใช้ให้ client ทุกครั้งที่หน้าเว็บรันใหม่"""
    s = st.session_state
    if all(k in s for k in ("user_id", "access_token", "refresh_token")):
        try:
            db_core.get_client().auth.set_session(s["access_token"], s["refresh_token"])
        except Exception:
            pass


def restore_session():
    """ขั้นแรกของทุกรอบ (หลัง set_page_config):
    (ก) สร้าง CookieController ใหม่ทุกรอบ (ข) คืนล็อกอินจากคุกกี้ (ค) set_session"""
    st.session_state["auth_cookie_ctl"] = CookieController()
    restore_login(_controller())
    apply_session()


def logout():
    """ออกจากระบบ: ลบแถวใน user_sessions -> ลบคุกกี้ -> sign_out -> ล้าง session_state
    -> time.sleep(1) -> st.rerun()"""
    cookie_controller = _controller()
    try:
        cookie_token = cookie_controller.get(COOKIE_NAME)
        if cookie_token:
            delete_saved_session(cookie_token)

        cookie_controller.remove(COOKIE_NAME)
        db_core.get_client().auth.sign_out()
    except Exception:
        pass

    # ล้างทุกอย่างใน session รวมถึงช่องติ๊กสุขภาพ กันข้อมูลคนก่อนค้างอยู่
    clear_session_state()
    time.sleep(1)
    st.rerun()


# ==========================================
# หน้าสมัครสมาชิก / เข้าสู่ระบบ
# ==========================================

def render_login():
    cookie_controller = _controller()

    st.markdown(
        "<div style='display:flex;align-items:center;gap:14px;margin-bottom:4px;'>"
        "<div style='background:#06060a;border-radius:16px;padding:10px;display:flex;'>"
        + theme.logo_svg(44) +
        "</div>"
        "<span style='font-size:44px;font-weight:800;letter-spacing:2px;'>Korvian</span>"
        "</div>",
        unsafe_allow_html=True
    )
    st.caption("Your Future Depends on What You Do Today (v1.1)")
    st.subheader("Start your goals")

    login_tab, signup_tab = st.tabs(["เข้าสู่ระบบ", "สมัครสมาชิก"])

    with login_tab:
        with st.form("auth_login_form"):
            login_email = st.text_input("อีเมล")
            login_password = st.text_input("รหัสผ่าน", type="password")
            login_submit = st.form_submit_button(
                "เข้าสู่ระบบ",
                use_container_width=True
            )

        if login_submit:
            try:
                result = db_core.get_client().auth.sign_in_with_password({
                    "email": login_email.strip(),
                    "password": login_password
                })

                if result.user and result.session:
                    _finish_login(cookie_controller, result)
                    time.sleep(1)
                    st.rerun()

            except Exception:
                st.error("เข้าสู่ระบบไม่สำเร็จ โปรดตรวจสอบอีเมล รหัสผ่าน หรือการยืนยันอีเมล")

    with signup_tab:
        with st.form("auth_signup_form"):
            signup_email = st.text_input("อีเมลสำหรับสมัคร")
            signup_password = st.text_input("ตั้งรหัสผ่าน", type="password")
            signup_password_again = st.text_input("ยืนยันรหัสผ่าน", type="password")
            signup_submit = st.form_submit_button(
                "สมัครสมาชิก",
                use_container_width=True
            )

        if signup_submit:
            if not signup_email.strip():
                st.error("กรุณากรอกอีเมล")
            elif len(signup_password) < 8:
                st.error("รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")
            elif signup_password != signup_password_again:
                st.error("รหัสผ่านทั้งสองช่องไม่ตรงกัน")
            else:
                try:
                    result = db_core.get_client().auth.sign_up({
                        "email": signup_email.strip(),
                        "password": signup_password
                    })

                    if result.session and result.user:
                        _finish_login(cookie_controller, result)
                        st.success("สมัครสมาชิกสำเร็จ!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.success(
                            "ส่งคำขอสมัครแล้ว "
                            "กรุณาตรวจอีเมลเพื่อยืนยันบัญชี "
                            "ก่อนเข้าสู่ระบบ"
                        )

                except Exception as e:
                    st.error(f"สมัครสมาชิกไม่สำเร็จ: {e}")
