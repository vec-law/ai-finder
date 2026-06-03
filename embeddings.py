from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

model = SentenceTransformer('LaBSE')

def get_embedding(text):
    return model.encode(text).tolist()
