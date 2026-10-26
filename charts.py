# FILE: charts.py | OWNER: #3 | VERSION: 0 | BASE: - | DATE: 2026-10-24
# CHANGES: v0 ย้ายเนื้อหาจาก views.py/db.py ไม่เปลี่ยนพฤติกรรม (เขียนโดย mr1)
"""Korvian: กราฟรายรับ-รายจ่าย"""
import altair as alt
import pandas as pd
import streamlit as st


def show_bar_chart(df, monthly=False, goal=0.0, goal_name=""):
    """แท่งรายรับ/รายจ่าย + เส้นเงินเก็บ + เส้นเป้าหมาย ใช้แกนตัวเลขเดียวกัน"""
    data = df.reset_index()
    time_col = data.columns[0]
    data["label"] = data[time_col].dt.strftime("%m/%Y" if monthly else "%d/%m")
    order = list(dict.fromkeys(data["label"]))

    bars_data = data.melt(
        id_vars=[time_col, "label"],
        value_vars=["รายรับ", "รายจ่าย"],
        var_name="ประเภท",
        value_name="จำนวนเงิน"
    )

    has_balance = "เงินเก็บ" in data.columns

    # หาช่วงแกนเดียวที่ครอบคลุมทุกอย่าง เผื่อที่ว่างด้านบน 20%
    tops = [float(bars_data["จำนวนเงิน"].max())]
    lows = [0.0]
    if has_balance:
        tops.append(float(data["เงินเก็บ"].max()))
        lows.append(float(data["เงินเก็บ"].min()))
    if goal > 0:
        tops.append(float(goal))
    top, low = max(tops), min(lows)
    span = top - low
    y_max = top + span * 0.2 if span > 0 else 100
    y_scale = alt.Scale(domain=[low, y_max])

    x_enc = alt.X(
        "label:N", sort=order, title=None,
        axis=alt.Axis(labelAngle=-45)
    )

    bars = (
        alt.Chart(bars_data)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=x_enc,
            xOffset=alt.XOffset("ประเภท:N", sort=["รายรับ", "รายจ่าย"]),
            y=alt.Y("จำนวนเงิน:Q", title="บาท", scale=y_scale),
            color=alt.Color(
                "ประเภท:N",
                scale=alt.Scale(
                    domain=["รายรับ", "รายจ่าย"],
                    range=["#2ECC71", "#E74C3C"]
                ),
                legend=alt.Legend(title=None, orient="top")
            ),
            tooltip=["label", "ประเภท", "จำนวนเงิน"]
        )
    )

    layers = [bars]

    if has_balance:
        line = (
            alt.Chart(data)
            .mark_line(
                color="#3498DB", strokeWidth=3,
                point=alt.OverlayMarkDef(color="#3498DB", size=60)
            )
            .encode(
                x=x_enc,
                y=alt.Y("เงินเก็บ:Q", title="บาท", scale=y_scale),
                tooltip=[
                    alt.Tooltip("label:N", title="ช่วง"),
                    alt.Tooltip("เงินเก็บ:Q", title="เงินเก็บ", format=",.2f")
                ]
            )
        )
        layers.append(line)

    if goal > 0:
        rule = (
            alt.Chart(pd.DataFrame({"เป้าหมาย": [float(goal)]}))
            .mark_rule(color="#F39C12", strokeWidth=1.5, strokeDash=[6, 4])
            .encode(
                y=alt.Y("เป้าหมาย:Q", title="บาท", scale=y_scale),
                tooltip=[alt.Tooltip("เป้าหมาย:Q", format=",.2f")]
            )
        )
        layers.append(rule)

    chart = alt.layer(*layers).properties(height=380, width=520)
    st.altair_chart(chart, use_container_width=False)

    if has_balance:
        text = "🔵 เส้นฟ้า = เงินเก็บ"
        if goal > 0:
            text += (
                f"   ·  🟠 เส้นประ = เป้าหมาย {goal_name} {goal:,.2f} บาท "
                "(เส้นฟ้าแตะเส้นนี้ = ถึงเป้าแล้ว)"
            )
        st.caption(text)
