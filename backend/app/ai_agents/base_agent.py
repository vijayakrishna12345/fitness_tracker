from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from ..config.ai_config import model_config, LEARNING_CONFIG

class BaseAgent:
    def __init__(
        self,
        role: str,
        prompt_template: str,
        tools: List[str],
        model_name: str = model_config.model_name
    ):
        self.role = role
        self.tools = tools
        self.model_name = model_name
        self.memory = ConversationBufferWindowMemory(k=10)
        self.learning_data = []
        self.last_adaptation = datetime.now()
        
        # Initialize LLM
        self.llm = OpenAI(
            model_name=model_name,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens
        )
        
        # Create base prompt
        self.prompt = PromptTemplate(
            input_variables=["context", "history", "instruction"],
            template=f"{prompt_template}\n\nContext: {{context}}\nConversation History: {{history}}\nInstruction: {{instruction}}"
        )
        
        # Initialize chain
        self.chain = LLMChain(
            llm=self.llm,
            prompt=self.prompt,
            memory=self.memory
        )

    async def process(self, instruction: str, context: Dict) -> Dict:
        """Process an instruction with context"""
        try:
            # Get relevant history
            history = self.memory.load_memory_variables({})
            
            # Execute chain
            response = await self.chain.arun(
                instruction=instruction,
                context=context,
                history=history.get("history", "")
            )
            
            # Process response
            result = self._process_response(response)
            
            # Store interaction for learning
            self._store_interaction(instruction, context, result)
            
            # Check if adaptation is needed
            await self._check_adaptation()
            
            return result
        except Exception as e:
            print(f"Error in {self.role} processing: {e}")
            return {"error": str(e)}

    def _process_response(self, response: str) -> Dict:
        """Process the raw response into structured data"""
        try:
            # Basic parsing - enhance based on needs
            sections = response.split("\n\n")
            processed = {
                "analysis": sections[0] if sections else response,
                "recommendations": sections[1] if len(sections) > 1 else None,
                "confidence": self._calculate_confidence(response)
            }
            return processed
        except Exception as e:
            print(f"Error processing response: {e}")
            return {"error": str(e)}

    def _calculate_confidence(self, response: str) -> float:
        """Calculate confidence score for the response"""
        # Implement confidence calculation logic
        # For now, return a default value
        return 0.8

    def _store_interaction(self, instruction: str, context: Dict, result: Dict):
        """Store interaction for learning"""
        self.learning_data.append({
            "timestamp": datetime.now(),
            "instruction": instruction,
            "context": context,
            "result": result,
            "confidence": result.get("confidence", 0)
        })
        
        # Prune old data
        self._prune_learning_data()

    def _prune_learning_data(self):
        """Remove old learning data"""
        retention_days = LEARNING_CONFIG["memory_retention"]
        cutoff = datetime.now() - timedelta(days=retention_days)
        self.learning_data = [
            data for data in self.learning_data
            if data["timestamp"] > cutoff
        ]

    async def _check_adaptation(self):
        """Check if agent needs to adapt its behavior"""
        if not self._should_adapt():
            return

        await self._adapt()
        self.last_adaptation = datetime.now()

    def _should_adapt(self) -> bool:
        """Determine if adaptation is needed"""
        # Check if enough time has passed since last adaptation
        if datetime.now() - self.last_adaptation < timedelta(days=1):
            return False

        # Check if we have enough low-confidence responses
        recent_confidence = [
            data["confidence"] for data in self.learning_data[-10:]
            if data["confidence"] < LEARNING_CONFIG["feedback_threshold"]
        ]
        
        return len(recent_confidence) >= 3

    async def _adapt(self):
        """Adapt agent behavior based on learning data"""
        try:
            # Analyze patterns in learning data
            patterns = self._analyze_patterns()
            
            # Update prompt template if needed
            if patterns.get("prompt_improvement"):
                self._update_prompt(patterns["prompt_improvement"])
            
            # Adjust temperature if needed
            if patterns.get("temperature_adjustment"):
                self._adjust_temperature(patterns["temperature_adjustment"])
            
            print(f"{self.role} adapted based on learning patterns")
        except Exception as e:
            print(f"Error during adaptation: {e}")

    def _analyze_patterns(self) -> Dict:
        """Analyze patterns in learning data"""
        # Implement pattern analysis logic
        # For now, return empty patterns
        return {}

    def _update_prompt(self, improvement: str):
        """Update the prompt template"""
        # Implement prompt update logic
        pass

    def _adjust_temperature(self, adjustment: float):
        """Adjust model temperature"""
        new_temp = max(0.1, min(1.0, self.llm.temperature + adjustment))
        self.llm = OpenAI(
            model_name=self.model_name,
            temperature=new_temp,
            max_tokens=model_config.max_tokens
        ) 