from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"

class WorkoutType(str, Enum):
    HIIT = "hiit"
    STRENGTH = "strength"
    CARDIO = "cardio"
    FLEXIBILITY = "flexibility"

class FoodItem(BaseModel):
    name: str
    portion: float
    unit: str
    calories: float
    protein: float
    carbs: float
    fats: float

class Meal(BaseModel):
    meal_type: MealType
    foods: List[FoodItem]
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fats: float
    notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class Exercise(BaseModel):
    name: str
    sets: Optional[int] = None
    reps: Optional[int] = None
    duration_minutes: Optional[int] = None
    calories_burned: Optional[float] = None
    weight: Optional[float] = None
    weight_unit: Optional[str] = None

class Workout(BaseModel):
    workout_type: WorkoutType
    exercises: List[Exercise]
    total_duration: int
    total_calories_burned: float
    notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class UserProfile(BaseModel):
    height: float
    weight: float
    age: int
    gender: str
    activity_level: str
    fitness_goals: List[str]
    dietary_restrictions: Optional[List[str]] = None

class DailyReport(BaseModel):
    date: datetime
    total_calories_consumed: float
    total_calories_burned: float
    total_protein: float
    total_carbs: float
    total_fats: float
    workout_minutes: int
    goal_progress: dict

class WeeklyReport(BaseModel):
    start_date: datetime
    end_date: datetime
    average_daily_calories: float
    average_daily_protein: float
    average_daily_carbs: float
    average_daily_fats: float
    total_workout_minutes: int
    workouts_completed: int
    goal_progress: dict 