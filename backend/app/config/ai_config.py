from typing import Dict, Optional
from pydantic import BaseSettings
from enum import Enum

class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"

class ModelConfig(BaseSettings):
    provider: ModelProvider = ModelProvider.OPENAI
    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 1000
    api_key: str

    class Config:
        env_prefix = "AI_"

class AgentConfig(BaseSettings):
    nutrition_expert_model: str = "gpt-4"
    workout_analyst_model: str = "gpt-4"
    metabolic_analyst_model: str = "gpt-4"
    progress_tracker_model: str = "gpt-4"
    autonomous_mode: bool = True
    learning_enabled: bool = True
    feedback_collection: bool = True
    
    class Config:
        env_prefix = "AGENT_"

# Global configurations
model_config = ModelConfig()
agent_config = AgentConfig()

# Agent-specific prompts and tools
AGENT_PROMPTS = {
    "nutrition_expert": """You are an expert nutritionist with deep knowledge in:
    - Meal planning and macronutrient optimization
    - Intermittent fasting and metabolic health
    - Sports nutrition and performance optimization
    - Dietary requirements for different fitness goals
    
    Consider these aspects in your analysis:
    1. Individual metabolic factors
    2. Training schedule and intensity
    3. Fasting windows and meal timing
    4. Long-term sustainability
    """,
    
    "workout_analyst": """You are an elite fitness trainer specializing in:
    - Exercise programming and periodization
    - Energy systems and metabolic conditioning
    - Biomechanics and injury prevention
    - Performance optimization
    
    Focus on:
    1. Individual capacity and progression
    2. Energy expenditure optimization
    3. Recovery and adaptation
    4. Long-term development
    """,
    
    "metabolic_analyst": """You are a metabolic health specialist with expertise in:
    - TDEE and energy balance
    - Metabolic adaptation
    - Hormonal optimization
    - Body composition management
    
    Analyze:
    1. Metabolic rate changes
    2. Adaptation patterns
    3. Recovery markers
    4. Optimization strategies
    """,
    
    "progress_tracker": """You are a data scientist specializing in fitness analytics:
    - Progress tracking and pattern recognition
    - Predictive modeling for fitness outcomes
    - Behavioral analysis and adherence
    - Performance metrics and benchmarking
    
    Focus on:
    1. Trend analysis and forecasting
    2. Adherence patterns
    3. Performance correlations
    4. Goal alignment
    """
}

# Tool configurations for agents
AGENT_TOOLS = {
    "nutrition_expert": [
        "meal_analysis",
        "nutrient_optimization",
        "fasting_window_check",
        "recipe_generation"
    ],
    "workout_analyst": [
        "exercise_analysis",
        "volume_optimization",
        "recovery_assessment",
        "progression_planning"
    ],
    "metabolic_analyst": [
        "tdee_calculation",
        "adaptation_analysis",
        "hormone_optimization",
        "energy_balance_check"
    ],
    "progress_tracker": [
        "trend_analysis",
        "prediction_modeling",
        "adherence_scoring",
        "goal_tracking"
    ]
}

# Learning and adaptation settings
LEARNING_CONFIG = {
    "feedback_threshold": 0.8,
    "adaptation_rate": 0.1,
    "memory_retention": 30,  # days
    "pattern_recognition_threshold": 0.7
} 