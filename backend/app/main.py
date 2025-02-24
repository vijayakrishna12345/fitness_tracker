from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from typing import Dict, List, Optional
from datetime import datetime, date
import os

from .services.supabase_service import SupabaseService
from .services.ai_service import AIService
from .models.schemas import (
    Meal, Workout, UserProfile, DailyReport, 
    WeeklyReport, MealType, WorkoutType,
    FoodItem, Exercise, SleepData,
    MicronutrientData, Recommendation
)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Fitness Tracker API",
    description="AI-powered Fitness Tracking System API",
    version="1.0.0"
)

# Configure CORS and initialize services
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
ai_service = AIService()

# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    # In a real application, you would verify the token and get the user_id
    return "dummy_user_id"

# Root endpoints
@app.get("/")
async def root():
    return {"message": "Welcome to Fitness Tracker API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Profile endpoints
@app.get("/profile", response_model=UserProfile)
async def get_profile(current_user: str = Depends(get_current_user)):
    profile = await SupabaseService.get_user_profile(current_user)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.put("/profile", response_model=UserProfile)
async def update_profile(profile: UserProfile, current_user: str = Depends(get_current_user)):
    result = await SupabaseService.update_profile(current_user, profile.dict())
    if not result:
        raise HTTPException(status_code=400, detail="Failed to update profile")
    return result

# Fasting schedule endpoints
@app.post("/fasting-schedules")
async def create_fasting_schedule(
    schedule_data: Dict,
    current_user: str = Depends(get_current_user)
):
    profile = await SupabaseService.get_user_profile(current_user)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Get AI analysis of the schedule
    analysis = await ai_service.analyze_fasting_schedule(
        UserProfile(**profile),
        schedule_data
    )
    
    # Save schedule with analysis
    result = await SupabaseService.create_fasting_schedule(
        current_user,
        {**schedule_data, "analysis": analysis}
    )
    return {"schedule": result, "analysis": analysis}

@app.get("/fasting-schedules/active")
async def get_active_fasting_schedule(current_user: str = Depends(get_current_user)):
    return await SupabaseService.get_active_fasting_schedule(current_user)

# TDEE and weight tracking endpoints
@app.post("/weight/track")
async def track_weight(
    weight_data: Dict,
    current_user: str = Depends(get_current_user)
):
    profile = await SupabaseService.get_user_profile(current_user)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    result = await SupabaseService.track_weight(current_user, weight_data)
    
    # Analyze TDEE adjustment if needed
    weight_history = await SupabaseService.get_weight_history(current_user, days=30)
    calorie_history = await SupabaseService.get_calorie_history(current_user, days=30)
    
    tdee_analysis = await ai_service.analyze_tdee_adjustment(
        UserProfile(**profile),
        weight_history,
        calorie_history
    )
    
    return {
        "weight_tracking": result,
        "tdee_analysis": tdee_analysis
    }

@app.get("/tdee/calculate")
async def calculate_tdee(current_user: str = Depends(get_current_user)):
    profile = await SupabaseService.get_user_profile(current_user)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    weight_history = await SupabaseService.get_weight_history(current_user, days=30)
    calorie_history = await SupabaseService.get_calorie_history(current_user, days=30)
    
    return await ai_service.analyze_tdee_adjustment(
        UserProfile(**profile),
        weight_history,
        calorie_history
    )

# Meal endpoints with fasting compliance
@app.post("/meals", response_model=Dict)
async def save_meal(meal: Meal, current_user: str = Depends(get_current_user)):
    profile = await SupabaseService.get_user_profile(current_user)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Check fasting schedule compliance
    active_schedule = await SupabaseService.get_active_fasting_schedule(current_user)
    
    # Get AI analysis
    analysis = await ai_service.analyze_meal_plan(meal, UserProfile(**profile))
    
    # Save meal with analysis and fasting compliance
    meal_data = {
        **meal.dict(),
        "analysis": analysis,
        "within_feeding_window": True,  # Will be calculated based on schedule
        "fasting_schedule_id": active_schedule.get("id") if active_schedule else None
    }
    
    result = await SupabaseService.save_meal(current_user, meal_data)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to save meal")
    
    return {"meal": result, "analysis": analysis}

@app.get("/meals/suggestions")
async def get_meal_suggestions(
    consider_fasting: bool = Query(True, description="Whether to consider fasting schedule"),
    current_user: str = Depends(get_current_user)
):
    profile = await SupabaseService.get_user_profile(current_user)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    fasting_schedule = None
    if consider_fasting:
        fasting_schedule = await SupabaseService.get_active_fasting_schedule(current_user)
    
    suggestions = await ai_service.generate_meal_suggestions(
        UserProfile(**profile),
        fasting_schedule
    )
    return suggestions

# Progress tracking endpoints
@app.get("/progress/daily", response_model=DailyReport)
async def get_daily_progress(current_user: str = Depends(get_current_user)):
    result = await SupabaseService.get_daily_progress(current_user)
    if not result:
        raise HTTPException(status_code=404, detail="Daily progress not found")
    return result

@app.get("/progress/weekly", response_model=WeeklyReport)
async def get_weekly_progress(current_user: str = Depends(get_current_user)):
    result = await SupabaseService.get_weekly_progress(current_user)
    if not result:
        raise HTTPException(status_code=404, detail="Weekly progress not found")
    return result

# Workout endpoints with energy expenditure
@app.post("/workouts", response_model=Dict)
async def save_workout(workout: Workout, current_user: str = Depends(get_current_user)):
    profile = await SupabaseService.get_user_profile(current_user)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Get AI analysis with energy expenditure
    analysis = await ai_service.analyze_workout(workout, UserProfile(**profile))
    
    # Save workout with analysis
    workout_data = {**workout.dict(), "analysis": analysis}
    result = await SupabaseService.save_workout(current_user, workout_data)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to save workout")
    
    return {"workout": result, "analysis": analysis}

# Comprehensive progress analysis
@app.get("/progress/analysis")
async def get_progress_analysis(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: str = Depends(get_current_user)
):
    profile = await SupabaseService.get_user_profile(current_user)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Gather all necessary data
    weight_history = await SupabaseService.get_weight_history(current_user, days)
    workout_history = await SupabaseService.get_workout_history(current_user, days)
    meal_history = await SupabaseService.get_meal_history(current_user, days)
    fasting_adherence = await SupabaseService.get_fasting_adherence(current_user, days)
    
    # Get comprehensive analysis
    analysis = await ai_service.analyze_progress(
        UserProfile(**profile),
        weight_history,
        workout_history,
        meal_history,
        fasting_adherence
    )
    
    return analysis

# Search endpoints
@app.get("/search/{category}")
async def search_items(
    category: str,
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: str = Depends(get_current_user)
):
    """
    Smart search with personalized suggestions based on usage history
    """
    if category not in ['food', 'exercise']:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    results = await SupabaseService.search_items(
        current_user,
        query,
        category,
        limit
    )
    return results

@app.post("/search/select/{category}/{item_id}")
async def record_search_selection(
    category: str,
    item_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Record when a user selects an item from search results
    """
    if category not in ['food', 'exercise']:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    await SupabaseService.record_item_usage(current_user, item_id, category)
    return {"status": "success"}

@app.get("/frequently-used/{category}")
async def get_frequently_used(
    category: str,
    limit: int = Query(5, ge=1, le=20),
    current_user: str = Depends(get_current_user)
):
    """
    Get user's frequently used items
    """
    if category not in ['food', 'exercise']:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    items = await SupabaseService.get_frequently_used_items(
        current_user,
        category,
        limit
    )
    return items

@app.get("/trending/{category}")
async def get_trending_items(
    category: str,
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(5, ge=1, le=20)
):
    """
    Get trending items based on overall usage
    """
    if category not in ['food', 'exercise']:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    items = await SupabaseService.get_trending_items(
        category,
        days,
        limit
    )
    return items

# Sleep tracking endpoints
@app.post("/sleep/track")
async def track_sleep(
    sleep_data: SleepData,
    current_user: str = Depends(get_current_user)
):
    """
    Track user's sleep data
    """
    result = await SupabaseService.track_sleep(current_user, sleep_data.dict())
    if not result:
        raise HTTPException(status_code=400, detail="Failed to track sleep")
    return result

@app.get("/sleep/history")
async def get_sleep_history(
    days: int = Query(7, ge=1, le=30),
    current_user: str = Depends(get_current_user)
):
    """
    Get user's sleep history
    """
    return await SupabaseService.get_sleep_history(current_user, days)

@app.get("/sleep/analysis")
async def analyze_sleep(
    days: int = Query(7, ge=1, le=30),
    current_user: str = Depends(get_current_user)
):
    """
    Get analysis of sleep patterns
    """
    profile = await SupabaseService.get_user_profile(current_user)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    sleep_history = await SupabaseService.get_sleep_history(current_user, days)
    analysis = await ai_service.analyze_sleep_patterns(
        UserProfile(**profile),
        sleep_history
    )
    return analysis

# BMI tracking endpoints
@app.get("/health/bmi")
async def get_bmi(current_user: str = Depends(get_current_user)):
    """
    Get user's current BMI and history
    """
    profile = await SupabaseService.get_user_profile(current_user)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    weight_history = await SupabaseService.get_weight_history(current_user, days=30)
    
    return {
        "current_bmi": profile.get("bmi"),
        "weight_history": weight_history,
        "bmi_category": get_bmi_category(profile.get("bmi"))
    }

# Micronutrient tracking endpoints
@app.post("/nutrition/micronutrients")
async def track_micronutrients(
    nutrient_data: MicronutrientData,
    current_user: str = Depends(get_current_user)
):
    """
    Track daily micronutrient intake
    """
    result = await SupabaseService.track_micronutrients(
        current_user,
        nutrient_data.date.isoformat(),
        nutrient_data.nutrients
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to track micronutrients")
    return result

@app.get("/nutrition/micronutrients/history")
async def get_micronutrient_history(
    days: int = Query(7, ge=1, le=30),
    current_user: str = Depends(get_current_user)
):
    """
    Get micronutrient intake history
    """
    return await SupabaseService.get_micronutrient_history(current_user, days)

@app.get("/nutrition/micronutrients/analysis")
async def analyze_micronutrients(
    days: int = Query(7, ge=1, le=30),
    current_user: str = Depends(get_current_user)
):
    """
    Get analysis of micronutrient intake
    """
    profile = await SupabaseService.get_user_profile(current_user)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    nutrient_history = await SupabaseService.get_micronutrient_history(current_user, days)
    analysis = await ai_service.analyze_micronutrient_intake(
        UserProfile(**profile),
        nutrient_history
    )
    return analysis

# Recommendation endpoints
@app.get("/recommendations/daily")
async def get_daily_recommendations(
    current_user: str = Depends(get_current_user)
):
    """
    Get personalized daily recommendations
    """
    return await SupabaseService.get_daily_recommendations(current_user)

@app.post("/recommendations/{recommendation_id}/feedback")
async def save_recommendation_feedback(
    recommendation_id: str,
    is_implemented: bool,
    feedback: Optional[str] = None,
    current_user: str = Depends(get_current_user)
):
    """
    Save user feedback for a recommendation
    """
    result = await SupabaseService.save_recommendation_feedback(
        current_user,
        recommendation_id,
        is_implemented,
        feedback
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to save feedback")
    return result

@app.get("/recommendations/{category}")
async def get_category_recommendations(
    category: str,
    limit: int = Query(5, ge=1, le=20),
    current_user: str = Depends(get_current_user)
):
    """
    Get recommendations for a specific category
    """
    if category not in ['nutrition', 'workout', 'sleep']:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    profile = await SupabaseService.get_user_profile(current_user)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Get relevant user data for context
    context_data = {
        'profile': profile,
        'sleep': await SupabaseService.get_sleep_history(current_user, 7),
        'nutrients': await SupabaseService.get_micronutrient_history(current_user, 7),
        'workouts': await SupabaseService.get_workout_history(current_user, 7)
    }
    
    # Generate query embedding based on user context
    query_embedding = [0] * 1536  # Placeholder - implement embedding generation
    
    recommendations = await SupabaseService.get_personalized_recommendations(
        current_user,
        category,
        query_embedding,
        limit
    )
    return recommendations

# Helper function for BMI categorization
def get_bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese" 