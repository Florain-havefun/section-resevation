"""
西南交通大学场地预约自动抢票脚本
每晚 22:30 放出后天场次，脚本会提前就位并高频轮询抢票
"""

import requests
import time
import json
from datetime import datetime, timedelta
from config import *

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://zhcg.swjtu.edu.cn/onesports-gateway"

HEADERS = {
    "Content-Type": "application/json",
    "token": TOKEN,
    "X-UserToken": TOKEN,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindo",
    "xweb_xhr": "1",
    "device-name": "microsoft",
    "os": "windows",
    "os-version": "Windows 10 x64",
}


def get_target_date():
    """获取目标日期（后天）"""
    if TARGET_DATE:
        return TARGET_DATE
    day_after_tomorrow = datetime.now() + timedelta(days=2)
    return day_after_tomorrow.strftime("%Y-%m-%d")


def date_to_timestamp(date_str):
    """日期字符串转毫秒时间戳"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return str(int(dt.timestamp() * 1000))


def query_sessions(date_str):
    """查询可预约时段"""
    url = f"{BASE_URL}/wechat-c/api/wechat/memberBookController/weChatSessionsList"
    body = {
        "fieldId": FIELD_ID,
        "isIndoor": "",
        "placeTypeId": "",
        "searchDate": date_str,
        "sportTypeId": SPORT_TYPE_ID,
        "memberId": MEMBER_ID,
    }
    resp = requests.post(url, json=body, headers=HEADERS, verify=False)
    resp.raise_for_status()
    return resp.json()

def check_token():
    """检测 token 是否有效"""
    url = f"{BASE_URL}/wechat-c/api/wechat/indexController/sportTypeList"
    try:
        resp = requests.get(url, headers=HEADERS, verify=False)
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            print("[+] Token 有效")
            return True
        if isinstance(data, dict):
            code = data.get("code")
            msg = data.get("msg", "")
            if code in (401, 403, 501):
                print(f"[-] Token 已过期! (code={code}, msg={msg})")
                print("    请重新打开微信小程序，用 Fiddler 抓取新 token 后更新 config.py")
                return False
    except Exception as e:
        print(f"[-] 网络异常，无法验证 token: {e}")
        return False
    print("[-] Token 可能已失效，返回异常")
    return False


def flatten_sessions(data):
    """展平响应数据（可能是嵌套列表）"""
    sessions = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, list):
                sessions.extend(item)
            elif isinstance(item, dict):
                sessions.append(item)
    elif isinstance(data, dict):
        inner = data.get("data", data.get("rows", []))
        if isinstance(inner, list):
            return flatten_sessions(inner)
    return sessions


def find_available_sessions(sessions):
    """从返回数据中筛选可预约时段"""
    available = []
    for s in sessions:
        status = s.get("sessionsStatus", "")
        if status == "NO_RESERVED":
            available.append(s)
    return available


def pick_best_session(available):
    """根据偏好选择最优时段"""
    if not available:
        return None

    if PREFERRED_START_TIMES:
        for pref_time in PREFERRED_START_TIMES:
            for s in available:
                if s.get("openStartTime") == pref_time:
                    if not PREFERRED_SITE_NAMES or s.get("placeName") in PREFERRED_SITE_NAMES:
                        return s

    if PREFERRED_SITE_NAMES:
        for s in available:
            if s.get("placeName") in PREFERRED_SITE_NAMES:
                return s

    return available[0]


def reserve_session(session, date_str):
    """提交预约"""
    url = f"{BASE_URL}/business-service/orders/weChatSessionsReserve"
    body = {
        "number": 1,
        "orderUseDate": date_to_timestamp(date_str),
        "requestsList": [{"sessionsId": session["id"]}],
        "fieldName": FIELD_NAME,
        "fieldId": FIELD_ID,
        "siteName": session.get("placeName", ""),
        "sportTypeName": SPORT_TYPE_NAME,
        "sportTypeId": SPORT_TYPE_ID,
    }
    resp = requests.post(url, json=body, headers=HEADERS, verify=False)
    resp.raise_for_status()
    return resp.json()


def wait_until_grab_time():
    """等待到放票时间前 PRE_START_SECONDS 秒"""
    now = datetime.now()
    grab_h, grab_m, grab_s = map(int, GRAB_TIME.split(":"))
    target_time = now.replace(hour=grab_h, minute=grab_m, second=grab_s, microsecond=0)

    # 如果已经过了今天的放票时间，说明手动运行的，直接开抢
    if now >= target_time:
        print(f"[*] 已过今天的放票时间 {GRAB_TIME}，直接开始抢票")
        return

    start_time = target_time - timedelta(seconds=PRE_START_SECONDS)
    wait_seconds = (start_time - now).total_seconds()

    if wait_seconds > 0:
        print(f"[*] 当前时间: {now.strftime('%H:%M:%S')}")
        print(f"[*] 放票时间: {GRAB_TIME}")
        print(f"[*] 将在 {start_time.strftime('%H:%M:%S')} 开始发请求（提前 {PRE_START_SECONDS} 秒）")
        print(f"[*] 等待 {wait_seconds:.0f} 秒...")
        print()

        # 每30秒打印一次倒计时
        while True:
            remaining = (start_time - datetime.now()).total_seconds()
            if remaining <= 0:
                break
            if remaining > 30:
                print(f"    倒计时: {remaining:.0f} 秒")
                time.sleep(30)
            else:
                time.sleep(remaining)
                break

    print(f"[!] 开始抢票! 当前时间: {datetime.now().strftime('%H:%M:%S.%f')}")


def run():
    """主流程"""
    date_str = get_target_date()
    print("=" * 50)
    print(f"  西南交通大学网球场自动抢票")
    print("=" * 50)
    print(f"[*] 目标日期: {date_str}")
    print(f"[*] 运动类型: {SPORT_TYPE_NAME} (ID: {SPORT_TYPE_ID})")
    print(f"[*] 场地: {FIELD_NAME}")
    print(f"[*] 偏好时段: {PREFERRED_START_TIMES or '任意'}")
    print(f"[*] 轮询间隔: {RETRY_INTERVAL}s，最多 {MAX_RETRIES} 次")
    print()

    # 检测 token
    if not check_token():
        return False

    # 等待放票时间
    wait_until_grab_time()
    print("-" * 50)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            data = query_sessions(date_str)
            sessions = flatten_sessions(data)
            available = find_available_sessions(sessions)

            if available:
                print(f"\n[+] 第 {attempt} 次查询，找到 {len(available)} 个可预约时段:")
                for s in available[:5]:
                    print(f"    {s.get('placeName')} {s.get('openStartTime')}-{s.get('openEndTime')}")

                target = pick_best_session(available)
                print(f"\n[!] 选中: {target.get('placeName')} {target.get('openStartTime')}-{target.get('openEndTime')}")
                print("[*] 正在提交预约...")

                result = reserve_session(target, date_str)
                print(f"[+] 预约结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                print(f"\n{'=' * 50}")
                print(f"  抢票成功! {target.get('placeName')} {date_str} {target.get('openStartTime')}")
                print(f"{'=' * 50}")
                return True
            else:
                ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                status_set = set(s.get("sessionsStatus") for s in sessions) if sessions else set()
                print(f"[{ts}] 第{attempt}次 | 暂无可用 | 状态: {status_set}")

        except requests.exceptions.RequestException as e:
            print(f"[{attempt}/{MAX_RETRIES}] 请求异常: {e}")
        except Exception as e:
            print(f"[{attempt}/{MAX_RETRIES}] 错误: {e}")

        time.sleep(RETRY_INTERVAL)

    print("\n[-] 达到最大重试次数，抢票失败")
    return False


if __name__ == "__main__":
    run()
