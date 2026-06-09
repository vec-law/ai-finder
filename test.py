import os
import json
from transformers import AutoTokenizer, AutoModelForCausalLM
from embeddings import get_embedding
from db.queries.search import search_links
from db.queries.link import get_links
from dotenv import load_dotenv

load_dotenv()

QUERY = os.getenv("QUERY", "")

# === OPTYMALIZACJA FRAZY ===

tokenizer_4b = AutoTokenizer.from_pretrained("Qwen/Qwen3-4B")
llm_4b = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-4B")

general_prompt = os.getenv("GENERAL_SYSTEM_PROMPT", "")
search_prompt = os.getenv("SEARCH_SYSTEM_PROMPT", "")
filter_prompt = os.getenv("FILTER_SYSTEM_PROMPT", "")

messages = [
    {"role": "system", "content": general_prompt + search_prompt},
    {"role": "user", "content": QUERY}
]

inputs = tokenizer_4b.apply_chat_template(
    messages,
    return_tensors="pt",
    add_generation_prompt=True,
    return_dict=True,
    enable_thinking=False
)

outputs = llm_4b.generate(**inputs, max_new_tokens=50, do_sample=False)
search_phrase = tokenizer_4b.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
print(f"Fraza wyszukiwania: {search_phrase}")

# === EMBEDDING SEARCH TOP 300 ===

query_embedding = get_embedding(search_phrase, is_query=True)
link_ids = search_links(query_embedding)
links = get_links(link_ids[:300])

# === FILTROWANIE PRZEZ QWEN - PO 1 WYNIKU ===

print("\nSprawdzanie wyników:")
selected_links = []

for i, link in enumerate(links, 1):
    print(f"Sprawdzam {i}/300: {link['title']}...", end=" ", flush=True)

    messages = [
        {"role": "system", "content": general_prompt + filter_prompt},
        {"role": "user", "content": f"Zapytanie użytkownika: {QUERY}\n\nWynik: {link['title']}"}
    ]

    inputs = tokenizer_4b.apply_chat_template(
        messages,
        return_tensors="pt",
        add_generation_prompt=True,
        return_dict=True,
        enable_thinking=False
    )

    outputs = llm_4b.generate(**inputs, max_new_tokens=5, do_sample=False)
    response = tokenizer_4b.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True).strip().lower()

    if "tak" in response or "yes" in response:
        print("✓")
        selected_links.append(link)
    else:
        print("✗")

print(f"\nWybrane: {len(selected_links)}")
for link in selected_links:
    print(f"  {link['title']}")
