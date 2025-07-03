# Mirror - 个人金融数据智能分析平台 🔍

**让每一笔交易都有迹可循，用AI点亮你的财务洞察。**

---

## 📖 项目简介 (About The Project)

**Mirror** 是一个基于现代Python技术栈构建的高级个人数据分析平台。

在我们的日常生活中，银行流水数据分散在各个银行的App或导出的不同格式文件中，难以进行统一的管理和分析。本项目旨在解决这一痛点，其核心目标是：

1.  **整合分析**：自动化地整合、分析来自不同银行的个人交易流水（Excel/CSV格式）。
2.  **深度洞察**：利用数据分析和AI技术进行深度取证分析，以识别潜在的金融风险模式。
3.  **学习实践**：作为一个绝佳的学习平台，旨在实践并掌握全栈的、异步的Python Web开发与数据科学技术。

本项目将严格遵循敏捷开发的思想，通过一系列迭代（Sprints）逐步构建，确保每个阶段都有可用的功能产出。

## ✨ 核心功能 (Key Features)

- **📂 多源数据整合**: 支持并自动化解析、清洗、标准化来自不同银行的Excel和CSV流水文件。
- **⚙️ 异步任务处理**: 所有耗时的数据处理任务均在后台异步执行，保证前端界面的流畅体验。
- **🔒 安全数据存储**: 将所有交易数据持久化存储在强大的PostgreSQL数据库中（后期将加入加密功能）。
- **📊 交互式仪表盘**: 通过Streamlit构建美观、可交互的数据看板，直观展示财务状况。
- **💬 AI对话式分析**: 集成以本地大语言模型（LLM）驱动的AI，允许用户通过自然语言进行数据查询。
- **🤖 智能异常检测**: 在后期迭代中，将引入多层次的机器学习模型，以发现潜在的、未知的异常模式。

## 🛠️ 技术栈 (Tech Stack)

| 类别 | 技术/工具 |
| :--- | :--- |
| **后端 API** | FastAPI, Pydantic |
| **数据库** | PostgreSQL |
| **ORM & 迁移** | SQLAlchemy 2.0 (async), Alembic |
| **异步任务队列** | Taskiq, RabbitMQ, Redis |
| **前端界面** | Streamlit |
| **数据处理** | Pandas, openpyxl |
| **AI 交互/分析** | Pandas-AI, Ollama, Scikit-learn, PyTorch |
| **开发与部署** | Docker, uv |

## 🚧 开发进度 (Development Progress)

> **当前状态：** 第一阶段（核心数据管道）已实现，筹备第二阶段中...

---

### 敏捷迭代计划 (Agile Sprints)

- ✅ **Sprint 0: 项目基础与架构设计**
    - [x] 技术选型与可行性分析
    - [x] 系统分层架构设计
    - [x] 数据库模型构建与关系设计
    - [x] 初始化项目结构与Git工作流

- ⏳ **Sprint 1: 核心数据管道与展示 (已完成，后续再优化...)**
    - [x] **后端**: 实现文件上传API接口
    - [x] **异步任务**: 集成Taskiq，实现后台数据解析任务
    - [x] **数据处理**: 使用Pandas实现对Excel/CSV的清洗与标准化
    - [x] **数据库**: 实现数据入库逻辑
    - [x] **前端**: 使用Streamlit实现文件上传和基本的数据表格展示

- 📝 **Sprint 2: 高级分析与交互式仪表盘 (计划中)**
- 📝 **Sprint 3 & 4: AI 集成与智能交互 (计划中)**
- 📝 **Sprint 5: 安全强化与打包 (计划中)**

## 🚀 快速开始 (Getting Started)

### 先决条件

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (推荐的包管理工具)
- [Docker](https://www.docker.com/) (用于运行外部服务)
- 本地已通过Docker运行PostgreSQL, Redis, RabbitMQ服务。

### 安装与配置

1.  **克隆项目**
    ```bash
    git clone [https://github.com/acelee0621/Mirror.git](https://github.com/acelee0621/Mirror.git)
    cd Mirror
    ```

2.  **创建并激活虚拟环境**
    ```bash
    uv venv
    source .venv/bin/activate
    ```

3.  **安装依赖**
    ```bash
    uv pip install -r requirements.txt
    ```

4.  **配置环境变量**
    复制`.env.example`文件为`.env`，并根据你的本地服务配置修改其中的数据库、Redis和RabbitMQ连接信息。
    ```bash
    cp .env.example .env
    ```

5.  **运行数据库迁移**
    首次运行时，需要创建所有数据表。
    ```bash
    alembic upgrade head
    ```

### 运行项目

1.  **启动FastAPI后端服务**
    ```bash
    uvicorn app.main:app --reload
    ```
    API将在 `http://127.0.0.1:8000` 运行。

2.  **启动Streamlit前端应用**
    在新的终端窗口中运行：
    ```bash
    streamlit run app_streamlit/Home.py
    ```
    前端应用将在 `http://localhost:8501` 运行。
    
3.  **启动Taskiq Worker进程**
    在新的终端窗口中运行：
    ```bash
    taskiq worker app.tasks.broker:broker
    ```

## 🗺️ 未来路线图 (Roadmap)

- [ ] **支持PDF文件解析**
- [ ] **实现用户认证与数据隔离**
- [ ] **对敏感数据进行列级加密**
- [ ] **实现AI驱动的“个人财务顾问”报告生成**
- [ ] **集成“百变性格”的AI助手**
- [ ] **打包整个应用为Docker Compose，实现一键部署**

## 📄 许可证 (License)

本项目采用 MIT 许可证。详情请见 `LICENSE` 文件。

## 🙏 致谢 (Acknowledgements)

- 感谢所有本项目使用的开源工具的开发者。

---
