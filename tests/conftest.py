import pytest


@pytest.fixture
def test_env(tmp_path, monkeypatch):
    """为需要隔离环境的测试提供独立配置。

    使用方式：在测试函数参数中声明 test_env fixture。
    不声明的测试将使用真实环境变量（便于测试默认值行为）。
    """
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("THS_API_USERNAME", "test_user")
    monkeypatch.setenv("THS_API_PASSWORD", "test_pass")
    monkeypatch.setenv("THS_API_TOKEN", "test_token")
    monkeypatch.setenv("API_TIMEOUT", "10")
    monkeypatch.setenv("API_MAX_RETRIES", "1")


@pytest.fixture
def mock_api_response():
    """返回模拟的同花顺 API 响应数据。"""
    return {
        "status": "ok",
        "data": {
            "fund_code": "000001",
            "fund_name": "华夏成长混合",
            "fund_type": "混合型",
            "nav": 1.234,
            "acc_nav": 3.456,
        },
    }
