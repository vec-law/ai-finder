import os
import time
from dotenv import load_dotenv
from embedder import Embedder
from db.queries.search import search_links as db_search_links
from db.queries.link import get_links as db_get_links
from db.queries.page import get_domain as db_get_domain

load_dotenv()

class RAG:
    def __init__(self, embedder=None):
        self.model_name = os.getenv("LLM_MODEL")
        self.rag_limit = int(os.getenv("RAG_LIMIT", 20))
        self.domain_prompt = "Określ jednym słowem dziedzinę strony internetowej pod podanym adresem URL. Zwróć tylko jedno słowo bez żadnych komentarzy."
        self._domain = None 
        self.expander_prompt = "Rozszerz zapytanie użytkownika o synonimy i powiązane terminy dla lepszego wyszukiwania. Zwróć tylko rozszerzone zapytanie bez żadnych komentarzy."
        self.embedder = embedder or Embedder()
        
        if self.model_name == "gpt-4o":
            from openai import OpenAI
            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self._expand = self._expand_openai
            self._generate = self._generate_openai
            self._get_domain = self._get_domain_openai

        elif self.model_name == "Qwen/Qwen3-4B":
            from transformers import pipeline
            self._pipeline = pipeline(
                "text-generation",
                self.model_name,
                torch_dtype="auto",
                device_map="auto"
            )
            self._expand = self._expand_qwen
            self._generate = self._generate_qwen
            self._get_domain = self._get_domain_qwen

        else:
            raise NotImplementedError(f"Brak implementacji dla modelu: {self.model_name}. Dodaj implementację do rag.py.")
        
    @property
    def domain(self):
        if self._domain is None:
            self._domain = db_get_domain(os.getenv("PAGE_URL"))
        return self._domain

    @property
    def system_prompt(self):
        if not self.domain:
            return "Odpowiadaj na podstawie dostarczonych wyników wyszukiwania."
        return f"Jesteś wyszukiwarką {self.domain}. Odpowiadaj na podstawie dostarczonych wyników wyszukiwania. Jeśli pytanie nie dotyczy {self.domain}, poinformuj użytkownika że możesz pomóc tylko w wyszukiwaniu {self.domain}."

    def run(self, query):
        expanded_query = self._expand(query)
        embedding = self.embedder.get_embedding(expanded_query, type="query")
        link_ids = db_search_links(embedding, limit=self.rag_limit)
        results = db_get_links(link_ids)
        return self._generate(query, results)

    def _expand_openai(self, query):
        from openai import RateLimitError, APIError
        while True:
            try:
                response = self._client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.expander_prompt},
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
                    model=self.model_name,
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
            {"role": "system", "content": self.expander_prompt},
            {"role": "user", "content": query}
        ]
        result = self._pipeline(messages, max_new_tokens=256)[0]["generated_text"]
        return result[-1]["content"]

    def _generate_qwen(self, query, results):
        context = "\n---\n".join([
            f"{r['title']}\n{r['url']}\n{r['content'][len(r['content'])//5:4*len(r['content'])//5]}"
            for r in results
        ])
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"{query}\n\n{context}"}
        ]
        result = self._pipeline(messages, max_new_tokens=1024)[0]["generated_text"]
        return result[-1]["content"]

    def get_domain(self, url):
        return self._get_domain(url)

    def _get_domain_openai(self, url):
        from openai import RateLimitError, APIError
        while True:
            try:
                response = self._client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.domain_prompt},
                        {"role": "user", "content": url}
                    ]
                )
                return response.choices[0].message.content.strip().lower()
            except RateLimitError:
                print("Rate limit w domain, czekam 60s...")
                time.sleep(60)
            except APIError as e:
                print(f"Błąd API w domain: {e}")
                return None

    def _get_domain_qwen(self, url):
        messages = [
            {"role": "system", "content": self.domain_prompt},
            {"role": "user", "content": url}
        ]
        result = self._pipeline(messages, max_new_tokens=10)[0]["generated_text"]
        return result[-1]["content"].strip().lower()