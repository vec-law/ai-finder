import os
import hashlib
from db.queries.config import get_saved_config, del_old_configs, save_config
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
        raise ValueError("Brak konfiguracji")

    if config_hash != get_saved_config():
        del_old_configs()
        save_config(config_hash)
    
    return config_hash
