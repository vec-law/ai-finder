import os
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

model = SentenceTransformer(
    os.getenv("EMBEDDING_MODEL"),
    device="cpu",
    model_kwargs={"attn_implementation": "eager"}
)

def get_embedding(text, is_query=False):
    prefix = os.getenv("EMBEDDING_QUERY_PROMPT" if is_query else "EMBEDDING_DOCUMENT_PROMPT", "")
    return model.encode([prefix + text])[0]
