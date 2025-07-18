import streamlit as st
import json
import uuid
from datetime import datetime, date, time, timedelta
import os

# ---------- 文件操作 ----------

def load_json(file):
    if not os.path.exists(file):
        return [] if file != "users.json" else {}
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

items = load_json("items.json")
bids = load_json("bids.json")
users = load_json("users.json")

# ---------- 登录功能 ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

def login():
    st.title("🔐 用户登录")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")
    if st.button("登录"):
        if username in users and users[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"🎉 欢迎回来，{username}！")
            st.rerun()
        else:
            st.error("❌ 用户名或密码错误")

if not st.session_state.logged_in:
    login()
    st.stop()

# ---------- 页面标题 ----------
st.title("🖼️ 在线拍卖平台")

# ---------- 添加拍品 ----------
st.header("➕ 添加拍品")

with st.form("add_item_form"):
    name = st.text_input("拍品名称")
    description = st.text_area("拍品描述")
    starting_price = st.number_input("起拍价（元）", min_value=0.0, step=0.01)
    increment = st.number_input("加价幅度（元）", min_value=0.01, step=0.01)

    start_date = st.date_input("竞拍开始日期", value=date.today())
    start_time = st.time_input("竞拍开始时间", value=time(9, 0))

    end_date = st.date_input("竞拍截止日期", value=date.today() + timedelta(days=1))
    end_time = st.time_input("竞拍截止时间", value=time(17, 0))

    submitted = st.form_submit_button("➕ 添加拍品")

if submitted:
    start_datetime = datetime.combine(start_date, start_time)
    end_datetime = datetime.combine(end_date, end_time)

    if start_datetime >= end_datetime:
        st.error("❌ 截止时间必须晚于开始时间")
    else:
        new_item = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "starting_price": starting_price,
            "increment": increment,
            "start_time": start_datetime.isoformat(),
            "end_time": end_datetime.isoformat(),
            "bids": []
        }
        items.append(new_item)
        save_json("items.json", items)
        st.success("✅ 拍品添加成功！")
        st.rerun()

# ---------- 展示拍品及出价 ----------
st.header("📦 拍品竞价区")
now = datetime.now()

def place_bid(item_id, user, bid_amount):
    for item in items:
        if item["id"] == item_id:
            item["bids"].append({"user": user, "amount": bid_amount, "time": now.isoformat()})
            save_json("items.json", items)
            break

for item in items:
    st.subheader(f"📌 {item['name']}")
    st.write(f"📃 描述：{item['description']}")
    st.write(f"💰 起拍价：¥{item['starting_price']:.2f} | 加价：¥{item['increment']:.2f}")

    start_time = datetime.fromisoformat(item["start_time"])
    end_time = datetime.fromisoformat(item["end_time"])
    st.write(f"⏱️ 起始：{start_time.strftime('%Y-%m-%d %H:%M')} | 截止：{end_time.strftime('%Y-%m-%d %H:%M')}")

    if now < start_time:
        st.info("⌛ 拍卖尚未开始")
    elif now > end_time:
        st.warning("⛔ 拍卖已结束")
    else:
        current_bid = item['bids'][-1]['amount'] if item['bids'] else item['starting_price']
        st.write(f"🔼 当前最高出价：¥{current_bid:.2f}")
        bid_amount = current_bid + item['increment']
        if st.button(f"出价（¥{bid_amount:.2f}）", key=f"bid_{item['id']}"):
            place_bid(item['id'], st.session_state.username, bid_amount)
            st.success("✅ 出价成功！")
            st.rerun()

    if item['bids']:
        st.markdown("**📈 出价记录：**")
        for bid in reversed(item['bids']):
            bid_time = datetime.fromisoformat(bid['time']).strftime("%Y-%m-%d %H:%M:%S")
            st.write(f"🧍 {bid['user']} 出价 ¥{bid['amount']:.2f} （{bid_time}）")
    st.divider()