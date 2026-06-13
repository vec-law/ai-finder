# rag-searcher

**PL:** System RAG (Retrieval-Augmented Generation) do przeszukiwania automatycznie indeksowanych, paginowanych stron internetowych za pomocą zapytań w języku naturalnym, oparty na embeddingach wektorowych oraz modelach LLM.

**EN:** A RAG (Retrieval-Augmented Generation) system for searching automatically indexed, paginated websites using natural language queries, based on vector embeddings and LLM models.

## Architektura (Architecture)

**PL:** Program składa się z dwóch niezależnych procesów:

**Indexer** (`run_indexer.py`) — działa w tle, odświeża indeks co godzinę:
1. Określa dziedzinę strony przez LLM
2. Pobiera linki ze wszystkich podstron paginacji
3. Pobiera i ekstrahuje treść każdego linku (`trafilatura`)
4. Oblicza embedding wektorowy i zapisuje do PostgreSQL (`pgvector`)

**Chat** (`chat.py`) — odpowiada na zapytania:
1. Rozszerza zapytanie o synonimy przez LLM
2. Oblicza embedding rozszerzonego zapytania
3. Wyszukuje top-N dokumentów przez cosine similarity (`pgvector`)
4. Generuje odpowiedź przez LLM na podstawie pobranych dokumentów

---

**EN:** The program consists of two independent processes:

**Indexer** (`run_indexer.py`) — runs in the background, refreshes the index every hour:
1. Determines the domain of the page via LLM
2. Fetches links from all pagination subpages
3. Fetches and extracts content from each link (`trafilatura`)
4. Computes vector embeddings and saves to PostgreSQL (`pgvector`)

**Chat** (`chat.py`) — answers queries:
1. Expands the query with synonyms via LLM
2. Computes the embedding of the expanded query
3. Retrieves top-N documents by cosine similarity (`pgvector`)
4. Generates a response via LLM based on the retrieved documents

## Filtrowanie linków (Link Filtering)

**PL:** Program nie używa żadnych hardkodowanych selektorów ani słów kluczowych. Struktura strony jest dedukowana statystycznie:

- linki wspólne dla pierwszych kilku podstron (nawigacja, footer) są usuwane przez część wspólną zbiorów
- spośród pozostałych linków wybierany jest dominujący segment URL przez zliczanie wystąpień
- paginacja kończy się automatycznie gdy kolejne strony zaczynają zwracać te same linki

Zmiana indeksowanego serwisu wymaga tylko zmiany `PAGE_URL` w `.env`.

---

**EN:** The program does not use any hardcoded selectors or keywords. The page structure is inferred statistically:

- links common to the first few subpages (navigation, footer) are removed via set intersection
- among the remaining links, the dominant URL segment is selected by counting occurrences
- pagination ends automatically when consecutive pages start returning the same links

Switching to a different website requires only changing `PAGE_URL` in `.env`.

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
git clone https://github.com/vec-law/rag-searcher.git
cd rag-searcher
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
| `OPENAI_API_KEY` | Klucz API OpenAI / OpenAI API key | |
| `HF_TOKEN` | Token HuggingFace | |



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
rag-searcher/
├── chat.py            # interfejs czatu
├── run_indexer.py     # uruchomienie indexera
├── indexer.py         # pipeline indeksowania
├── ingester.py        # pobieranie i ekstrakcja treści
├── embedder.py        # klasa embeddera
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
rag-searcher/
├── chat.py            # chat interface
├── run_indexer.py     # indexer entry point
├── indexer.py         # indexing pipeline
├── ingester.py        # content fetching and extraction
├── embedder.py        # embedder class
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

## Zastrzeżenie (Disclaimer)

**PL**: Oprogramowanie służy wyłącznie do celów edukacyjnych i badawczych. Autor nie ponosi odpowiedzialności za sposób wykorzystania narzędzia ani za zgodność jego użycia z regulaminami serwisów internetowych.

**EN**: This software is for educational and research purposes only. The author bears no responsibility for the use of the tool or for compliance with the terms of service of any website.

## Licencja (License)

**PL:** Ten projekt jest udostępniany na licencji **GNU General Public License v3.0**. Szczegóły znajdują się w pliku [LICENSE](LICENSE).

**EN:** This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](LICENSE) file for details.
