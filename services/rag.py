import logging
from db.connection import db

logger = logging.getLogger(__name__)

class RAGEngine:
    @staticmethod
    async def find_matching_candidates(jd_embedding, limit=10, threshold=0.7):
        """
        Find candidates whose resume embeddings are similar to the JD embedding.
        pgvector uses <=> for cosine distance, so 1 - <=> is cosine similarity.
        """
        query = """
            SELECT 
                c.id, 
                c.user_id, 
                c.resume_structured, 
                (1 - (embedding <=> $1)) as score
            FROM candidates c
            WHERE (1 - (embedding <=> $1)) >= $2
            ORDER BY score DESC
            LIMIT $3
        """
        return await db.fetch(query, jd_embedding, threshold, limit)

    @staticmethod
    async def find_matching_jds(candidate_embedding, limit=10, threshold=0.7):
        """
        Find job descriptions similar to the candidate's resume embedding.
        """
        query = """
            SELECT 
                jd.id, 
                jd.title, 
                jd.full_jd, 
                (1 - (embedding <=> $1)) as score
            FROM job_descriptions jd
            WHERE (1 - (embedding <=> $1)) >= $2 AND jd.status = 'active'
            ORDER BY score DESC
            LIMIT $3
        """
        return await db.fetch(query, candidate_embedding, threshold, limit)

rag_engine = RAGEngine()
