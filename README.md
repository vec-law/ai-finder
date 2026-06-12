# ai-finder

**PL:** Program do przeszukiwania paginowanych stron internetowych za pomocą języka naturalnego. Użytkownik podaje jedynie adres strony i określa dziedzinę wyszukiwania, a program automatycznie indeksuje jej zawartość. Użytkownik opisuje czego szuka w języku naturalnym i otrzymuje odpowiedź na podstawie zapisanych treści.

**EN:** A program for searching paginated websites using natural language. The user provides only the URL and defines the search domain, and the program automatically indexes the content. The user describes what they are looking for in natural language and receives an answer based on the indexed content.

## Zastrzeżenie (Disclaimer)

**PL:** Oprogramowanie służy wyłącznie do celów edukacyjnych i badawczych. Autor nie ponosi odpowiedzialności za sposób wykorzystania narzędzia ani za zgodność jego użycia z regulaminami serwisów internetowych.

**EN:** This software is for educational and research purposes only. The author bears no responsibility for the use of the tool or for compliance with the terms of service of any website.

## Architektura (Architecture)

**PL:** Program składa się z dwóch niezależnych procesów:

**Indexer** (`run_indexer.py`) — działa w tle, odświeża indeks co godzinę:
1. Pobiera linki ze wszystkich podstron paginacji
2. Pobiera i ekstrahuje treść każdego linku (`trafilatura`)
3. Oblicza embedding wektorowy i zapisuje do PostgreSQL (`pgvector`)

**Chat** (`chat.py`) — odpowiada na zapytania:
1. Rozszerza zapytanie o synonimy przez LLM (`EXPANDER_PROMPT`)
2. Oblicza embedding rozszerzonego zapytania
3. Wyszukuje top-N dokumentów przez cosine similarity (`pgvector`)
4. Generuje odpowiedź przez LLM na podstawie pobranych dokumentów

---

**EN:** The program consists of two independent processes:

**Indexer** (`run_indexer.py`) — runs in the background, refreshes the index every hour:
1. Fetches links from all pagination subpages
2. Fetches and extracts content from each link (`trafilatura`)
3. Computes vector embeddings and saves to PostgreSQL (`pgvector`)

**Chat** (`chat.py`) — answers queries:
1. Expands the query with synonyms via LLM (`EXPANDER_PROMPT`)
2. Computes the embedding of the expanded query
3. Retrieves top-N documents by cosine similarity (`pgvector`)
4. Generates a response via LLM based on the retrieved documents

## Filtrowanie linków (Link Filtering)

**PL:** Program nie używa żadnych hardkodowanych selektorów ani słów kluczowych. Struktura strony jest dedukowana statystycznie:

- linki wspólne dla pierwszych kilku podstron (nawigacja, footer) są usuwane przez część wspólną zbiorów
- spośród pozostałych linków wybierany jest dominujący segment URL przez zliczanie wystąpień
- paginacja kończy się automatycznie gdy kolejne strony zaczynają zwracać te same linki

Zmiana indeksowanego serwisu wymaga tylko zmiany `PAGE_URL` i `SYSTEM_PROMPT` w `.env`.

---

**EN:** The program does not use any hardcoded selectors or keywords. The page structure is inferred statistically:

- links common to the first few subpages (navigation, footer) are removed via set intersection
- among the remaining links, the dominant URL segment is selected by counting occurrences
- pagination ends automatically when consecutive pages start returning the same links

Switching to a different website requires only changing `PAGE_URL` and `SYSTEM_PROMPT` in `.env`.

## Rozszerzalność (Extensibility)

**PL:** Fetchery i modele są konfigurowane przez `.env`. Dodanie nowego fetchera (Selenium, API zewnętrzne) wymaga dopisania metody w `ingester.py` — reszta pipeline'u nie wymaga zmian. Analogicznie dla modeli embeddingów i LLM.

---

**EN:** Fetchers and models are configured via `.env`. Adding a new fetcher (Selenium, external API) requires adding a method in `ingester.py` — the rest of the pipeline remains unchanged. The same applies to embedding models and LLMs.

## Modele (Models)

**PL:**

Embeddingi:
- `text-embedding-3-large` (OpenAI API)
- `sdadas/mmlw-retrieval-roberta-large-v2` (lokalny)

LLM:
- `gpt-4o` (OpenAI API)
- `Qwen/Qwen3-4B` (lokalny)

---

**EN:**

Embeddings:
- `text-embedding-3-large` (OpenAI API)
- `sdadas/mmlw-retrieval-roberta-large-v2` (local)

LLM:
- `gpt-4o` (OpenAI API)
- `Qwen/Qwen3-4B` (local)

## Wymagania (Requirements)

**PL:**
- Python 3.12+
- PostgreSQL z rozszerzeniem [`pgvector`](https://github.com/pgvector/pgvector)
- Klucz API OpenAI lub token HuggingFace dla lokalnych modeli (przyspiesza pobieranie)

---

**EN:**
- Python 3.12+
- PostgreSQL with [`pgvector`](https://github.com/pgvector/pgvector) extension
- OpenAI API key or HuggingFace token for local models (speeds up download)

## Instalacja (Installation)

```bash
git clone https://github.com/vec-law/ai-finder.git
cd ai-finder
uv sync
```

## Konfiguracja (Configuration)

**PL:** Uzupełnij `.env`:

**EN:** Fill in `.env`:

| Zmienna / Variable | Opis / Description | Domyślnie / Default |
|---|---|---|
| `DB_NAME` | Nazwa bazy danych / Database name | `ai_finder_db` |
| `DB_USER` | Użytkownik PostgreSQL / PostgreSQL user | `postgres` |
| `DB_PASSWORD` | Hasło / Password | |
| `DB_HOST` | Host | `localhost` |
| `DB_PORT` | Port | `5432` |
| `PAGE_URL` | URL paginacji z `{page_number}` / Pagination URL with `{page_number}` | |
| `PAGE_TYPE` | Typ strony / Page type | `paginated` |
| `PAGE_MAX` | Limit podstron / Subpage limit | `1000` |
| `FETCHER_NAME` | Silnik pobierania / Fetcher engine | `curl` |
| `LINK_EXPIRY_DAYS` | Czas życia linków w dniach / Link expiry in days | `30` |
| `EMBEDDING_MODEL_NAME` | Model embeddingów / Embedding model | `text-embedding-3-large` |
| `EMBEDDING_VECTOR_SIZE` | Rozmiar wektora embeddingów / Embedding vector size | `3072` |
| `LLM_MODEL` | Model LLM | `gpt-4o` |
| `RAG_LIMIT` | Liczba dokumentów przekazywanych do LLM / Number of documents passed to LLM | `20` |
| `SYSTEM_PROMPT` | Instrukcja systemowa LLM / LLM system prompt | |
| `EXPANDER_PROMPT` | Instrukcja expandera zapytań / Query expander prompt | |
| `OPENAI_API_KEY` | Klucz API OpenAI / OpenAI API key | |
| `HF_TOKEN` | Token HuggingFace | |

## Przykłady promptów (Prompt examples)

| SYSTEM_PROMPT | EXPANDER_PROMPT |
|---|---|
| Jesteś wyszukiwarką [...]. Odpowiadaj na podstawie dostarczonych wyników wyszukiwania. Jeśli pytanie nie dotyczy [...], poinformuj użytkownika że możesz pomóc tylko w wyszukiwaniu [...]. | Rozszerz zapytanie użytkownika o synonimy i powiązane terminy dla lepszego wyszukiwania. Zwróć tylko rozszerzone zapytanie bez żadnych komentarzy. |

## Uruchomienie (Usage)

```bash
# Przygotowanie bazy / Database setup
psql -U postgres -c "CREATE DATABASE ai_finder_db;"
psql -U postgres -d ai_finder_db -c "CREATE EXTENSION vector;"
uv run python db/migrate.py

# Indeksowanie / Indexing
uv run python run_indexer.py

# Wyszukiwanie / Search
uv run python chat.py
```

## Struktura projektu (Project Structure)

**PL:**
```
ai-finder/
├── chat.py            # interfejs czatu
├── run_indexer.py     # uruchamia indexer
├── indexer.py         # pipeline indeksowania
├── ingester.py        # pobieranie i ekstrakcja treści
├── embedder.py        # obliczanie embeddingów
├── rag.py             # wyszukiwanie i generowanie odpowiedzi
├── page.py            # klasa indeksowanej strony
├── pyproject.toml
└── db/
    ├── connection.py  # połączenie z bazą danych
    ├── migrate.py     # migracje
    ├── schema.sql     # schemat bazy
    ├── seeds.sql      # dane startowe
    └── queries/       # zapytania do bazy danych
```

**EN:**
```
ai-finder/
├── chat.py            # chat interface
├── run_indexer.py     # runs the indexer
├── indexer.py         # indexing pipeline
├── ingester.py        # content fetching and extraction
├── embedder.py        # embedding computation
├── rag.py             # search and response generation
├── page.py            # indexed page class
├── pyproject.toml
└── db/
    ├── connection.py  # database connection
    ├── migrate.py     # migrations
    ├── schema.sql     # database schema
    ├── seeds.sql      # seed data
    └── queries/       # database queries
```

## Historia zmian (Change Log)

**PL:**
- **v0.1.0**: Wersja bazowa

**EN:**
- **v0.1.0**: Initial version

## Licencja (License)

**PL:** Ten projekt jest udostępniany na licencji **GNU General Public License v3.0**. Szczegóły znajdują się w pliku [LICENSE](LICENSE).

**EN:** This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](LICENSE) file for details.
