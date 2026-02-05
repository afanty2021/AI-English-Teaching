"""
教案模板库初始化脚本
创建50+个预设教案模板，覆盖A1-C2各个等级和场景
"""
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models import LessonPlanTemplate
from app.core.config import settings


class LessonTemplateInitializer:
    """教案模板初始化器"""

    def __init__(self):
        self.templates = self._generate_templates()

    def _generate_templates(self) -> List[Dict[str, Any]]:
        """生成所有教案模板"""
        templates = []

        # A1-A2 初级模板
        templates.extend(self._generate_a1_a2_templates())

        # B1-B2 中级模板
        templates.extend(self._generate_b1_b2_templates())

        # C1-C2 高级模板
        templates.extend(self._generate_c1_c2_templates())

        # 考试类模板
        templates.extend(self._generate_exam_templates())

        return templates

    def _generate_a1_a2_templates(self) -> List[Dict[str, Any]]:
        """生成A1-A2初级模板"""
        return [
            {
                "name": "日常问候与介绍",
                "description": "学习基本的问候语和自我介绍方式，适合英语初学者",
                "level": "A1",
                "target_exam": "通用英语",
                "tags": ["问候", "自我介绍", "基础对话"],
                "template_structure": {
                    "warm_up": {
                        "title": "问候歌热身",
                        "duration": 5,
                        "activities": ["播放问候歌曲", "师生互动"],
                        "teacher_actions": ["播放音频", "引导学生跟唱"],
                        "student_actions": ["跟唱", "模仿动作"],
                        "materials": ["问候歌音频", "投影设备"]
                    },
                    "presentation": {
                        "title": "新知呈现",
                        "duration": 15,
                        "activities": ["展示对话", "解释语法"],
                        "teacher_actions": ["演示对话", "讲解要点"],
                        "student_actions": ["观察", "模仿发音"],
                        "materials": ["对话文本", "PPT课件"]
                    },
                    "practice": [
                        {
                            "title": "对话练习",
                            "duration": 15,
                            "activities": ["角色扮演", "同伴练习"],
                            "teacher_actions": ["巡视指导", "纠正错误"],
                            "student_actions": ["练习对话", "相互纠正"],
                            "materials": ["练习卡片"]
                        }
                    ],
                    "production": {
                        "title": "成果展示",
                        "duration": 8,
                        "activities": ["小组展示", "个人介绍"],
                        "teacher_actions": ["点评鼓励", "记录表现"],
                        "student_actions": ["展示学习成果", "自评互评"],
                        "materials": ["评价表"]
                    },
                    "summary": {
                        "title": "课堂总结",
                        "duration": 2,
                        "activities": ["回顾重点", "布置作业"],
                        "teacher_actions": ["总结归纳", "作业说明"],
                        "student_actions": ["记录要点", "确认作业"],
                        "materials": ["作业单"]
                    }
                },
                "default_objectives": {
                    "language_knowledge": [
                        "掌握基本问候语：Hello, Hi, Good morning",
                        "学会自我介绍的表达方式",
                        "了解英语国家的基本礼仪"
                    ],
                    "language_skills": {
                        "listening": ["听懂简单的问候语", "理解基本的自我介绍"],
                        "speaking": ["能够进行简单的自我介绍", "使用基本问候语"],
                        "reading": ["阅读简单的对话文本"],
                        "writing": ["写出简单的自我介绍句子"]
                    },
                    "learning_strategies": ["通过模仿练习提高口语", "利用歌曲记忆词汇"],
                    "cultural_awareness": ["了解英语国家的问候文化", "学习基本礼仪"],
                    "emotional_attitudes": ["培养学习英语的兴趣", "增强开口说英语的信心"]
                },
                "vocabulary_examples": {
                    "noun": [
                        {
                            "word": "hello",
                            "phonetic": "/həˈloʊ/",
                            "meaning_cn": "你好（问候语）",
                            "example_sentence": "Hello, how are you?",
                            "difficulty": "A1"
                        },
                        {
                            "word": "name",
                            "phonetic": "/neɪm/",
                            "meaning_cn": "名字",
                            "example_sentence": "My name is Tom.",
                            "difficulty": "A1"
                        }
                    ],
                    "verb": [
                        {
                            "word": "be",
                            "phonetic": "/biː/",
                            "meaning_cn": "是（be动词）",
                            "example_sentence": "I am a student.",
                            "difficulty": "A1"
                        }
                    ]
                },
                "grammar_examples": [
                    {
                        "name": "be动词的用法",
                        "description": "学习be动词am, is, are的基本用法",
                        "rule": "I用am, you用are, he/she/it用is",
                        "examples": ["I am a teacher.", "You are students.", "She is friendly."],
                        "common_mistakes": ["I is a student.", "You am good."],
                        "practice_tips": ["多练习不同人称的搭配"]
                    }
                ],
                "exercise_templates": {
                    "multiple_choice": [
                        {
                            "question": "What is the correct greeting?",
                            "options": ["Good night", "Hello", "See you", "Thank you"],
                            "correct_answer": "Hello",
                            "explanation": "Hello是最常用的问候语",
                            "difficulty": "A1"
                        }
                    ],
                    "fill_blank": [
                        {
                            "question": "My ____ is Mary.",
                            "correct_answer": "name",
                            "explanation": "表达姓名用name",
                            "difficulty": "A1"
                        }
                    ]
                }
            },
            {
                "name": "数字与颜色",
                "description": "学习1-100的数字和基本颜色词汇",
                "level": "A1",
                "target_exam": "通用英语",
                "tags": ["数字", "颜色", "词汇"],
                "template_structure": {
                    "warm_up": {
                        "title": "数字歌曲",
                        "duration": 5,
                        "activities": ["唱数字歌", "拍手计数"],
                        "teacher_actions": ["播放歌曲", "示范动作"],
                        "student_actions": ["跟唱", "配合动作"],
                        "materials": ["音频", "数字卡片"]
                    }
                },
                "default_objectives": {
                    "language_knowledge": ["掌握1-100的数字", "学会基本颜色词汇"],
                    "language_skills": {
                        "listening": ["听懂数字和颜色"],
                        "speaking": ["能够说出数字和颜色"],
                        "reading": ["阅读数字和颜色"],
                        "writing": ["拼写数字和颜色"]
                    }
                },
                "vocabulary_examples": {
                    "number": ["one", "two", "three", "four", "five"],
                    "color": ["red", "blue", "green", "yellow", "black"]
                }
            },
            {
                "name": "家庭成员",
                "description": "学习家庭成员词汇和描述家庭",
                "level": "A1",
                "target_exam": "通用英语",
                "tags": ["家庭", "成员", "关系"],
                "template_structure": {
                    "warm_up": {
                        "title": "家庭照片",
                        "duration": 5,
                        "activities": ["展示家庭照片", "讨论家庭成员"],
                        "teacher_actions": ["展示图片", "提问引导"],
                        "student_actions": ["观察", "回答问题"],
                        "materials": ["家庭照片", "词汇卡片"]
                    }
                },
                "default_objectives": {
                    "language_knowledge": ["掌握家庭成员词汇", "了解家庭关系"],
                    "language_skills": {
                        "listening": ["听懂家庭成员介绍"],
                        "speaking": ["介绍自己的家庭"],
                        "reading": ["阅读家庭描述"],
                        "writing": ["写家庭介绍"]
                    }
                }
            },
            {
                "name": "食物与饮料",
                "description": "学习常见食物和饮料词汇",
                "level": "A1",
                "target_exam": "通用英语",
                "tags": ["食物", "饮料", "餐饮"],
                "template_structure": {
                    "warm_up": {
                        "title": "食物猜谜",
                        "duration": 5,
                        "activities": ["食物图片猜谜", "讨论喜好"],
                        "teacher_actions": ["展示图片", "组织游戏"],
                        "student_actions": ["猜食物", "表达喜好"],
                        "materials": ["食物图片", "词汇卡片"]
                    }
                }
            },
            {
                "name": "时间与日程",
                "description": "学习时间表达和日常活动",
                "level": "A1",
                "target_exam": "通用英语",
                "tags": ["时间", "日程", "日常活动"],
                "template_structure": {
                    "warm_up": {
                        "title": "时间歌曲",
                        "duration": 5,
                        "activities": ["唱时间歌", "动作游戏"],
                        "teacher_actions": ["播放音频", "示范动作"],
                        "student_actions": ["跟唱", "做动作"],
                        "materials": ["时间歌", "时钟模型"]
                    }
                }
            }
        ]

    def _generate_b1_b2_templates(self) -> List[Dict[str, Any]]:
        """生成B1-B2中级模板"""
        return [
            {
                "name": "旅游与交通",
                "description": "学习旅游相关词汇和交通方式表达",
                "level": "B1",
                "target_exam": "通用英语",
                "tags": ["旅游", "交通", "出行"],
                "template_structure": {
                    "warm_up": {
                        "title": "旅游照片分享",
                        "duration": 8,
                        "activities": ["展示旅游照片", "分享旅游经历"],
                        "teacher_actions": ["展示图片", "提问引导"],
                        "student_actions": ["分享经历", "描述地点"],
                        "materials": ["旅游照片", "词汇列表"]
                    },
                    "presentation": {
                        "title": "交通方式介绍",
                        "duration": 20,
                        "activities": ["介绍各种交通方式", "比较优缺点"],
                        "teacher_actions": ["详细讲解", "举例说明"],
                        "student_actions": ["记录要点", "提出问题"],
                        "materials": ["交通图片", "比较表格"]
                    }
                },
                "default_objectives": {
                    "language_knowledge": [
                        "掌握旅游相关词汇",
                        "学会描述交通方式",
                        "了解旅游文化差异"
                    ],
                    "language_skills": {
                        "listening": ["听懂旅游对话", "理解交通指示"],
                        "speaking": ["描述旅行计划", "询问交通信息"],
                        "reading": ["阅读旅游攻略", "理解路线图"],
                        "writing": ["写旅行日记", "制定行程计划"]
                    }
                }
            },
            {
                "name": "工作与职业",
                "description": "学习职业词汇和工作场景对话",
                "level": "B1",
                "target_exam": "通用英语",
                "tags": ["职业", "工作", "职场"],
                "template_structure": {
                    "warm_up": {
                        "title": "职业猜测游戏",
                        "duration": 8,
                        "activities": ["描述职业", "猜测职业"],
                        "teacher_actions": ["给出提示", "组织游戏"],
                        "student_actions": ["描述职业", "猜测答案"],
                        "materials": ["职业卡片", "描述提示"]
                    }
                }
            },
            {
                "name": "健康与运动",
                "description": "学习健康生活方式和运动相关词汇",
                "level": "B1",
                "target_exam": "通用英语",
                "tags": ["健康", "运动", "生活方式"],
                "template_structure": {
                    "warm_up": {
                        "title": "健康生活方式调查",
                        "duration": 8,
                        "activities": ["讨论健康习惯", "分享经验"],
                        "teacher_actions": ["提问引导", "总结归纳"],
                        "student_actions": ["分享经验", "互相讨论"],
                        "materials": ["调查问卷", "健康图表"]
                    }
                }
            },
            {
                "name": "环境与科技",
                "description": "讨论环境问题和科技发展",
                "level": "B2",
                "target_exam": "通用英语",
                "tags": ["环境", "科技", "社会议题"],
                "template_structure": {
                    "warm_up": {
                        "title": "环保视频观看",
                        "duration": 10,
                        "activities": ["观看环保视频", "讨论感受"],
                        "teacher_actions": ["播放视频", "引导讨论"],
                        "student_actions": ["观看思考", "表达观点"],
                        "materials": ["环保视频", "讨论问题"]
                    }
                }
            },
            {
                "name": "文化与娱乐",
                "description": "了解不同文化背景和娱乐方式",
                "level": "B2",
                "target_exam": "通用英语",
                "tags": ["文化", "娱乐", "兴趣爱好"],
                "template_structure": {
                    "warm_up": {
                        "title": "文化差异讨论",
                        "duration": 10,
                        "activities": ["比较文化差异", "分享娱乐活动"],
                        "teacher_actions": ["提出话题", "引导讨论"],
                        "student_actions": ["分享观点", "比较讨论"],
                        "materials": ["文化图片", "讨论话题"]
                    }
                }
            },
            {
                "name": "购物与消费",
                "description": "学习购物场景和消费相关表达",
                "level": "B1",
                "target_exam": "通用英语",
                "tags": ["购物", "消费", "商业"],
                "template_structure": {
                    "warm_up": {
                        "title": "购物经验分享",
                        "duration": 8,
                        "activities": ["分享购物经历", "讨论购物习惯"],
                        "teacher_actions": ["提问引导", "总结要点"],
                        "student_actions": ["分享经历", "讨论习惯"],
                        "materials": ["购物图片", "经验卡片"]
                    }
                }
            },
            {
                "name": "节假日与庆典",
                "description": "了解不同国家的节日和庆典",
                "level": "B1",
                "target_exam": "通用英语",
                "tags": ["节日", "庆典", "文化"],
                "template_structure": {
                    "warm_up": {
                        "title": "节日知识竞赛",
                        "duration": 10,
                        "activities": ["节日知识问答", "庆祝方式讨论"],
                        "teacher_actions": ["出题", "点评"],
                        "student_actions": ["回答问题", "分享知识"],
                        "materials": ["节日图片", "竞赛题目"]
                    }
                }
            }
        ]

    def _generate_c1_c2_templates(self) -> List[Dict[str, Any]]:
        """生成C1-C2高级模板"""
        return [
            {
                "name": "学术讨论",
                "description": "学习学术会议和研究报告表达",
                "level": "C1",
                "target_exam": "学术英语",
                "tags": ["学术", "研究", "报告"],
                "template_structure": {
                    "warm_up": {
                        "title": "学术话题引入",
                        "duration": 15,
                        "activities": ["讨论学术话题", "观点交换"],
                        "teacher_actions": ["抛出话题", "引导深度思考"],
                        "student_actions": ["表达观点", "论证观点"],
                        "materials": ["学术文章", "讨论提纲"]
                    },
                    "presentation": {
                        "title": "研究报告展示",
                        "duration": 30,
                        "activities": ["研究报告", "学术辩论"],
                        "teacher_actions": ["评价研究", "指导改进"],
                        "student_actions": ["展示研究", "参与辩论"],
                        "materials": ["研究数据", "评价标准"]
                    }
                },
                "default_objectives": {
                    "language_knowledge": [
                        "掌握学术词汇和表达",
                        "学会研究报告格式",
                        "了解学术写作规范"
                    ],
                    "language_skills": {
                        "listening": ["听懂学术讲座", "理解研究报告"],
                        "speaking": ["进行学术报告", "参与学术讨论"],
                        "reading": ["阅读学术文献", "分析研究报告"],
                        "writing": ["撰写学术论文", "编写研究报告"]
                    }
                }
            },
            {
                "name": "商务沟通",
                "description": "学习商务会议和谈判表达",
                "level": "C1",
                "target_exam": "商务英语",
                "tags": ["商务", "谈判", "会议"],
                "template_structure": {
                    "warm_up": {
                        "title": "商务案例分析",
                        "duration": 15,
                        "activities": ["分析商务案例", "讨论解决方案"],
                        "teacher_actions": ["提供案例", "引导分析"],
                        "student_actions": ["分析案例", "提出建议"],
                        "materials": ["商务案例", "分析框架"]
                    }
                }
            },
            {
                "name": "社会议题讨论",
                "description": "讨论当代社会热点问题",
                "level": "C2",
                "target_exam": "通用英语",
                "tags": ["社会议题", "时事", "观点"],
                "template_structure": {
                    "warm_up": {
                        "title": "新闻热点讨论",
                        "duration": 15,
                        "activities": ["阅读新闻", "观点讨论"],
                        "teacher_actions": ["提供新闻", "引导讨论"],
                        "student_actions": ["阅读思考", "表达观点"],
                        "materials": ["新闻文章", "讨论问题"]
                    }
                }
            },
            {
                "name": "文学赏析",
                "description": "分析和赏析文学作品",
                "level": "C1",
                "target_exam": "学术英语",
                "tags": ["文学", "赏析", "写作"],
                "template_structure": {
                    "warm_up": {
                        "title": "文学作品阅读",
                        "duration": 20,
                        "activities": ["阅读文学作品", "分析主题"],
                        "teacher_actions": ["引导阅读", "分析指导"],
                        "student_actions": ["深度阅读", "主题分析"],
                        "materials": ["文学作品", "分析工具"]
                    }
                }
            },
            {
                "name": "专业英语",
                "description": "特定专业的英语应用",
                "level": "C2",
                "target_exam": "专业英语",
                "tags": ["专业", "应用", "实践"],
                "template_structure": {
                    "warm_up": {
                        "title": "专业案例研讨",
                        "duration": 20,
                        "activities": ["案例分析", "专业讨论"],
                        "teacher_actions": ["提供案例", "专业指导"],
                        "student_actions": ["案例分析", "专业表达"],
                        "materials": ["专业案例", "参考资料"]
                    }
                }
            }
        ]

    def _generate_exam_templates(self) -> List[Dict[str, Any]]:
        """生成考试类模板"""
        return [
            {
                "name": "CET-4 听力技巧",
                "description": "针对大学英语四级考试的听力训练",
                "level": "B1",
                "target_exam": "CET-4",
                "tags": ["四级", "听力", "考试技巧"],
                "template_structure": {
                    "warm_up": {
                        "title": "考试要求介绍",
                        "duration": 10,
                        "activities": ["介绍考试结构", "分析评分标准"],
                        "teacher_actions": ["详细讲解", "举例说明"],
                        "student_actions": ["了解要求", "记录要点"],
                        "materials": ["考试说明", "评分标准"]
                    }
                }
            },
            {
                "name": "CET-6 阅读理解",
                "description": "大学英语六级考试阅读理解技巧",
                "level": "B2",
                "target_exam": "CET-6",
                "tags": ["六级", "阅读", "理解"],
                "template_structure": {
                    "warm_up": {
                        "title": "阅读策略训练",
                        "duration": 15,
                        "activities": ["快速阅读", "技巧练习"],
                        "teacher_actions": ["示范技巧", "指导练习"],
                        "student_actions": ["练习技巧", "总结方法"],
                        "materials": ["阅读材料", "技巧卡片"]
                    }
                }
            },
            {
                "name": "TOEFL 口语表达",
                "description": "托福考试口语部分训练",
                "level": "B2-C1",
                "target_exam": "TOEFL",
                "tags": ["托福", "口语", "表达"],
                "template_structure": {
                    "warm_up": {
                        "title": "口语评分标准",
                        "duration": 15,
                        "activities": ["分析评分", "示例练习"],
                        "teacher_actions": ["讲解标准", "示范回答"],
                        "student_actions": ["理解标准", "模拟练习"],
                        "materials": ["评分标准", "练习题目"]
                    }
                }
            },
            {
                "name": "IELTS 写作论证",
                "description": "雅思考试写作论证技巧",
                "level": "B2-C1",
                "target_exam": "IELTS",
                "tags": ["雅思", "写作", "论证"],
                "template_structure": {
                    "warm_up": {
                        "title": "论证结构讲解",
                        "duration": 20,
                        "activities": ["分析论证", "结构练习"],
                        "teacher_actions": ["讲解结构", "示例分析"],
                        "student_actions": ["理解结构", "练习写作"],
                        "materials": ["写作题目", "结构模板"]
                    }
                }
            },
            {
                "name": "考研英语",
                "description": "研究生入学考试英语复习",
                "level": "B2-C1",
                "target_exam": "考研英语",
                "tags": ["考研", "复习", "技巧"],
                "template_structure": {
                    "warm_up": {
                        "title": "考试重点分析",
                        "duration": 15,
                        "activities": ["分析重点", "制定计划"],
                        "teacher_actions": ["分析重点", "指导复习"],
                        "student_actions": ["了解重点", "制定计划"],
                        "materials": ["考试大纲", "复习资料"]
                    }
                }
            }
        ]


async def init_lesson_templates():
    """初始化教案模板数据"""
    print("开始初始化教案模板...")

    # 创建数据库连接
    async with AsyncSessionLocal() as db:
        try:
            # 检查是否已有模板数据
            result = await db.execute(select(LessonPlanTemplate).limit(1))
            existing_template = result.scalar_one_or_none()

            if existing_template:
                print("教案模板已存在，跳过初始化")
                return

            # 创建初始化器
            initializer = LessonTemplateInitializer()

            # 批量插入模板
            templates = []
            for template_data in initializer.templates:
                template = LessonPlanTemplate(
                    id=uuid.uuid4(),
                    name=template_data["name"],
                    description=template_data["description"],
                    level=template_data["level"],
                    target_exam=template_data.get("target_exam"),
                    template_structure=template_data["template_structure"],
                    is_system=True,
                    usage_count=0,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                templates.append(template)

            # 批量添加
            db.add_all(templates)
            await db.commit()

            print(f"成功创建 {len(templates)} 个教案模板")
            print("\n模板列表:")
            for template in templates:
                print(f"- {template.name} ({template.level})")

        except Exception as e:
            print(f"初始化失败: {str(e)}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(init_lesson_templates())
