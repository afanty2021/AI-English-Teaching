"""AI Speaking Practice Service.

This service manages AI-powered conversation practice sessions,
including conversation creation, message handling, and scoring.
"""
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from openai import OpenAI

from app.models.conversation import (
    Conversation,
    ConversationScenario,
    ConversationStatus
)
from app.models.student import Student
from app.db.session import get_db

logger = logging.getLogger(__name__)


class SpeakingService:
    """
    Service for AI-powered speaking practice sessions.

    Manages conversation sessions with AI, including:
    - Creating conversations for different scenarios
    - Handling multi-turn dialogue
    - Scoring performance on completion
    """

    # Scenario definitions with descriptions and prompts
    SCENARIOS: Dict[ConversationScenario, Dict[str, str]] = {
        ConversationScenario.DAILY_GREETING: {
            "name": "Daily Greeting",
            "description": "Practice everyday greetings and small talk",
            "context": "You are meeting someone for the first time today"
        },
        ConversationScenario.ORDERING_FOOD: {
            "name": "Ordering Food",
            "description": "Practice ordering at a restaurant",
            "context": "You are at a restaurant and want to order food"
        },
        ConversationScenario.ASKING_DIRECTIONS: {
            "name": "Asking Directions",
            "description": "Practice asking for and giving directions",
            "context": "You are lost and need to find a specific location"
        },
        ConversationScenario.JOB_INTERVIEW: {
            "name": "Job Interview",
            "description": "Practice job interview conversations",
            "context": "You are interviewing for a position at a company"
        },
        ConversationScenario.SHOPPING: {
            "name": "Shopping",
            "description": "Practice shopping interactions",
            "context": "You are shopping at a store and want to buy items"
        },
        ConversationScenario.MAKING_APPOINTMENTS: {
            "name": "Making Appointments",
            "description": "Practice scheduling appointments",
            "context": "You need to schedule an appointment with someone"
        },
        ConversationScenario.TRAVEL_PLANNING: {
            "name": "Travel Planning",
            "description": "Planning a trip and discussing travel arrangements",
            "context": "You are planning a vacation and discussing options"
        },
        ConversationScenario.EMERGENCY_SITUATIONS: {
            "name": "Emergency Situations",
            "description": "Practice handling emergency communications",
            "context": "You are in an emergency situation and need help"
        }
    }

    def __init__(self, openai_client: Optional[OpenAI] = None):
        """
        Initialize the SpeakingService.

        Args:
            openai_client: Optional OpenAI client (for testing)
        """
        self.client = openai_client or OpenAI()
        self.model = "gpt-4o-mini"

    def create_conversation(
        self,
        student_id: int,
        scenario: ConversationScenario,
        level: str
    ) -> Conversation:
        """
        Create a new conversation session.

        Args:
            student_id: ID of the student
            scenario: Conversation scenario
            level: Student's English level (A1-C2)

        Returns:
            Created Conversation object

        Raises:
            ValueError: If student not found or level invalid
        """
        db = next(get_db())

        # Validate student
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise ValueError(f"Student with id {student_id} not found")

        # Validate level
        valid_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        if level not in valid_levels:
            raise ValueError(f"Invalid level {level}. Must be one of {valid_levels}")

        # Create conversation
        conversation = Conversation(
            student_id=student_id,
            scenario=scenario,
            level=level,
            status=ConversationStatus.ACTIVE
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        logger.info(
            f"Created conversation {conversation.id} for student {student_id} "
            f"with scenario {scenario.value} at level {level}"
        )

        return conversation

    def send_message(
        self,
        conversation_id: int,
        user_message: str
    ) -> str:
        """
        Send a user message and get AI response.

        Args:
            conversation_id: ID of the conversation
            user_message: User's message content

        Returns:
            AI's response message

        Raises:
            ValueError: If conversation not found or not active
        """
        db = next(get_db())

        # Get conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        if conversation.status != ConversationStatus.ACTIVE:
            raise ValueError(
                f"Conversation {conversation_id} is not active "
                f"(status: {conversation.status})"
            )

        # Add user message
        conversation.add_message("user", user_message)

        # Prepare messages for AI
        system_prompt = self._get_system_prompt(
            conversation.scenario,
            conversation.level
        )

        # Get recent messages for context (last 10 turns)
        recent_messages = conversation.get_recent_messages(limit=10)

        # Build API messages
        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in recent_messages:
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Get AI response
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                temperature=0.7,
                max_tokens=300
            )
            ai_message = response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            raise

        # Add AI message to conversation
        conversation.add_message("assistant", ai_message)

        db.commit()
        db.refresh(conversation)

        return ai_message

    def complete_conversation(
        self,
        conversation_id: int
    ) -> Dict[str, Any]:
        """
        Complete a conversation and generate scoring.

        Args:
            conversation_id: ID of the conversation to complete

        Returns:
            Dictionary with scores and feedback

        Raises:
            ValueError: If conversation not found or already completed
        """
        db = next(get_db())

        # Get conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        if conversation.status != ConversationStatus.ACTIVE:
            raise ValueError(
                f"Conversation {conversation_id} is not active "
                f"(status: {conversation.status})"
            )

        # Get all messages
        messages = conversation.get_messages()

        if len(messages) < 2:
            # Not enough messages to score
            conversation.status = ConversationStatus.COMPLETED
            conversation.completed_at = datetime.utcnow()
            conversation.overall_score = 50.0
            conversation.feedback = (
                "Conversation was too short for detailed assessment. "
                "Try to have a longer conversation next time!"
            )
            db.commit()
            return {
                "fluency_score": 50.0,
                "vocabulary_score": 50.0,
                "grammar_score": 50.0,
                "overall_score": 50.0,
                "feedback": conversation.feedback
            }

        # Generate scoring prompt
        scoring_prompt = self._get_scoring_prompt(
            conversation.scenario,
            conversation.level,
            messages
        )

        # Get scores from AI
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert English language evaluator. "
                                  "Provide fair and encouraging assessments."
                    },
                    {"role": "user", "content": scoring_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            fluency_score = result.get("fluency_score", 50.0)
            vocabulary_score = result.get("vocabulary_score", 50.0)
            grammar_score = result.get("grammar_score", 50.0)
            overall_score = result.get("overall_score", 50.0)
            feedback = result.get("feedback", "")

        except Exception as e:
            logger.error(f"Error generating scores: {e}")
            # Use default scores on error
            fluency_score = 60.0
            vocabulary_score = 60.0
            grammar_score = 60.0
            overall_score = 60.0
            feedback = (
                "Great effort completing the conversation! "
                "Keep practicing to improve your skills."
            )

        # Update conversation
        conversation.status = ConversationStatus.COMPLETED
        conversation.completed_at = datetime.utcnow()
        conversation.fluency_score = fluency_score
        conversation.vocabulary_score = vocabulary_score
        conversation.grammar_score = grammar_score
        conversation.overall_score = overall_score
        conversation.feedback = feedback

        db.commit()
        db.refresh(conversation)

        logger.info(
            f"Completed conversation {conversation_id} with overall score {overall_score}"
        )

        return {
            "fluency_score": fluency_score,
            "vocabulary_score": vocabulary_score,
            "grammar_score": grammar_score,
            "overall_score": overall_score,
            "feedback": feedback
        }

    def _get_system_prompt(
        self,
        scenario: ConversationScenario,
        level: str
    ) -> str:
        """
        Generate system prompt based on scenario and student level.

        Args:
            scenario: Conversation scenario
            level: Student's English level

        Returns:
            System prompt string
        """
        scenario_info = self.SCENARIOS.get(scenario, self.SCENARIOS[ConversationScenario.DAILY_GREETING])

        level_guidance = self._get_level_guidance(level)

        prompt = f"""You are a friendly and patient English conversation partner.

Current Scenario: {scenario_info["name"]}
Description: {scenario_info["description"]}
Context: {scenario_info["context"]}

Student Level: {level} {level_guidance}

Your Role:
1. Engage in natural conversation within the given scenario
2. Use vocabulary and grammar appropriate for the student's level
3. If the student makes mistakes, gently model correct language in your responses
4. Be encouraging and supportive
5. Keep responses concise (2-3 sentences usually)
6. Ask follow-up questions to keep the conversation flowing
7. Stay in character for the scenario (e.g., as a waiter, interviewer, etc.)

Remember:
- Be patient if the student struggles
- Use simple, clear language
- Praise good communication
- Make the conversation feel natural and enjoyable
"""

        return prompt

    def _get_level_guidance(self, level: str) -> str:
        """
        Get level-specific guidance for the AI.

        Args:
            level: Student's English level

        Returns:
            Level guidance string
        """
        guidance_map = {
            "A1": "(Beginner - Use very simple words and short sentences. Basic greetings and phrases.)",
            "A2": "(Elementary - Use simple vocabulary and basic grammar. Everyday expressions.)",
            "B1": "(Intermediate - Use common vocabulary and standard grammar. Can discuss familiar topics.)",
            "B2": "(Upper Intermediate - Use varied vocabulary. Can handle most situations.)",
            "C1": "(Advanced - Use rich vocabulary and complex grammar. Can express ideas fluently.)",
            "C2": "(Proficiency - Use sophisticated language. Nuanced and precise communication.)"
        }
        return guidance_map.get(level, guidance_map["B1"])

    def _get_scoring_prompt(
        self,
        scenario: ConversationScenario,
        level: str,
        messages: List[Dict]
    ) -> str:
        """
        Generate scoring prompt for conversation evaluation.

        Args:
            scenario: Conversation scenario
            level: Student's level
            messages: Conversation messages

        Returns:
            Scoring prompt string
        """
        scenario_info = self.SCENARIOS.get(scenario, self.SCENARIOS[ConversationScenario.DAILY_GREETING])

        # Format conversation for prompt
        conversation_text = "\n".join([
            f"{msg['role'].capitalize()}: {msg['content']}"
            for msg in messages
        ])

        prompt = f"""Evaluate this English conversation practice session.

Scenario: {scenario_info["name"]}
Student Level: {level}

Conversation:
{conversation_text}

Provide your evaluation as a JSON object with the following structure:
{{
    "fluency_score": <number 0-100, how smoothly they spoke>,
    "vocabulary_score": <number 0-100, appropriateness and variety of words used>,
    "grammar_score": <number 0-100, accuracy of grammar and sentence structure>,
    "overall_score": <number 0-100, weighted average performance>,
    "feedback": "<string, 2-3 sentences of encouraging feedback with 1-2 specific suggestions for improvement>"
}}

Scoring Guidelines:
- 90-100: Excellent - Exceeded expectations for this level
- 75-89: Good - Met expectations well with minor issues
- 60-74: Satisfactory - Adequate performance with room for improvement
- 40-59: Fair - Below expectations for this level, needs more practice
- 0-39: Poor - Significant difficulties, needs focused practice

Remember:
- Score fairly based on the student's level ({level})
- Be constructive and encouraging
- Provide actionable feedback
- Highlight what they did well
"""

        return prompt

    def get_available_scenarios(self) -> List[Dict[str, str]]:
        """
        Get list of available conversation scenarios.

        Returns:
            List of scenario dictionaries with id, name, and description
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

    def get_conversation_by_id(
        self,
        conversation_id: int
    ) -> Optional[Conversation]:
        """
        Get a conversation by ID.

        Args:
            conversation_id: ID of the conversation

        Returns:
            Conversation object or None if not found
        """
        db = next(get_db())
        return db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
