import streamlit as st


def make_sidebar():
    """
    创建一个统一的、在所有页面共享的侧边栏 (V4: 最终完美版)
    - 使用官方推荐的 pages 文件夹结构
    - 使用 st.page_link 实现无刷新、单页内导航
    - 使用 CSS 隐藏自动生成的英文导航，只保留我们自定义的中文导航
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
        st.header("功能导航")

        st.page_link("Home.py", label="主页", icon="🏠")

        st.page_link("pages/1_File_Upload.py", label="文件上传", icon="📄")

        st.page_link("pages/2_Account_Details.py", label="账户明细", icon="📊")

        st.page_link("pages/3_Global_Dashboard.py", label="个人全景视图", icon="🌍")

        st.page_link("pages/4_Counterparty_Analysis.py", label="对手方网络", icon="🤝")

        # 如果未来有更多页面，在这里继续添加即可
        # st.page_link("pages/3_AI_Analysis.py", label="AI智能分析", icon="🤖")
