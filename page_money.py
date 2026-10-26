# FILE: page_money.py | OWNER: #3 | VERSION: 0 | BASE: - | DATE: 2026-10-24
# CHANGES: v0 ย้ายเนื้อหาจาก views.py/db.py ไม่เปลี่ยนพฤติกรรม (เขียนโดย mr1)
"""Korvian: หน้า Money Line"""
from datetime import timedelta

import streamlit as st

import db_core
import finance_data
import theme


def render():
    st.subheader("💰 Money Line: วางแผนการเงินเพื่อเป้าหมาย")

    ss = st.session_state
    sb = db_core.get_client()
    uid = ss["user_id"]

    # ----- เป้าหมาย -----
    item = st.text_input(
        "คุณกำลังเก็บเงินไปเพื่อซื้ออะไร? (เช่น หูฟัง, เกม):",
        value=ss.item_name
    )
    target_goal = st.number_input(
        "ของชิ้นนั้นราคากี่บาท?:",
        min_value=0.0,
        value=ss.goal,
        step=100.0
    )

    if st.button("บันทึกเป้าหมายการซื้อของ"):
        try:
            sb.table("player_data").update({
                "item": item,
                "goal": str(target_goal)
            }).eq("user_id", uid).execute()

            ss.item_name = item
            ss.goal = target_goal
            st.success("บันทึกข้อมูลเป้าหมายใหม่เรียบร้อยแล้ว!")

        except Exception as e:
            st.error(f"บันทึกเป้าหมายไม่สำเร็จ: {e}")

    # ----- รายรับ-รายจ่าย -----
    st.write("---")
    st.write("### บันทึกรายรับ-รายจ่าย")

    today = theme.today_th()
    record_date = st.date_input(
        "วันที่",
        value=today,
        min_value=today - timedelta(days=30),
        max_value=today
    )
    income = st.number_input("ได้เงินกี่บาท💰:", min_value=0.0, value=0.0)
    expense = st.number_input("ใช้จ่ายกี่บาท💸:", min_value=0.0, value=0.0)

    if st.button("คำนวณและบันทึกยอดเงิน"):
        if income == 0 and expense == 0:
            st.warning("กรุณากรอกรายรับหรือรายจ่ายอย่างน้อยหนึ่งช่อง")
        else:
            try:
                # 1) บันทึกลง daily_records (ถ้ามีวันนั้นอยู่แล้วให้บวกทบ)
                existing = (
                    sb.table("daily_records")
                    .select("income, expense")
                    .eq("user_id", uid)
                    .eq("record_date", record_date.isoformat())
                    .execute()
                )
                old_income = float(existing.data[0]["income"]) if existing.data else 0.0
                old_expense = float(existing.data[0]["expense"]) if existing.data else 0.0

                sb.table("daily_records").upsert({
                    "user_id": uid,
                    "record_date": record_date.isoformat(),
                    "income": old_income + income,
                    "expense": old_expense + expense
                }).execute()

                # 2) อัปเดตยอดเงินเก็บปัจจุบัน
                new_balance = ss.balance + income - expense
                sb.table("player_data").update({
                    "balance": new_balance
                }).eq("user_id", uid).execute()

                ss.balance = new_balance
                st.success(
                    "บันทึกเรียบร้อยแล้ว! "
                    "ลองกลับไปดูหน้าแรกเพื่อเช็กยอดเงิน"
                )

            except Exception as e:
                st.error(f"บันทึกยอดเงินไม่สำเร็จ: {e}")

    # ----- ล้างเงินเก็บ -----
    st.write("---")
    st.subheader("🧹 จัดการเงินเก็บ")

    if st.button("ล้างเงินเก็บ", key="fin_reset_balance"):
        ss["fin_show_reset_balance_confirm"] = True

    if ss.get("fin_show_reset_balance_confirm", False):
        st.warning(
            "⚠️ คุณกำลังจะตั้งยอดเงินเก็บเป็น 0 บาท และล้างประวัติรายรับ-รายจ่าย "
            "(รวมกราฟ) ทั้งหมด การดำเนินการนี้ไม่สามารถย้อนกลับได้ "
            "แต่ชื่อเป้าหมายและราคาเป้าหมายจะไม่ถูกลบ"
        )

        confirm_col, cancel_col = st.columns(2)

        with confirm_col:
            if st.button("ยืนยันล้างเงินเก็บ", key="fin_btn_confirm_reset_balance"):
                try:
                    # ล้างประวัติก่อน เพื่อให้เส้นเงินเก็บเริ่มนับใหม่จาก 0
                    finance_data.clear_history(uid)
                    sb.table("player_data").update({
                        "balance": 0
                    }).eq("user_id", uid).execute()

                    ss.balance = 0.0
                    ss["fin_show_reset_balance_confirm"] = False
                    st.success("ล้างเงินเก็บเรียบร้อยแล้ว!")
                    st.rerun()

                except Exception as e:
                    st.error(f"ล้างเงินเก็บไม่สำเร็จ: {e}")

        with cancel_col:
            if st.button("ยกเลิก", key="fin_btn_cancel_reset_balance"):
                ss["fin_show_reset_balance_confirm"] = False
                st.rerun()

    st.caption(
        "หมายเหตุ: ปุ่มนี้จะล้างยอดเงินเก็บและประวัติรายรับ-รายจ่ายของบัญชีที่เข้าสู่ระบบ "
        "ไม่ลบชื่อสิ่งของหรือราคาเป้าหมาย"
    )
