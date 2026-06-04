from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

model = SentenceTransformer('intfloat/multilingual-e5-large')

def get_embedding(text):
    return model.encode([text])[0]
