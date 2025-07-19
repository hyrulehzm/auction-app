import streamlit as st
import json
import uuid
from datetime import datetime, timedelta
import os
from streamlit_autorefresh import st_autorefresh

# ====== 初始化文件路径 ======
ITEMS_FILE = "items.json"
USERS_FILE = "users.json"
BIDS_FILE = "bids.json"
UPLOAD_DIR = "uploads"

# ====== 文件初始化 ======
for file, default in [
    (ITEMS_FILE, []),
    (USERS_FILE, {"admin": "admin123!"}),
    (BIDS_FILE, [])
]:
    if not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=4)

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# ====== 读取数据 ======
def load_json(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ====== 登录逻辑 ======
def login():
    st.title("🔐 用户登录")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")
    if st.button("登录"):
        users = load_json(USERS_FILE)
        if username in users and users[username] == password:
            st.session_state.username = username
            st.success(f"欢迎回来，{username}！")
            st.rerun()
        else:
            st.error("用户名或密码错误。")

# ====== 添加拍品 ======
def add_item():
    st.subheader("🆕 添加拍品")
    name = st.text_input("拍品名称")
    description = st.text_area("拍品描述")
    start_price = st.number_input("起拍价（元）", min_value=0.01)
    increment = st.number_input("加价幅度（元）", min_value=0.01)
    start_date = st.date_input("竞拍开始日期", value=datetime.today())
    start_time = st.time_input("竞拍开始时间", value=datetime.now().time())
    end_date = st.date_input("竞拍截止日期", value=datetime.today())
    end_time = st.time_input("竞拍截止时间", value=(datetime.now() + timedelta(hours=1)).time())
    image = st.file_uploader("上传拍品图片", type=["jpg", "jpeg", "png"])

    if st.button("✅ 提交拍品", key="submit_item"):
        if not name.strip() or not description.strip():
            st.error("❗ 拍品名称和描述不能为空")
            return

    start_dt = datetime.combine(start_date, start_time).isoformat()
    end_dt = datetime.combine(end_date, end_time).isoformat()
    image_path = None
    if image:
        image_name = f"{uuid.uuid4().hex}_{image.name}"
        image_path = os.path.join(UPLOAD_DIR, image_name)
        with open(image_path, "wb") as f:
            f.write(image.read())

        new_item = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "starting_price": start_price,
            "increment": increment,
            "start_time": start_dt,
            "end_time": end_dt,
            "image": image_path,
            "bids": []
        }
        items = load_json(ITEMS_FILE)
        items.append(new_item)
        save_json(ITEMS_FILE, items)
        st.success("拍品添加成功！")

# ====== 编辑拍品 ======
def edit_items():
    st.subheader("🛠️ 编辑拍品")
    items = load_json(ITEMS_FILE)
    for item in items:
        with st.expander(f"{item['name']}（截止于 {item['end_time'][:16].replace('T',' ')}）"):
            item['name'] = st.text_input("名称", value=item['name'], key=f"name_{item['id']}")
            item['description'] = st.text_area("描述", value=item['description'], key=f"desc_{item['id']}")
            item['starting_price'] = st.number_input("起拍价", value=item['starting_price'], key=f"start_{item['id']}")
            item['increment'] = st.number_input("加价幅度", value=item['increment'], key=f"inc_{item['id']}")

            if st.button("💾 保存修改", key=f"save_{item['id']}"):
                save_json(ITEMS_FILE, items)
                st.success("保存成功！")
                st.rerun()

            if st.button("🗑️ 删除该拍品", key=f"del_{item['id']}"):
                items.remove(item)
                save_json(ITEMS_FILE, items)
                st.warning("拍品已删除")
                st.rerun()

# ====== 拍品竞价 ======
def bidding_area():
    st.subheader("📦 拍品竞价区")
    st_autorefresh(interval=1000, key="refresh")

    items = load_json(ITEMS_FILE)
    for item in items:
        now = datetime.now()

        # 新增：防止时间字段缺失导致崩溃
        if not item.get("start_time") or not item.get("end_time"):
            st.warning(f"⚠️ 拍品 `{item['name']}` 缺少时间信息，已跳过展示。")
            continue

        start = datetime.fromisoformat(item['start_time'])
        end = datetime.fromisoformat(item['end_time'])

        with st.container():
            st.markdown(f"### {item['name']}")
            if item.get("image") and os.path.exists(item['image']):
                st.image(item['image'], width=300)
            st.markdown(f"描述：{item['description']}")
            st.markdown(f"⏰ 拍卖时间：{start.strftime('%Y-%m-%d %H:%M')} ~ {end.strftime('%Y-%m-%d %H:%M')}")

            if now < start:
                st.info("⚠️ 拍卖尚未开始")
            elif now > end:
                st.error("拍卖已结束")
                if item['bids']:
                    last_bid = item['bids'][-1]
                    st.success(f"🎉 中标者：{last_bid['user']}，成交时间：{last_bid['time']}")
            else:
                current_price = item['starting_price'] + len(item['bids']) * item['increment']
                st.markdown(f"💰 当前价：¥{current_price:.2f}")

                remaining = end - now
                seconds = int(remaining.total_seconds())
                mins, secs = divmod(seconds, 60)
                hours, mins = divmod(mins, 60)
                st.markdown(f"⏳ 剩余时间：`{hours:02d}:{mins:02d}:{secs:02d}`")

                if st.button(f"出价 +¥{item['increment']:.2f}", key=f"bid_{item['id']}"):
                    item['bids'].append({"user": st.session_state.username, "time": datetime.now().isoformat()})
                    save_json(ITEMS_FILE, items)
                    st.success("出价成功！")
                    st.rerun()

            if item['bids']:
                st.markdown("📜 出价记录：")
                for bid in reversed(item['bids']):
                    st.markdown(f"- {bid['user']} @ {bid['time'][:19].replace('T', ' ')}")

# ====== 页面布局 ======
def main():
    st.set_page_config("在线拍卖系统", layout="centered")
    #st_autorefresh(interval=1000, key="global-refresh")

    if "username" not in st.session_state:
        login()
        return

    st.sidebar.markdown(f"👤 当前用户：`{st.session_state.username}`")
    if st.sidebar.button("🔒 退出登录"):
        del st.session_state.username
        st.rerun()

    if st.session_state.username == "admin":
        st.title("🖥️ 管理员后台")
        tabs = st.tabs(["➕ 添加拍品", "🛠️ 编辑拍品", "📦 拍品竞价区"])
        with tabs[0]: add_item()
        with tabs[1]: edit_items()
        with tabs[2]: bidding_area()
    else:
        st.title("🖼️ 在线拍卖平台")
        bidding_area()

if __name__ == '__main__':
    main()
