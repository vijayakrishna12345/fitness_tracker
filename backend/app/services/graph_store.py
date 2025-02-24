from typing import List, Dict, Optional
from neo4j import GraphDatabase, AsyncGraphDatabase
from ..config.db_config import neo4j_settings

class GraphStore:
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            neo4j_settings.uri,
            auth=(neo4j_settings.username, neo4j_settings.password)
        )

    async def close(self):
        """Close the database connection"""
        await self.driver.close()

    async def create_recommendation_node(
        self,
        recommendation_id: str,
        properties: Dict
    ) -> bool:
        """Create a recommendation node"""
        query = """
        CREATE (r:Recommendation {
            id: $id,
            title: $title,
            category: $category,
            created_at: datetime()
        })
        """
        try:
            async with self.driver.session(database=neo4j_settings.database) as session:
                await session.run(
                    query,
                    id=recommendation_id,
                    **properties
                )
            return True
        except Exception as e:
            print(f"Error creating recommendation node: {e}")
            return False

    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Dict = None
    ) -> bool:
        """Create a relationship between recommendations"""
        query = """
        MATCH (source:Recommendation {id: $source_id})
        MATCH (target:Recommendation {id: $target_id})
        CREATE (source)-[r:RELATES_TO {
            type: $relationship_type,
            weight: $weight,
            created_at: datetime()
        }]->(target)
        """
        try:
            props = properties or {}
            weight = props.get('weight', 1.0)
            
            async with self.driver.session(database=neo4j_settings.database) as session:
                await session.run(
                    query,
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type=relationship_type,
                    weight=weight
                )
            return True
        except Exception as e:
            print(f"Error creating relationship: {e}")
            return False

    async def get_related_recommendations(
        self,
        recommendation_id: str,
        relationship_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """Get recommendations related to the given one"""
        query = """
        MATCH (source:Recommendation {id: $id})
        -[r:RELATES_TO]->
        (related:Recommendation)
        WHERE $relationship_type IS NULL OR r.type = $relationship_type
        RETURN related.id as id,
               related.title as title,
               r.type as relationship_type,
               r.weight as weight
        ORDER BY r.weight DESC
        LIMIT $limit
        """
        try:
            async with self.driver.session(database=neo4j_settings.database) as session:
                result = await session.run(
                    query,
                    id=recommendation_id,
                    relationship_type=relationship_type,
                    limit=limit
                )
                return [dict(record) for record in await result.data()]
        except Exception as e:
            print(f"Error getting related recommendations: {e}")
            return []

    async def update_relationship_weight(
        self,
        source_id: str,
        target_id: str,
        weight_change: float
    ) -> bool:
        """Update the weight of a relationship"""
        query = """
        MATCH (source:Recommendation {id: $source_id})
        -[r:RELATES_TO]->
        (target:Recommendation {id: $target_id})
        SET r.weight = r.weight + $weight_change,
            r.updated_at = datetime()
        """
        try:
            async with self.driver.session(database=neo4j_settings.database) as session:
                await session.run(
                    query,
                    source_id=source_id,
                    target_id=target_id,
                    weight_change=weight_change
                )
            return True
        except Exception as e:
            print(f"Error updating relationship weight: {e}")
            return False

    async def get_recommendation_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 3
    ) -> List[Dict]:
        """Find paths between recommendations"""
        query = """
        MATCH path = shortestPath(
            (start:Recommendation {id: $start_id})
            -[*..%d]->
            (end:Recommendation {id: $end_id})
        )
        RETURN [node in nodes(path) | node.id] as node_ids,
               [rel in relationships(path) | {
                   type: rel.type,
                   weight: rel.weight
               }] as relationships
        """ % max_depth
        
        try:
            async with self.driver.session(database=neo4j_settings.database) as session:
                result = await session.run(
                    query,
                    start_id=start_id,
                    end_id=end_id
                )
                return [dict(record) for record in await result.data()]
        except Exception as e:
            print(f"Error finding recommendation path: {e}")
            return []

    async def get_recommendation_cluster(
        self,
        recommendation_id: str,
        min_weight: float = 0.5,
        max_depth: int = 2
    ) -> List[Dict]:
        """Get a cluster of related recommendations"""
        query = """
        MATCH path = (source:Recommendation {id: $id})
        -[r:RELATES_TO*..%d]->
        (related:Recommendation)
        WHERE ALL(rel in r WHERE rel.weight >= $min_weight)
        RETURN related.id as id,
               related.title as title,
               reduce(weight = 1.0, rel in r | weight * rel.weight) as cluster_score
        ORDER BY cluster_score DESC
        """ % max_depth
        
        try:
            async with self.driver.session(database=neo4j_settings.database) as session:
                result = await session.run(
                    query,
                    id=recommendation_id,
                    min_weight=min_weight
                )
                return [dict(record) for record in await result.data()]
        except Exception as e:
            print(f"Error getting recommendation cluster: {e}")
            return []

    async def delete_recommendation(self, recommendation_id: str) -> bool:
        """Delete a recommendation and its relationships"""
        query = """
        MATCH (r:Recommendation {id: $id})
        DETACH DELETE r
        """
        try:
            async with self.driver.session(database=neo4j_settings.database) as session:
                await session.run(query, id=recommendation_id)
            return True
        except Exception as e:
            print(f"Error deleting recommendation: {e}")
            return False 