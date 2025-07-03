import streamlit as st
from navigation import make_sidebar


st.set_page_config(page_title="明镜 D-Sensor", page_icon="🔍", layout="wide")

make_sidebar()  # 一定要在set_page_config之后调用

st.title("欢迎来到 明镜 D-Sensor 智能分析平台 🔍")
st.markdown("""
### 让每一笔交易都有迹可循，用AI点亮你的财务洞察。

**“明镜”** 是一个高级个人数据分析平台，旨在整合、分析来自不同银行的个人交易流水，利用现代化的Python技术栈进行深度分析。

**请在左侧的侧边栏中选择您要使用的功能：**
- 📄**文件上传**: 上传新的银行流水单 (Excel/CSV)。
- 📊**交易看板**: 查看和分析您的交易数据。
""")
