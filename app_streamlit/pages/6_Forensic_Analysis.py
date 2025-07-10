import streamlit as st
import requests
import pandas as pd
import os
from navigation import make_sidebar

# --- 配置 ---
API_BASE_URL = os.getenv("STREAMLIT_API_BASE_URL", "http://127.0.0.1:8000/api/v1")

st.set_page_config(page_title="法证分析 - 明镜 D-Sensor", page_icon="🔬", layout="wide")

make_sidebar()

st.title("🔬 法证分析：U型/快进快出检测")
st.markdown(
    "此工具用于检测在短时间内，与大额流入资金相匹配的大额流出交易，常用于识别可疑的资金通道活动。"
)

# --- 会话状态初始化 ---
if "selected_person_id" not in st.session_state:
    st.session_state.selected_person_id = None
if "uturn_events" not in st.session_state:
    st.session_state.uturn_events = []


# --- API 调用函数 ---
@st.cache_data(ttl=60)
def get_all_persons():
    try:
        response = requests.get(f"{API_BASE_URL}/persons/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"无法连接到后端服务获取用户列表: {e}")
        return []


def run_analysis(person_id, threshold, window, tolerance):
    """调用后端API运行分析"""
    payload = {
        "amount_threshold": threshold,
        "time_window_hours": window,
        "amount_tolerance": tolerance,
    }
    with st.spinner("正在运行分析，请稍候..."):
        try:
            response = requests.post(
                f"{API_BASE_URL}/analysis/persons/{person_id}/u-turn", json=payload
            )
            if response.status_code == 200:
                results = response.json()
                st.session_state.uturn_events = results.get("found_events", [])
                st.success(
                    f"分析完成！共发现 {len(st.session_state.uturn_events)} 个疑似事件。"
                )
            else:
                st.error(f"分析失败，错误码: {response.status_code}")
                st.json(response.json())
        except requests.exceptions.RequestException as e:
            st.error(f"请求失败: {e}")


# --- 页面布局与逻辑 ---
st.markdown("---")
st.subheader("分析参数设置")

persons = get_all_persons()
if not persons:
    st.warning("系统中还没有任何用户。请先在“管理中心”创建用户。")
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
        "第一步：选择要分析的用户",
        options=person_df["full_name"],
        index=person_index,
        placeholder="请选择一个用户...",
    )

    if selected_person_name:
        st.session_state.selected_person_id = person_df[
            person_df["full_name"] == selected_person_name
        ]["id"].iloc[0]

        col1, col2, col3 = st.columns(3)
        with col1:
            amount_thresh = st.number_input(
                "金额阈值 (元)", min_value=1000.0, value=10000.0, step=1000.0
            )
        with col2:
            time_win = st.slider(
                "时间窗口 (小时)", min_value=1, max_value=168, value=72
            )
        with col3:
            amount_tol = (
                st.slider(
                    "金额容差 (%)",
                    min_value=0.0,
                    max_value=50.0,
                    value=10.0,
                    format="%.1f%%",
                )
                / 100.0
            )

        if st.button("🚀 开始分析", type="primary"):
            run_analysis(
                st.session_state.selected_person_id, amount_thresh, time_win, amount_tol
            )

# --- 结果展示 ---
st.markdown("---")
st.subheader("分析结果")

if not st.session_state.uturn_events:
    st.info("暂无分析结果。请选择用户并点击“开始分析”按钮。")
else:
    for i, event in enumerate(st.session_state.uturn_events):
        inflow = event["inflow"]
        outflows = event["outflows"]

        with st.expander(
            f"**事件 {i + 1}:** 流入 **¥{inflow['amount']:,.2f}** 后，在 **{event['time_diff_hours']:.1f}** 小时内流出 **¥{event['total_outflow']:,.2f}**",
            expanded=True,
        ):
            in_col, out_col = st.columns(2)

            with in_col:
                st.markdown("##### ➡️ 流入交易")
                st.metric(label="金额", value=f"¥ {inflow['amount']:,.2f}")
                st.text(
                    f"时间: {pd.to_datetime(inflow['transaction_date']).strftime('%Y-%m-%d %H:%M')}"
                )
                st.text(f"对手: {inflow['counterparty']['name']}")
                st.caption(f"摘要: {inflow['description']}")

            with out_col:
                st.markdown("##### ⬅️ 流出交易")
                for outflow in outflows:
                    st.metric(label="金额", value=f"¥ {outflow['amount']:,.2f}")
                    st.text(
                        f"时间: {pd.to_datetime(outflow['transaction_date']).strftime('%Y-%m-%d %H:%M')}"
                    )
                    st.text(f"对手: {outflow['counterparty']['name']}")
                    st.caption(f"摘要: {outflow['description']}")
                    st.markdown("---")
