import streamlit as st


def make_sidebar():
    """
    创建一个统一的、在所有页面共享的侧边栏 (V5: 增加管理中心)
    """
    with st.sidebar:
        # 隐藏 Streamlit 自动生成的页面导航
        st.markdown(
            """
            <style>
                [data-testid="stSidebarNav"] > ul {
                    display: none;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # 创建我们自己的、完全自定义的导航
        st.title("🔍 明镜 D-Sensor")
        st.markdown("---")
        st.header("数据看板")
        st.page_link("Home.py", label="主页", icon="🏠")
        st.page_link("pages/2_Account_Details.py", label="账户明细", icon="🧾")
        st.page_link("pages/3_Global_Dashboard.py", label="个人全局视图", icon="🌍")
        st.page_link("pages/4_Counterparty_Analysis.py", label="对手方网络", icon="🤝")        
        st.markdown("---")
        st.header("智能分析")        
        st.page_link("pages/6_Forensic_Analysis.py", label="法证分析", icon="🔬")
        st.page_link("pages/7_Group_Analysis.py", label="共同对手方分析", icon="🔗")
        st.markdown("---")
        st.header("数据管理")
        st.page_link("pages/1_File_Upload.py", label="文件上传", icon="📄")        
        st.page_link("pages/5_Management_Center.py", label="管理中心", icon="⚙️")
