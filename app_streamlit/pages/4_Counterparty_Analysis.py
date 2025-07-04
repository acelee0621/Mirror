import streamlit as st
import requests
import pandas as pd
import altair as alt
from navigation import make_sidebar

# --- 配置 ---
API_BASE_URL = "http://127.0.0.1:8000/api/v1"

st.set_page_config(
    page_title="核心对手分析 - 明镜 D-Sensor", page_icon="🤝", layout="wide"
)

make_sidebar()

st.title("🤝 核心对手分析")
st.markdown("从对手方的视角，洞察您的核心资金往来网络。")

# --- 会话状态初始化 ---
if "selected_person_id" not in st.session_state:
    st.session_state.selected_person_id = None
if "opponent_summary_df" not in st.session_state:
    st.session_state.opponent_summary_df = pd.DataFrame()
if "opponent_detail_df" not in st.session_state:
    st.session_state.opponent_detail_df = pd.DataFrame()
if "opponent_loaded_person_id" not in st.session_state:
    st.session_state.opponent_loaded_person_id = None


# --- API 调用函数 ---
@st.cache_data(ttl=60)
def get_all_persons():
    try:
        response = requests.get(f"{API_BASE_URL}/persons/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []


def load_opponent_data(person_id: int):
    if not person_id:
        st.session_state.opponent_summary_df = pd.DataFrame()
        st.session_state.opponent_detail_df = pd.DataFrame()
        return

    with st.spinner(f"正在深度分析用户ID {person_id} 的对手方网络..."):
        try:
            # 1. 获取按名称聚合的分析数据
            summary_response = requests.get(
                f"{API_BASE_URL}/persons/{person_id}/counterparties/analysis_summary"
            )
            summary_response.raise_for_status()
            summary_data = summary_response.json()
            st.session_state.opponent_summary_df = (
                pd.DataFrame(summary_data) if summary_data else pd.DataFrame()
            )

            # 2. 获取该用户的所有原始交易记录
            all_transactions = []
            limit, skip = 100, 0
            while True:
                detail_response = requests.get(
                    f"{API_BASE_URL}/persons/{person_id}/transactions",
                    params={"skip": skip, "limit": limit},
                )
                detail_response.raise_for_status()
                detail_data = detail_response.json()
                if not detail_data:
                    break
                all_transactions.extend(detail_data)
                skip += limit

            if all_transactions:
                detail_df = pd.DataFrame(all_transactions)
                detail_df["transaction_date"] = pd.to_datetime(
                    detail_df["transaction_date"]
                ).dt.tz_convert("Asia/Shanghai")
                detail_df["counterparty_name"] = detail_df["counterparty"].apply(
                    lambda x: x["name"]
                )
                st.session_state.opponent_detail_df = detail_df
            else:
                st.session_state.opponent_detail_df = pd.DataFrame()

        except requests.exceptions.RequestException as e:
            st.error(f"加载对手方分析数据失败: {e}")
            st.session_state.opponent_summary_df = pd.DataFrame()
            st.session_state.opponent_detail_df = pd.DataFrame()


# --- 页面布局与逻辑 ---
persons = get_all_persons()
if not persons:
    st.warning("系统中还没有任何用户。")
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
        "请选择要分析的用户",
        options=person_df["full_name"],
        index=person_index,
        placeholder="请选择一个用户...",
    )

    if selected_person_name:
        st.session_state.selected_person_id = person_df[
            person_df["full_name"] == selected_person_name
        ]["id"].iloc[0]
        if (
            st.session_state.selected_person_id
            != st.session_state.opponent_loaded_person_id
        ):
            load_opponent_data(st.session_state.selected_person_id)
            st.session_state.opponent_loaded_person_id = (
                st.session_state.selected_person_id
            )
            st.rerun()
    else:
        st.session_state.opponent_summary_df = pd.DataFrame()
        st.session_state.opponent_detail_df = pd.DataFrame()
        st.session_state.opponent_loaded_person_id = None

# --- 数据展示 ---
if not st.session_state.opponent_summary_df.empty:
    summary_df = st.session_state.opponent_summary_df.copy()
    detail_df = st.session_state.opponent_detail_df.copy()

    st.markdown("---")
    st.markdown(f"### **{selected_person_name}** 的核心对手方网络")

    # 指标卡片
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric(label="👥 交易对手总数 (按名称)", value=len(summary_df))
    kpi2.metric(label="💰 全局总流水", value=f"¥ {summary_df['total_flow'].sum():,.2f}")
    if not summary_df.empty:
        top_flow_contact = summary_df.loc[summary_df["total_flow"].idxmax()]
        kpi3.metric(label="🔗 最大资金往来对手", value=str(top_flow_contact["name"]))
        top_freq_contact = summary_df.loc[summary_df["transaction_count"].idxmax()]
        kpi4.metric(label="📞 最频繁交易对手", value=str(top_freq_contact["name"]))

    # 可视化图表
    st.markdown("#### 资金往来 Top 10 对手方 (按总流水)")
    top_10_by_total_flow = summary_df.nlargest(10, "total_flow", keep="all")
    chart = (
        alt.Chart(top_10_by_total_flow)
        .mark_bar()
        .encode(
            x=alt.X("net_flow:Q", title="净流量 (元)"),
            y=alt.Y(
                "name:N",
                sort=alt.EncodingSortField(
                    field="total_flow", op="sum", order="descending"
                ),
                title="对手方",
            ),
            color=alt.condition(
                alt.datum.net_flow > 0, alt.value("green"), alt.value("red")
            ),
            tooltip=[
                "name",
                "total_income",
                "total_expense",
                "net_flow",
                "transaction_count",
                "total_flow",
            ],
        )
        .properties(height=400)
    )
    st.altair_chart(chart, use_container_width=True)

    # 详细交易使用 expander 和原始交易数据
    st.markdown("#### 对手方交易明细")
    sorted_summary_df = summary_df.sort_values("total_flow", ascending=False)

    for _, opponent in sorted_summary_df.iterrows():
        opponent_name = opponent["name"]
        with st.expander(
            f"**{opponent_name}** (总流水: ¥ {opponent['total_flow']:,.2f} | 交易次数: {opponent['transaction_count']})"
        ):
            opponent_transactions = detail_df[
                detail_df["counterparty_name"] == opponent_name
            ].copy()

            # 1. 在这里对局部的 DataFrame 进行中文映射
            type_mapping = {"CREDIT": "收入", "DEBIT": "支出"}
            opponent_transactions["type_cn"] = opponent_transactions[
                "transaction_type"
            ].map(type_mapping)

            # 2. 在表格中展示新列，并为时间列配置好格式
            st.dataframe(
                opponent_transactions[
                    [
                        "transaction_date",
                        "description",
                        "amount",
                        "type_cn",
                    ]
                ],
                column_config={
                    "transaction_date": st.column_config.DatetimeColumn(
                        "交易时间 (北京)", format="YYYY-MM-DD HH:mm:ss"
                    ),
                    "description": "摘要",
                    "amount": st.column_config.NumberColumn("金额", format="¥ %.2f"),
                    "type_cn": "类型",
                },
                use_container_width=True,
                hide_index=True,
            )
else:
    if selected_person_name:
        st.info("分析完毕，该用户没有任何对手方交易数据。")
