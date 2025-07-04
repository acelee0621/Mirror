import os
import streamlit as st
import requests
import pandas as pd
from navigation import make_sidebar


# --- 配置 ---
API_BASE_URL = os.getenv("STREAMLIT_API_BASE_URL", "http://127.0.0.1:8000/api/v1")

st.set_page_config(page_title="管理中心 - 明镜 D-Sensor", page_icon="⚙️", layout="wide")

make_sidebar()

st.title("⚙️ 管理中心")
st.markdown("在这里，您可以创建新的用户和银行账户。")


# --- API 调用函数 ---
@st.cache_data(ttl=60)
def get_all_persons():
    try:
        response = requests.get(f"{API_BASE_URL}/persons/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []


# --- 页面布局与逻辑 ---

tab1, tab2 = st.tabs(["👤 创建新用户", "💳 为用户添加新账户"])

# --- Tab 1: 创建新用户 ---
with tab1:
    st.subheader("创建新的用户实体")
    with st.form("new_person_form", clear_on_submit=True):
        full_name = st.text_input("用户全名", placeholder="例如：张三")
        id_type = st.text_input("证件类型 (可选)", placeholder="例如：身份证")
        id_number = st.text_input("证件号码 (可选)", placeholder="请输入证件号码")

        submitted = st.form_submit_button("创建用户")

        if submitted and full_name:
            payload = {
                "full_name": full_name,
                "id_type": id_type or None,
                "id_number": id_number or None,
            }
            try:
                response = requests.post(f"{API_BASE_URL}/persons/", json=payload)
                if response.status_code == 201:
                    st.success(f"🎉 用户 '{full_name}' 创建成功！")
                    # 清除缓存，以便其他页面的用户下拉列表能立即更新
                    get_all_persons.clear()
                else:
                    st.error(f"创建失败，错误码: {response.status_code}")
                    st.json(response.json())
            except requests.exceptions.RequestException as e:
                st.error(f"请求失败: {e}")
        elif submitted:
            st.warning("“用户全名”是必填项。")

# --- Tab 2: 添加新账户 ---
with tab2:
    st.subheader("为现有用户添加新的银行账户")
    persons = get_all_persons()
    if not persons:
        st.warning("系统中还没有任何用户，请先在左侧标签页创建新用户。")
    else:
        person_df = pd.DataFrame(persons)
        selected_person_name = st.selectbox(
            "第一步：选择要操作的用户",
            options=person_df["full_name"],
            index=None,
            placeholder="请选择一个用户...",
        )

        if selected_person_name:
            person_id = person_df[person_df["full_name"] == selected_person_name][
                "id"
            ].iloc[0]

            with st.form("new_account_form", clear_on_submit=True):
                st.write(f"正在为 **{selected_person_name}** 添加新账户：")
                account_name = st.text_input("账户名称", placeholder="例如：招行工资卡")
                account_number = st.text_input("银行账号/卡号")
                account_type = st.text_input(
                    "账户类型 (可选)", placeholder="例如：储蓄卡、信用卡"
                )
                institution = st.text_input(
                    "所属金融机构 (可选)", placeholder="例如：招商银行"
                )

                submitted = st.form_submit_button("添加账户")

                if submitted and account_name and account_number:
                    payload = {
                        "account_name": account_name,
                        "account_number": account_number,
                        "account_type": account_type or None,
                        "institution": institution or None,
                    }
                    try:
                        # 调用正确的API端点
                        response = requests.post(
                            f"{API_BASE_URL}/persons/{person_id}/accounts", json=payload
                        )
                        if response.status_code == 201:
                            st.success(
                                f"🎉 成功为 '{selected_person_name}' 添加了新账户 '{account_name}'！"
                            )
                            # 此处可以考虑清除 get_person_accounts 的缓存，但这需要更复杂的缓存管理
                            # 简单起见，用户下次在其他页面选择该用户时，缓存会自动刷新
                        else:
                            st.error(f"添加失败，错误码: {response.status_code}")
                            st.json(response.json())
                    except requests.exceptions.RequestException as e:
                        st.error(f"请求失败: {e}")
                elif submitted:
                    st.warning("“账户名称”和“银行账号”是必填项。")
