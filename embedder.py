import os
import time
from dotenv import load_dotenv

load_dotenv()

class Embedder:
    def __init__(self):
        self.model_name = os.getenv("EMBEDDING_MODEL_NAME")
        self.vector_size = int(os.getenv("EMBEDDING_VECTOR_SIZE"))

        if self.model_name == "text-embedding-3-large":
            from openai import OpenAI
            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self._get_embedding = self._get_embedding_openai

        elif self.model_name == "sdadas/mmlw-retrieval-roberta-large-v2":
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            self._get_embedding = self._get_embedding_roberta
            
        else:
            raise NotImplementedError(f"Brak implementacji dla modelu: {self.model_name}. Dodaj implementację do embedder.py.")

    def get_embedding(self, text, type=None):
        return self._get_embedding(text, type)

    def _get_embedding_openai(self, text, type=None):
        from openai import RateLimitError, APIError
        while True:
            try:
                response = self._client.embeddings.create(
                    input=text,
                    model=self.model_name
                )
                return response.data[0].embedding
            except RateLimitError:
                print("Rate limit, czekam 60s...")
                time.sleep(60)
            except APIError as e:
                print(f"Błąd API: {e}")
                return None

    def _get_embedding_roberta(self, text, type=None):
        try:
            if type == "query":
                text = f"[query]: {text}"
            return self._model.encode(text).tolist()
        except Exception as e:
            print(f"Błąd embeddera: {e}")
            return None
