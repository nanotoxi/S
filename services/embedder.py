import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbedderService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        # all-MiniLM-L6-v2 produces 384-dimensional embeddings
        self.model = SentenceTransformer(model_name)
        logger.info(f"Loaded embedding model: {model_name}")

    def get_embedding(self, text: str):
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

embedder = EmbedderService()
