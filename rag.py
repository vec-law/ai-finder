import os
import time
from dotenv import load_dotenv
from embedder import Embedder
from db.queries.search import search_links as db_search_links
from db.queries.link import get_links as db_get_links

load_dotenv()

class RAG:
    def __init__(self):
        self._model_name = os.getenv("LLM_MODEL")
        self._rag_limit = int(os.getenv("RAG_LIMIT", 20))
        self._domain_prompt = "Określ jednym słowem dziedzinę strony internetowej pod podanym adresem URL. Zwróć tylko jedno słowo bez żadnych komentarzy."
        self._expander_prompt = "Rozszerz zapytanie użytkownika o synonimy i powiązane terminy dla lepszego wyszukiwania. Zwróć tylko rozszerzone zapytanie bez żadnych komentarzy."
        self._url = os.getenv("PAGE_URL")
        self._embedder = Embedder()

        if self._model_name == "gpt-4o":
            from openai import OpenAI
            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self._expand = self._expand_openai
            self._generate = self._generate_openai
            self._domain = self._get_domain_openai()

        elif self._model_name == "Qwen/Qwen3-4B":
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
            self._model = AutoModelForCausalLM.from_pretrained(
                self._model_name,
                torch_dtype="auto",
                device_map="auto"
            )
            self._expand = self._expand_qwen
            self._generate = self._generate_qwen
            self._domain = self._get_domain_qwen()

        else:
            raise NotImplementedError(f"Brak implementacji dla modelu: {self._model_name}. Dodaj implementację do rag.py.")
        
        if not self._domain:
            self.system_prompt = "Odpowiadaj na podstawie dostarczonych wyników wyszukiwania."
        else:
            self.system_prompt = f"Jesteś wyszukiwarką w dziedzinie ({self._domain}). Odpowiadaj w języku użytkownika na podstawie dostarczonych wyników wyszukiwania. Zawsze podawaj linki do źródeł. Jeśli pytanie nie dotyczy dziedziny ({self._domain}), poinformuj użytkownika że możesz pomóc tylko w tej dziedzinie."

    def run(self, query):
        expanded_query = self._expand(query)
        embedding = self._embedder.get_embedding(expanded_query, type="query")
        link_ids = db_search_links(embedding, limit=self._rag_limit)
        results = db_get_links(link_ids)
        return self._generate(query, results)

    def _expand_openai(self, query):
        from openai import RateLimitError, APIError
        while True:
            try:
                response = self._client.chat.completions.create(
                    model=self._model_name,
                    messages=[
                        {"role": "system", "content": self._expander_prompt},
                        {"role": "user", "content": query}
                    ]
                )
                return response.choices[0].message.content
            except RateLimitError:
                print("Rate limit w expander, czekam 60s...")
                time.sleep(60)
            except APIError as e:
                print(f"Błąd API w expander: {e}")
                return query

    def _generate_openai(self, query, results):
        from openai import RateLimitError, APIError
        context = "\n---\n".join([
            f"{r['title']}\n{r['url']}\n{r['content'][len(r['content'])//5:4*len(r['content'])//5]}"
            for r in results
        ])
        while True:
            try:
                response = self._client.chat.completions.create(
                    model=self._model_name,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": f"{query}\n\n{context}"}
                    ]
                )
                return response.choices[0].message.content
            except RateLimitError:
                print("Rate limit w generator, czekam 60s...")
                time.sleep(60)
            except APIError as e:
                print(f"Błąd API w generator: {e}")
                return None

    def _expand_qwen(self, query):
        messages = [
            {"role": "system", "content": self._expander_prompt},
            {"role": "user", "content": query}
        ]
        return self._qwen_generate(messages, max_new_tokens=256)

    def _generate_qwen(self, query, results):
        context = "\n---\n".join([
            f"{r['title']}\n{r['url']}\n{r['content'][len(r['content'])//5:4*len(r['content'])//5]}"
            for r in results
        ])
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"{query}\n\n{context}"}
        ]
        return self._qwen_generate(messages, max_new_tokens=1024)

    def _qwen_generate(self, messages, max_new_tokens=512, enable_thinking=False):
        text = self._tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=enable_thinking
        )
        model_inputs = self._tokenizer([text], return_tensors="pt").to(self._model.device)
        generated_ids = self._model.generate(
            **model_inputs,
            max_new_tokens=max_new_tokens
        )
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
        try:
            index = len(output_ids) - output_ids[::-1].index(151668)
        except ValueError:
            index = 0
        return self._tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip()

    def _get_domain_openai(self):
        from openai import RateLimitError, APIError
        while True:
            try:
                response = self._client.chat.completions.create(
                    model=self._model_name,
                    messages=[
                        {"role": "system", "content": self._domain_prompt},
                        {"role": "user", "content": self._url}
                    ]
                )
                return response.choices[0].message.content.strip().lower()
            except RateLimitError:
                print("Rate limit w domain, czekam 60s...")
                time.sleep(60)
            except APIError as e:
                print(f"Błąd API w domain: {e}")
                return None

    def _get_domain_qwen(self):
        messages = [
            {"role": "system", "content": self._domain_prompt},
            {"role": "user", "content": self._url}
        ]
        return self._qwen_generate(messages, max_new_tokens=64)