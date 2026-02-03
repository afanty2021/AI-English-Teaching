"""
内容推荐服务 - AI英语教学系统
实现基于i+1理论的智能内容推荐

核心功能：
- 学生画像构建
- 三段式召回（向量召回 → 规则过滤 → AI精排）
- i+1难度控制
- 内容多样性保证
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid

import numpy as np
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models import Content, Student, KnowledgeGraph, ContentType, DifficultyLevel, ExamType
from app.schemas.recommendation import (
    StudentProfile,
    ReadingRecommendation,
    ExerciseRecommendation,
    SpeakingRecommendation,
    DailyContentResponse,
    RecommendationFilter,
)

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    内容推荐服务类

    实现基于i+1理论的智能内容推荐系统：
    1. 向量召回：基于Qdrant向量相似度进行初步召回
    2. 规则过滤：应用i+1理论、难度、主题等规则过滤
    3. AI精排：使用LLM对候选内容进行精细化排序

    成本优化策略：
    - 90%的召回通过本地向量检索完成
    - 仅对Top 10%候选内容使用AI精排
    """

    # 难度等级映射（用于i+1计算）
    DIFFICULTY_ORDER = {
        DifficultyLevel.BEGINNER.value: 1,
        DifficultyLevel.ELEMENTARY.value: 2,
        DifficultyLevel.INTERMEDIATE.value: 3,
        DifficultyLevel.UPPER_INTERMEDIATE.value: 4,
        DifficultyLevel.ADVANCED.value: 5,
        DifficultyLevel.PROFICIENT.value: 6,
    }

    # CEFR到难度等级的映射
    CEFR_TO_DIFFICULTY = {
        "A1": DifficultyLevel.BEGINNER.value,
        "A2": DifficultyLevel.ELEMENTARY.value,
        "B1": DifficultyLevel.INTERMEDIATE.value,
        "B2": DifficultyLevel.UPPER_INTERMEDIATE.value,
        "C1": DifficultyLevel.ADVANCED.value,
        "C2": DifficultyLevel.PROFICIENT.value,
    }

    @staticmethod
    async def get_student_profile(
        db: AsyncSession,
        student_id: uuid.UUID
    ) -> StudentProfile:
        """
        获取学生画像

        从数据库中获取学生信息、知识图谱等数据，
        构建完整的学生学习画像。

        Args:
            db: 数据库会话
            student_id: 学生ID

        Returns:
            StudentProfile: 学生画像

        Raises:
            ValueError: 如果学生不存在
        """
        # 获取学生基本信息
        student = await db.execute(
            select(Student)
            .options(selectinload(Student.knowledge_graph))
            .where(Student.id == student_id)
        )
        student = student.scalar_one_or_none()

        if not student:
            raise ValueError(f"学生不存在: {student_id}")

        # 从知识图谱获取能力评估
        abilities = {}
        mastered_points = []
        weak_points = []
        learning_points = []

        if student.knowledge_graph:
            kg = student.knowledge_graph
            abilities = kg.abilities or {}
            nodes = kg.nodes or {}

            # 提取知识点掌握情况
            for node_id, node_data in nodes.items():
                mastery = node_data.get("mastery", 0)
                if mastery >= 0.8:
                    mastered_points.append(node_id)
                elif mastery >= 0.5:
                    learning_points.append(node_id)
                else:
                    weak_points.append(node_id)

        # 构建学生画像
        profile = StudentProfile(
            student_id=student.id,
            target_exam=student.target_exam,
            target_score=student.target_score,
            current_cefr_level=student.current_cefr_level,
            abilities=abilities,
            mastered_points=mastered_points,
            weak_points=weak_points,
            learning_points=learning_points,
            # 默认偏好
            preferred_topics=[],
            preferred_content_types=[ContentType.READING.value],
            completed_content_count=0,
            total_study_time=0,
        )

        return profile

    @staticmethod
    async def recommend_daily(
        db: AsyncSession,
        student_id: uuid.UUID,
        filter_params: Optional[RecommendationFilter] = None
    ) -> DailyContentResponse:
        """
        每日内容推荐

        核心推荐方法，实现三段式召回策略：
        1. 向量召回：使用Qdrant进行语义相似度检索
        2. 规则过滤：应用i+1理论、难度、主题等规则
        3. AI精排：使用LLM对Top候选进行精细化排序

        Args:
            db: 数据库会话
            student_id: 学生ID
            filter_params: 推荐过滤条件

        Returns:
            DailyContentResponse: 每日推荐响应
        """
        # 1. 获取学生画像
        profile = await RecommendationService.get_student_profile(db, student_id)

        # 2. 确定推荐难度范围（i+1理论）
        target_difficulty = RecommendationService._get_target_difficulty(profile)
        difficulty_range = RecommendationService._get_i_plus_one_range(target_difficulty)

        logger.info(
            f"学生 {student_id} 的推荐难度范围: {difficulty_range}, "
            f"目标难度: {target_difficulty}"
        )

        # 3. 第一阶段：向量召回
        vector_candidates = await RecommendationService._vector_recall(
            db=db,
            profile=profile,
            top_k=100,  # 召回100个候选
        )

        logger.info(f"向量召回候选数: {len(vector_candidates)}")

        # 4. 第二阶段：规则过滤
        filtered_candidates = await RecommendationService._filter_by_i_plus_one(
            candidates=vector_candidates,
            difficulty_range=difficulty_range,
            profile=profile,
            filter_params=filter_params,
        )

        logger.info(f"规则过滤后候选数: {len(filtered_candidates)}")

        # 5. 内容多样性控制
        diversified = await RecommendationService._diversify_content(
            candidates=filtered_candidates,
            max_per_type=5,
            max_per_topic=3,
        )

        logger.info(f"多样性控制后候选数: {len(diversified)}")

        # 6. 第三阶段：AI精排（仅对Top 10%）
        ai_reranked = await RecommendationService._ai_rerank(
            candidates=diversified[:10],  # 仅精排Top 10
            profile=profile,
        )

        logger.info(f"AI精排后候选数: {len(ai_reranked)}")

        # 7. 按类型分组推荐
        recommendations = await RecommendationService._group_recommendations(
            candidates=ai_reranked,
            profile=profile,
        )

        # 8. 构建响应
        return DailyContentResponse(
            date=datetime.now(),
            student_profile_summary={
                "student_id": str(profile.student_id),
                "target_exam": profile.target_exam,
                "current_cefr_level": profile.current_cefr_level,
                "weak_points_count": len(profile.weak_points),
                "mastered_points_count": len(profile.mastered_points),
            },
            reading_recommendations=recommendations.get("reading", []),
            exercise_recommendations=recommendations.get("exercise", []),
            speaking_recommendations=recommendations.get("speaking", []),
            daily_goals=RecommendationService._generate_daily_goals(profile),
            total_recommendations=len(ai_reranked),
            retrieval_strategy="three_stage",
            ai_reranked_count=10,
        )

    @staticmethod
    def _get_target_difficulty(profile: StudentProfile) -> str:
        """
        根据学生画像确定目标难度

        Args:
            profile: 学生画像

        Returns:
            str: 目标难度等级
        """
        # 优先使用CEFR等级
        if profile.current_cefr_level:
            return RecommendationService.CEFR_TO_DIFFICULTY.get(
                profile.current_cefr_level,
                DifficultyLevel.INTERMEDIATE.value
            )

        # 根据考试类型推断
        exam_difficulty_map = {
            ExamType.CET4.value: DifficultyLevel.ELEMENTARY.value,
            ExamType.CET6.value: DifficultyLevel.INTERMEDIATE.value,
            ExamType.IELTS.value: DifficultyLevel.UPPER_INTERMEDIATE.value,
            ExamType.TOEFL.value: DifficultyLevel.UPPER_INTERMEDIATE.value,
        }

        if profile.target_exam:
            return exam_difficulty_map.get(
                profile.target_exam,
                DifficultyLevel.INTERMEDIATE.value
            )

        return DifficultyLevel.INTERMEDIATE.value

    @staticmethod
    def _get_i_plus_one_range(current_difficulty: str) -> List[str]:
        """
        计算i+1难度范围

        i+1理论：推荐内容应该略高于学生当前水平
        返回当前难度和下一个难度的列表

        Args:
            current_difficulty: 当前难度

        Returns:
            List[str]: 可接受的难度列表
        """
        current_level = RecommendationService.DIFFICULTY_ORDER.get(current_difficulty, 3)

        # i+1: 当前难度 + 下一级难度
        acceptable_levels = [current_level, current_level + 1]

        # 转换回难度名称
        range_list = []
        for level, name in RecommendationService.DIFFICULTY_ORDER.items():
            if RecommendationService.DIFFICULTY_ORDER[level] in acceptable_levels:
                range_list.append(level)

        return range_list

    @staticmethod
    async def _vector_recall(
        db: AsyncSession,
        profile: StudentProfile,
        top_k: int = 100
    ) -> List[Content]:
        """
        第一阶段：向量召回

        基于学生画像构建查询向量，从Qdrant检索相似内容。
        使用真实的向量检索实现。

        Args:
            db: 数据库会话
            profile: 学生画像
            top_k: 召回数量

        Returns:
            List[Content]: 召回的内容列表
        """
        from app.services.vector_service import get_vector_service

        vector_service = get_vector_service()

        # 构建查询文本（基于学生画像）
        query_parts = []

        # 添加目标考试
        if profile.target_exam:
            query_parts.append(profile.target_exam)

        # 添加薄弱知识点
        if profile.weak_points:
            query_parts.extend(profile.weak_points[:5])

        # 添加偏好主题
        if profile.preferred_topics:
            query_parts.extend(profile.preferred_topics[:3])

        # 如果没有明确偏好，使用当前等级
        if not query_parts:
            query_parts.append(f"英语学习 {profile.current_cefr_level}")

        query_text = " ".join(query_parts)

        # 构建过滤条件
        filters = {
            "is_published": True,
        }

        # 根据目标考试过滤
        if profile.target_exam:
            filters["exam_type"] = profile.target_exam

        # 使用向量搜索
        try:
            vector_results = await vector_service.search_by_text(
                query_text=query_text,
                limit=top_k * 2,
                score_threshold=0.5,
                filters=filters,
            )

            # 提取内容ID
            content_ids = []
            for result in vector_results:
                payload = result.get("payload", {})
                content_id = payload.get("content_id")
                if content_id:
                    content_ids.append(content_id)

            # 如果向量搜索有结果，从数据库获取完整内容
            if content_ids:
                import uuid as uuid_lib
                uuid_ids = []
                for cid in content_ids[:top_k]:
                    try:
                        uuid_ids.append(uuid_lib.UUID(cid))
                    except ValueError:
                        continue

                if uuid_ids:
                    result = await db.execute(
                        select(Content).where(
                            and_(
                                Content.id.in_(uuid_ids),
                                Content.is_published == True,
                            )
                        )
                    )
                    contents = result.scalars().all()

                    # 按向量搜索结果的顺序排序
                    content_map = {c.id: c for c in contents}
                    ordered_contents = []
                    for cid in uuid_ids:
                        if cid in content_map:
                            ordered_contents.append(content_map[cid])

                    return ordered_contents

        except Exception as e:
            logger.warning(f"向量搜索失败，使用数据库回退: {e}")

        # 回退到数据库查询（如果向量搜索失败）
        conditions = [Content.is_published == True]

        if profile.target_exam:
            conditions.append(
                or_(
                    Content.exam_type == profile.target_exam,
                    Content.exam_type.is_(None),
                    Content.exam_type == ExamType.GENERAL.value
                )
            )

        if profile.weak_points:
            for point in profile.weak_points[:3]:
                conditions.append(Content.knowledge_points.contains([point]))

        query = select(Content).where(and_(*conditions))
        query = query.order_by(
            Content.is_featured.desc(),
            Content.view_count.desc(),
            Content.sort_order.desc()
        ).limit(top_k)

        result = await db.execute(query)
        return list(result.scalars().all())
    @staticmethod
    async def _filter_by_i_plus_one(
        candidates: List[Content],
        difficulty_range: List[str],
        profile: StudentProfile,
        filter_params: Optional[RecommendationFilter] = None
    ) -> List[Content]:
        """
        第二阶段：规则过滤

        应用i+1理论、难度、主题等规则对召回的候选内容进行过滤。

        Args:
            candidates: 候选内容列表
            difficulty_range: 可接受的难度范围
            profile: 学生画像
            filter_params: 额外的过滤条件

        Returns:
            List[Content]: 过滤后的内容列表
        """
        filtered = []

        for content in candidates:
            # i+1 难度过滤
            if content.difficulty_level not in difficulty_range:
                continue

            # 主题过滤（如果有偏好）
            if profile.preferred_topics and content.topic:
                if content.topic not in profile.preferred_topics:
                    # 降低概率但不过滤完全
                    import random
                    if random.random() > 0.3:  # 70%概率过滤
                        continue

            # 应用额外过滤条件
            if filter_params:
                # 内容类型过滤
                if filter_params.content_types:
                    if content.content_type not in filter_params.content_types:
                        continue

                # 难度等级过滤
                if filter_params.difficulty_levels:
                    if content.difficulty_level not in filter_params.difficulty_levels:
                        continue

                # 主题过滤
                if filter_params.topics and content.topic:
                    if content.topic not in filter_params.topics:
                        continue

                # 考试类型过滤
                if filter_params.exam_types:
                    if content.exam_type not in filter_params.exam_types:
                        continue

            filtered.append(content)

        return filtered

    @staticmethod
    async def _diversify_content(
        candidates: List[Content],
        max_per_type: int = 5,
        max_per_topic: int = 3
    ) -> List[Content]:
        """
        内容多样性控制

        确保推荐内容在类型、主题等方面具有多样性，
        避免推荐过于相似的内容。

        Args:
            candidates: 候选内容列表
            max_per_type: 每种内容类型最大数量
            max_per_topic: 每个主题最大数量

        Returns:
            List[Content]: 多样化后的内容列表
        """
        type_counts = {}
        topic_counts = {}
        diversified = []

        for content in candidates:
            content_type = content.content_type
            topic = content.topic or "general"

            # 检查类型数量
            if type_counts.get(content_type, 0) >= max_per_type:
                continue

            # 检查主题数量
            if topic_counts.get(topic, 0) >= max_per_topic:
                continue

            diversified.append(content)
            type_counts[content_type] = type_counts.get(content_type, 0) + 1
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        return diversified

    @staticmethod
    async def _ai_rerank(
        candidates: List[Content],
        profile: StudentProfile
    ) -> List[Content]:
        """
        第三阶段：AI精排

        使用LLM对候选内容进行精细化排序。
        这是成本优化的关键：仅对少量候选内容使用AI。

        Args:
            candidates: 候选内容列表
            profile: 学生画像

        Returns:
            List[Content]: 精排后的内容列表
        """
        if not candidates:
            return []

        # 对于少量候选（<=5），使用LLM精排
        if len(candidates) <= 5:
            return await RecommendationService._llm_rerank(candidates, profile)
        
        # 对于较多候选，先使用规则评分筛选，再对Top 5使用LLM精排
        scored_candidates = []
        for content in candidates:
            score = await RecommendationService._calculate_recommendation_score(
                content=content,
                profile=profile
            )
            scored_candidates.append((content, score))
        
        # 按分数排序，取Top 5
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        top_5 = [c[0] for c in scored_candidates[:5]]
        
        # 对Top 5使用LLM精排
        return await RecommendationService._llm_rerank(top_5, profile)

    @staticmethod
    async def _llm_rerank(
        candidates: List[Content],
        profile: StudentProfile
    ) -> List[Content]:
        """
        使用LLM对候选内容进行精排

        Args:
            candidates: 候选内容列表
            profile: 学生画像

        Returns:
            List[Content]: 精排后的内容列表
        """
        from app.services.zhipu_service import ZhipuAIService
        
        llm_service = ZhipuAIService()
        
        # 构建LLM请求
        content_descriptions = []
        for idx, content in enumerate(candidates):
            desc = f"{idx + 1}. 标题: {content.title}\n"
            desc += f"   类型: {content.content_type}\n"
            desc += f"   难度: {content.difficulty_level}\n"
            desc += f"   主题: {content.topic or '通用'}\n"
            if content.description:
                desc += f"   描述: {content.description[:100]}...\n"
            if content.knowledge_points:
                desc += f"   知识点: {', '.join(content.knowledge_points[:5])}\n"
            content_descriptions.append(desc)
        
        # 构建学生画像描述
        profile_desc = f"学生当前CEFR等级: {profile.current_cefr_level}\n"
        if profile.target_exam:
            profile_desc += f"目标考试: {profile.target_exam}\n"
        if profile.weak_points:
            profile_desc += f"薄弱知识点: {', '.join(profile.weak_points[:3])}\n"
        if profile.preferred_topics:
            profile_desc += f"偏好主题: {', '.join(profile.preferred_topics[:3])}\n"
        
        # 构建prompt
        prompt = f"""你是一个专业的英语教学推荐专家。

# 学生画像
{profile_desc}

# 候选学习内容
{chr(10).join(content_descriptions)}

# 任务
请根据学生的画像，对上述候选内容进行排序，选择最适合学生学习的内容。
考虑以下因素：
1. 难度匹配度（i+1理论 - 略高于学生当前水平）
2. 知识点针对性（优先覆盖薄弱知识点）
3. 学习目标相关性（匹配目标考试）
4. 内容多样性（避免推荐过于相似的内容）

请返回JSON格式：
{{
  "ranking": [1, 3, 2, 5, 4],
  "reasons": {{
    "1": "适合当前水平，覆盖薄弱语法点",
    "3": "i+1难度，有助于提升",
    ...
  }}
}}

其中ranking数组中的数字是对应内容列表的序号，按推荐优先级从高到低排序。
"""

        try:
            # 调用LLM
            response = await llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的英语教学推荐专家，擅长根据学生情况推荐最合适的学习内容。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
            )
            
            # 解析响应
            import json
            response_text = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # 提取JSON
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                
                # 根据ranking重新排序
                ranking = result.get("ranking", list(range(1, len(candidates) + 1)))
                reranked = []
                for idx in ranking:
                    if 1 <= idx <= len(candidates):
                        reranked.append(candidates[idx - 1])
                
                return reranked
            
        except Exception as e:
            logger.warning(f"LLM精排失败，使用原始顺序: {e}")
        
        # 失败时返回原始顺序
        return candidates
    async def _calculate_recommendation_score(
        content: Content,
        profile: StudentProfile
    ) -> float:
        """
        计算推荐分数

        综合多个因素计算内容的推荐分数：
        - 难度匹配度（i+1理论）
        - 主题相关性
        - 知识点覆盖度
        - 内容质量（热度、精选等）

        Args:
            content: 内容对象
            profile: 学生画像

        Returns:
            float: 推荐分数（0-100）
        """
        score = 0.0

        # 1. 难度匹配度（30分）
        target_difficulty = RecommendationService._get_target_difficulty(profile)
        if content.difficulty_level == target_difficulty:
            score += 20  # 完全匹配
        else:
            # 检查是否是i+1
            current_level = RecommendationService.DIFFICULTY_ORDER.get(target_difficulty, 3)
            content_level = RecommendationService.DIFFICULTY_ORDER.get(content.difficulty_level, 3)
            if content_level == current_level + 1:
                score += 30  # i+1给予更高分数
            elif content_level == current_level:
                score += 20  # 同等级
            else:
                score += 10  # 其他情况

        # 2. 知识点覆盖度（25分）
        if content.knowledge_points:
            # 计算与薄弱知识点的重叠
            weak_overlap = len(set(content.knowledge_points) & set(profile.weak_points))
            learning_overlap = len(set(content.knowledge_points) & set(profile.learning_points))
            score += (weak_overlap * 10 + learning_overlap * 5)

        # 3. 主题相关性（20分）
        if content.topic and content.topic in profile.preferred_topics:
            score += 20

        # 4. 内容质量（25分）
        if content.is_featured:
            score += 15
        if content.view_count > 100:
            score += 5
        if content.favorite_count > 10:
            score += 5

        return min(score, 100.0)

    @staticmethod
    async def _group_recommendations(
        candidates: List[Content],
        profile: StudentProfile
    ) -> Dict[str, List]:
        """
        按类型分组推荐内容

        Args:
            candidates: 候选内容列表
            profile: 学生画像

        Returns:
            Dict: 分组后的推荐
        """
        result = {
            "reading": [],
            "exercise": [],
            "speaking": [],
        }

        for content in candidates:
            # 计算推荐分数
            score = await RecommendationService._calculate_recommendation_score(
                content=content,
                profile=profile
            )

            # 生成推荐理由
            reason = RecommendationService._generate_recommendation_reason(
                content=content,
                profile=profile,
                score=score
            )

            # 按类型添加到对应分组
            if content.content_type == ContentType.READING.value:
                result["reading"].append(ReadingRecommendation(
                    content_id=content.id,
                    title=content.title,
                    description=content.description,
                    difficulty_level=content.difficulty_level,
                    topic=content.topic,
                    word_count=content.word_count,
                    estimated_time=content.word_count // 200 if content.word_count else None,  # 假设每分钟200词
                    reason=reason,
                    knowledge_points=content.knowledge_points or [],
                    score=score,
                    i_plus_one_info={
                        "current_level": profile.current_cefr_level,
                        "content_level": content.difficulty_level,
                        "is_i_plus_one": content.difficulty_level != RecommendationService._get_target_difficulty(profile)
                    }
                ))
            elif content.content_type in [ContentType.GRAMMAR.value, ContentType.VOCABULARY.value]:
                result["exercise"].append(ExerciseRecommendation(
                    exercise_id=content.id,
                    title=content.title,
                    question_type=content.content_type,
                    difficulty_level=content.difficulty_level,
                    topic=content.topic,
                    estimated_time=10,  # 默认10分钟
                    reason=reason,
                    exam_points=content.knowledge_points or [],
                    score=score
                ))
            elif content.content_type in [ContentType.VIDEO.value, ContentType.LISTENING.value]:
                result["speaking"].append(SpeakingRecommendation(
                    content_id=content.id,
                    title=content.title,
                    description=content.description,
                    difficulty_level=content.difficulty_level,
                    topic=content.topic,
                    duration=content.duration,
                    reason=reason,
                    practice_type="listening" if content.content_type == ContentType.LISTENING.value else "speaking",
                    score=score
                ))

        return result

    @staticmethod
    def _generate_recommendation_reason(
        content: Content,
        profile: StudentProfile,
        score: float
    ) -> str:
        """
        生成推荐理由

        Args:
            content: 内容对象
            profile: 学生画像
            score: 推荐分数

        Returns:
            str: 推荐理由
        """
        reasons = []

        # 难度匹配
        target_difficulty = RecommendationService._get_target_difficulty(profile)
        if content.difficulty_level == target_difficulty:
            reasons.append(f"适合您当前的{target_difficulty}水平")
        else:
            reasons.append(f"略高于当前水平，有助于提升到{content.difficulty_level}")

        # 知识点覆盖
        if content.knowledge_points:
            weak_overlap = set(content.knowledge_points) & set(profile.weak_points)
            if weak_overlap:
                reasons.append(f"针对您的薄弱点：{', '.join(list(weak_overlap)[:2])}")

        # 主题相关
        if content.topic and content.topic in profile.preferred_topics:
            reasons.append(f"符合您感兴趣的{content.topic}主题")

        # 内容质量
        if content.is_featured:
            reasons.append("精选优质内容")

        return "；".join(reasons) if reasons else "智能推荐内容"

    @staticmethod
    def _generate_daily_goals(profile: StudentProfile) -> Dict[str, Any]:
        """
        生成每日学习目标

        Args:
            profile: 学生画像

        Returns:
            Dict: 每日学习目标
        """
        return {
            "reading_time": 30,  # 阅读30分钟
            "exercise_count": 10,  # 完成10道练习题
            "speaking_practice": 1,  # 1次口语练习
            "vocabulary_count": 20,  # 学习20个单词
            "focus_points": profile.weak_points[:3] if profile.weak_points else ["综合提升"],
        }
