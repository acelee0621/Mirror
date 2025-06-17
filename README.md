
# Mirror - Personal Financial Analysis System

**Mirror** is a Python-based project designed to automate the processing and analysis of bank transaction data from various sources. By leveraging modern Python technologies and an agile development approach, it aims to standardize, clean, and analyze financial data, providing clear insights into fund flows with AI-driven capabilities.

## Key Features
- **Data Integration**: Parses and standardizes Excel/CSV bank statements with varying formats.
- **Asynchronous Processing**: Uses FastAPI, SQLAlchemy 2.0, and TaskIQ for efficient data handling.
- **AI-Powered Insights**: Integrates PandasAI and local LLMs (via Ollama) for natural language queries and fraud detection.
- **Interactive Dashboard**: Visualizes transaction data with Streamlit for intuitive analysis.

## Tech Stack
- **Backend**: FastAPI, SQLAlchemy 2.0 (async), PostgreSQL
- **Task Queue**: TaskIQ, RabbitMQ, Redis
- **Data Analysis**: Pandas, PandasAI
- **Frontend**: Streamlit
- **AI Engine**: Ollama (local LLM)

## Goals
Built as a learning project, Mirror follows an agile development roadmap with iterative sprints to deliver functional modules, from data ingestion to AI-driven financial insights, potentially aiding in corruption case analysis.

