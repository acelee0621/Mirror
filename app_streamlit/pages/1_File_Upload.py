import os
import streamlit as st
import requests
import pandas as pd
from navigation import make_sidebar


# --- 配置 ---
API_BASE_URL = os.getenv("STREAMLIT_API_BASE_URL", "http://127.0.0.1:8000/api/v1")

st.set_page_config(page_title="文件上传 - 明镜 D-Sensor", page_icon="📄", layout="wide")

make_sidebar()

st.title("📄 上传银行流水文件")
st.markdown("请选择用户和对应的银行账户，然后上传您的Excel或CSV流水文件。")

# --- 会话状态初始化 (V2版：增加 history_loaded_account_id) ---
if "selected_person_id" not in st.session_state:
    st.session_state.selected_person_id = None
if "selected_account_id" not in st.session_state:
    st.session_state.selected_account_id = None
if "file_history" not in st.session_state:
    st.session_state.file_history = []
# 新增一个状态，用于追踪当前已加载文件历史的账户ID
if "history_loaded_account_id" not in st.session_state:
    st.session_state.history_loaded_account_id = None


# --- API 调用函数 (保持不变) ---
@st.cache_data(ttl=60)
def get_all_persons():
    try:
        response = requests.get(f"{API_BASE_URL}/persons/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"无法连接到后端服务获取用户列表: {e}")
        return []


@st.cache_data(ttl=60)
def get_person_accounts(person_id: int):
    if not person_id:
        return []
    try:
        response = requests.get(f"{API_BASE_URL}/persons/{person_id}")
        response.raise_for_status()
        return response.json().get("accounts", [])
    except requests.exceptions.RequestException as e:
        st.error(f"获取账户列表失败: {e}")
        return []


def refresh_file_history(account_id: int):
    if not account_id:
        st.session_state.file_history = []
        return
    try:
        response = requests.get(f"{API_BASE_URL}/files/by_account/{account_id}")
        response.raise_for_status()
        st.session_state.file_history = response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"刷新文件历史失败: {e}")
        st.session_state.file_history = []


def delete_file(file_id: int, account_id_to_refresh: int):
    try:
        response = requests.delete(f"{API_BASE_URL}/files/{file_id}")
        if response.status_code == 204:
            st.success(f"文件ID {file_id} 已成功删除！")
            refresh_file_history(account_id_to_refresh)
        else:
            st.error(f"删除文件失败，错误码: {response.status_code}")
            st.json(response.json())
    except requests.exceptions.RequestException as e:
        st.error(f"删除请求失败: {e}")


def format_status(status: str) -> str:
    status_map = {
        "SUCCESS": "✅ 成功",
        "FAILED": "❌ 失败",
        "PROCESSING": "⏳ 处理中",
        "PENDING": "⌛ 等待中",
    }
    return status_map.get(status, status)


# --- 页面布局与逻辑 ---
persons = get_all_persons()
if not persons:
    st.warning("系统中还没有任何用户。请先通过API或后台创建用户。")
else:
    person_df = pd.DataFrame(persons)

    person_index = None
    if st.session_state.selected_person_id is not None:
        matching_person = person_df[
            person_df["id"] == st.session_state.selected_person_id
        ]
        if not matching_person.empty:
            person_index = int(matching_person.index[0])

    selected_person_name = st.selectbox(
        "第一步：选择用户",
        options=person_df["full_name"],
        index=person_index,
        placeholder="请选择一个用户...",
    )

    if selected_person_name:
        st.session_state.selected_person_id = person_df[
            person_df["full_name"] == selected_person_name
        ]["id"].iloc[0]
        accounts = get_person_accounts(st.session_state.selected_person_id)

        if not accounts:
            st.warning(f"用户 **{selected_person_name}** 名下还没有任何银行账户。")
        else:
            account_df = pd.DataFrame(accounts)

            account_index = None
            if st.session_state.selected_account_id is not None:
                matching_account = account_df[
                    account_df["id"] == st.session_state.selected_account_id
                ]
                if not matching_account.empty:
                    account_index = int(matching_account.index[0])

            selected_account_name = st.selectbox(
                "第二步：选择银行账户",
                options=account_df["account_name"],
                index=account_index,
                placeholder="请选择一个银行账户...",
            )

            if selected_account_name:
                st.session_state.selected_account_id = account_df[
                    account_df["account_name"] == selected_account_name
                ]["id"].iloc[0]

                # --- 【核心修复点】: 响应式地加载文件历史 ---
                if (
                    st.session_state.selected_account_id
                    != st.session_state.history_loaded_account_id
                ):
                    with st.spinner("正在获取文件历史..."):
                        refresh_file_history(st.session_state.selected_account_id)
                        st.session_state.history_loaded_account_id = (
                            st.session_state.selected_account_id
                        )
                        st.rerun()

                # ... 后续的表单和文件历史代码保持不变 ...
                with st.form("upload_form", clear_on_submit=True):
                    st.markdown("---")
                    st.markdown("#### 第三步：上传文件")
                    uploaded_file = st.file_uploader(
                        "选择一个Excel或CSV文件", type=["xlsx", "xls", "csv"]
                    )
                    submitted = st.form_submit_button("🚀 开始上传和处理")

                    if submitted and uploaded_file is not None:
                        files = {
                            "file": (
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                uploaded_file.type,
                            )
                        }
                        data = {"account_id": st.session_state.selected_account_id}

                        with st.spinner(f"正在上传文件 '{uploaded_file.name}'..."):
                            try:
                                response = requests.post(
                                    f"{API_BASE_URL}/files/upload",
                                    files=files,
                                    data=data,
                                )
                                if response.status_code == 201:
                                    st.success("🎉 文件上传成功！后台正在异步处理中...")
                                    refresh_file_history(
                                        st.session_state.selected_account_id
                                    )
                                else:
                                    st.error(
                                        f"上传失败，错误码: {response.status_code}"
                                    )
                                    try:
                                        st.json(response.json())
                                    except requests.exceptions.JSONDecodeError:
                                        st.text(response.text)
                            except requests.exceptions.RequestException as e:
                                st.error(f"上传请求失败: {e}")

                st.markdown("---")
                st.subheader("📂 文件上传历史")

                if st.button("🔄 手动刷新"):
                    refresh_file_history(st.session_state.selected_account_id)

                if st.session_state.file_history:
                    header_cols = st.columns([3, 2, 1, 2, 2, 1])
                    headers = [
                        "文件名",
                        "处理状态",
                        "大小(KB)",
                        "上传时间",
                        "错误信息",
                        "操作",
                    ]
                    for col, header in zip(header_cols, headers):
                        col.markdown(f"**{header}**")

                    for file in st.session_state.file_history:
                        row_cols = st.columns([3, 2, 1, 2, 2, 1])
                        row_cols[0].text(file["filename"])
                        row_cols[1].markdown(format_status(file["processing_status"]))
                        row_cols[2].text(f"{(file['filesize'] / 1024):.2f}")
                        row_cols[3].text(
                            pd.to_datetime(file["upload_timestamp"]).strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        )
                        row_cols[4].text(file["error_message"] or "无")
                        if row_cols[5].button(
                            "🗑️ 删除",
                            key=f"del_{file['id']}",
                            help="删除此文件及其关联的所有交易数据",
                        ):
                            delete_file(
                                file["id"], st.session_state.selected_account_id
                            )
                else:
                    st.info("该账户还没有任何文件上传记录。")
            else:
                # 如果用户清空了账户选择，我们也清空文件历史
                st.session_state.file_history = []
                st.session_state.history_loaded_account_id = None
