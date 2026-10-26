# FILE: page_summary.py | OWNER: #3 | VERSION: 0 | BASE: - | DATE: 2026-10-24
# CHANGES: v0 ย้ายเนื้อหาจาก views.py/db.py ไม่เปลี่ยนพฤติกรรม (เขียนโดย mr1)
"""Korvian: หน้าสรุปผล"""
import random

import streamlit as st

import charts
import finance_data


def _goal_message(name, far):
    """สุ่มข้อความให้กำลังใจตามความคืบหน้า (far = เงินที่ยังขาดถึงเป้า)"""
    if far > 0:
        messages = [
            f"คุณยังขาดเงินอีก {far:,.2f} บาทนะ แล้ว **{name}** ที่คุณอยากได้ล่ะ?",
            f"ขาดอีกแค่ {far:,.2f} บาทเองงงง อีกนิดเดียวก็ได้แล้ว 🤏🤏",
            f"เอ้าท่องพร้อมกันนน เพื่อ **{name}** เพื่อ **{name}** เพื่อ **{name}** 😀",
            "อย่าเพิ่งยอมแพ้ ความสำเร็จมันต้องใช้เวลานะ! 👊",
            "วันนี้อาจยังไม่ถึง แต่คุณต้องทำได้แน่!",
            f"ลำบากตอนนี้ เดี๋ยวตอนได้ **{name}** ก็สบายแล้ววว 😣😣",
        ]
    elif far == 0:
        messages = [
            f"เย้!! คุณสามารถซื้อ **{name}** ได้แล้ว 🎉🎉",
            "ยินดีด้วยยยย คุณทำสำเร็จแล้ว!",
            "ได้แล้วววว นี่แหละชัยชนะ ฮ่าฮ่าฮ่า",
            f"เห็นมั้ยล่ะ **{name}** อยู่ใกล้แค่เอื้อมเท่านั้นแหละ",
            "สบายมาก 💪💪",
            "ได้เวลาสำหรับของชิ้นต่อไปแล้ว 🤩🤩",
        ]
    else:
        over = -far
        messages = [
            f"ตอนนี้คุณสามารถซื้อ **{name}** ได้เป็นร้อยอันแล้วม้าง",
            "คุณนี่อัจฉริยะด้านการเก็บเงินชัดๆ!!",
            f"ทำได้แล้วว และยังมีเงินเกินมาอีกตั้ง {over:,.2f} บาทแหละ",
            f"เห็นมั้ยล่ะ **{name}** อยู่ใกล้แค่เอื้อมเท่านั้นแหละ",
            "สบายมาก 💪💪",
            "คุณมีเงินเกินแล้ว ซื้อได้ทั้งบริษัทแล้วมั้งเนี่ย 💰",
            "อนาคตเศรษฐีพันล้านรึป่าวเนี่ยย 💸💸",
        ]
    return random.choice(messages)


def _chart_section():
    st.write("---")
    st.subheader("📊 รายรับ-รายจ่าย")

    period = st.radio(
        "ช่วงเวลา",
        ["7 วัน", "30 วัน", "รายเดือน"],
        horizontal=True,
        label_visibility="collapsed"
    )

    try:
        uid = st.session_state["user_id"]
        balance = st.session_state.balance
        goal = st.session_state.goal
        goal_name = st.session_state.item_name

        if period == "รายเดือน":
            df = finance_data.load_monthly(uid)
            if df.empty:
                st.info(
                    "ยังไม่มีสรุปรายเดือน "
                    "ข้อมูลจะถูกรวมเป็นรายเดือนเมื่อเก่ากว่า 30 วัน"
                )
            else:
                chart_df = finance_data.add_balance_monthly(uid, df, balance)
                charts.show_bar_chart(chart_df, monthly=True, goal=goal, goal_name=goal_name)

                table = df.copy()
                table.index = table.index.strftime("%m/%Y")
                table["คงเหลือ"] = table["รายรับ"] - table["รายจ่าย"]
                st.dataframe(table, use_container_width=True)
        else:
            days = 7 if period == "7 วัน" else 30
            df = finance_data.load_daily_range(uid, days)

            total_in = df["รายรับ"].sum()
            total_out = df["รายจ่าย"].sum()

            c1, c2, c3 = st.columns(3)
            c1.metric("รายรับรวม", f"{total_in:,.2f}")
            c2.metric("รายจ่ายรวม", f"{total_out:,.2f}")
            c3.metric("สุทธิ", f"{total_in - total_out:,.2f}")

            if total_in == 0 and total_out == 0:
                st.info(f"ใน {days} วันที่ผ่านมายังไม่มีการบันทึก")
            else:
                chart_df = finance_data.add_balance_daily(df, balance)
                charts.show_bar_chart(chart_df, goal=goal, goal_name=goal_name)

    except Exception as e:
        st.error(f"โหลดกราฟไม่สำเร็จ: {e}")


def render():
    st.subheader("🏆 สรุปเป้าหมาย")
    st.write("ยินดีต้อนรับ นี่คือภาพรวมในตอนนี้")

    ss = st.session_state
    st.metric(label="เงินเก็บปัจจุบันของคุณ", value=f"{ss.balance:,.2f} บาท")
    st.text(f"🎯 Goal : {ss.item_name} ราคา {ss.goal:,.2f} บาท")

    if ss.goal > 0:
        st.info(_goal_message(ss.item_name, ss.goal - ss.balance))

    _chart_section()
