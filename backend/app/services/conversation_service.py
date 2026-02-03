"""
AI Conversation Service - Async Version
使用 ZhipuAI 提供对话式英语口语练习服务
"""
import json
import logging
import re
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

from app.models.conversation import (
    Conversation,
    ConversationScenario,
    ConversationStatus
)
from app.models.student import Student
from app.services.zhipu_service import get_zhipuai_service

logger = logging.getLogger(__name__)


class ConversationService:
    """
    异步对话服务

    管理 AI 驱动的英语口语练习会话，包括：
    - 创建不同场景的对话
    - 处理多轮对话
    - 完成时进行评分
    """

    # 场景定义
    SCENARIOS: Dict[ConversationScenario, Dict[str, str]] = {
        ConversationScenario.DAILY_GREETING: {
            "name": "Daily Greeting",
            "description": "练习日常问候和闲聊",
            "context": "你今天第一次遇见某人"
        },
        ConversationScenario.ORDERING_FOOD: {
            "name": "Ordering Food",
            "description": "练习在餐厅点餐",
            "context": "你在餐厅想要点餐"
        },
        ConversationScenario.ASKING_DIRECTIONS: {
            "name": "Asking Directions",
            "description": "练习问路和指路",
            "context": "你迷路了，需要找一个地方"
        },
        ConversationScenario.JOB_INTERVIEW: {
            "name": "Job Interview",
            "description": "练习求职面试对话",
            "context": "你正在某家公司面试"
        },
        ConversationScenario.SHOPPING: {
            "name": "Shopping",
            "description": "练习购物对话",
            "context": "你在商店想要买商品"
        },
        ConversationScenario.MAKING_APPOINTMENTS: {
            "name": "Making Appointments",
            "description": "练习预约对话",
            "context": "你需要和某人预约时间"
        },
        ConversationScenario.TRAVEL_PLANNING: {
            "name": "Travel Planning",
            "description": "讨论旅行计划和安排",
            "context": "你正在计划度假并讨论选择"
        },
        ConversationScenario.EMERGENCY_SITUATIONS: {
            "name": "Emergency Situations",
            "description": "练习紧急情况交流",
            "context": "你处于紧急情况，需要帮助"
        },
        ConversationScenario.HOTEL_CHECK_IN: {
            "name": "Hotel Check-in",
            "description": "练习酒店入住对话",
            "context": "你到达酒店，需要办理入住手续"
        },
        ConversationScenario.DOCTOR_VISIT: {
            "name": "Doctor Visit",
            "description": "练习看医生描述症状",
            "context": "你不舒服，去诊所看病"
        },
        ConversationScenario.BUSINESS_MEETING: {
            "name": "Business Meeting",
            "description": "练习商务会议讨论",
            "context": "你在参加一个商务会议，讨论项目进展"
        },
        ConversationScenario.RESTAURANT_COMPLAINT: {
            "name": "Restaurant Complaint",
            "description": "练习礼貌投诉和解决问题",
            "context": "你在餐厅用餐遇到问题，需要与服务员沟通"
        },
        ConversationScenario.CASUAL_CONVERSATION: {
            "name": "Casual Conversation",
            "description": "自由话题轻松聊天",
            "context": "你和朋友在咖啡馆聊天，讨论日常话题"
        }
    }

    def __init__(self):
        """初始化对话服务"""
        self.zhipu_service = get_zhipuai_service()

    async def create_conversation(
        self,
        db: AsyncSession,
        student_id: str,
        scenario: ConversationScenario,
        level: str
    ) -> Conversation:
        """
        创建新对话会话

        Args:
            db: 数据库会话
            student_id: 学生 ID (UUID)
            scenario: 对话场景
            level: 英语水平 (A1-C2)

        Returns:
            创建的 Conversation 对象

        Raises:
            ValueError: 如果学生不存在或级别无效
        """
        # 验证学生
        result = await db.execute(
            select(Student).where(Student.id == student_id)
        )
        student = result.scalar_one_or_none()
        if not student:
            raise ValueError(f"Student with id {student_id} not found")

        # 验证级别
        valid_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        if level.upper() not in valid_levels:
            raise ValueError(f"Invalid level {level}. Must be one of {valid_levels}")

        # 创建对话
        conversation = Conversation(
            student_id=student_id,
            scenario=scenario,
            level=level.upper(),
            status=ConversationStatus.ACTIVE,
            messages="[]"
        )

        db.add(conversation)
        await db.flush()

        logger.info(
            f"Created conversation {conversation.id} for student {student_id} "
            f"with scenario {scenario.value} at level {level}"
        )

        return conversation

    async def send_message(
        self,
        db: AsyncSession,
        conversation_id: str,
        user_message: str
    ) -> str:
        """
        发送用户消息并获取 AI 回复

        Args:
            db: 数据库会话
            conversation_id: 对话 ID (UUID)
            user_message: 用户消息内容

        Returns:
            AI 回复消息

        Raises:
            ValueError: 如果对话不存在或未激活
        """
        # 获取对话
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        if conversation.status != ConversationStatus.ACTIVE:
            raise ValueError(
                f"Conversation {conversation_id} is not active "
                f"(status: {conversation.status})"
            )

        # 添加用户消息 - 重新获取对话以确保有最新数据
        await db.refresh(conversation)
        current_messages = conversation.get_messages()
        current_messages.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        conversation.messages = json.dumps(current_messages)
        flag_modified(conversation, "messages")

        # 立即刷新以确保消息被正确保存
        await db.flush()

        # 准备 AI 消息
        system_prompt = self._get_system_prompt(
            conversation.scenario,
            conversation.level
        )

        # 获取最近消息作为上下文（需要重新刷新以确保获取最新数据）
        await db.refresh(conversation)
        recent_messages = conversation.get_recent_messages(limit=10)

        # 构建 API 消息
        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in recent_messages:
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # 获取 AI 回复
        try:
            response = await self.zhipu_service.chat_completion(
                messages=api_messages,
                temperature=0.7,
                max_tokens=500
            )
            raw_message = response.get("choices", [{}])[0].get("message", {}).get("content", "")

            # 临时调试：记录原始响应
            logger.info(f"Raw AI response: {raw_message[:200]}...")

            # 提取最终对话回复（过滤掉思考过程）
            ai_message = self._extract_final_response(raw_message)

            logger.info(f"Extracted response: {ai_message[:100]}...")
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            raise

        # 添加 AI 消息到对话
        current_messages = conversation.get_messages()
        current_messages.append({
            "role": "assistant",
            "content": ai_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        conversation.messages = json.dumps(current_messages)
        flag_modified(conversation, "messages")

        await db.flush()

        return ai_message

    async def complete_conversation(
        self,
        db: AsyncSession,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        完成对话并生成评分

        Args:
            db: 数据库会话
            conversation_id: 对话 ID (UUID)

        Returns:
            包含评分和反馈的字典

        Raises:
            ValueError: 如果对话不存在或已完成
        """
        # 获取对话
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        if conversation.status != ConversationStatus.ACTIVE:
            raise ValueError(
                f"Conversation {conversation_id} is not active "
                f"(status: {conversation.status})"
            )

        # 刷新以确保获取最新的消息
        await db.refresh(conversation)

        # 获取所有消息
        messages = conversation.get_messages()

        if len(messages) < 2:
            # 消息太少无法评分
            conversation.status = ConversationStatus.COMPLETED
            conversation.completed_at = datetime.utcnow()
            conversation.overall_score = 50.0
            conversation.feedback = (
                "对话太短，无法进行详细评估。"
                "下次尝试进行更长的对话！"
            )
            return {
                "fluency_score": 50.0,
                "vocabulary_score": 50.0,
                "grammar_score": 50.0,
                "overall_score": 50.0,
                "feedback": conversation.feedback
            }

        # 生成评分
        scores = await self._generate_scores(
            conversation.scenario,
            conversation.level,
            messages
        )

        # 更新对话
        conversation.status = ConversationStatus.COMPLETED
        conversation.completed_at = datetime.utcnow()
        conversation.fluency_score = scores["fluency_score"]
        conversation.vocabulary_score = scores["vocabulary_score"]
        conversation.grammar_score = scores["grammar_score"]
        conversation.overall_score = scores["overall_score"]
        conversation.feedback = scores["feedback"]

        # 保存增强分析字段（将列表转换为 JSON 字符串）
        import json as json_lib
        conversation.strengths = json_lib.dumps(scores.get("strengths", []))
        conversation.improvements = json_lib.dumps(scores.get("improvements", []))
        conversation.grammar_notes = scores.get("grammar_notes", "")
        conversation.vocabulary_notes = scores.get("vocabulary_notes", "")
        conversation.recommendations = json_lib.dumps(scores.get("recommendations", []))

        await db.flush()

        logger.info(
            f"Completed conversation {conversation_id} with overall score {scores['overall_score']}"
        )

        return scores

    def _extract_final_response(self, raw_response: str) -> str:
        """
        从 AI 原始响应中提取最终对话回复

        处理智谱 AI 返回的带思考过程的响应。
        如果响应本身就是正常对话，直接返回。
        """
        if not raw_response:
            return ""

        # 首先检查：如果响应看起来像正常对话（没有明显的思考标记），直接返回
        thinking_markers = ['**分析**', '**检查**', '**确定**', '**优化**', '**替代**', '**选择**',
                          '分析', '检查', '确定', '优化', '替代', '选择', '对照', '起草', '草稿']
        has_thinking = any(marker in raw_response for marker in thinking_markers)

        # 如果没有明显的思考标记，且响应以大写字母开头或包含完整句子，直接使用
        if not has_thinking:
            # 清理可能的引用但保持主要内容
            cleaned = raw_response.strip()
            # 移除可能的markdown格式标记
            cleaned = re.sub(r'^\*\*+', '', cleaned)  # 移除开头的 **
            cleaned = re.sub(r'\*\*+$', '', cleaned)  # 移除结尾的 **
            cleaned = cleaned.strip()

            # 检查是否看起来像对话（包含字母和空格，长度合理）
            if len(cleaned) > 10 and any(c.isalpha() for c in cleaned):
                logger.info(f"No thinking markers detected, using raw response: {cleaned[:50]}...")
                return cleaned[:500]  # 限制长度但保持完整

        # 方法1: 查找 "**选择:*" 或 "选择:" 标记后的引号内容
        selection_patterns = [
            r'\*\*?选择\*\*?:\s*\*?\s*["\']([^"\']+)["\']',  # **选择:** "text"
            r'选择:\s*\*?\s*["\']([^"\']+)["\']',           # 选择: * "text"
            r'\*选择\*:?\s*["\']([^"\']+)["\']',           # *选择*: "text"
        ]
        for pattern in selection_patterns:
            match = re.search(pattern, raw_response, re.MULTILINE)
            if match:
                result = match.group(1).strip()
                if len(result) > 5:  # 确保有足够的内容
                    return result

        # 方法2: 从草稿中提取 - 查找 "草稿 X：* dialogue" 格式
        draft_pattern = r'草稿\s+\d+[:：]\s*\*?\s*["\']?([^"\'\n]{10,})["\']?'
        drafts = re.findall(draft_pattern, raw_response)
        if drafts:
            # 返回最后一个完整的草稿
            for draft in reversed(drafts):
                # 清理草稿内容（移除中文注释）
                cleaned = re.split(r'[（\(][^)）]*[）\)]', draft)[0].strip()
                if len(cleaned) > 10 and any(c.isalpha() and c.isascii() for c in cleaned):
                    return cleaned

        # 方法3: 查找引号中的英文对话（至少10个字符，包含字母和空格）
        quote_patterns = [
            r'["\']([A-Z][^"\']{10,200}[.!?])["\']',  # 大写开头，标点结尾
            r'["\']([A-Z][a-zA-Z\s,.!?]{10,200})["\']',  # 引号中的英文句子
        ]
        for pattern in quote_patterns:
            matches = re.findall(pattern, raw_response)
            if matches:
                # 返回最后一个匹配
                return matches[-1].strip()

        # 方法4: 提取包含英文句子的行
        lines = raw_response.split('\n')
        for line in reversed(lines):
            # 跳过标记行
            if any(marker in line for marker in ['分析', '检查', '确定', '优化', '替代', '选择',
                                                   '对照', '起草', '标准', '草稿', '**']):
                continue
            # 查找包含英文句子的行
            sentence_match = re.search(r'[A-Z][a-zA-Z\s,.!?]{10,}', line)
            if sentence_match:
                return sentence_match.group(0).strip()

        # 方法5: 最后的回退 - 清理并返回最后一段非空内容
        logger.warning(f"Could not extract clean response from: {raw_response[:100]}...")
        paragraphs = [p.strip() for p in raw_response.split('\n\n') if p.strip()]
        if paragraphs:
            last_para = paragraphs[-1]
            # 移除中文注释和标记
            last_para = re.sub(r'[（\(][^)）]*[）\)]', '', last_para)
            last_para = re.sub(r'^[\*\-\d+\.\s\*]+', '', last_para, flags=re.MULTILINE).strip()
            if len(last_para) > 10:
                return last_para[:500]

        return "I'm sorry, I couldn't generate a response. Please try again."


    def _get_system_prompt(
        self,
        scenario: ConversationScenario,
        level: str
    ) -> str:
        """
        根据场景和学生级别生成系统提示

        Args:
            scenario: 对话场景
            level: 学生英语水平

        Returns:
            系统提示字符串
        """
        scenario_info = self.SCENARIOS.get(
            scenario,
            self.SCENARIOS[ConversationScenario.DAILY_GREETING]
        )

        level_guidance = self._get_level_guidance(level)

        prompt = f"""你是一位友好耐心的英语对话伙伴。

当前场景：{scenario_info["name"]}
描述：{scenario_info["description"]}
上下文：{scenario_info["context"]}

学生水平：{level} {level_guidance}

你的角色：
1. 在给定场景中进行自然对话
2. 使用适合学生水平的词汇和语法
3. 如果学生犯错，在你的回复中温和地示范正确语言
4. 给予鼓励和支持
5. 保持回复简洁（通常2-3句话）
6. 提出后续问题以保持对话流畅
7. 保持场景中的角色（如服务员、面试官等）

记住：
- 对学生的困难保持耐心
- 使用简单清晰的语言
- 赞赏良好的交流
- 让对话感觉自然愉快
"""
        return prompt

    def _get_level_guidance(self, level: str) -> str:
        """
        获取针对 AI 的级别指导

        Args:
            level: 学生英语水平

        Returns:
            级别指导字符串
        """
        guidance_map = {
            "A1": "(初学者 - 使用非常简单的词汇和短句。基本问候和短语。)",
            "A2": "(基础 - 使用简单词汇和基础语法。日常表达。)",
            "B1": "(中级 - 使用常用词汇和标准语法。可以讨论熟悉的话题。)",
            "B2": "(中高级 - 使用多样的词汇。能处理大多数情况。)",
            "C1": "(高级 - 使用丰富的词汇和复杂的语法。能流利表达想法。)",
            "C2": "(精通 - 使用复杂的语言。细致准确的交流。)"
        }
        return guidance_map.get(level, guidance_map["B1"])

    async def _generate_scores(
        self,
        scenario: ConversationScenario,
        level: str,
        messages: List[Dict]
    ) -> Dict[str, Any]:
        """
        生成对话评分 - 增强版，包含详细能力分析和学习建议

        Args:
            scenario: 对话场景
            level: 学生水平
            messages: 对话消息

        Returns:
            增强的评分字典，包含分数、详细分析、改进建议
        """
        scenario_info = self.SCENARIOS.get(
            scenario,
            self.SCENARIOS[ConversationScenario.DAILY_GREETING]
        )

        # 格式化对话
        conversation_text = "\n".join([
            f"{msg['role'].capitalize()}: {msg['content']}"
            for msg in messages
        ])

        # 消息数量
        user_messages = [m for m in messages if m['role'] == 'user']
        assistant_messages = [m for m in messages if m['role'] == 'assistant']
        msg_count = len(user_messages)

        # 级别期望标准
        level_standards = {
            "A1": "基本问候和简单短语，使用现在时态",
            "A2": "日常表达，使用一般现在/过去/将来时",
            "B1": "常用词汇和标准语法，能描述经历和表达观点",
            "B2": "多样词汇，能处理大多数情况，使用复杂句式",
            "C1": "丰富词汇和复杂语法，能流利表达抽象想法",
            "C2": "细致准确的语言，能处理专业和学术话题"
        }

        prompt = f"""作为专业英语语言评估专家，请评估以下对话。

**场景**: {scenario_info["name"]} - {scenario_info["description"]}
**学生水平**: {level}
**级别标准**: {level_standards.get(level, "")}
**对话轮数**: {msg_count}

**对话内容**:
{conversation_text}

**评分标准**（针对 {level} 水平）:
- **流利度** (0-100): 表达连贯性、响应速度、对话参与度
- **词汇** (0-100): 词汇恰当性、丰富程度、场景相关词汇使用
- **语法** (0-100): 时态准确性、句子结构、语法错误频率
- **整体表现** (0-100): 综合表现，沟通效果

**评分范围**:
- 90-100: 优秀 - 超出该水平预期
- 75-89: 良好 - 很好达到预期，有小瑕疵
- 60-74: 满意 - 达到基本要求，有改进空间
- 40-59: 一般 - 低于预期，需要更多练习
- 0-39: 较差 - 困难较大，建议降低难度

请以 JSON 格式返回评估:
{{
    "fluency_score": <数字 0-100>,
    "vocabulary_score": <数字 0-100>,
    "grammar_score": <数字 0-100>,
    "overall_score": <数字 0-100>,
    "strengths": ["优点1", "优点2"],
    "improvements": ["需改进点1", "需改进点2"],
    "grammar_notes": "<具体的语法观察，如时态使用、句式结构等>",
    "vocabulary_notes": "<词汇使用观察，如场景词汇、词汇多样性等>",
    "recommendations": ["具体学习建议1", "具体学习建议2"],
    "feedback": "<2-3句鼓励性总体反馈>"
}}

注意：
1. 根据 {level} 水平公平评估，不期望 C1 水平的复杂度
2. 关注沟通效果而非完美语法
3. 提供具体、可操作的建议
4. 强调学生的进步和优点
5. 建议应与对话场景相关
"""

        try:
            response = await self.zhipu_service.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位经验丰富的英语语言评估专家，擅长分析学生的口语表现并提供有针对性的改进建议。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")

            # 尝试解析 JSON
            result = json.loads(content)

            return {
                "fluency_score": float(result.get("fluency_score", 60.0)),
                "vocabulary_score": float(result.get("vocabulary_score", 60.0)),
                "grammar_score": float(result.get("grammar_score", 60.0)),
                "overall_score": float(result.get("overall_score", 60.0)),
                "strengths": result.get("strengths", []),
                "improvements": result.get("improvements", []),
                "grammar_notes": result.get("grammar_notes", ""),
                "vocabulary_notes": result.get("vocabulary_notes", ""),
                "recommendations": result.get("recommendations", []),
                "feedback": result.get("feedback", "继续练习！"),
            }

        except Exception as e:
            logger.error(f"Error generating scores: {e}")
            # 返回增强的默认评分
            return {
                "fluency_score": 60.0,
                "vocabulary_score": 60.0,
                "grammar_score": 60.0,
                "overall_score": 60.0,
                "strengths": ["完成了对话", "使用了基本词汇"],
                "improvements": ["可以尝试更多样化的表达"],
                "grammar_notes": "注意时态的一致性",
                "vocabulary_notes": "继续积累场景相关词汇",
                "recommendations": [
                    "多练习 {level} 水平的对话",
                    "复习常用时态用法"
                ],
                "feedback": "很好地完成了对话！继续练习以提升技能。"
            }

    def get_available_scenarios(self) -> List[Dict[str, str]]:
        """
        获取可用的对话场景列表

        Returns:
            场景字典列表，包含 id、name 和 description
        """
        return [
            {
                "id": scenario.value,
                "name": info["name"],
                "description": info["description"],
                "context": info["context"]
            }
            for scenario, info in self.SCENARIOS.items()
        ]

    async def get_conversation_by_id(
        self,
        db: AsyncSession,
        conversation_id: str,
        with_student: bool = False
    ) -> Optional[Conversation]:
        """
        通过 ID 获取对话

        Args:
            db: 数据库会话
            conversation_id: 对话 ID (UUID)
            with_student: 是否预加载学生关系

        Returns:
            Conversation 对象或 None
        """
        query = select(Conversation).where(Conversation.id == conversation_id)
        if with_student:
            query = query.options(selectinload(Conversation.student))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def list_conversations(
        self,
        db: AsyncSession,
        student_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Conversation]:
        """
        获取学生的对话列表

        Args:
            db: 数据库会话
            student_id: 学生 ID (UUID)
            skip: 跳过记录数
            limit: 返回记录上限

        Returns:
            Conversation 对象列表
        """
        result = await db.execute(
            select(Conversation)
            .where(Conversation.student_id == student_id)
            .order_by(Conversation.started_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


# 全局服务实例
_conversation_service: Optional[ConversationService] = None


def get_conversation_service() -> ConversationService:
    """
    获取对话服务实例（单例模式）

    Returns:
        ConversationService 实例
    """
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService()
    return _conversation_service
