"""
规则引擎 - AI英语教学系统
实现基于规则的零成本知识图谱更新策略

核心思想：
- 90%的日常更新使用规则引擎（零成本）
- 仅在初始诊断和定期复盘时使用AI（5%）
- 预计节省95%的AI调用成本

规则类型：
1. 能力值更新规则：根据练习结果实时更新能力值
2. 薄弱点识别规则：基于历史表现识别薄弱环节
3. 学习进度规则：评估学习进展和趋势
4. 异常检测规则：识别需要人工干预的情况
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class RuleEngine:
    """
    规则引擎类

    提供基于规则的零成本知识图谱更新能力

    设计原则：
    - 简单高效：每条规则执行时间 < 1ms
    - 可解释性：每条规则都有明确的业务含义
    - 可配置：规则参数可调整
    - 可扩展：新增规则不影响现有规则
    """

    # 主题到能力的映射
    TOPIC_ABILITY_MAP = {
        "听力": "listening",
        "阅读": "reading",
        "口语": "speaking",
        "写作": "writing",
        "语法": "grammar",
        "词汇": "vocabulary",
        "listening": "listening",
        "reading": "reading",
        "speaking": "speaking",
        "writing": "writing",
        "grammar": "grammar",
        "vocabulary": "vocabulary",
    }

    # 难度权重
    DIFFICULTY_WEIGHTS = {
        "beginner": 0.5,
        "basic": 0.7,
        "intermediate": 1.0,
        "advanced": 1.3,
        "expert": 1.5,
    }

    # 能力值更新参数
    LEARNING_RATE = 0.1  # 学习率：单次练习的最大影响幅度
    DECAY_RATE = 0.001   # 衰减率：长期未练习的能力缓慢衰减

    def __init__(self):
        """初始化规则引擎"""
        self.rules = [
            self._rule_correct_rate_update,
            self._rule_difficulty_bonus,
            self._rule_consistency_bonus,
            self._rule_time_efficiency,
            self._rule_streak_bonus,
        ]

    def analyze_practice(
        self,
        practice_record: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        分析练习记录

        Args:
            practice_record: 练习记录，包含：
                - content_id: 内容ID
                - topic: 主题
                - difficulty: 难度等级
                - score: 得分 (0-100)
                - correct_rate: 正确率 (0-1)
                - time_spent: 耗时（秒）

        Returns:
            Dict[str, Any]: 分析结果，包含：
                - topic: 主题
                - ability: 相关能力
                - difficulty: 难度
                - performance: 表现评分
                - improvement: 改进方向
                - rule_scores: 各规则评分
        """
        topic = practice_record.get("topic", "unknown")
        difficulty = practice_record.get("difficulty", "intermediate")
        score = practice_record.get("score", 0)
        correct_rate = practice_record.get("correct_rate", 0)
        time_spent = practice_record.get("time_spent", 0)

        # 确定相关能力
        ability = self.TOPIC_ABILITY_MAP.get(topic, "vocabulary")

        # 计算表现评分（0-100）
        performance = self._calculate_performance(
            score=score,
            correct_rate=correct_rate,
            difficulty=difficulty,
            time_spent=time_spent,
        )

        # 确定改进方向
        improvement = self._determine_improvement(
            correct_rate=correct_rate,
            performance=performance,
        )

        # 应用所有规则
        rule_scores = {}
        for rule in self.rules:
            rule_name = rule.__name__
            rule_scores[rule_name] = rule(practice_record)

        return {
            "topic": topic,
            "ability": ability,
            "difficulty": difficulty,
            "performance": performance,
            "improvement": improvement,
            "rule_scores": rule_scores,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def calculate_ability_update(
        self,
        current_abilities: Dict[str, float],
        practice_analysis: Dict[str, Any],
    ) -> Tuple[Dict[str, float], Dict[str, Any]]:
        """
        计算能力值更新

        Args:
            current_abilities: 当前能力值字典
            practice_analysis: 练习分析结果

        Returns:
            Tuple[Dict[str, float], Dict[str, Any]]:
                - 更新后的能力值
                - 变化详情
        """
        ability = practice_analysis["ability"]
        performance = practice_analysis["performance"]
        difficulty = practice_analysis["difficulty"]
        rule_scores = practice_analysis["rule_scores"]

        # 初始化更新后的能力值
        updated_abilities = current_abilities.copy()

        # 获取当前能力值（默认50）
        current_value = current_abilities.get(ability, 50.0)

        # 计算变化量
        delta = self._calculate_delta(
            current_value=current_value,
            performance=performance,
            difficulty=difficulty,
            rule_scores=rule_scores,
        )

        # 更新能力值（限制在0-100范围内）
        new_value = max(0, min(100, current_value + delta))
        updated_abilities[ability] = new_value

        # 记录变化详情
        changes = {
            "ability": ability,
            "old_value": current_value,
            "new_value": new_value,
            "delta": delta,
            "delta_percent": (delta / current_value * 100) if current_value > 0 else 0,
            "rules_applied": list(rule_scores.keys()),
        }

        return updated_abilities, changes

    def _calculate_performance(
        self,
        score: float,
        correct_rate: float,
        difficulty: str,
        time_spent: float,
    ) -> float:
        """
        计算综合表现评分

        Args:
            score: 得分 (0-100)
            correct_rate: 正确率 (0-1)
            difficulty: 难度等级
            time_spent: 耗时（秒）

        Returns:
            float: 表现评分 (0-100)
        """
        # 基础分：得分和正确率的加权平均
        base_score = (score + correct_rate * 100) / 2

        # 难度加成
        difficulty_bonus = self.DIFFICULTY_WEIGHTS.get(difficulty, 1.0)

        # 时间效率（假设标准时间为题目数量的2分钟/题）
        # 这里简化处理，实际需要根据题目数量计算
        time_efficiency = 1.0
        if time_spent > 0:
            # 假设平均每题2分钟为标准
            standard_time = 120  # 秒
            if time_spent <= standard_time:
                time_efficiency = 1.1  # 快速完成加成
            elif time_spent <= standard_time * 2:
                time_efficiency = 1.0  # 正常时间
            else:
                time_efficiency = 0.9  # 超时扣分

        # 综合评分
        performance = base_score * difficulty_bonus * time_efficiency

        # 限制在0-100范围
        return max(0, min(100, performance))

    def _determine_improvement(
        self,
        correct_rate: float,
        performance: float,
    ) -> str:
        """
        确定改进方向

        Args:
            correct_rate: 正确率
            performance: 表现评分

        Returns:
            str: 改进方向
        """
        if correct_rate < 0.6:
            return "accuracy"  # 需要提高准确性
        elif performance < 70:
            return "comprehensive"  # 需要全面提升
        elif correct_rate > 0.9:
            return "challenge"  # 需要更高难度挑战
        else:
            return "maintain"  # 保持当前水平

    def _calculate_delta(
        self,
        current_value: float,
        performance: float,
        difficulty: str,
        rule_scores: Dict[str, float],
    ) -> float:
        """
        计算能力值变化量

        Args:
            current_value: 当前能力值
            performance: 表现评分
            difficulty: 难度等级
            rule_scores: 规则评分

        Returns:
            float: 变化量（正数表示提升，负数表示下降）
        """
        # 基础变化量：基于表现评分
        # 表现评分 > 60 时提升，< 60 时下降
        base_delta = (performance - 60) * self.LEARNING_RATE

        # 难度调整：高难度练习的变化幅度更大
        difficulty_weight = self.DIFFICULTY_WEIGHTS.get(difficulty, 1.0)
        adjusted_delta = base_delta * difficulty_weight

        # 规则加成：叠加所有规则的影响
        rule_bonus = sum(rule_scores.values())

        # 最终变化量
        final_delta = adjusted_delta + rule_bonus

        # 限制单次最大变化幅度
        max_delta = 10 * self.LEARNING_RATE  # 单次最大变化 ±1 分
        return max(-max_delta, min(max_delta, final_delta))

    # ==================== 规则定义 ====================

    def _rule_correct_rate_update(
        self,
        practice_record: Dict[str, Any],
    ) -> float:
        """
        规则1：正确率更新规则
        正确率越高，能力值提升越大
        """
        correct_rate = practice_record.get("correct_rate", 0)
        # 正确率每超过60%，额外提升0.5分
        if correct_rate > 0.6:
            return (correct_rate - 0.6) * 0.5
        elif correct_rate < 0.4:
            # 正确率低于40%，额外扣分
            return (correct_rate - 0.4) * 0.5
        return 0

    def _rule_difficulty_bonus(
        self,
        practice_record: Dict[str, Any],
    ) -> float:
        """
        规则2：难度加成规则
        完成高难度练习获得额外加成
        """
        difficulty = practice_record.get("difficulty", "intermediate")
        score = practice_record.get("score", 0)

        # 高难度且得分良好时加成
        if difficulty in ["advanced", "expert"] and score >= 70:
            return 0.5
        elif difficulty == "advanced" and score >= 60:
            return 0.3
        return 0

    def _rule_consistency_bonus(
        self,
        practice_record: Dict[str, Any],
    ) -> float:
        """
        规则3：一致性加成规则
        连续表现良好获得额外加成
        """
        score = practice_record.get("score", 0)
        correct_rate = practice_record.get("correct_rate", 0)

        # 得分和正确率都稳定在良好水平
        if score >= 80 and correct_rate >= 0.85:
            return 0.3
        elif score >= 70 and correct_rate >= 0.75:
            return 0.1
        return 0

    def _rule_time_efficiency(
        self,
        practice_record: Dict[str, Any],
    ) -> float:
        """
        规则4：时间效率规则
        快速准确完成获得加成
        """
        score = practice_record.get("score", 0)
        correct_rate = practice_record.get("correct_rate", 0)
        time_spent = practice_record.get("time_spent", 0)

        # 又快又准
        if score >= 80 and correct_rate >= 0.9 and time_spent > 0:
            # 假设标准时间是2分钟，如果更快则加成
            if time_spent < 120:
                return 0.2
        return 0

    def _rule_streak_bonus(
        self,
        practice_record: Dict[str, Any],
    ) -> float:
        """
        规则5：连续学习加成规则
        需要配合前端传递的连续学习天数
        """
        # 这里简化处理，实际需要从学生记录中获取连续天数
        streak_days = practice_record.get("streak_days", 0)

        # 连续学习7天以上加成
        if streak_days >= 7:
            return 0.2
        elif streak_days >= 3:
            return 0.1
        return 0

    # ==================== 批量处理 ====================

    def batch_update_from_practices(
        self,
        current_abilities: Dict[str, float],
        practice_records: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
        """
        批量更新能力值（用于历史数据同步）

        Args:
            current_abilities: 当前能力值
            practice_records: 练习记录列表

        Returns:
            Tuple[Dict[str, float], List[Dict[str, Any]]]:
                - 更新后的能力值
                - 所有变化的详情
        """
        updated_abilities = current_abilities.copy()
        all_changes = []

        for record in practice_records:
            # 分析练习
            analysis = self.analyze_practice(record)

            # 计算更新
            updated_abilities, changes = self.calculate_ability_update(
                current_abilities=updated_abilities,
                practice_analysis=analysis,
            )

            all_changes.append(changes)

        return updated_abilities, all_changes

    # ==================== 薄弱点识别 ====================

    def identify_weak_points(
        self,
        abilities: Dict[str, float],
        practice_history: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        基于规则识别薄弱点

        Args:
            abilities: 当前能力值
            practice_history: 练习历史

        Returns:
            List[Dict[str, Any]]: 薄弱点列表
        """
        weak_points = []

        # 规则1：能力值低于60的视为薄弱
        for ability, value in abilities.items():
            if value < 60:
                weak_points.append({
                    "ability": ability,
                    "current_level": value,
                    "reason": f"{ability}能力值低于基础水平",
                    "priority": "high" if value < 40 else "medium",
                    "rule": "low_ability_value",
                })

        # 规则2：近期练习正确率持续低于60%
        if practice_history:
            recent_practices = practice_history[-10:]  # 最近10次
            topic_performance = {}

            for practice in recent_practices:
                topic = practice.get("topic", "unknown")
                if topic not in topic_performance:
                    topic_performance[topic] = []
                topic_performance[topic].append(practice.get("correct_rate", 0))

            for topic, rates in topic_performance.items():
                avg_rate = sum(rates) / len(rates)
                if avg_rate < 0.6 and len(rates) >= 3:
                    ability = self.TOPIC_ABILITY_MAP.get(topic, "vocabulary")
                    weak_points.append({
                        "topic": topic,
                        "ability": ability,
                        "current_level": abilities.get(ability, 50),
                        "reason": f"{topic}近期正确率平均{avg_rate:.1%}，持续偏低",
                        "priority": "high",
                        "rule": "low_recent_performance",
                    })

        return weak_points

    # ==================== 异常检测 ====================

    def detect_anomalies(
        self,
        practice_record: Dict[str, Any],
        student_history: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        检测异常情况

        Args:
            practice_record: 当前练习记录
            student_history: 学生历史记录

        Returns:
            List[Dict[str, Any]]: 异常列表
        """
        anomalies = []

        # 规则1：得分突然大幅下降
        if student_history:
            recent_scores = [
                p.get("score", 0)
                for p in student_history[-5:]
            ]
            if recent_scores:
                avg_score = sum(recent_scores) / len(recent_scores)
                current_score = practice_record.get("score", 0)
                if current_score < avg_score - 30:
                    anomalies.append({
                        "type": "score_drop",
                        "severity": "high",
                        "message": f"得分{current_score}远低于近期平均{avg_score:.1f}",
                        "action": "suggest_review",
                    })

        # 规则2：完成时间异常
        time_spent = practice_record.get("time_spent", 0)
        if time_spent == 0:
            anomalies.append({
                "type": "no_time_record",
                "severity": "low",
                "message": "未记录练习耗时",
                "action": "ignore",
            })
        elif time_spent < 10:
            anomalies.append({
                "type": "too_fast",
                "severity": "medium",
                "message": f"练习时间仅{time_spent}秒，可能未认真完成",
                "action": "suggest_retake",
            })

        # 规则3：正确率异常高（可能作弊）
        correct_rate = practice_record.get("correct_rate", 0)
        if correct_rate == 1.0 and practice_record.get("difficulty", "intermediate") in ["advanced", "expert"]:
            anomalies.append({
                "type": "suspicious_performance",
                "severity": "medium",
                "message": "高难度练习获得满分，建议人工核查",
                "action": "flag_for_review",
            })

        return anomalies


# 创建全局单例
_rule_engine: Optional[RuleEngine] = None


def get_rule_engine() -> RuleEngine:
    """
    获取规则引擎单例

    Returns:
        RuleEngine: 规则引擎实例
    """
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = RuleEngine()
    return _rule_engine
