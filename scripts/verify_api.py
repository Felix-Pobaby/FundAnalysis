"""同花顺 API 连通性验证脚本。

运行: python scripts/verify_api.py
返回: 0 表示连接成功，1 表示失败
"""
import sys
from pathlib import Path
from iFinDPy import *  # noqa: F401, F403

# 将项目根目录加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.config import settings


def connect_to_api():
    """尝试连接同花顺 API。

    TODO: 接入真实的同花顺 API SDK 或 HTTP 请求。
    当前使用占位实现，仅验证凭证是否已配置。
    """
    if not settings.ths_api_username or not settings.ths_api_token:
        raise ConnectionError(
            "未配置 API 凭证，请编辑 .env 文件填写 THS_API_USERNAME 和 THS_API_TOKEN"
        )

    # TODO: 替换为真实 API 调用
    # 示例：使用同花顺 iFinD SDK 或 HTTP 接口
    # from ths_api import THSClient
    # client = THSClient(username=settings.ths_api_username, token=settings.ths_api_token)
    # client.login()
    # return client.query("test_query")

    return {"status": "ok", "message": "凭证已配置（真实API调用待接入）"}


def main_logic():
    """执行连通性检查，返回 True/False。"""
    try:
        print("正在连接同花顺 API...")
        print(f"  用户名: {settings.ths_api_username or '(未配置)'}")
        print(f"  超时设置: {settings.api_timeout}s")

        result = connect_to_api()

        if result.get("status") == "ok":
            print(f"[OK] 连接成功: {result.get('message', 'OK')}")
            return True
        else:
            print(f"[FAIL] 连接失败: {result.get('message', '未知错误')}")
            return False

    except ConnectionError as e:
        print(f"[FAIL] 连接失败: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] 未知错误: {type(e).__name__}: {e}")
        return False


def main_THS():
    """同花顺 API 连接测试入口。"""
    print("=== 同花顺 API 连通性验证 ===")
    THS_iFinDLogin(settings.ths_api_username, settings.ths_api_password)
    a = THS_RQ('920000.BJ','open')
    print(a)
    print(a.data)

if __name__ == "__main__":
    success = main_THS()
    sys.exit(0 if success else 1)
