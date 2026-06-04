from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

model = SentenceTransformer('BAAI/bge-m3')

def get_embedding(text):
    return model.encode([text])[0]
