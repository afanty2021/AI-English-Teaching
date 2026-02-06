"""
业务常量定义 - AI英语教学系统

集中管理系统中的硬编码数字和配置值，提高代码可维护性。
遵循 DRY 原则，消除魔法数字。

模块结构：
- ABILITY_LEVELS: 能力等级阈值
- REVIEW_INTERVALS: 复习间隔（艾宾浩斯遗忘曲线）
- TIME_THRESHOLDS: 时间阈值（小时）
- PRIORITY_WEIGHTS: 优先级计算权重
- MASTERY_LEVELS: 掌握度等级
- TOKEN_CONSTANTS: Token相关常量
"""

from enum import IntEnum
from typing import Dict

# =============================================================================
# 能力等级常量
# =============================================================================

class AbilityLevels(IntEnum):
    """
    能力等级枚举

    等级划分基于欧洲语言共同参考框架（CEFR）和英语能力评分标准：
    - EXCELLENT (90+): 优秀水平，接近母语者
    - GOOD (75-89): 良好水平，可流畅交流
    - INTERMEDIATE (60-74): 中级水平，日常沟通无障碍
    - BASIC (40-59): 基础水平，简单表达
    - NEEDS_IMPROVEMENT (0-39): 需要提升，基础薄弱
    """
    EXCELLENT = 90
    GOOD = 75
    INTERMEDIATE = 60
    BASIC = 40
    NEEDS_IMPROVEMENT = 0

    @classmethod
    def get_level_name(cls, score: float) -> str:
        """根据分数获取等级名称"""
        if score >= cls.EXCELLENT:
            return "excellent"
        elif score >= cls.GOOD:
            return "good"
        elif score >= cls.INTERMEDIATE:
            return "intermediate"
        elif score >= cls.BASIC:
            return "basic"
        else:
            return "needs_improvement"


# 能力等级区间映射（用于UI显示和分类）
ABILITY_RANGES = {
    "excellent": (AbilityLevels.EXCELLENT, 100),
    "good": (AbilityLevels.GOOD, AbilityLevels.EXCELLENT - 1),
    "intermediate": (AbilityLevels.INTERMEDIATE, AbilityLevels.GOOD - 1),
    "basic": (AbilityLevels.BASIC, AbilityLevels.INTERMEDIATE - 1),
    "needs_improvement": (AbilityLevels.NEEDS_IMPROVEMENT, AbilityLevels.BASIC - 1),
}


# =============================================================================
# 复习间隔常量（艾宾浩斯遗忘曲线）
# =============================================================================

class ReviewIntervals(IntEnum):
    """
    复习间隔常量（单位：天）

    基于艾宾浩斯遗忘曲线的复习间隔：
    - 1天、3天、7天、14天、30天

    科学依据：
    - 遗忘在学习后的最初几小时内最快
    - 第1次复习应在学习后24小时内
    - 后续复习间隔逐渐延长
    """
    FIRST = 1          # 第1次复习：1天后
    SECOND = 3         # 第2次复习：3天后
    THIRD = 7          # 第3次复习：7天后
    FOURTH = 14        # 第4次复习：14天后
    FIFTH = 30         # 第5次复习：30天后
    MAX = 30           # 最大复习间隔

    @classmethod
    def get_interval_sequence(cls) -> list[int]:
        """获取完整的复习间隔序列"""
        return [cls.FIRST, cls.SECOND, cls.THIRD, cls.FOURTH, cls.FIFTH]


# =============================================================================
# 时间阈值常量（单位：小时）
# =============================================================================

class TimeThresholds(IntEnum):
    """
    时间阈值常量（单位：小时）

    用于判定错题的新旧程度、紧急程度等
    """
    # 错题相关
    NEW_MISTAKE_THRESHOLD = 24          # 24小时内为新错题
    RECENT_REVIEW_THRESHOLD = 72       # 72小时内为最近复习
    URGENT_REVIEW_THRESHOLD = 24       # 24小时内为紧急复习

    # Token相关
    ACCESS_TOKEN_EXPIRE_MINUTES = 30   # 访问令牌有效期：30分钟
    REFRESH_TOKEN_EXPIRE_DAYS = 7      # 刷新令牌有效期：7天

    # 其他
    DEFAULT_TIMEOUT = 30                # 默认超时时间：30秒


# =============================================================================
# 优先级计算权重
# =============================================================================

class PriorityWeights(IntEnum):
    """
    优先级分数计算权重

    用于错题复习优先级的计算：
    - 超期权重：每小时增加的优先级分数
    - 错题次数权重：每次错误增加的分数
    - 复习次数权重：每次复习减少的分数（负值）
    - 新错题奖励：新错题额外增加的分数
    """
    OVERDUE_PER_HOUR = 10       # 每超期1小时增加10分
    MISTAKE_COUNT = 6           # 每错误1次增加6分
    REVIEW_COUNT = -5           # 每复习1次减少5分
    NEW_MISTAKE_BONUS = 10      # 新错题额外增加10分


# =============================================================================
# 掌握度等级
# =============================================================================

class MasteryLevels(IntEnum):
    """
    掌握度等级

    用于评估学生对某个知识点的掌握程度
    """
    MASTERED = 90          # 已掌握（90%+）
    PROFICIENT = 75        # 熟练（75-89%）
    LEARNING = 50          # 学习中（50-74%）
    FAMILIAR = 25          # 熟悉（25-49%）
    UNFAMILIAR = 0         # 不熟悉（0-24%）


# =============================================================================
# Token相关常量
# =============================================================================

class TokenConstants:
    """Token认证相关常量"""
    SECRET_KEY_MIN_LENGTH = 32      # JWT密钥最小长度
    ALGORITHM = "HS256"             # 默认加密算法


# =============================================================================
# 分页相关常量
# =============================================================================

class PaginationConstants:
    """分页相关常量"""
    DEFAULT_PAGE = 1                # 默认页码
    DEFAULT_PAGE_SIZE = 20          # 默认每页数量
    MAX_PAGE_SIZE = 100             # 最大每页数量

    PAGE_SIZE_OPTIONS = [10, 20, 50, 100]  # 可选分页大小


# =============================================================================
# AI服务相关常量
# =============================================================================

class AIServiceConstants:
    """AI服务相关常量"""
    # 向量搜索相关
    DEFAULT_VECTOR_SIZE = 1536      # 默认向量维度（OpenAI embeddings）
    DEFAULT_TOP_K = 10              # 默认返回结果数量
    SIMILARITY_THRESHOLD = 0.75     # 相似度阈值

    # 内容推荐相关
    MIN_RECOMMENDATIONS = 3         # 最小推荐数量
    MAX_RECOMMENDATIONS = 10        # 最大推荐数量


# =============================================================================
# 错题相关常量
# =============================================================================

class MistakeConstants:
    """错题相关常量"""
    # 状态
    STATUS_PENDING = "pending"              # 待复习
    STATUS_REVIEWING = "reviewing"          # 复习中
    STATUS_MASTERED = "mastered"            # 已掌握
    STATUS_IGNORED = "ignored"              # 已忽略

    # 类型
    TYPE_GRAMMAR = "grammar"                # 语法
    TYPE_VOCABULARY = "vocabulary"          # 词汇
    TYPE_READING = "reading"                # 阅读
    TYPE_LISTENING = "listening"            # 听力
    TYPE_WRITING = "writing"                # 写作
    TYPE_SPEAKING = "speaking"              # 口语


# =============================================================================
# 导出所有常量的便捷访问字典
# =============================================================================

# 能力等级快速访问
ABILITY_LEVELS = {
    "EXCELLENT": AbilityLevels.EXCELLENT,
    "GOOD": AbilityLevels.GOOD,
    "INTERMEDIATE": AbilityLevels.INTERMEDIATE,
    "BASIC": AbilityLevels.BASIC,
    "NEEDS_IMPROVEMENT": AbilityLevels.NEEDS_IMPROVEMENT,
}

# 复习间隔快速访问
REVIEW_INTERVALS = {
    "FIRST": ReviewIntervals.FIRST,
    "SECOND": ReviewIntervals.SECOND,
    "THIRD": ReviewIntervals.THIRD,
    "FOURTH": ReviewIntervals.FOURTH,
    "FIFTH": ReviewIntervals.FIFTH,
    "MAX": ReviewIntervals.MAX,
}

# 时间阈值快速访问
TIME_THRESHOLDS = {
    "NEW_MISTAKE": TimeThresholds.NEW_MISTAKE_THRESHOLD,
    "RECENT_REVIEW": TimeThresholds.RECENT_REVIEW_THRESHOLD,
    "URGENT_REVIEW": TimeThresholds.URGENT_REVIEW_THRESHOLD,
    "ACCESS_TOKEN_EXPIRE": TimeThresholds.ACCESS_TOKEN_EXPIRE_MINUTES,
    "REFRESH_TOKEN_EXPIRE": TimeThresholds.REFRESH_TOKEN_EXPIRE_DAYS,
}

# 优先级权重快速访问
PRIORITY_WEIGHTS = {
    "OVERDUE_PER_HOUR": PriorityWeights.OVERDUE_PER_HOUR,
    "MISTAKE_COUNT": PriorityWeights.MISTAKE_COUNT,
    "REVIEW_COUNT": PriorityWeights.REVIEW_COUNT,
    "NEW_MISTAKE_BONUS": PriorityWeights.NEW_MISTAKE_BONUS,
}
