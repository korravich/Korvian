# FILE: health.py | OWNER: #2 | VERSION: 0 | BASE: - | DATE: 2026-10-24
# CHANGES: v0 ย้ายเนื้อหาจาก views.py/db.py ไม่เปลี่ยนพฤติกรรม (เขียนโดย mr1)
"""Korvian: หน้า Health Line (หน้าจอ + ค่าคงที่ของหน้า)"""
import random

import streamlit as st


# ทุก key ที่หน้า Health ใช้เก็บสถานะ (ช่องติ๊ก + ข้อความสุ่ม)
# ใช้ล้างทิ้งเมื่อเจ้าของข้อมูลเปลี่ยน เพื่อไม่ให้ข้อมูลของผู้ใช้คนก่อนค้างอยู่
HEALTH_KEYS = (
    [f"health_water_{i}" for i in range(1, 9)]
    + ["health_meal_breakfast", "health_meal_lunch", "health_meal_dinner",
       "health_time_breakfast", "health_time_lunch", "health_time_dinner",
       "health_sleep_enough", "health_sleep_schedule", "health_sleep_screen",
       "health_move_walk", "health_move_stretch", "health_move_activity",
       "health_mind_relax", "health_mind_enjoy", "health_mind_connect",
       "health_previous_water_count", "health_previous_meal_count",
       "health_water_tip", "health_meal_tip", "health_time_tip",
       "health_sleep_tip", "health_move_tip", "health_mind_tip"]
)

WATER_TIPS = [
    "พักแล้วจิบน้ำสักหน่อยมั้ยย 💧",
    "น้ำช่วยให้ร่างกายทำงานได้ดีตามปกตินะ อย่าลืมล่ะ!",
    "ไม่ต้องรีบดื่มรวดเดียว ค่อย ๆ จิบระหว่างวันเอานะ 😉😉",
]
MEAL_TIPS = [
    "อีกมื้อเดียวก็ครบแล้วนะ",
    "อย่าลืมกินอาหารให้ครบ 5 หมู่ด้วยหล่ะ 😌",
    "อย่าลืมหาเวลากินมื้อที่เหลือนะ 😉😉",
]

# ภารกิจที่เหลือ (ติ๊กครบทุกข้อ = สำเร็จ) เพิ่มภารกิจใหม่ได้ที่นี่
SIMPLE_MISSIONS = [
    {
        "title": "⏰ ภารกิจที่ 3: วันนี้ได้พักกินข้าวเป็นเวลาหรือยัง?",
        "desc": "หาเวลาพักกินอาหาร ไม่ปล่อยให้กิจกรรมต่าง ๆ เบียดเวลามื้ออาหาร",
        "items": [
            ("จัดเวลามื้อเช้าได้เหมาะสม", "health_time_breakfast"),
            ("มีเวลาพักกินมื้อกลางวัน", "health_time_lunch"),
            ("จัดเวลามื้อเย็นได้เหมาะสม", "health_time_dinner"),
        ],
        "tip_key": "health_time_tip",
        "tips": [
            "ภารกิจในเกมรอได้ แต่ท้องร้องนี่สิไม่ยอมรอ 😂",
            "อย่าลืมพักจากการเรียนหรือเล่นเกมมากินข้าวนะ!",
            "การกินอาหารสม่ำเสมอช่วยให้จัดกิจวัตรได้ดีขึ้น 🍱",
        ],
        "success": "วันนี้จัดเวลามื้ออาหารได้ครบแล้ว! ⏰",
    },
    {
        "title": "🛌 ภารกิจที่ 4: วันนี้พักผ่อนเพียงพอหรือยัง?",
        "desc": "การนอนช่วยให้ร่างกายและสมองได้พักฟื้น",
        "items": [
            ("เมื่อคืนได้นอนเพียงพอสำหรับตัวเอง", "health_sleep_enough"),
            ("พยายามเข้านอนและตื่นให้เป็นเวลา", "health_sleep_schedule"),
            ("เตรียมตัวพักจากหน้าจอก่อนนอน", "health_sleep_screen"),
        ],
        "tip_key": "health_sleep_tip",
        "tips": [
            "ตัวละครยังต้องพักฟื้น แล้วคุณล่ะ? 😂",
            "นอนดึกทุกคืน เดี๋ยวพรุ่งนี้สมองขอโหลดช้านะ 💤",
            "วัยรุ่นส่วนใหญ่มักต้องการนอนประมาณ 8–10 ชั่วโมงต่อคืน",
            "ลองวางมือถือก่อนนอน แล้วให้สมองได้พักบ้างนะ 📱",
        ],
        "success": "ภารกิจดูแลการนอนครบแล้ว ขอให้พักผ่อนเต็มที่! 💤",
    },
    {
        "title": "🚶 ภารกิจที่ 5: วันนี้ได้ขยับร่างกายหรือยัง?",
        "desc": "ไม่จำเป็นต้องออกกำลังหนัก เริ่มจากการเคลื่อนไหวที่เหมาะกับตัวเองได้",
        "items": [
            ("🚶 เดินหรือขยับร่างกายระหว่างวัน", "health_move_walk"),
            ("🙆 ยืดเหยียดร่างกาย", "health_move_stretch"),
            ("⚽ ทำกิจกรรมที่ชอบ เช่น เล่นกีฬา", "health_move_activity"),
        ],
        "tip_key": "health_move_tip",
        "tips": [
            "อย่านั่งนิ่งจนรากงอกเหมือนต้นไม้สิ 😂",
            "ลุกมายืดเส้นสักนิด ร่างกายจะได้เปลี่ยนอิริยาบถ!",
            "การเคลื่อนไหวสม่ำเสมอดีต่อสุขภาพนะ ไม่จำเป็นต้องหักโหม 💪",
        ],
        "success": "ภารกิจขยับร่างกายครบแล้ว เยี่ยมมาก! 🚶",
    },
    {
        "title": "💚 ภารกิจที่ 6: วันนี้ได้ดูแลความรู้สึกตัวเองหรือยัง?",
        "desc": "การพักใจเป็นส่วนหนึ่งของการดูแลตัวเองเหมือนกันนะ",
        "items": [
            ("หาเวลาพักจากสิ่งที่ทำอยู่", "health_mind_relax"),
            ("ทำกิจกรรมที่ทำให้ตัวเองมีความสุข", "health_mind_enjoy"),
            ("พูดคุยกับคนที่ไว้ใจเมื่ออยากระบาย", "health_mind_connect"),
        ],
        "tip_key": "health_mind_tip",
        "tips": [
            "คุณไม่ใช่หุ่นยนต์นะ พักบ้างก็ได้ 🤖",
            "ไม่จำเป็นต้องเก่งทุกนาที แค่วันนี้ดูแลตัวเองได้ก็ดีแล้ว 💚",
            "พักใจสักนิด ไม่ใช่การแพ้ แต่เป็นการให้เวลากับตัวเอง",
        ],
        "success": "ภารกิจดูแลใจสำเร็จแล้ว อย่าลืมใจดีกับตัวเองนะ 💚",
    },
]


def _isolate_health_state():
    """ถ้าเจ้าของข้อมูลเปลี่ยน (ล็อกอินคนใหม่) ให้ล้างช่องติ๊กสุขภาพของคนเดิมทิ้ง"""
    uid = st.session_state.get("user_id")
    if st.session_state.get("health_owner") != uid:
        for key in HEALTH_KEYS:
            st.session_state.pop(key, None)
        st.session_state["health_owner"] = uid


def _tip(text, color):
    st.markdown(
        f"<p style='color:{color}; font-size:12px;'>💬 {text}</p>",
        unsafe_allow_html=True
    )


def _progress(done, total, unit=""):
    st.caption(f"ความคืบหน้า: {done}/{total}{unit}")
    st.progress(done / total)


def _rotating_tip(tip_key, prev_key, count, options):
    """สุ่มข้อความใหม่เมื่อจำนวนที่ติ๊กเปลี่ยน ถ้าไม่เปลี่ยนใช้ข้อความเดิม"""
    if count != st.session_state.get(prev_key, -1):
        st.session_state[tip_key] = random.choice(options)
    return st.session_state.get(tip_key, options[0])


def _simple_mission(m):
    with st.expander(m["title"]):
        st.write(m["desc"])

        done = sum(
            1 for label, key in m["items"] if st.checkbox(label, key=key)
        )
        total = len(m["items"])

        if done == total:
            st.success(m["success"])
        else:
            if m["tip_key"] not in st.session_state:
                st.session_state[m["tip_key"]] = random.choice(m["tips"])
            _tip(st.session_state[m["tip_key"]], "#e05252")

        _progress(done, total)


def render():
    _isolate_health_state()

    st.subheader("เช็คลิสต์ร่างกายประจำวัน")
    st.write("🌱 สุขภาพที่ดีเริ่มจากสิ่งเล็ก ๆ ที่คุณทำในทุกวัน มาเช็คไปพร้อมกันเลย !😁")

    # 1. ดื่มน้ำ
    with st.expander("💧 ภารกิจที่ 1: วันนี้ดื่มน้ำครบ 8 แก้วหรือยัง?"):
        st.write("เติมพลังให้ร่างกาย จิบน้ำให้เหมาะกับความต้องการของตัวเอง!")

        cols = st.columns(4)
        water_count = 0
        for i in range(8):
            with cols[i % 4]:
                if st.checkbox(f"แก้วที่ {i + 1}", key=f"health_water_{i + 1}"):
                    water_count += 1

        if water_count == 8:
            st.success("ภารกิจเช็กการดื่มน้ำครบแล้ว! เยี่ยมเลย 💧")
        elif water_count == 0:
            _tip("วันนี้คุณยังไม่ได้เช็กการดื่มน้ำเลยนะ 💧", "#E53935")
        elif water_count <= 3:
            _tip("ปากแห้งเป็นทะเลทรายแล้วมั้งเนี่ย 🏜️", "#F39C12")
        else:
            _tip(
                _rotating_tip("health_water_tip", "health_previous_water_count", water_count, WATER_TIPS),
                "#3498DB"
            )

        st.session_state["health_previous_water_count"] = water_count
        _progress(water_count, 8)

    # 2. กินอาหารครบ 3 มื้อ
    with st.expander("🍚 ภารกิจที่ 2: วันนี้กินอาหารครบ 3 มื้อหรือยัง?"):
        st.write("เติมพลังงานให้ร่างกายด้วยมื้ออาหารที่หลากหลาย")

        meal_count = sum([
            st.checkbox("🌅 มื้อเช้า", key="health_meal_breakfast"),
            st.checkbox("🌄 มื้อกลางวัน", key="health_meal_lunch"),
            st.checkbox("🌆 มื้อเย็น", key="health_meal_dinner"),
        ])

        if meal_count == 3:
            st.success("บันทึกมื้ออาหารครบทั้ง 3 มื้อแล้ว! เก่งมาก 🍚")
        elif meal_count == 0:
            _tip("วันนี้คุณยังไม่ได้กินอะไรเลยนะ 🍚", "#E53935")
        elif meal_count == 1:
            _tip("อาหารที่หลากหลายช่วยให้ร่างกายได้รับสารอาหารที่จำเป็นนะ! 💪", "#F39C12")
        else:
            _tip(
                _rotating_tip("health_meal_tip", "health_previous_meal_count", meal_count, MEAL_TIPS),
                "#3498DB"
            )

        st.session_state["health_previous_meal_count"] = meal_count
        _progress(meal_count, 3, " มื้อ")

    # 3-6. ภารกิจที่เหลือ
    for mission in SIMPLE_MISSIONS:
        _simple_mission(mission)

    st.write("---")
    st.caption(
        "💚 เช็กลิสต์นี้มีไว้ช่วยติดตามการดูแลตัวเอง การทำได้ครบทุกข้อเป็นเรื่องดี "
        "แต่สิ่งสำคัญคือการดูแลตัวเองอย่างเหมาะสมและสม่ำเสมอในทุก ๆ วันนะ!"
    )

    # TODO: ปุ่มนี้ยังไม่ได้บันทึกลงฐานข้อมูลจริง (งานถัดไป)
    if st.button("บันทึกคะแนนสุขภาพประจำวัน"):
        st.success("บันทึกพฤติกรรมเรียบร้อย! รักษาวินัยแบบนี้ในทุกๆ วันนะครับ")
