"""
AI内容生成Prompt模板 - AI英语教学系统
用于AI生成英语学习内容
"""

# ============================================================================
# 内容生成Prompt模板
# ============================================================================

CONTENT_GENERATION_PROMPT = """你是一位专业的英语教育内容创作者。请根据以下要求生成英语学习内容。

## 要求
- **内容类型**: {content_type}
- **难度等级**: {difficulty_level}
- **考试类型**: {exam_type}
- **主题**: {topic}
- **目标学生**: 中国的英语学习者，难度为{difficulty_level}级别

## 输出格式 (JSON)
请严格按照以下JSON格式输出，不要包含任何其他内容：

{{
  "contents": [
    {{
      "title": "英文标题",
      "description": "简短描述（2-3句话）",
      "content_type": "{content_type}",
      "difficulty_level": "{difficulty_level}",
      "exam_type": "{exam_type}",
      "topic": "{topic}",
      "tags": ["标签1", "标签2"],
      "content_text": "完整的阅读/听力/视频内容文本...",
      "word_count": 500,
      "knowledge_points": ["知识点1", "知识点2"]
    }}
  ]
}}

## 指南
1. 使用真实、地道的英语表达
2. 包含适当的中文注释或翻译
3. 内容难度与指定等级相匹配
4. 如果是考试相关内容，确保符合{exam_type}考试要求
5. 提供足够的语言点和知识点覆盖

请生成1-3条符合要求的内容。
"""


VOCABULARY_GENERATION_PROMPT = """你是一位专业的英语词汇教学专家。请根据以下要求生成词汇学习内容。

## 要求
- **难度等级**: {difficulty_level}
- **词汇数量**: {quantity}
- **词汇主题**: {topic} (可选，留空则生成通用词汇)

## 输出格式 (JSON)
请严格按照以下JSON格式输出，不要包含任何其他内容：

{{
  "vocabularies": [
    {{
      "word": "词汇",
      "phonetic": "/音标/",
      "part_of_speech": ["词性1", "词性2"],
      "definitions": ["中文释义1", "中文释义2"],
      "english_definition": "英文释义",
      "examples": ["例句1。", "例句2。"],
      "difficulty_level": "{difficulty_level}",
      "frequency_level": 7,
      "synonyms": ["同义词1", "同义词2"],
      "antonyms": ["反义词"],
      "collocations": ["搭配1", "搭配2"]
    }}
  ]
}}

## 指南
1. 提供准确的音标（IPA格式）
2. 每个词汇提供2-3个常用释义
3. 每个释义配一个例句
4. 标注词性和频率等级
5. 包含同义词、反义词和常用搭配
6. 确保词汇难度与指定等级匹配

请生成{quantity}个{difficulty_level}级别的词汇。
"""


GRAMMAR_GENERATION_PROMPT = """你是一位专业的英语语法教学专家。请根据以下要求生成语法讲解内容。

## 要求
- **语法点**: {grammar_point}
- **难度等级**: {difficulty_level}
- **考试类型**: {exam_type}

## 输出格式 (JSON)
请严格按照以下JSON格式输出，不要包含任何其他内容：

{{
  "contents": [
    {{
      "title": "英文标题",
      "description": "简短描述",
      "content_type": "grammar",
      "difficulty_level": "{difficulty_level}",
      "exam_type": "{exam_type}",
      "topic": "{grammar_point}",
      "tags": ["grammar", "{difficulty_level}"],
      "content_text": "## 语法讲解\\n\\n### 定义\\n...\\n\\n### 规则\\n...\\n\\n### 例句\\n...\\n\\n### 练习\\n...",
      "knowledge_points": ["规则1", "规则2", "常见错误"]
    }}
  ]
}}

## 指南
1. 清晰解释语法规则
2. 提供正例和反例
3. 说明常见错误
4. 包含难度适中的练习题
5. 如果是考试相关内容，标注考试要点

请生成1条完整的语法讲解内容。
"""


READING_GENERATION_PROMPT = """你是一位专业的英语阅读材料编辑。请根据以下要求生成阅读理解材料。

## 要求
- **主题**: {topic}
- **难度等级**: {difficulty_level}
- **考试类型**: {exam_type}
- **字数**: {word_count}

## 输出格式 (JSON)
请严格按照以下JSON格式输出，不要包含任何其他内容：

{{
  "contents": [
    {{
      "title": "英文标题",
      "description": "文章简介",
      "content_type": "reading",
      "difficulty_level": "{difficulty_level}",
      "exam_type": "{exam_type}",
      "topic": "{topic}",
      "tags": ["reading", "{topic}", "{difficulty_level}"],
      "content_text": "完整的阅读文章...",
      "word_count": {word_count},
      "knowledge_points": ["词汇点1", "句型点1", "理解要点1"]
    }}
  ]
}}

## 指南
1. 文章内容真实、有趣、信息丰富
2. 词汇难度适中，适量使用生词（带中文注释）
3. 包含2-3道阅读理解题目
4. 难度与{difficulty_level}级别相匹配
5. 如果是考试材料，符合{exam_type}题型

请生成1篇完整的阅读材料。
"""


LISTENING_GENERATION_PROMPT = """你是一位专业的英语听力材料编辑。请根据以下要求生成听力材料。

## 要求
- **主题**: {topic}
- **难度等级**: {difficulty_level}
- **考试类型**: {exam_type}
- **时长**: {duration_seconds}秒

## 输出格式 (JSON)
请严格按照以下JSON格式输出，不要包含任何其他内容：

{{
  "contents": [
    {{
      "title": "英文标题",
      "description": "听力材料简介",
      "content_type": "listening",
      "difficulty_level": "{difficulty_level}",
      "exam_type": "{exam_type}",
      "topic": "{topic}",
      "tags": ["listening", "{topic}", "{difficulty_level}"],
      "content_text": "## 听力原文\\n\\n## 参考译文\\n\\n## 词汇表\\n...",
      "duration": {duration_seconds},
      "word_count": 300,
      "knowledge_points": ["听力技巧1", "词汇点1"]
    }}
  ]
}}

## 指南
1. 听力脚本自然、口语化
2. 包含常见的口语表达
3. 提供中文参考译文
4. 标注重点词汇
5. 如果是考试材料，符合{exam_type}听力题型

请生成1篇完整的听力材料脚本。
"""


# ============================================================================
# Prompt生成辅助函数
# ============================================================================

def generate_content_prompt(
    content_type: str,
    difficulty_level: str,
    exam_type: str,
    topic: str,
    quantity: int = 3
) -> str:
    """生成内容Prompt

    Args:
        content_type: 内容类型
        difficulty_level: 难度等级
        exam_type: 考试类型
        topic: 主题
        quantity: 生成数量

    Returns:
        完整的Prompt字符串
    """
    prompts = {
        "reading": READING_GENERATION_PROMPT,
        "listening": LISTENING_GENERATION_PROMPT,
        "grammar": GRAMMAR_GENERATION_PROMPT,
        "vocabulary": VOCABULARY_GENERATION_PROMPT,
    }

    base_prompt = prompts.get(content_type, CONTENT_GENERATION_PROMPT)

    return base_prompt.format(
        content_type=content_type,
        difficulty_level=difficulty_level,
        exam_type=exam_type,
        topic=topic,
        quantity=quantity,
        word_count=500,
        duration_seconds=180,
        grammar_point=topic
    )


def generate_vocabulary_prompt(
    difficulty_level: str,
    quantity: int = 20,
    topic: Optional[str] = None
) -> str:
    """生成词汇Prompt

    Args:
        difficulty_level: 难度等级
        quantity: 生成数量
        topic: 主题（可选）

    Returns:
        完整的Prompt字符串
    """
    topic_str = topic or "general English"
    return VOCABULARY_GENERATION_PROMPT.format(
        difficulty_level=difficulty_level,
        quantity=quantity,
        topic=topic_str
    )
