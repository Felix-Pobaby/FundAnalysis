import os
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录（data/config.py 的上两级）
BASE_DIR = Path(__file__).resolve().parent.parent

# 加载 .env 文件
load_dotenv(BASE_DIR / ".env")


class Settings:
    """集中管理所有配置项，从环境变量读取。"""

    def __init__(self):
        # 同花顺 API
        self.ths_api_username = os.getenv("THS_API_USERNAME", "")
        self.ths_api_password = os.getenv("THS_API_PASSWORD", "")
        self.ths_api_token = os.getenv("THS_API_TOKEN", "")

        # 数据库
        self.db_path = os.getenv("DB_PATH", "data/fund_analysis.db")

        # API 请求
        self.api_timeout = int(os.getenv("API_TIMEOUT", "30"))
        self.api_max_retries = int(os.getenv("API_MAX_RETRIES", "3"))


# 全局单例
settings = Settings()
