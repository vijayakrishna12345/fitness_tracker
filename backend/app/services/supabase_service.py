from typing import Dict, List, Optional
from datetime import datetime, timedelta
from ..config.supabase import supabase

class SupabaseService:
    @staticmethod
    async def get_user_profile(user_id: str) -> Optional[Dict]:
        try:
            response = supabase.table('profiles').select('*').eq('id', user_id).single().execute()
            return response.data
        except Exception as e:
            print(f"Error fetching user profile: {e}")
            return None

    @staticmethod
    async def update_profile(user_id: str, profile_data: Dict) -> Optional[Dict]:
        try:
            response = supabase.table('profiles').update(profile_data).eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating profile: {e}")
            return None

    @staticmethod
    async def save_workout(user_id: str, workout_data: Dict) -> Optional[Dict]:
        try:
            workout_data['user_id'] = user_id
            response = supabase.table('workouts').insert(workout_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error saving workout: {e}")
            return None

    @staticmethod
    async def save_meal(user_id: str, meal_data: Dict) -> Optional[Dict]:
        try:
            meal_data['user_id'] = user_id
            response = supabase.table('meals').insert(meal_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error saving meal: {e}")
            return None

    @staticmethod
    async def get_daily_progress(user_id: str) -> Optional[Dict]:
        try:
            today = datetime.now().date()
            
            # Get today's meals
            meals = supabase.table('meals')\
                .select('*')\
                .eq('user_id', user_id)\
                .gte('timestamp', today.isoformat())\
                .lt('timestamp', (today + timedelta(days=1)).isoformat())\
                .execute()

            # Get today's workouts
            workouts = supabase.table('workouts')\
                .select('*')\
                .eq('user_id', user_id)\
                .gte('timestamp', today.isoformat())\
                .lt('timestamp', (today + timedelta(days=1)).isoformat())\
                .execute()

            return {
                'date': today.isoformat(),
                'meals': meals.data,
                'workouts': workouts.data,
                'total_calories_consumed': sum(meal.get('total_calories', 0) for meal in meals.data),
                'total_calories_burned': sum(workout.get('total_calories_burned', 0) for workout in workouts.data),
                'total_protein': sum(meal.get('total_protein', 0) for meal in meals.data),
                'total_carbs': sum(meal.get('total_carbs', 0) for meal in meals.data),
                'total_fats': sum(meal.get('total_fats', 0) for meal in meals.data),
                'workout_minutes': sum(workout.get('total_duration', 0) for workout in workouts.data)
            }
        except Exception as e:
            print(f"Error fetching daily progress: {e}")
            return None

    @staticmethod
    async def get_weekly_progress(user_id: str) -> Optional[Dict]:
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=7)
            
            # Get week's meals
            meals = supabase.table('meals')\
                .select('*')\
                .eq('user_id', user_id)\
                .gte('timestamp', start_date.isoformat())\
                .lt('timestamp', (end_date + timedelta(days=1)).isoformat())\
                .execute()

            # Get week's workouts
            workouts = supabase.table('workouts')\
                .select('*')\
                .eq('user_id', user_id)\
                .gte('timestamp', start_date.isoformat())\
                .lt('timestamp', (end_date + timedelta(days=1)).isoformat())\
                .execute()

            total_days = len(set(meal.get('timestamp', '').split('T')[0] for meal in meals.data))
            
            return {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'average_daily_calories': sum(meal.get('total_calories', 0) for meal in meals.data) / max(total_days, 1),
                'average_daily_protein': sum(meal.get('total_protein', 0) for meal in meals.data) / max(total_days, 1),
                'average_daily_carbs': sum(meal.get('total_carbs', 0) for meal in meals.data) / max(total_days, 1),
                'average_daily_fats': sum(meal.get('total_fats', 0) for meal in meals.data) / max(total_days, 1),
                'total_workout_minutes': sum(workout.get('total_duration', 0) for workout in workouts.data),
                'workouts_completed': len(workouts.data)
            }
        except Exception as e:
            print(f"Error fetching weekly progress: {e}")
            return None

    @staticmethod
    async def get_user_progress(user_id: str, days: int = 30) -> Dict[str, List]:
        try:
            workouts = supabase.table('workouts')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(days)\
                .execute()
            
            meals = supabase.table('meals')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(days)\
                .execute()

            return {
                'workouts': workouts.data,
                'meals': meals.data
            }
        except Exception as e:
            print(f"Error fetching user progress: {e}")
            return {'workouts': [], 'meals': []}

    @staticmethod
    async def search_items(
        user_id: str,
        search_term: str,
        category: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search for items with smart suggestions based on history and similarity
        """
        try:
            # Call the smart suggestions function
            response = supabase.rpc(
                'get_smart_suggestions',
                {
                    'p_user_id': user_id,
                    'p_search_term': search_term,
                    'p_category': category,
                    'p_limit': limit
                }
            ).execute()

            # Log the search
            await SupabaseService.log_search(user_id, search_term, category)

            return response.data if response.data else []
        except Exception as e:
            print(f"Error in smart search: {e}")
            return []

    @staticmethod
    async def log_search(
        user_id: str,
        search_term: str,
        category: str,
        selected_item_id: Optional[str] = None
    ) -> None:
        """
        Log search history for improving suggestions
        """
        try:
            supabase.table('search_history').insert({
                'user_id': user_id,
                'search_term': search_term,
                'category': category,
                'selected_item_id': selected_item_id
            }).execute()
        except Exception as e:
            print(f"Error logging search: {e}")

    @staticmethod
    async def get_frequently_used_items(
        user_id: str,
        category: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Get user's frequently used items for a category
        """
        try:
            response = supabase.table('frequently_used_items')\
                .select('*, food_items(*), exercises(*)')\
                .eq('user_id', user_id)\
                .eq('item_type', category)\
                .order('use_count', desc=True)\
                .limit(limit)\
                .execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching frequently used items: {e}")
            return []

    @staticmethod
    async def record_item_usage(
        user_id: str,
        item_id: str,
        item_type: str
    ) -> None:
        """
        Record when an item is used to update frequency counts
        """
        try:
            # First try to update existing record
            response = supabase.table('frequently_used_items')\
                .upsert({
                    'user_id': user_id,
                    'item_id': item_id,
                    'item_type': item_type,
                    'use_count': 1,
                    'last_used': datetime.now().isoformat()
                })\
                .execute()
        except Exception as e:
            print(f"Error recording item usage: {e}")

    @staticmethod
    async def get_trending_items(
        category: str,
        days: int = 7,
        limit: int = 5
    ) -> List[Dict]:
        """
        Get trending items based on overall usage
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            response = supabase.table('frequently_used_items')\
                .select('item_id, item_type, count(*) as trend_count')\
                .eq('item_type', category)\
                .gte('last_used', cutoff_date)\
                .group('item_id, item_type')\
                .order('trend_count', desc=True)\
                .limit(limit)\
                .execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching trending items: {e}")
            return []

    @staticmethod
    async def track_sleep(user_id: str, sleep_data: Dict) -> Optional[Dict]:
        """
        Track user's sleep data
        """
        try:
            sleep_data['user_id'] = user_id
            response = supabase.table('sleep_tracking').insert(sleep_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error tracking sleep: {e}")
            return None

    @staticmethod
    async def get_sleep_history(
        user_id: str,
        days: int = 7
    ) -> List[Dict]:
        """
        Get user's sleep history for the specified number of days
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            response = supabase.table('sleep_tracking')\
                .select('*')\
                .eq('user_id', user_id)\
                .gte('created_at', start_date)\
                .order('created_at', desc=True)\
                .execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching sleep history: {e}")
            return []

    @staticmethod
    async def track_micronutrients(
        user_id: str,
        date: str,
        nutrients: Dict
    ) -> Optional[Dict]:
        """
        Track daily micronutrient intake
        """
        try:
            data = {
                'user_id': user_id,
                'date': date,
                'nutrients': nutrients
            }
            response = supabase.table('micronutrient_tracking')\
                .insert(data)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error tracking micronutrients: {e}")
            return None

    @staticmethod
    async def get_micronutrient_history(
        user_id: str,
        days: int = 7
    ) -> List[Dict]:
        """
        Get user's micronutrient history
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).date().isoformat()
            response = supabase.table('micronutrient_tracking')\
                .select('*')\
                .eq('user_id', user_id)\
                .gte('date', start_date)\
                .order('date', desc=True)\
                .execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching micronutrient history: {e}")
            return []

    @staticmethod
    async def get_personalized_recommendations(
        user_id: str,
        category: str,
        query_embedding: List[float],
        limit: int = 5
    ) -> List[Dict]:
        """
        Get personalized recommendations using Vector + Graph RAG
        """
        try:
            response = supabase.rpc(
                'get_personalized_recommendations',
                {
                    'p_user_id': user_id,
                    'p_category': category,
                    'p_query_embedding': query_embedding,
                    'p_limit': limit
                }
            ).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching recommendations: {e}")
            return []

    @staticmethod
    async def save_recommendation_feedback(
        user_id: str,
        recommendation_id: str,
        is_implemented: bool,
        feedback: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Save user feedback for a recommendation
        """
        try:
            data = {
                'user_id': user_id,
                'recommendation_id': recommendation_id,
                'is_implemented': is_implemented,
                'feedback': feedback
            }
            response = supabase.table('user_recommendations')\
                .upsert(data)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error saving recommendation feedback: {e}")
            return None

    @staticmethod
    async def get_daily_recommendations(
        user_id: str,
        categories: List[str] = ['nutrition', 'workout', 'sleep']
    ) -> Dict[str, List[Dict]]:
        """
        Get daily personalized recommendations for multiple categories
        """
        try:
            recommendations = {}
            for category in categories:
                # Get user's profile and recent data for context
                profile = await SupabaseService.get_user_profile(user_id)
                recent_data = {
                    'sleep': await SupabaseService.get_sleep_history(user_id, 7),
                    'nutrients': await SupabaseService.get_micronutrient_history(user_id, 7),
                    'workouts': await SupabaseService.get_workout_history(user_id, 7)
                }
                
                # Generate query embedding based on user context
                # This would typically be done through an embedding service
                query_embedding = [0] * 1536  # Placeholder
                
                category_recommendations = await SupabaseService.get_personalized_recommendations(
                    user_id,
                    category,
                    query_embedding
                )
                recommendations[category] = category_recommendations
            
            return recommendations
        except Exception as e:
            print(f"Error fetching daily recommendations: {e}")
            return {} 