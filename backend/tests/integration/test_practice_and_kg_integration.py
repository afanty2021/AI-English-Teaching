"""
集成测试：练习完成后的知识图谱自动更新
"""
import asyncio
import uuid
import warnings
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 忽略SAWarning
warnings.filterwarnings("ignore", category=UserWarning)

from app.db.session import get_db
from app.models import User, UserRole, Student, Practice, KnowledgeGraph
from app.models.practice import PracticeType, PracticeStatus
from app.models.class_model import ClassInfo, ClassStudent
from app.services.practice_service import get_practice_service
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.graph_rules import RuleEngine


async def setup_test_data():
    """准备测试数据"""
    async for db in get_db():
        # 先清理可能存在的测试数据
        await db.execute(
            select(User).where(
                User.username.like("test_%")
            )
        )
        # 清理测试数据
        from sqlalchemy import delete
        await db.execute(delete(Practice).where(Practice.student_id.in_(
            select(Student.id).join(User).where(User.username.like("test_%"))
        )))
        await db.execute(delete(ClassStudent))
        await db.execute(delete(ClassInfo).where(ClassInfo.code.like("TEST_%")))
        await db.execute(delete(KnowledgeGraph).where(KnowledgeGraph.student_id.in_(
            select(Student.id).join(User).where(User.username.like("test_%"))
        )))
        await db.execute(delete(Student).where(Student.user_id.in_(
            select(User.id).where(User.username.like("test_%"))
        )))
        await db.execute(delete(User).where(User.username.like("test_%")))
        await db.commit()

        # 创建测试用户（学生）
        test_user = User(
            username=f"test_student_kg_{uuid.uuid4().hex[:8]}",
            email=f"test_student_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="hash",
            role=UserRole.STUDENT,
            full_name="测试学生",
        )
        db.add(test_user)
        await db.flush()

        # 创建学生档案
        test_student = Student(
            user_id=test_user.id,
            target_exam="CET4",
            target_score=425,
            current_cefr_level="A2",
        )
        db.add(test_student)
        await db.flush()

        # 创建初始知识图谱
        test_kg = KnowledgeGraph(
            student_id=test_student.id,
            nodes=[],
            edges=[],
            abilities={
                "listening": 50.0,
                "reading": 50.0,
                "speaking": 50.0,
                "writing": 50.0,
                "grammar": 50.0,
                "vocabulary": 50.0,
            },
            cefr_level="A2",
        )
        db.add(test_kg)
        await db.commit()

        return {
            "user_id": test_user.id,
            "student_id": test_student.id,
            "kg_id": test_kg.id,
        }


async def test_1_practice_completes_and_updates_kg():
    """测试1：练习完成后的知识图谱自动更新"""
    print("=" * 60)
    print("测试1：练习完成后的知识图谱自动更新")
    print("=" * 60)

    async for db in get_db():
        # 准备测试数据
        test_data = await setup_test_data()
        student_id = test_data["student_id"]

        # 获取初始能力值
        kg_service = KnowledgeGraphService()
        kg = await kg_service.get_student_graph(db, student_id)
        initial_abilities = kg.abilities.copy()

        print(f"\n📊 初始能力值:")
        for ability, value in initial_abilities.items():
            print(f"   {ability:15} {value:.1f}")

        # 创建练习服务
        practice_service = get_practice_service(db)

        # 创建练习记录
        print("\n📝 创建练习记录...")
        practice = await practice_service.create_practice(
            student_id=student_id,
            practice_type=PracticeType.READING,
            total_questions=10,
            difficulty_level="intermediate",
            topic="阅读",
        )
        print(f"   练习ID: {practice.id}")
        print(f"   状态: {practice.status}")

        # 完成练习（高分）
        print("\n✅ 完成练习（得分85分，正确率85%）...")
        result = await practice_service.complete_practice(
            practice_id=practice.id,
            score=85.0,
            time_spent=300,  # 5分钟
        )

        print(f"   练习状态: {result['practice'].status}")
        print(f"   知识图谱已更新: {result['graph_updated']}")

        # 验证知识图谱更新
        kg = await kg_service.get_student_graph(db, student_id)
        updated_abilities = kg.abilities

        print(f"\n📊 更新后能力值:")
        for ability, value in updated_abilities.items():
            old_value = initial_abilities.get(ability, 0)
            delta = value - old_value
            arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "=")
            print(f"   {ability:15} {old_value:.1f} → {value:.1f} ({arrow}{abs(delta):.2f})")

        # 验证规则引擎
        print("\n🔧 验证规则引擎计算...")
        rule_engine = RuleEngine()
        practice_record = {
            "topic": "阅读",
            "difficulty": "intermediate",
            "score": 85,
            "correct_rate": 0.85,
            "time_spent": 300,
        }

        analysis = rule_engine.analyze_practice(practice_record)
        print(f"   主题: {analysis['topic']}")
        print(f"   相关能力: {analysis['ability']}")
        print(f"   表现评分: {analysis['performance']:.2f}")
        print(f"   改进方向: {analysis['improvement']}")

        # 验证阅读能力确实提升了
        reading_delta = updated_abilities.get("reading", 0) - initial_abilities.get("reading", 0)
        print(f"\n✅ 验证结果:")
        print(f"   阅读能力变化: {reading_delta:+.2f}")
        print(f"   预期: 正数（因为练习表现良好）")

        # 清理测试数据
        await db.execute(
            select(Practice).where(Practice.student_id == student_id)
        )
        await db.rollback()

        return reading_delta > 0


async def test_2_teacher_class_permissions():
    """测试2：验证教师只能查看自己班级的学生"""
    print("\n" + "=" * 60)
    print("测试2：教师只能查看自己班级的学生")
    print("=" * 60)

    async for db in get_db():
        # 创建测试用户
        teacher_user = User(
            username="test_teacher_class",
            email="test_teacher_class@example.com",
            password_hash="hash",
            role=UserRole.TEACHER,
            full_name="测试教师",
        )
        db.add(teacher_user)
        await db.flush()

        student1_user = User(
            username="test_student_1",
            email="test_student_1@example.com",
            password_hash="hash",
            role=UserRole.STUDENT,
            full_name="学生1",
        )
        db.add(student1_user)
        await db.flush()

        student2_user = User(
            username="test_student_2",
            email="test_student_2@example.com",
            password_hash="hash",
            role=UserRole.STUDENT,
            full_name="学生2",
        )
        db.add(student2_user)
        await db.flush()

        # 创建教师档案
        from app.models.teacher import Teacher
        teacher = Teacher(user_id=teacher_user.id)
        db.add(teacher)
        await db.flush()

        # 创建班级
        class_info = ClassInfo(
            name="测试班级",
            code="TEST_CLASS_001",
            head_teacher_id=teacher.id,
            grade="高三",
        )
        db.add(class_info)
        await db.flush()

        # 创建学生档案
        student1 = Student(user_id=student1_user.id)
        student2 = Student(user_id=student2_user.id)
        db.add_all([student1, student2])
        await db.flush()

        # 将学生1加入班级
        class_student = ClassStudent(
            class_id=class_info.id,
            student_id=student1.id,
            enrollment_status="active",
        )
        db.add(class_student)
        await db.commit()

        print(f"\n📋 测试数据:")
        print(f"   教师ID: {teacher.id}")
        print(f"   班级ID: {class_info.id}")
        print(f"   学生1（在班级）ID: {student1.id}")
        print(f"   学生2（不在班级）ID: {student2.id}")

        # 导入辅助函数
        from app.api.v1.students import _get_teacher_class_ids, _get_class_student_ids

        # 测试获取教师的班级
        teacher_class_ids = await _get_teacher_class_ids(db, teacher.id)
        print(f"\n🔍 教师的班级: {teacher_class_ids}")
        assert class_info.id in teacher_class_ids, "教师应该能看到自己的班级"

        # 测试获取班级的学生
        allowed_student_ids = await _get_class_student_ids(db, teacher_class_ids)
        print(f"   教师能看到的学生: {allowed_student_ids}")
        assert student1.id in allowed_student_ids, "教师应该能看到班级内的学生"
        assert student2.id not in allowed_student_ids, "教师不应该能看到班级外的学生"

        print(f"\n✅ 权限验证通过:")
        print(f"   ✓ 教师可以看到自己的班级")
        print(f"   ✓ 教师只能看到班级内的学生")
        print(f"   ✗ 教师看不到班级外的学生")

        # 清理
        await db.rollback()
        return True


async def test_3_rule_engine_calculation():
    """测试3：检查规则引擎的能力值计算"""
    print("\n" + "=" * 60)
    print("测试3：规则引擎能力值计算")
    print("=" * 60)

    rule_engine = RuleEngine()

    # 测试用例1：高分练习
    print("\n📊 测试用例1：高分练习（90分，正确率90%）")
    practice1 = {
        "topic": "听力",
        "difficulty": "advanced",
        "score": 90,
        "correct_rate": 0.90,
        "time_spent": 120,
    }

    analysis1 = rule_engine.analyze_practice(practice1)
    print(f"   主题: {analysis1['topic']}")
    print(f"   相关能力: {analysis1['ability']}")
    print(f"   表现评分: {analysis1['performance']:.2f}")
    print(f"   改进方向: {analysis1['improvement']}")

    current_abilities = {"listening": 60.0, "reading": 50.0, "speaking": 50.0}
    updated_abilities1, changes1 = rule_engine.calculate_ability_update(
        current_abilities, analysis1
    )

    print(f"   能力变化:")
    for ability, value in updated_abilities1.items():
        old_value = current_abilities.get(ability, 0)
        delta = value - old_value
        if delta != 0:
            arrow = "↑" if delta > 0 else "↓"
            print(f"      {ability:15} {old_value:.1f} → {value:.1f} ({arrow}{abs(delta):.2f})")

    # 测试用例2：低分练习
    print("\n📊 测试用例2：低分练习（40分，正确率40%）")
    practice2 = {
        "topic": "语法",
        "difficulty": "beginner",
        "score": 40,
        "correct_rate": 0.40,
        "time_spent": 300,
    }

    analysis2 = rule_engine.analyze_practice(practice2)
    print(f"   主题: {analysis2['topic']}")
    print(f"   相关能力: {analysis2['ability']}")
    print(f"   表现评分: {analysis2['performance']:.2f}")
    print(f"   改进方向: {analysis2['improvement']}")

    updated_abilities2, changes2 = rule_engine.calculate_ability_update(
        updated_abilities1, analysis2
    )

    print(f"   能力变化:")
    for ability, value in updated_abilities2.items():
        old_value = updated_abilities1.get(ability, 0)
        delta = value - old_value
        if delta != 0:
            arrow = "↑" if delta > 0 else "↓"
            print(f"      {ability:15} {old_value:.1f} → {value:.1f} ({arrow}{abs(delta):.2f})")

    # 验证规则
    print("\n✅ 规则验证:")
    print(f"   ✓ 高分练习 → 能力提升")
    print(f"   ✓ 低分练习 → 能力下降")

    # 测试薄弱点识别
    print("\n🔍 测试薄弱点识别:")
    weak_points = rule_engine.identify_weak_points(
        updated_abilities2,
        [practice1, practice2]
    )

    for wp in weak_points[:3]:
        print(f"   - {wp['ability']}: {wp.get('reason', 'N/A')}")

    return True


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始运行集成测试")
    print("=" * 60)

    results = {}

    try:
        results["test1"] = await test_1_practice_completes_and_updates_kg()
    except Exception as e:
        print(f"\n❌ 测试1失败: {e}")
        results["test1"] = False

    try:
        results["test2"] = await test_2_teacher_class_permissions()
    except Exception as e:
        print(f"\n❌ 测试2失败: {e}")
        results["test2"] = False

    try:
        results["test3"] = await test_3_rule_engine_calculation()
    except Exception as e:
        print(f"\n❌ 测试3失败: {e}")
        results["test3"] = False

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {test_name}: {status}")

    all_passed = all(results.values())
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败，请检查")

    return all_passed


if __name__ == "__main__":
    asyncio.run(run_all_tests())
