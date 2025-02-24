-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create enum types
CREATE TYPE meal_type AS ENUM ('breakfast', 'lunch', 'dinner', 'snack');
CREATE TYPE workout_type AS ENUM ('hiit', 'strength', 'cardio', 'flexibility');
CREATE TYPE fasting_type AS ENUM ('intermittent_fasting', 'time_restricted_feeding');
CREATE TYPE goal_type AS ENUM ('weight_loss', 'muscle_gain', 'maintenance', 'recomposition');
CREATE TYPE activity_level AS ENUM (
    'sedentary',
    'lightly_active',
    'moderately_active',
    'very_active',
    'extremely_active'
);

-- Add sleep quality enum
CREATE TYPE sleep_quality AS ENUM ('poor', 'fair', 'good', 'excellent');

-- Create profiles table with enhanced tracking
CREATE TABLE profiles (
    id UUID REFERENCES auth.users ON DELETE CASCADE,
    height FLOAT NOT NULL,
    weight FLOAT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    activity_level activity_level NOT NULL,
    fitness_goals goal_type[] NOT NULL,
    dietary_restrictions TEXT[],
    target_weight FLOAT,
    weekly_goal_rate FLOAT, -- in kg/week, can be negative for weight loss
    tdee FLOAT, -- Total Daily Energy Expenditure
    bmr FLOAT,  -- Basal Metabolic Rate
    bmi FLOAT,  -- Added BMI field
    daily_calorie_target FLOAT,
    macro_split JSONB, -- {"protein": 30, "carbs": 40, "fats": 30}
    micro_targets JSONB, -- Added micronutrient targets
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id)
);

-- Create fasting_schedules table
CREATE TABLE fasting_schedules (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    fasting_type fasting_type NOT NULL,
    fasting_window_start TIME NOT NULL,
    fasting_window_end TIME NOT NULL,
    feeding_window_start TIME NOT NULL,
    feeding_window_end TIME NOT NULL,
    active_days INTEGER[], -- Array of days (1-7) when schedule is active
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create weight_tracking table for detailed weight history
CREATE TABLE weight_tracking (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    weight FLOAT NOT NULL,
    body_fat_percentage FLOAT,
    lean_mass FLOAT,
    waist_circumference FLOAT,
    notes TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create tdee_tracking table for metabolic rate adjustments
CREATE TABLE tdee_tracking (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    calories_consumed FLOAT NOT NULL,
    weight_change FLOAT, -- weekly weight change
    adjusted_tdee FLOAT, -- calculated based on weight change and intake
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create food_items table
CREATE TABLE food_items (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    portion FLOAT NOT NULL,
    unit TEXT NOT NULL,
    calories FLOAT NOT NULL,
    protein FLOAT NOT NULL,
    carbs FLOAT NOT NULL,
    fats FLOAT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create meals table
CREATE TABLE meals (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    meal_type meal_type NOT NULL,
    total_calories FLOAT NOT NULL,
    total_protein FLOAT NOT NULL,
    total_carbs FLOAT NOT NULL,
    total_fats FLOAT NOT NULL,
    within_feeding_window BOOLEAN DEFAULT true,
    fasting_schedule_id UUID REFERENCES fasting_schedules(id),
    notes TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    analysis JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create meal_foods junction table
CREATE TABLE meal_foods (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    meal_id UUID REFERENCES meals(id) ON DELETE CASCADE,
    food_item_id UUID REFERENCES food_items(id) ON DELETE CASCADE,
    portion FLOAT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create exercises table
CREATE TABLE exercises (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    equipment_needed TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create workouts table
CREATE TABLE workouts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    workout_type workout_type NOT NULL,
    total_duration INTEGER NOT NULL,
    total_calories_burned FLOAT NOT NULL,
    notes TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    analysis JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create workout_exercises junction table
CREATE TABLE workout_exercises (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    workout_id UUID REFERENCES workouts(id) ON DELETE CASCADE,
    exercise_id UUID REFERENCES exercises(id) ON DELETE CASCADE,
    sets INTEGER,
    reps INTEGER,
    duration_minutes INTEGER,
    calories_burned FLOAT,
    weight FLOAT,
    weight_unit TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create progress_tracking table
CREATE TABLE progress_tracking (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    weight FLOAT,
    body_fat_percentage FLOAT,
    measurements JSONB,
    progress_photos TEXT[],
    notes TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create search_history table
CREATE TABLE search_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    search_term TEXT NOT NULL,
    category TEXT NOT NULL, -- 'food', 'exercise', etc.
    selected_item_id UUID,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create frequently_used_items table
CREATE TABLE frequently_used_items (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    item_id UUID NOT NULL,
    item_type TEXT NOT NULL, -- 'food', 'exercise', etc.
    use_count INTEGER DEFAULT 1,
    last_used TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create sleep_tracking table
CREATE TABLE sleep_tracking (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    sleep_duration FLOAT NOT NULL, -- in hours
    sleep_quality sleep_quality NOT NULL,
    bed_time TIMESTAMPTZ NOT NULL,
    wake_time TIMESTAMPTZ NOT NULL,
    deep_sleep_duration FLOAT, -- in hours
    rem_sleep_duration FLOAT, -- in hours
    interruptions INTEGER,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create micronutrient_tracking table
CREATE TABLE micronutrient_tracking (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    nutrients JSONB NOT NULL, -- Store all micronutrients
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create recommendations table with vector support
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE recommendations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    category TEXT NOT NULL, -- 'nutrition', 'workout', 'sleep', etc.
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT[] NOT NULL,
    embedding vector(1536), -- For similarity search
    metadata JSONB, -- Additional structured data
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create user_recommendations junction table
CREATE TABLE user_recommendations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    recommendation_id UUID REFERENCES recommendations(id) ON DELETE CASCADE,
    relevance_score FLOAT,
    is_implemented BOOLEAN DEFAULT false,
    feedback TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create recommendation_graph table for Graph RAG
CREATE TABLE recommendation_graph (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    source_id UUID REFERENCES recommendations(id) ON DELETE CASCADE,
    target_id UUID REFERENCES recommendations(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    weight FLOAT DEFAULT 1.0,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX idx_meals_user_timestamp ON meals(user_id, timestamp);
CREATE INDEX idx_workouts_user_timestamp ON workouts(user_id, timestamp);
CREATE INDEX idx_progress_user_timestamp ON progress_tracking(user_id, timestamp);
CREATE INDEX idx_meal_foods_meal ON meal_foods(meal_id);
CREATE INDEX idx_workout_exercises_workout ON workout_exercises(workout_id);
CREATE INDEX idx_fasting_schedules_user ON fasting_schedules(user_id);
CREATE INDEX idx_weight_tracking_user_timestamp ON weight_tracking(user_id, timestamp);
CREATE INDEX idx_tdee_tracking_user_date ON tdee_tracking(user_id, date);
CREATE INDEX idx_search_history_user_term ON search_history(user_id, search_term);
CREATE INDEX idx_search_history_category ON search_history(category);
CREATE INDEX idx_frequently_used_items_user ON frequently_used_items(user_id, item_type);
CREATE INDEX idx_search_history_term_trgm ON search_history USING gin (search_term gin_trgm_ops);

-- Add indexes for new tables
CREATE INDEX idx_sleep_tracking_user ON sleep_tracking(user_id);
CREATE INDEX idx_micronutrient_tracking_user_date ON micronutrient_tracking(user_id, date);
CREATE INDEX idx_recommendations_category ON recommendations(category);
CREATE INDEX idx_recommendations_embedding ON recommendations USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_user_recommendations_user ON user_recommendations(user_id);
CREATE INDEX idx_recommendation_graph_source ON recommendation_graph(source_id);
CREATE INDEX idx_recommendation_graph_target ON recommendation_graph(target_id);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE meals ENABLE ROW LEVEL SECURITY;
ALTER TABLE workouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE progress_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE meal_foods ENABLE ROW LEVEL SECURITY;
ALTER TABLE workout_exercises ENABLE ROW LEVEL SECURITY;
ALTER TABLE fasting_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE weight_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE tdee_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE frequently_used_items ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Profiles: Users can only read and update their own profile
CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    USING (auth.uid() = id);

-- Meals: Users can CRUD their own meals
CREATE POLICY "Users can manage own meals"
    ON meals FOR ALL
    USING (auth.uid() = user_id);

-- Workouts: Users can CRUD their own workouts
CREATE POLICY "Users can manage own workouts"
    ON workouts FOR ALL
    USING (auth.uid() = user_id);

-- Progress: Users can CRUD their own progress entries
CREATE POLICY "Users can manage own progress"
    ON progress_tracking FOR ALL
    USING (auth.uid() = user_id);

-- Junction tables inherit RLS from parent tables
CREATE POLICY "Users can manage own meal foods"
    ON meal_foods FOR ALL
    USING (EXISTS (
        SELECT 1 FROM meals
        WHERE meals.id = meal_foods.meal_id
        AND meals.user_id = auth.uid()
    ));

CREATE POLICY "Users can manage own workout exercises"
    ON workout_exercises FOR ALL
    USING (EXISTS (
        SELECT 1 FROM workouts
        WHERE workouts.id = workout_exercises.workout_id
        AND workouts.user_id = auth.uid()
    ));

-- Create RLS policies for new tables
CREATE POLICY "Users can manage own fasting schedules"
    ON fasting_schedules FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own weight tracking"
    ON weight_tracking FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own tdee tracking"
    ON tdee_tracking FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own search history"
    ON search_history FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own frequently used items"
    ON frequently_used_items FOR ALL
    USING (auth.uid() = user_id);

-- Create RLS policies for new tables
CREATE POLICY "Users can manage own sleep tracking"
    ON sleep_tracking FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own micronutrient tracking"
    ON micronutrient_tracking FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view recommendations"
    ON recommendations FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Users can manage own recommendation relationships"
    ON user_recommendations FOR ALL
    USING (auth.uid() = user_id);

-- Create function for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updating timestamps
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_food_items_updated_at
    BEFORE UPDATE ON food_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meals_updated_at
    BEFORE UPDATE ON meals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_exercises_updated_at
    BEFORE UPDATE ON exercises
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workouts_updated_at
    BEFORE UPDATE ON workouts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fasting_schedules_updated_at
    BEFORE UPDATE ON fasting_schedules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create functions for TDEE calculations
CREATE OR REPLACE FUNCTION calculate_bmr(
    weight FLOAT,
    height FLOAT,
    age INTEGER,
    gender TEXT
) RETURNS FLOAT AS $$
BEGIN
    -- Mifflin-St Jeor Equation
    IF gender = 'male' THEN
        RETURN (10 * weight) + (6.25 * height) - (5 * age) + 5;
    ELSE
        RETURN (10 * weight) + (6.25 * height) - (5 * age) - 161;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION calculate_tdee(
    bmr FLOAT,
    activity_level activity_level
) RETURNS FLOAT AS $$
BEGIN
    RETURN bmr * 
        CASE activity_level
            WHEN 'sedentary' THEN 1.2
            WHEN 'lightly_active' THEN 1.375
            WHEN 'moderately_active' THEN 1.55
            WHEN 'very_active' THEN 1.725
            WHEN 'extremely_active' THEN 1.9
            ELSE 1.2
        END;
END;
$$ LANGUAGE plpgsql;

-- Create function to update TDEE and calorie targets
CREATE OR REPLACE FUNCTION update_user_tdee_targets()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate BMR
    NEW.bmr := calculate_bmr(NEW.weight, NEW.height, NEW.age, NEW.gender);
    
    -- Calculate TDEE
    NEW.tdee := calculate_tdee(NEW.bmr, NEW.activity_level);
    
    -- Calculate BMI
    NEW.bmi := calculate_bmi(NEW.weight, NEW.height);
    
    -- Calculate daily calorie target based on goals
    -- Assuming weekly_goal_rate is in kg/week
    -- 1 kg of fat is approximately 7700 calories
    NEW.daily_calorie_target := NEW.tdee + (NEW.weekly_goal_rate * 7700 / 7);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update TDEE and targets
CREATE TRIGGER update_tdee_targets
    BEFORE INSERT OR UPDATE OF weight, height, age, gender, activity_level, weekly_goal_rate
    ON profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_user_tdee_targets();

-- Create function to update frequently used items
CREATE OR REPLACE FUNCTION update_frequently_used_item()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO frequently_used_items (user_id, item_id, item_type)
    VALUES (NEW.user_id, NEW.selected_item_id, NEW.category)
    ON CONFLICT (user_id, item_id) DO UPDATE
    SET use_count = frequently_used_items.use_count + 1,
        last_used = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updating frequently used items
CREATE TRIGGER update_frequently_used_item_trigger
    AFTER INSERT ON search_history
    FOR EACH ROW
    WHEN (NEW.selected_item_id IS NOT NULL)
    EXECUTE FUNCTION update_frequently_used_item();

-- Create function for smart search suggestions
CREATE OR REPLACE FUNCTION get_smart_suggestions(
    p_user_id UUID,
    p_search_term TEXT,
    p_category TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    item_id UUID,
    item_name TEXT,
    item_type TEXT,
    use_count INTEGER,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH combined_results AS (
        -- Get frequently used items
        (SELECT 
            i.id as item_id,
            CASE 
                WHEN i.item_type = 'food' THEN fi.name
                WHEN i.item_type = 'exercise' THEN e.name
            END as item_name,
            i.item_type,
            i.use_count,
            1.0 as similarity
        FROM frequently_used_items i
        LEFT JOIN food_items fi ON i.item_id = fi.id AND i.item_type = 'food'
        LEFT JOIN exercises e ON i.item_id = e.id AND i.item_type = 'exercise'
        WHERE i.user_id = p_user_id
        AND i.item_type = p_category
        ORDER BY i.use_count DESC, i.last_used DESC
        LIMIT p_limit)
        
        UNION ALL
        
        -- Get similar items based on search term
        (SELECT 
            CASE 
                WHEN p_category = 'food' THEN f.id
                WHEN p_category = 'exercise' THEN e.id
            END as item_id,
            CASE 
                WHEN p_category = 'food' THEN f.name
                WHEN p_category = 'exercise' THEN e.name
            END as item_name,
            p_category as item_type,
            0 as use_count,
            similarity(
                CASE 
                    WHEN p_category = 'food' THEN f.name
                    WHEN p_category = 'exercise' THEN e.name
                END,
                p_search_term
            ) as similarity
        FROM (
            SELECT * FROM food_items f WHERE p_category = 'food'
            UNION ALL
            SELECT * FROM exercises e WHERE p_category = 'exercise'
        ) items
        WHERE 
            CASE 
                WHEN p_category = 'food' THEN 
                    similarity(f.name, p_search_term) > 0.3
                WHEN p_category = 'exercise' THEN 
                    similarity(e.name, p_search_term) > 0.3
            END
        ORDER BY similarity DESC
        LIMIT p_limit)
    )
    SELECT DISTINCT ON (item_name)
        item_id,
        item_name,
        item_type,
        use_count,
        similarity
    FROM combined_results
    ORDER BY item_name, use_count DESC, similarity DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate BMI
CREATE OR REPLACE FUNCTION calculate_bmi(
    weight FLOAT,
    height FLOAT
) RETURNS FLOAT AS $$
BEGIN
    -- BMI = weight(kg) / height(m)²
    RETURN weight / ((height/100) * (height/100));
END;
$$ LANGUAGE plpgsql;

-- Function to get personalized recommendations using Vector + Graph RAG
CREATE OR REPLACE FUNCTION get_personalized_recommendations(
    p_user_id UUID,
    p_category TEXT,
    p_query_embedding vector(1536),
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    recommendation_id UUID,
    title TEXT,
    content TEXT,
    relevance_score FLOAT,
    graph_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH vector_matches AS (
        SELECT 
            r.id,
            r.title,
            r.content,
            1 - (r.embedding <=> p_query_embedding) as vector_similarity
        FROM recommendations r
        WHERE r.category = p_category
        ORDER BY r.embedding <=> p_query_embedding
        LIMIT 20
    ),
    graph_scores AS (
        SELECT
            r.id,
            SUM(rg.weight) as graph_weight
        FROM recommendations r
        JOIN recommendation_graph rg ON r.id = rg.target_id
        JOIN user_recommendations ur ON rg.source_id = ur.recommendation_id
        WHERE ur.user_id = p_user_id
        AND ur.is_implemented = true
        GROUP BY r.id
    )
    SELECT
        vm.id,
        vm.title,
        vm.content,
        vm.vector_similarity as relevance_score,
        COALESCE(gs.graph_weight, 0) as graph_score
    FROM vector_matches vm
    LEFT JOIN graph_scores gs ON vm.id = gs.id
    ORDER BY (vm.vector_similarity * 0.7 + COALESCE(gs.graph_weight, 0) * 0.3) DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql; 