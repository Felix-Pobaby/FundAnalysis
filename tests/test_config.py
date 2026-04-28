import os
from data.config import Settings


def test_settings_loads_from_env():
    """Settings 应从 .env 文件加载配置"""
    settings = Settings()
    assert hasattr(settings, "ths_api_username")
    assert hasattr(settings, "ths_api_password")
    assert hasattr(settings, "ths_api_token")
    assert hasattr(settings, "db_path")
    assert hasattr(settings, "api_timeout")
    assert hasattr(settings, "api_max_retries")


def test_settings_default_values():
    """未设置环境变量时应使用默认值"""
    settings = Settings()
    assert settings.db_path == "data/fund_analysis.db"
    assert settings.api_timeout == 30
    assert settings.api_max_retries == 3


def test_settings_env_overrides_defaults(test_env):
    """环境变量应覆盖默认值"""
    import os
    settings = Settings()
    assert settings.ths_api_username == os.getenv("THS_API_USERNAME")
    assert settings.api_timeout == 10
    assert settings.api_max_retries == 1
