import os
from transformers import AutoTokenizer, AutoModelForCausalLM
from dotenv import load_dotenv

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-1.7B")
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-1.7B")

load_dotenv()

def test_llm():
    while True:
        query = input("Zapytanie: ")
        if not query:
            continue
        if query == "exit":
            break
        
        messages = [
            {"role": "system", "content": os.getenv("SYSTEM_PROMPT", "")},
            {"role": "user", "content": query}
        ]
        
        inputs = tokenizer.apply_chat_template(
            messages, 
            return_tensors="pt", 
            add_generation_prompt=True,
            return_dict=True,
            enable_thinking=False
        )
        
        outputs = model.generate(**inputs, max_new_tokens=50)
        response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
        print(response)
