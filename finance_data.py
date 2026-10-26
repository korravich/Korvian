# FILE: finance_data.py | OWNER: #3 | VERSION: 0 | BASE: - | DATE: 2026-10-24
# CHANGES: v0 ย้ายเนื้อหาจาก views.py/db.py ไม่เปลี่ยนพฤติกรรม (เขียนโดย mr1)
"""Korvian: ข้อมูลการเงินทั้งหมด (ผู้เล่น, รายรับ-รายจ่าย, รวมยอดรายเดือน, ข้อมูลกราฟ)

จุดเชื่อม: init_player_state(uid), reset_user_data(uid)
"""
from datetime import timedelta

import pandas as pd
import streamlit as st

import db_core
import theme


# ==========================================
# ข้อมูลผู้เล่น
# ==========================================

def init_player_state(uid):
    """โหลดข้อมูลผู้เล่นเข้า session_state (ทำครั้งเดียวต่อการล็อกอิน)
    ถ้าพลาด จะ raise error ให้ฝั่งเรียกใช้แสดงข้อความ"""
    if "fin_player_loaded" in st.session_state:
        return

    sb = db_core.get_client()

    response = sb.table("player_data").select("*").eq("user_id", uid).execute()

    if response.data:
        player = response.data[0]
    else:
        player = {
            "user_id": uid,
            "balance": 0,
            "goal": "0",
            "item": "สิ่งที่อยากได้",
        }
        sb.table("player_data").insert(player).execute()

    st.session_state.balance = float(player["balance"])
    st.session_state.goal = float(player["goal"])
    st.session_state.item_name = player["item"]
    st.session_state.fin_player_loaded = True

    # รวมยอดเก่าเข้ารายเดือน (ทำครั้งเดียวตอนเปิดแอป)
    try:
        compact_old_records(uid)
    except Exception as e:
        st.warning(f"รวมยอดข้อมูลเก่าไม่สำเร็จ: {e}")


def clear_history(uid):
    """ล้างประวัติรายรับ-รายจ่ายทั้งหมด (รายวัน + รายเดือน)"""
    sb = db_core.get_client()
    sb.table("daily_records").delete().eq("user_id", uid).execute()
    sb.table("monthly_records").delete().eq("user_id", uid).execute()


def reset_user_data(uid):
    """รีเซ็ตข้อมูลการเงินทั้งหมด (จุดเชื่อมข้อ 8) ถ้าขั้นใดพลาดให้ raise
    ห้ามแสดง UI / st.rerun ที่นี่"""
    # ล้างประวัติก่อน (ถ้าพลาด จะยังไม่รีเซ็ตส่วนอื่น)
    clear_history(uid)

    db_core.get_client().table("player_data").update({
        "balance": 0,
        "goal": "0",
        "item": "สิ่งที่อยากได้",
    }).eq("user_id", uid).execute()

    st.session_state.balance = 0.0
    st.session_state.goal = 0.0
    st.session_state.item_name = "สิ่งที่อยากได้"


# ==========================================
# รายรับ-รายจ่าย
# ==========================================

def compact_old_records(uid):
    """รวมยอดรายวันที่เก่ากว่า 30 วันเข้ารายเดือน แล้วลบแถวรายวันทิ้ง"""
    sb = db_core.get_client()
    cutoff = theme.today_th() - timedelta(days=30)

    old = (
        sb.table("daily_records")
        .select("record_date, income, expense")
        .eq("user_id", uid)
        .lt("record_date", cutoff.isoformat())
        .execute()
    )
    if not old.data:
        return

    # รวมยอดแยกตามเดือน
    totals = {}
    for row in old.data:
        month_key = row["record_date"][:7] + "-01"   # เช่น 2026-09-01
        t = totals.setdefault(month_key, {"income": 0.0, "expense": 0.0})
        t["income"] += float(row["income"])
        t["expense"] += float(row["expense"])

    # บวกทบเข้ารายเดือน (ถ้าเดือนนั้นมีอยู่แล้ว)
    for month_key, t in totals.items():
        existing = (
            sb.table("monthly_records")
            .select("income, expense")
            .eq("user_id", uid)
            .eq("month", month_key)
            .execute()
        )
        old_inc = float(existing.data[0]["income"]) if existing.data else 0.0
        old_exp = float(existing.data[0]["expense"]) if existing.data else 0.0

        sb.table("monthly_records").upsert({
            "user_id": uid,
            "month": month_key,
            "income": old_inc + t["income"],
            "expense": old_exp + t["expense"],
        }).execute()

    # ลบแถวรายวันที่รวมแล้ว (ลบหลังรวมสำเร็จเท่านั้น)
    sb.table("daily_records") \
        .delete() \
        .eq("user_id", uid) \
        .lt("record_date", cutoff.isoformat()) \
        .execute()


def load_daily_range(uid, days):
    """ดึงรายรับ-รายจ่ายรายวันย้อนหลัง days วัน (วันที่ไม่มีข้อมูลเป็น 0)"""
    today = theme.today_th()
    start = today - timedelta(days=days - 1)

    res = (
        db_core.get_client().table("daily_records")
        .select("record_date, income, expense")
        .eq("user_id", uid)
        .gte("record_date", start.isoformat())
        .lte("record_date", today.isoformat())
        .execute()
    )
    data = {r["record_date"]: r for r in res.data}

    rows = []
    for i in range(days):
        d = start + timedelta(days=i)
        r = data.get(d.isoformat())
        rows.append({
            "วันที่": pd.Timestamp(d),
            "รายรับ": float(r["income"]) if r else 0.0,
            "รายจ่าย": float(r["expense"]) if r else 0.0,
        })
    return pd.DataFrame(rows).set_index("วันที่")


def load_monthly(uid):
    """ดึงสรุปรายเดือน (ข้อมูลที่เก่ากว่า 30 วัน)"""
    res = (
        db_core.get_client().table("monthly_records")
        .select("month, income, expense")
        .eq("user_id", uid)
        .order("month")
        .execute()
    )
    rows = [{
        "เดือน": pd.Timestamp(r["month"]),
        "รายรับ": float(r["income"]),
        "รายจ่าย": float(r["expense"]),
    } for r in res.data]
    if not rows:
        return pd.DataFrame(columns=["รายรับ", "รายจ่าย"])
    return pd.DataFrame(rows).set_index("เดือน")


def add_balance_daily(df, current_balance):
    """เติมคอลัมน์ 'เงินเก็บ' (ยอด ณ สิ้นวัน) โดยคำนวณย้อนจากยอดปัจจุบัน"""
    out = df.copy()
    net = out["รายรับ"] - out["รายจ่าย"]
    after = net[::-1].cumsum()[::-1] - net      # ผลรวมสุทธิของวันหลังจากวันนั้น
    out["เงินเก็บ"] = current_balance - after
    return out


def add_balance_monthly(uid, df, current_balance):
    """เติมคอลัมน์ 'เงินเก็บ' (ยอด ณ สิ้นเดือน) สำหรับกราฟรายเดือน"""
    res = (
        db_core.get_client().table("daily_records")
        .select("record_date, income, expense")
        .eq("user_id", uid)
        .execute()
    )
    daily = [
        (pd.Timestamp(r["record_date"]), float(r["income"]) - float(r["expense"]))
        for r in res.data
    ]

    out = df.copy()
    net_m = out["รายรับ"] - out["รายจ่าย"]
    later_months = net_m[::-1].cumsum()[::-1] - net_m

    values = []
    for month, later in later_months.items():
        month_end = month + pd.offsets.MonthEnd(0)
        daily_after = sum(n for d, n in daily if d > month_end)
        values.append(current_balance - later - daily_after)

    out["เงินเก็บ"] = values
    return out
