import streamlit as st
import requests
import pandas as pd
import altair as alt
from navigation import make_sidebar

# --- 配置 ---
API_BASE_URL = "http://127.0.0.1:8000/api/v1"

st.set_page_config(
    page_title="个人全局视图 - 明镜 D-Sensor", page_icon="🌍", layout="wide"
)

make_sidebar()

st.title("🌍 个人全局视图")
st.markdown("在这里，您可以一览自己所有账户的完整交易流水和财务全貌。")

# --- 会话状态初始化 ---
if "selected_person_id" not in st.session_state:
    st.session_state.selected_person_id = None
if "global_transactions_df" not in st.session_state:
    st.session_state.global_transactions_df = pd.DataFrame()
if "global_loaded_person_id" not in st.session_state:
    st.session_state.global_loaded_person_id = None


# --- API 调用函数 (不变) ---
@st.cache_data(ttl=60)
def get_all_persons():
    try:
        response = requests.get(f"{API_BASE_URL}/persons/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []


def load_global_transactions(person_id: int):
    if not person_id:
        st.session_state.global_transactions_df = pd.DataFrame()
        return
    with st.spinner(f"正在加载用户ID {person_id} 的全部交易数据..."):
        try:
            all_transactions = []
            limit, skip = 100, 0
            while True:
                response = requests.get(
                    f"{API_BASE_URL}/persons/{person_id}/transactions",
                    params={"skip": skip, "limit": limit},
                )
                response.raise_for_status()
                data = response.json()
                if not data:
                    break
                all_transactions.extend(data)
                skip += limit

            if all_transactions:
                df = pd.DataFrame(all_transactions)
                df["transaction_date"] = pd.to_datetime(
                    df["transaction_date"]
                ).dt.tz_convert("Asia/Shanghai")
                df["account_name"] = df["account"].apply(lambda x: x["account_name"])
                df["counterparty_name"] = df["counterparty"].apply(lambda x: x["name"])
                df.drop(columns=["account", "counterparty"], inplace=True)
                st.session_state.global_transactions_df = df
            else:
                st.session_state.global_transactions_df = pd.DataFrame()
        except requests.exceptions.RequestException as e:
            st.error(f"加载全局交易数据失败: {e}")
            st.session_state.global_transactions_df = pd.DataFrame()


@st.cache_data
def convert_df_to_csv(df: pd.DataFrame):
    return df.to_csv(index=False).encode("utf-8-sig")


# --- 页面布局与逻辑 (不变) ---
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
            != st.session_state.global_loaded_person_id
        ):
            load_global_transactions(st.session_state.selected_person_id)
            st.session_state.global_loaded_person_id = (
                st.session_state.selected_person_id
            )
            st.rerun()
    else:
        st.session_state.global_transactions_df = pd.DataFrame()
        st.session_state.global_loaded_person_id = None

# --- 数据展示与筛选 ---
if not st.session_state.global_transactions_df.empty:
    df = st.session_state.global_transactions_df.copy()
    type_mapping = {"CREDIT": "收入", "DEBIT": "支出"}
    df["type_cn"] = df["transaction_type"].map(type_mapping)

    st.markdown("---")
    st.markdown(f"### **{selected_person_name}** 的财务总览")

    # ... 筛选器代码不变 ...
    with st.expander("点击展开筛选器", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            min_date, max_date = (
                df["transaction_date"].min().date(),
                df["transaction_date"].max().date(),
            )
            date_range = st.date_input(
                "选择日期范围",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
        with col2:
            selected_types_cn = st.multiselect(
                "交易类型",
                options=df["type_cn"].unique(),
                default=df["type_cn"].unique(),
            )
        with col3:
            search_term = st.text_input(
                "摘要或对手方关键字", placeholder="例如：星巴克、工资..."
            )

    if len(date_range) == 2:
        start_date, end_date = date_range
        df = df[
            (df["transaction_date"].dt.date >= start_date)
            & (df["transaction_date"].dt.date <= end_date)
        ]
    if selected_types_cn:
        df = df[df["type_cn"].isin(selected_types_cn)]
    if search_term:
        df = df[
            df["description"].str.contains(search_term, case=False, na=False)
            | df["counterparty_name"].str.contains(search_term, case=False, na=False)
            | df["transaction_method"].str.contains(search_term, case=False, na=False)
            | df["location"].str.contains(search_term, case=False, na=False)
            | df["branch_name"].str.contains(search_term, case=False, na=False)
        ]

    filtered_df = df

    st.markdown("#### 📊 关键指标")
    total_income = filtered_df[filtered_df["transaction_type"] == "CREDIT"][
        "amount"
    ].sum()
    total_expense = filtered_df[filtered_df["transaction_type"] == "DEBIT"][
        "amount"
    ].sum()
    net_flow = total_income + total_expense

    # --- 【核心修改点 1】: 计算并显示全局最终余额 ---
    total_final_balance = 0.0
    if not filtered_df.empty:
        # 按账户分组，找到每个账户的最后一条交易，然后求和
        latest_txn_indices = filtered_df.groupby("account_name")[
            "transaction_date"
        ].idxmax()
        latest_txns_df = filtered_df.loc[latest_txn_indices]
        total_final_balance = latest_txns_df["balance_after_txn"].sum()

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric(label="🔼 总收入", value=f"¥ {total_income:,.2f}")
    kpi2.metric(label="🔽 总支出", value=f"¥ {abs(total_expense):,.2f}")
    kpi3.metric(label="↔️ 净流量", value=f"¥ {net_flow:,.2f}")
    kpi4.metric(label="🔢 总交易笔数", value=f"{len(filtered_df)}")
    kpi5.metric(label="🏦 全局期末余额", value=f"¥ {total_final_balance:,.2f}")

    st.markdown("#### 📈 可视化分析")
    # --- 【核心修改点 2】: 实现Top 5收支对手方合并图表 (逻辑同上) ---
    st.write("**Top 5 收入 & 支出对手方 (全局)**")
    top_5_expense_names = (
        filtered_df[filtered_df.type_cn == "支出"]
        .groupby("counterparty_name")["amount"]
        .sum()
        .abs()
        .nlargest(5)
        .index
    )
    top_5_income_names = (
        filtered_df[filtered_df.type_cn == "收入"]
        .groupby("counterparty_name")["amount"]
        .sum()
        .nlargest(5)
        .index
    )
    top_opponents = top_5_expense_names.union(top_5_income_names)
    chart_df = filtered_df[filtered_df.counterparty_name.isin(top_opponents)]
    chart_data = (
        chart_df.groupby(["counterparty_name", "type_cn"])["amount"].sum().reset_index()
    )
    chart = (
        alt.Chart(chart_data)
        .mark_bar()
        .encode(
            x=alt.X("amount:Q", title="金额 (元)"),
            y=alt.Y("counterparty_name:N", sort="-x", title="对手方"),
            color=alt.Color(
                "type_cn:N",
                scale=alt.Scale(domain=["收入", "支出"], range=["#2ca02c", "#d62728"]),
                title="类型",
            ),
            tooltip=["counterparty_name", "type_cn", "amount"],
        )
    )
    st.altair_chart(chart, use_container_width=True)

    st.markdown("#### 📋 交易明细 (全局)")
    # ... 表格部分代码不变 ...
    display_columns = [
        "transaction_date",
        "account_name",
        "description",
        "counterparty_name",
        "amount",
        "type_cn",
        "balance_after_txn",
        "currency",
        "transaction_method",
        "is_cash",
        "location",
        "branch_name",
        "bank_transaction_id",
        "category",
    ]
    csv = convert_df_to_csv(filtered_df[display_columns])
    st.download_button(
        label="📥 下载筛选结果为 CSV",
        data=csv,
        file_name=f"{selected_person_name}_global_transactions.csv",
        mime="text/csv",
    )
    st.dataframe(
        filtered_df[display_columns],
        column_config={
            "transaction_date": st.column_config.DatetimeColumn(
                "交易时间 (北京)", format="YYYY-MM-DD HH:mm:ss"
            ),
            "account_name": "所属账户",
            "description": "交易摘要",
            "counterparty_name": "对手方",
            "amount": st.column_config.NumberColumn("金额", format="¥ %.2f"),
            "type_cn": "类型",
            "balance_after_txn": st.column_config.NumberColumn(
                "交易后余额", format="¥ %.2f"
            ),
            "currency": "币种",
            "transaction_method": "交易渠道",
            "is_cash": "是否现金",
            "location": "交易地点",
            "branch_name": "交易网点",
            "bank_transaction_id": "银行流水号",
            "category": "交易分类",
        },
        use_container_width=True,
        hide_index=True,
        height=600,
    )

elif selected_person_name:
    st.info("该用户没有任何交易数据。")
