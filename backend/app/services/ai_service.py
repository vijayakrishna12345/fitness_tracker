from typing import List, Dict
from ..ai_agents.fitness_crew import FitnessCrewAI
from ..models.schemas import (
    UserProfile, Meal, Workout, 
    FoodItem, Exercise, WeeklyReport,
    DailyReport
)

class AIService:
    def __init__(self):
        self.crew_ai = FitnessCrewAI()

    async def analyze_meal_plan(self, meal: Meal, user_profile: UserProfile) -> Dict:
        """Analyze meal and provide nutritional insights with fasting compliance"""
        meal_data = {
            "meal": meal.dict(),
            "user_profile": user_profile.dict(),
            "tdee_data": {
                "daily_target": user_profile.daily_calorie_target,
                "macro_split": user_profile.macro_split
            }
        }
        analysis = await self.crew_ai.analyze_meal_plan(meal_data)
        return {
            "nutritional_analysis": analysis,
            "recommendations": self._generate_meal_recommendations(meal, user_profile),
            "alignment_with_goals": self._check_goal_alignment(meal, user_profile)
        }

    async def analyze_fasting_schedule(self, user_profile: UserProfile, schedule_data: Dict) -> Dict:
        """Analyze and optimize fasting schedule"""
        user_data = {
            "profile": user_profile.dict(),
            "schedule": schedule_data,
            "metabolic_data": {
                "tdee": user_profile.tdee,
                "bmr": user_profile.bmr
            }
        }
        return await self.crew_ai.analyze_fasting_schedule(user_data)

    async def analyze_tdee_adjustment(
        self, 
        user_profile: UserProfile, 
        weight_tracking: List[Dict],
        calorie_tracking: List[Dict]
    ) -> Dict:
        """Analyze TDEE and suggest adjustments"""
        tracking_data = {
            "profile": user_profile.dict(),
            "weight_history": weight_tracking,
            "calorie_history": calorie_tracking,
            "current_tdee": user_profile.tdee,
            "target_weight": user_profile.target_weight,
            "weekly_goal_rate": user_profile.weekly_goal_rate
        }
        return await self.crew_ai.analyze_tdee_adjustment(tracking_data)

    async def analyze_workout(self, workout: Workout, user_profile: UserProfile) -> Dict:
        """Analyze workout with energy expenditure focus"""
        workout_data = {
            "workout": workout.dict(),
            "user_profile": user_profile.dict(),
            "tdee_data": {
                "daily_target": user_profile.daily_calorie_target,
                "activity_level": user_profile.activity_level
            }
        }
        analysis = await self.crew_ai.analyze_workout(workout_data)
        return {
            "workout_analysis": analysis,
            "form_tips": self._generate_exercise_tips(workout),
            "progression_suggestions": self._suggest_progression(workout, user_profile),
            "energy_expenditure": self._calculate_energy_expenditure(workout, user_profile)
        }

    async def generate_meal_suggestions(self, user_profile: UserProfile, fasting_schedule: Dict = None) -> List[Dict]:
        """Generate personalized meal suggestions considering fasting schedule"""
        user_data = {
            "profile": user_profile.dict(),
            "fasting_schedule": fasting_schedule,
            "nutritional_targets": {
                "daily_calories": user_profile.daily_calorie_target,
                "macro_split": user_profile.macro_split
            }
        }
        return await self.crew_ai.generate_meal_suggestions(user_data)

    async def analyze_progress(
        self, 
        user_profile: UserProfile,
        weight_history: List[Dict],
        workout_history: List[Dict],
        meal_history: List[Dict],
        fasting_adherence: List[Dict]
    ) -> Dict:
        """Analyze overall progress including metabolic health"""
        progress_data = {
            "profile": user_profile.dict(),
            "weight_history": weight_history,
            "workout_history": workout_history,
            "meal_history": meal_history,
            "fasting_adherence": fasting_adherence,
            "goals": {
                "target_weight": user_profile.target_weight,
                "weekly_goal_rate": user_profile.weekly_goal_rate
            }
        }
        return await self.crew_ai.analyze_progress(progress_data)

    def _calculate_energy_expenditure(self, workout: Workout, profile: UserProfile) -> Dict:
        """Calculate detailed energy expenditure for workout"""
        # Implementation will be added
        return {}

    def _generate_meal_recommendations(self, meal: Meal, profile: UserProfile) -> List[str]:
        """Generate specific meal recommendations considering TDEE"""
        # Implementation will be added
        return []

    def _check_goal_alignment(self, meal: Meal, profile: UserProfile) -> Dict:
        """Check how well the meal aligns with user's goals and TDEE"""
        # Implementation will be added
        return {}

    def _generate_exercise_tips(self, workout: Workout) -> List[str]:
        """Generate form tips for exercises"""
        # Implementation will be added
        return []

    def _suggest_progression(self, workout: Workout, profile: UserProfile) -> List[str]:
        """Suggest workout progressions based on goals and TDEE"""
        # Implementation will be added
        return [] 