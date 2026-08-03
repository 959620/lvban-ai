"""学生 / 课程相关枚举与预设数据。"""

MAJORS = [
    "建筑设计",
    "工业设计",
    "服装设计",
    "视觉传达",
    "插画",
    "动画",
    "电影",
    "摄影",
    "游戏设计",
]

APPLICATION_STAGES = [
    "意向确认",
    "选校规划",
    "作品集制作",
    "文书准备",
    "网申提交",
    "面试/作品集面试",
    "录取结果",
    "签证入学",
]

SCHOOL_PRIORITIES = ["主申", "冲刺", "保底"]

COURSE_TYPES = ["训练营", "一对一", "工作坊", "系列课", "其他"]

COURSE_SUITABLE_STAGES = [
    *APPLICATION_STAGES,
    "申请前6个月",
    "申请前3个月",
    "临近网申",
]

PRESET_TAGS = [
    {"name": "执行力强", "category": "行为"},
    {"name": "拖延严重", "category": "行为"},
    {"name": "家长关注度高", "category": "家庭"},
    {"name": "需要强督促", "category": "行为"},
    {"name": "有艺术基础", "category": "学业"},
    {"name": "英语薄弱", "category": "学业"},
]
