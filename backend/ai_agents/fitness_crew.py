from typing import Dict, List
from .base_agent import BaseAgent
from ..config.ai_config import (
    AGENT_PROMPTS,
    AGENT_TOOLS,
    agent_config,
    LEARNING_CONFIG
)

class FitnessCrewAI:
    def __init__(self):
        # Initialize autonomous agents
        self.nutrition_expert = BaseAgent(
            role="nutrition_expert",
            prompt_template=AGENT_PROMPTS["nutrition_expert"],
            tools=AGENT_TOOLS["nutrition_expert"],
            model_name=agent_config.nutrition_expert_model
        )

        self.workout_analyst = BaseAgent(
            role="workout_analyst",
            prompt_template=AGENT_PROMPTS["workout_analyst"],
            tools=AGENT_TOOLS["workout_analyst"],
            model_name=agent_config.workout_analyst_model
        )

        self.metabolic_analyst = BaseAgent(
            role="metabolic_analyst",
            prompt_template=AGENT_PROMPTS["metabolic_analyst"],
            tools=AGENT_TOOLS["metabolic_analyst"],
            model_name=agent_config.metabolic_analyst_model
        )

        self.progress_tracker = BaseAgent(
            role="progress_tracker",
            prompt_template=AGENT_PROMPTS["progress_tracker"],
            tools=AGENT_TOOLS["progress_tracker"],
            model_name=agent_config.progress_tracker_model
        )

    async def analyze_meal_plan(self, meal_data: Dict) -> Dict:
        """Analyze meal with nutritional insights and fasting compliance"""
        instruction = """
        Analyze this meal plan in detail:
        1. Evaluate nutritional composition and balance
        2. Check alignment with user's goals and TDEE
        3. Verify fasting schedule compliance
        4. Suggest optimizations and alternatives
        5. Consider timing and meal distribution
        """
        return await self.nutrition_expert.process(instruction, meal_data)

    async def analyze_fasting_schedule(self, user_data: Dict) -> Dict:
        """Analyze and optimize fasting schedule"""
        instruction = """
        Analyze this fasting schedule:
        1. Evaluate timing and duration
        2. Check compatibility with lifestyle
        3. Assess metabolic impact
        4. Suggest optimizations
        5. Consider long-term sustainability
        """
        return await self.metabolic_analyst.process(instruction, user_data)

    async def analyze_tdee_adjustment(self, tracking_data: Dict) -> Dict:
        """Analyze TDEE and suggest adjustments"""
        instruction = """
        Analyze TDEE and metabolic data:
        1. Evaluate weight and calorie trends
        2. Identify metabolic adaptations
        3. Calculate optimal adjustments
        4. Suggest implementation strategy
        5. Consider long-term implications
        """
        return await self.metabolic_analyst.process(instruction, tracking_data)

    async def analyze_workout(self, workout_data: Dict) -> Dict:
        """Analyze workout with energy expenditure focus"""
        instruction = """
        Analyze this workout in detail:
        1. Evaluate exercise selection and structure
        2. Assess intensity and volume
        3. Calculate energy expenditure
        4. Check progression path
        5. Suggest optimizations
        """
        return await self.workout_analyst.process(instruction, workout_data)

    async def generate_meal_suggestions(self, user_data: Dict) -> List[Dict]:
        """Generate meal suggestions considering fasting schedule"""
        instruction = """
        Generate personalized meal suggestions:
        1. Consider nutritional requirements
        2. Account for fasting schedule
        3. Align with preferences
        4. Optimize for goals
        5. Ensure practical implementation
        """
        result = await self.nutrition_expert.process(instruction, user_data)
        return result.get("suggestions", [])

    async def analyze_progress(self, user_data: Dict) -> Dict:
        """Analyze overall progress including metabolic health"""
        # Get initial analysis from progress tracker
        progress_instruction = """
        Analyze overall progress:
        1. Evaluate key metrics and trends
        2. Identify patterns and correlations
        3. Assess goal alignment
        4. Calculate success metrics
        5. Generate insights and predictions
        """
        progress_analysis = await self.progress_tracker.process(progress_instruction, user_data)

        # Get metabolic insights
        metabolic_instruction = """
        Analyze metabolic health indicators:
        1. Evaluate energy balance
        2. Check adaptation patterns
        3. Assess hormonal indicators
        4. Review recovery metrics
        5. Suggest optimizations
        """
        metabolic_analysis = await self.metabolic_analyst.process(metabolic_instruction, user_data)

        # Combine insights
        return {
            "progress_analysis": progress_analysis,
            "metabolic_analysis": metabolic_analysis,
            "combined_recommendations": self._combine_recommendations(
                [progress_analysis, metabolic_analysis]
            )
        }

    def _combine_recommendations(self, analyses: List[Dict]) -> List[str]:
        """Combine and prioritize recommendations from multiple analyses"""
        all_recommendations = []
        for analysis in analyses:
            if "recommendations" in analysis and analysis["recommendations"]:
                if isinstance(analysis["recommendations"], list):
                    all_recommendations.extend(analysis["recommendations"])
                elif isinstance(analysis["recommendations"], str):
                    all_recommendations.append(analysis["recommendations"])

        # Remove duplicates and prioritize
        unique_recommendations = list(set(all_recommendations))
        
        # Sort by confidence if available
        return sorted(
            unique_recommendations,
            key=lambda x: next(
                (a.get("confidence", 0) for a in analyses if x in str(a.get("recommendations", ""))),
                0
            ),
            reverse=True
        ) 