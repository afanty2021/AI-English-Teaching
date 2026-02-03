"""
规则引擎测试 - AI英语教学系统
测试 RuleEngine 类的各项功能
"""
import pytest

from app.services.graph_rules import RuleEngine, get_rule_engine


class TestRuleEngine:
    """规则引擎测试类"""

    @pytest.fixture
    def rule_engine(self):
        """创建规则引擎实例"""
        return RuleEngine()

    def test_analyze_practice_success(self, rule_engine):
        """测试成功分析练习"""
        practice_record = {
            "content_id": "123",
            "topic": "阅读",
            "difficulty": "intermediate",
            "score": 80,
            "correct_rate": 0.85,
            "time_spent": 300,
        }

        result = rule_engine.analyze_practice(practice_record)

        # 验证结果结构
        assert "topic" in result
        assert "ability" in result
        assert "difficulty" in result
        assert "performance" in result
        assert "improvement" in result
        assert "rule_scores" in result

        # 验证值
        assert result["topic"] == "阅读"
        assert result["ability"] == "reading"
        assert result["difficulty"] == "intermediate"
        assert 0 <= result["performance"] <= 100

    def test_analyze_practice_unknown_topic(self, rule_engine):
        """测试未知主题映射到词汇能力"""
        practice_record = {
            "content_id": "123",
            "topic": "未知主题",
            "difficulty": "intermediate",
            "score": 80,
            "correct_rate": 0.85,
            "time_spent": 300,
        }

        result = rule_engine.analyze_practice(practice_record)

        # 未知主题应该映射到vocabulary
        assert result["ability"] == "vocabulary"

    def test_calculate_ability_update(self, rule_engine):
        """测试计算能力更新"""
        current_abilities = {
            "reading": 70.0,
            "listening": 60.0,
            "vocabulary": 50.0,
        }

        practice_analysis = {
            "ability": "reading",
            "performance": 80.0,
            "difficulty": "intermediate",
            "rule_scores": {
                "_rule_correct_rate_update": 0.5,
                "_rule_difficulty_bonus": 0.0,
            },
        }

        updated_abilities, changes = rule_engine.calculate_ability_update(
            current_abilities=current_abilities,
            practice_analysis=practice_analysis,
        )

        # 验证能力更新
        assert "reading" in updated_abilities
        # 表现良好应该提升
        assert updated_abilities["reading"] >= current_abilities["reading"]

        # 验证变化详情
        assert changes["ability"] == "reading"
        assert changes["old_value"] == 70.0
        assert "new_value" in changes
        assert "delta" in changes

    def test_calculate_performance(self, rule_engine):
        """测试计算表现评分"""
        # 高分高正确率
        performance = rule_engine._calculate_performance(
            score=90,
            correct_rate=0.95,
            difficulty="intermediate",
            time_spent=120,
        )
        assert performance > 85

        # 低分低正确率
        performance = rule_engine._calculate_performance(
            score=40,
            correct_rate=0.5,
            difficulty="intermediate",
            time_spent=300,
        )
        assert performance < 60

        # 高难度加成
        performance_high = rule_engine._calculate_performance(
            score=80,
            correct_rate=0.85,
            difficulty="advanced",
            time_spent=200,
        )
        performance_low = rule_engine._calculate_performance(
            score=80,
            correct_rate=0.85,
            difficulty="beginner",
            time_spent=200,
        )
        assert performance_high > performance_low

    def test_determine_improvement(self, rule_engine):
        """测试确定改进方向"""
        # 低正确率
        improvement = rule_engine._determine_improvement(
            correct_rate=0.5,
            performance=50,
        )
        assert improvement == "accuracy"

        # 高正确率高表现
        improvement = rule_engine._determine_improvement(
            correct_rate=0.95,
            performance=95,
        )
        assert improvement == "challenge"

        # 中等水平
        improvement = rule_engine._determine_improvement(
            correct_rate=0.8,
            performance=75,
        )
        assert improvement == "maintain"

    def test_rule_correct_rate_update(self, rule_engine):
        """测试正确率更新规则"""
        # 高正确率应该获得正分
        practice = {"correct_rate": 0.9}
        score = rule_engine._rule_correct_rate_update(practice)
        assert score > 0

        # 低正确率应该获得负分
        practice = {"correct_rate": 0.3}
        score = rule_engine._rule_correct_rate_update(practice)
        assert score < 0

    def test_rule_difficulty_bonus(self, rule_engine):
        """测试难度加成规则"""
        # 高难度高分
        practice = {"difficulty": "advanced", "score": 80}
        score = rule_engine._rule_difficulty_bonus(practice)
        assert score > 0

        # 低难度
        practice = {"difficulty": "beginner", "score": 80}
        score = rule_engine._rule_difficulty_bonus(practice)
        assert score == 0

    def test_rule_consistency_bonus(self, rule_engine):
        """测试一致性加成规则"""
        # 高分高正确率
        practice = {"score": 85, "correct_rate": 0.9}
        score = rule_engine._rule_consistency_bonus(practice)
        assert score > 0

        # 中等水平
        practice = {"score": 75, "correct_rate": 0.8}
        score = rule_engine._rule_consistency_bonus(practice)
        assert score > 0

        # 低分
        practice = {"score": 50, "correct_rate": 0.5}
        score = rule_engine._rule_consistency_bonus(practice)
        assert score == 0

    def test_identify_weak_points(self, rule_engine):
        """测试识别薄弱点"""
        abilities = {
            "reading": 80,
            "listening": 40,
            "vocabulary": 55,
        }

        practice_history = [
            {
                "topic": "听力",
                "correct_rate": 0.5,
            },
            {
                "topic": "听力",
                "correct_rate": 0.55,
            },
            {
                "topic": "听力",
                "correct_rate": 0.45,
            },
        ]

        weak_points = rule_engine.identify_weak_points(
            abilities=abilities,
            practice_history=practice_history,
        )

        # 应该识别出听力和词汇的薄弱
        assert len(weak_points) >= 2
        listening_weak = next((p for p in weak_points if p["ability"] == "listening"), None)
        assert listening_weak is not None
        assert listening_weak["priority"] == "high"

    def test_detect_anomalies(self, rule_engine):
        """测试异常检测"""
        current_practice = {
            "score": 30,
            "correct_rate": 0.3,
            "time_spent": 5,
            "difficulty": "advanced",
        }

        history = [
            {"score": 80},
            {"score": 85},
            {"score": 78},
            {"score": 82},
            {"score": 80},
        ]

        anomalies = rule_engine.detect_anomalies(
            practice_record=current_practice,
            student_history=history,
        )

        # 应该检测到得分下降
        assert len(anomalies) > 0
        score_drop = next((a for a in anomalies if a["type"] == "score_drop"), None)
        assert score_drop is not None
        assert score_drop["severity"] == "high"

    def test_batch_update_from_practices(self, rule_engine):
        """测试批量更新能力值"""
        current_abilities = {
            "reading": 50.0,
        }

        practice_records = [
            {
                "topic": "阅读",
                "difficulty": "intermediate",
                "score": 70,
                "correct_rate": 0.7,
                "time_spent": 200,
            },
            {
                "topic": "阅读",
                "difficulty": "intermediate",
                "score": 80,
                "correct_rate": 0.8,
                "time_spent": 180,
            },
        ]

        updated_abilities, changes = rule_engine.batch_update_from_practices(
            current_abilities=current_abilities,
            practice_records=practice_records,
        )

        # 验证能力提升
        assert updated_abilities["reading"] > current_abilities["reading"]
        assert len(changes) == 2

    def test_topic_ability_mapping(self, rule_engine):
        """测试主题到能力的映射"""
        # 中文主题
        assert rule_engine.TOPIC_ABILITY_MAP["听力"] == "listening"
        assert rule_engine.TOPIC_ABILITY_MAP["阅读"] == "reading"
        assert rule_engine.TOPIC_ABILITY_MAP["语法"] == "grammar"

        # 英文主题
        assert rule_engine.TOPIC_ABILITY_MAP["listening"] == "listening"
        assert rule_engine.TOPIC_ABILITY_MAP["writing"] == "writing"

    def test_difficulty_weights(self, rule_engine):
        """测试难度权重"""
        assert rule_engine.DIFFICULTY_WEIGHTS["beginner"] < rule_engine.DIFFICULTY_WEIGHTS["intermediate"]
        assert rule_engine.DIFFICULTY_WEIGHTS["expert"] > rule_engine.DIFFICULTY_WEIGHTS["advanced"]


class TestGetRuleEngine:
    """测试规则引擎单例"""

    def test_get_rule_engine_singleton(self):
        """测试获取单例"""
        engine1 = get_rule_engine()
        engine2 = get_rule_engine()

        # 验证返回同一个实例
        assert engine1 is engine2
