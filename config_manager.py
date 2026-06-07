import os
import hashlib
from db.queries.config import add_config, get_config_id, get_embedding_config, set_embedding_config
from dotenv import load_dotenv

load_dotenv()

def get_actual_config():
    configs = []
    for key, value in os.environ.items():
        if (key.startswith("HTML_SEARCH_URL") or key.startswith("API_SEARCH_URL")) and value:
            configs.append(value)

    if not configs:
        return None
        
    config = "".join(sorted(configs))

    return hashlib.sha256(config.encode()).hexdigest()
    
def set_config():
    if not (config_hash := get_actual_config()):
        raise ValueError("Błąd konfiguracji")

    result = get_actual_embedding_config()
    if not result:
        raise ValueError("Błąd konfiguracji")

    embedding_config_hash, vector_size = result
    
    if not (config_id := get_config_id(config_hash)):
        return add_config(config_hash, embedding_config_hash)
    
    if embedding_config_hash != get_embedding_config(config_id):
        set_embedding_config(config_id, embedding_config_hash, vector_size)
    
    return config_id

def get_actual_embedding_config():
    model = os.getenv("EMBEDDING_MODEL", "")
    vector_size = os.getenv("EMBEDDING_VECTOR_SIZE", "")
    
    if not model or not vector_size:
        return None
    
    config = f"{model}{vector_size}"
    return hashlib.sha256(config.encode()).hexdigest(), vector_size
