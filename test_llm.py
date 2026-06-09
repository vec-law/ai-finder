import os
import json
from transformers import AutoTokenizer, AutoModelForCausalLM
from dotenv import load_dotenv

load_dotenv()

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-0.6B")

GENERAL = os.getenv("GENERAL_SYSTEM_PROMPT", "")
STEP_1 = os.getenv("STEP_1_SYSTEM_PROMPT", "")

queries = [q.strip() for q in os.getenv("QUERIES", "").split(",")]

def call_model(system_prompt, user_content):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    inputs = tokenizer.apply_chat_template(
        messages,
        return_tensors="pt",
        add_generation_prompt=True,
        return_dict=True,
        enable_thinking=False
    )
    outputs = model.generate(**inputs, max_new_tokens=100, do_sample=False)
    return tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)

def test_llm():
    for query in queries:
        step1_response = call_model(GENERAL + STEP_1, query)

        try:
            keywords = json.loads(step1_response)
        except json.JSONDecodeError:
            print(f"Zapytanie: {query}")
            print(f"Step 1 błąd parsowania: {step1_response}\n")
            continue

        print(f"Zapytanie: {query}")
        print(f"Słowa kluczowe: {keywords}\n")
