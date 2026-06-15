# 西南交通大学场地预约 - 自动抢票脚本

## 文件说明

- `config.py` — 配置文件，修改 token、场地、时间偏好等
- `book.py` — 主抢票脚本，定时轮询+自动预约
- `query.py` — 查询工具，测试接口用

## 使用步骤

### 1. 安装依赖

```bash
pip install requests
```

### 2. 修改配置

编辑 `config.py`：

- `TOKEN` — 从 Fiddler 抓包获取（过期后需重新抓）
- `FIELD_ID` — 目标场地 ID
- `TARGET_DATE` — 想抢的日期（留空=明天）
- `PREFERRED_START_TIMES` — 偏好时段

### 3. 先测试查询

```bash
# 查看运动类型
python query.py types

# 查看场地列表
python query.py fields

# 查看明天的时段状态
python query.py sessions

# 查看指定日期
python query.py sessions 2026-06-20
```

### 4. 开始抢票

```bash
python book.py
```

脚本会每 0.5 秒查询一次，发现可预约时段后自动提交。

## 注意事项

- Token 有效期未知，建议每次使用前先 `python query.py` 测试是否能正常返回数据
- 如果返回 401 或空数据，需要重新打开小程序用 Fiddler 抓新 token
- `sessionsStatus` 的可用状态可能是 `AVAILABLE`、`CAN_BOOK` 或 `OPEN`，首次运行 `query.py` 观察实际值后可在 `book.py` 的 `find_available_sessions` 函数中调整
