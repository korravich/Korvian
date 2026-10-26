# FILE: health_data.py | OWNER: #2 | VERSION: 0 | BASE: - | DATE: 2026-10-24
# CHANGES: v0 ย้ายเนื้อหาจาก views.py/db.py ไม่เปลี่ยนพฤติกรรม (เขียนโดย mr1)
"""Korvian: ข้อมูล Health Line (ยังไม่มีข้อมูลที่เก็บลงฐานข้อมูล)"""


def reset_user_data(uid):
    """ยังไม่มีข้อมูลสุขภาพในฐานข้อมูล จึงไม่ทำอะไร (v0: ปุ่มรีเซ็ตไม่แตะช่องติ๊ก)
    เมื่อมีตาราง health_ ให้ลบแถวของ uid ที่นี่ และ raise ถ้าพลาด (ห้ามแสดง UI/rerun เอง)"""
    return None
