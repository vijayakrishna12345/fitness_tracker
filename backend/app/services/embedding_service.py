from typing import List, Dict, Union
import openai
from ..config.db_config import openai_settings

class EmbeddingService:
    def __init__(self):
        openai.api_key = openai_settings.api_key
        self.model = openai_settings.embedding_model

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            response = await openai.Embedding.acreate(
                input=text,
                model=self.model
            )
            return response['data'][0]['embedding']
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise

    async def generate_batch_embeddings(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                response = await openai.Embedding.acreate(
                    input=batch,
                    model=self.model
                )
                batch_embeddings = [data['embedding'] for data in response['data']]
                embeddings.extend(batch_embeddings)
            except Exception as e:
                print(f"Error generating batch embeddings: {e}")
                raise

        return embeddings

    def combine_text_fields(
        self,
        item: Dict[str, Union[str, List[str]]]
    ) -> str:
        """Combine relevant text fields for embedding generation"""
        fields = []
        
        if 'title' in item:
            fields.append(f"Title: {item['title']}")
        if 'content' in item:
            fields.append(f"Content: {item['content']}")
        if 'category' in item:
            fields.append(f"Category: {item['category']}")
        if 'tags' in item and isinstance(item['tags'], list):
            fields.append(f"Tags: {', '.join(item['tags'])}")
        
        return " | ".join(fields) 