# FILE: theme.py | OWNER: #1 | VERSION: 1 | BASE: 0 | DATE: 2026-10-24
# CHANGES: v1 แยกจากไฟล์ v0 (db.py: TH_TZ, today_th; sidebar.py: korvian_logo_svg -> logo_svg)
"""Korvian: ธีมกลาง (โลโก้ SVG, ค่าคงที่, วันที่เวลาไทย)

ไฟล์นี้ห้าม import ไฟล์อื่นของโปรเจกต์
"""
from datetime import datetime, timedelta, timezone

TH_TZ = timezone(timedelta(hours=7))  # เวลาไทย


def today_th():
    return datetime.now(TH_TZ).date()


def logo_svg(size=28, color="#b8bac2"):
    return (
        f"<svg width='{size}' height='{size}' viewBox='0 0 28 28' "
        "xmlns='http://www.w3.org/2000/svg'>"
        f"<circle cx='14' cy='14' r='11' fill='none' stroke='{color}' stroke-width='0.9'/>"
        f"<circle cx='14' cy='14' r='9.3' fill='none' stroke='{color}' stroke-width='0.9'/>"
        f"<path fill='{color}' d='M14 6.8 C14 12.2 15.8 14 21.2 14 "
        "C15.8 14 14 15.8 14 21.2 C14 15.8 12.2 14 6.8 14 "
        "C12.2 14 14 12.2 14 6.8 Z'/>"
        "</svg>"
    )
