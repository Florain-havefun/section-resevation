# ==================== 配置文件 ====================
# 修改以下参数来设置你的抢票偏好

# 认证信息（从 Fiddler 抓包获取，过期后需要重新抓）
TOKEN = "2b08b95f-bed6-4058-a81b-b69f5f1de9bf"
MEMBER_ID = "1827515696602423296"

# ==================== 场地配置 ====================
# 当前使用哪个配置：填 "tennis" 或 "pingpong"
ACTIVE = "tennis"

# 网球配置
TENNIS = {
    "sport_type_id": "4",
    "sport_type_name": "网球",
    "field_id": "1462414694990233600",
    "field_name": "犀浦网球场（露天场）",
    "preferred_times": ["20:00:00", "21:00:00", "22:00:00", "19:00:00"],
}

# 乒乓球配置
PINGPONG = {
    "sport_type_id": "3",
    "sport_type_name": "乒乓球",
    "field_id": "1575405781299240960",
    "field_name": "犀浦乒乓球馆",
    "preferred_times": ["20:00:00", "21:00:00", "19:00:00"],
}

# ==================== 根据 ACTIVE 加载配置 ====================
_CFG = TENNIS if ACTIVE == "tennis" else PINGPONG

SPORT_TYPE_ID = _CFG["sport_type_id"]
SPORT_TYPE_NAME = _CFG["sport_type_name"]
FIELD_ID = _CFG["field_id"]
FIELD_NAME = _CFG["field_name"]
PREFERRED_START_TIMES = _CFG["preferred_times"]

# 场地偏好（留空则抢任意可用场地）
PREFERRED_SITE_NAMES = []

# 目标日期（格式: YYYY-MM-DD，留空则自动选择后天 - 每晚22:30放出后天场次）
TARGET_DATE = ""

# 抢票设置
GRAB_TIME = "22:30:00"     # 每天放票时间
PRE_START_SECONDS = 5      # 提前多少秒开始发请求
RETRY_INTERVAL = 0.3       # 轮询间隔（秒）
MAX_RETRIES = 200          # 最大重试次数（0.3秒 * 200 = 60秒）
