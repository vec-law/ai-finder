import os
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

model = SentenceTransformer(
    os.getenv("EMBEDDING_MODEL"),
    trust_remote_code=os.getenv("EMBEDDING_TRUST_REMOTE_CODE", "false").lower() == "true",
    device="cpu"
)

def get_embedding(text, is_query=False):
    prompt = os.getenv("EMBEDDING_QUERY_PROMPT" if is_query else "EMBEDDING_DOCUMENT_PROMPT", "")
    if prompt and hasattr(model, 'prompts') and prompt in model.prompts:
        return model.encode([text], prompt_name=prompt)[0]
    return model.encode([text])[0]
