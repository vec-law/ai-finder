from db.queries.embedding import get_embedding_content, update_embedding
from embeddings import get_embedding

class ContentEmbedder():
    def __init__(self, embedding_id):
        self.embedding_id = embedding_id

    def embed(self):
        update_embedding(self.embedding_id, None, "running")

        content = get_embedding_content(self.embedding_id)

        if not content:
            update_embedding(self.embedding_id, None, "failed")
            return None

        embedding = get_embedding(content)
        embedding_str = "[" + ",".join(map(str, embedding.tolist())) + "]"

        if not update_embedding(self.embedding_id, embedding_str, "completed"):
            return None

        return embedding_str
