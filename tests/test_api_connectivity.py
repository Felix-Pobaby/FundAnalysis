from unittest.mock import patch


def test_verify_api_success(test_env):
    """模拟 API 连接成功场景"""
    mock_response = {"status": "ok", "message": "连接成功"}

    with patch("scripts.verify_api.connect_to_api", return_value=mock_response) as mock_connect:
        from scripts import verify_api
        result = verify_api.main_logic()
        assert result is True
        mock_connect.assert_called_once()


def test_verify_api_failure(test_env):
    """模拟 API 连接失败场景"""
    with patch("scripts.verify_api.connect_to_api", side_effect=ConnectionError("连接超时")):
        from scripts import verify_api
        result = verify_api.main_logic()
        assert result is False
