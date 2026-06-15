"""
查询工具 - 只查询不预约，用于测试接口和查看场地状态
"""

import json
from datetime import datetime, timedelta
from book import query_sessions, flatten_sessions, get_target_date, HEADERS, BASE_URL
from config import *
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def list_sport_types():
    """查看所有运动类型"""
    url = f"{BASE_URL}/wechat-c/api/wechat/indexController/sportTypeList"
    resp = requests.get(url, headers=HEADERS, verify=False)
    data = resp.json()
    print("=== 运动类型列表 ===")
    if isinstance(data, list):
        items = data
    else:
        items = data.get("data", [])
    for item in items:
        print(f"  ID: {item.get('id')} - {item.get('sportTypeName', item.get('name', ''))}")
    return data


def list_fields(sport_type_id=None):
    """查看某运动类型下的场地"""
    sid = sport_type_id or SPORT_TYPE_ID
    url = f"{BASE_URL}/wechat-c/api/wechat/memberBookController/fields?sportTypeId={sid}"
    resp = requests.get(url, headers=HEADERS, verify=False)
    data = resp.json()
    print(f"=== 场地列表 (sportTypeId={sid}) ===")
    if isinstance(data, list):
        items = data
    else:
        items = data.get("data", [])
    for item in items:
        print(f"  ID: {item.get('id')} - {item.get('fieldName', item.get('name', ''))}")
    return data


def show_sessions(date_str=None):
    """查看某天的所有时段状态"""
    date_str = date_str or get_target_date()
    print(f"=== {date_str} 时段状态 ({FIELD_NAME}) ===")
    data = query_sessions(date_str)
    sessions = flatten_sessions(data)

    for s in sessions:
        status = s.get("sessionsStatus", "?")
        marker = ">>>" if status in ("AVAILABLE", "CAN_BOOK", "OPEN") else "   "
        print(f"  {marker} {s.get('placeName', '?'):8} "
              f"{s.get('openStartTime', '?')}-{s.get('openEndTime', '?')} "
              f"状态: {status}")

    available_count = sum(1 for s in sessions if s.get("sessionsStatus") == "NO_RESERVED")
    print(f"\n  共 {len(sessions)} 个时段，{available_count} 个可预约")
    return sessions


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "types":
            list_sport_types()
        elif cmd == "fields":
            sid = sys.argv[2] if len(sys.argv) > 2 else None
            list_fields(sid)
        elif cmd == "sessions":
            date = sys.argv[2] if len(sys.argv) > 2 else None
            show_sessions(date)
        else:
            print("用法: python query.py [types|fields|sessions] [参数]")
    else:
        show_sessions()
