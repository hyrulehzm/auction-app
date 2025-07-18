import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd

# ---------- 配置文件 ----------
USERS_FILE = "users.json"
ITEMS_FILE = "items.json"
BIDS_FILE = "bids.json"
IMAGE_FOLDER = "images"

# ---------- 工具函数 ----------
def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def authenticate(username, password):
    users = load_json(USERS_FILE)
    st.write("DEBUG: 当前用户数据", users)
    return users.get(username) == password

def is_admin(username):
    return username == "admin"

def get_item_by_id(item_id):
    items = load_json(ITEMS_FILE)
    return items.get(item_id)

def get_bids_for_item(item_id):
    bids = load_json(BIDS_FILE)
    return bids.get(item_id, [])

def place_bid(item_id, username, amount):
    bids = load_json(BIDS_FILE)
    if item_id not in bids:
        bids[item_id] = []
    bids[item_id].append({
        "user": username,
        "amount": amount,
        "timestamp": datetime.now().isoformat()
    })
    save_json(BIDS_FILE, bids)

# ---------- 页面设置 ----------
st.set_page_config("Auction App", layout="wide")
st.title("🖼️ 在线拍卖平台")

# ---------- 登录系统 ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.subheader("🔐 登录")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")
    if st.button("登录"):
        if authenticate(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"欢迎回来，{username}！")
            st.rerun()
        else:
            st.error("用户名或密码错误。")
    st.stop()

# ---------- 顶部信息栏 ----------
st.sidebar.success(f"已登录：{st.session_state.username}")
if st.sidebar.button("退出登录"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()
# ---------- 管理员界面 ----------
if is_admin(st.session_state.username):
    st.sidebar.markdown("---")
    st.sidebar.subheader("🛠️ 管理员面板")
    admin_mode = st.sidebar.radio("选择功能", ["添加拍品", "编辑拍品", "查看出价记录"])

    if admin_mode == "添加拍品":
        st.subheader("➕ 添加拍品")
        name = st.text_input("拍品名称")
        description = st.text_area("拍品描述")
        starting_price = st.number_input("起拍价（元）", min_value=1.0)
        bid_increment = st.number_input("加价幅度（元）", min_value=1.0)
        date = st.date_input("竞拍截止日期", value=datetime.now().date())
        time = st.time_input("竞拍截止时间", value=datetime.now().time())
        end_time = datetime.combine(date, time)
        image = st.file_uploader("上传图片", type=["png", "jpg", "jpeg"])
        if st.button("添加拍品"):
            items = load_json(ITEMS_FILE)
            item_id = f"item_{len(items)+1}"
            image_path = os.path.join(IMAGE_FOLDER, f"{item_id}.png")
            if image:
                os.makedirs(IMAGE_FOLDER, exist_ok=True)
                with open(image_path, "wb") as f:
                    f.write(image.read())
            items[item_id] = {
                "name": name,
                "description": description,
                "start_price": starting_price,
                "increment": bid_increment,
                "end_time": end_time.isoformat(),
                "image": image_path if image else ""
            }
            save_json(ITEMS_FILE, items)
            st.success("拍品添加成功！")

    elif admin_mode == "编辑拍品":
        items = load_json(ITEMS_FILE)
        if items:
            selected = st.selectbox("选择要编辑的拍品", list(items.keys()))
            item = items[selected]
            new_price = st.number_input("修改起拍价", value=item["start_price"])
            new_inc = st.number_input("修改加价幅度", value=item["increment"])
            new_end = st.datetime_input("修改截止时间", value=datetime.fromisoformat(item["end_time"]))
            if st.button("更新拍品"):
                item["start_price"] = new_price
                item["increment"] = new_inc
                item["end_time"] = new_end.isoformat()
                items[selected] = item
                save_json(ITEMS_FILE, items)
                st.success("更新成功！")
        else:
            st.warning("暂无拍品。")

    elif admin_mode == "查看出价记录":
        bids = load_json(BIDS_FILE)
        st.subheader("📊 出价记录")
        for item_id, bid_list in bids.items():
            st.markdown(f"**{item_id}**")
            df = pd.DataFrame(bid_list)
            st.dataframe(df)

# ---------- 用户界面 ----------
st.subheader("🎯 拍卖中心")
items = load_json(ITEMS_FILE)

if not items:
    st.info("暂无拍品，请等待管理员添加。")

for item_id, item in items.items():
    col1, col2 = st.columns([1, 2])
    with col1:
        if item["image"] and os.path.exists(item["image"]):
            st.image(item["image"], width=200)
    with col2:
        st.markdown(f"### {item['name']}")
        st.markdown(item["description"])
        end_time = datetime.fromisoformat(item["end_time"])
        st.markdown(f"**结束时间：** {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        bids = get_bids_for_item(item_id)
        current_price = item["start_price"]
        if bids:
            current_price = max(bid["amount"] for bid in bids)
        st.markdown(f"**当前价格：** ${current_price}")
        st.markdown(f"**下次最低出价：** ${current_price + item['increment']}")
        if datetime.now() < end_time:
            bid_amount = st.number_input(f"为 {item['name']} 出价", min_value=current_price + item["increment"], step=item["increment"], key=item_id)
            if st.button(f"提交出价：{item['name']}", key=f"bid_{item_id}"):
                place_bid(item_id, st.session_state.username, bid_amount)
                st.success("出价成功！")
            st.rerun()
        else:
            st.error("⏰ 本拍品竞价已结束。")
