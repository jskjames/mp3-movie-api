# MP3 Movie API

DS3500 MP3 Part 1. This project extends the MP2 REST API with a SQLite movie collection. The existing MP1 validation and cleaning functions are copied in `data_pipeline/`.

## Setup

Use Python 3.12 or newer. Run these commands from the project root.

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m uvicorn main:app --reload
```

### macOS / Linux

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs for Swagger UI. The database is created automatically at `data/movies.db`, relative to the project root. The database, virtual environment, and caches are ignored by Git.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Application status and version |
| POST | `/upload` | Validate a movie CSV and replace the collection |
| GET | `/movies` | Return up to `limit` rows, ordered by id, plus `total_rows` |
| GET | `/movies/search` | Select movie fields and filter by minimum rating |
| POST | `/movies/process` | Validate and clean the stored movies, then save the result |

Uploads must contain at least one row and exactly `title`, `release_year`, `rating`, and `genre`. Column order may vary; storage uses the order above. Missing values become SQL NULL. Uploads retain duplicates until processing is requested.

A successful upload replaces the collection in one transaction. A SQLite error rolls back the entire replacement. `id` is an `INTEGER PRIMARY KEY`, generated on insertion. Replacing or processing the collection regenerates ids, so they are not permanent movie identifiers.

Column names are checked against an allowlist before they are used in SQL. Filter values and limits use SQL placeholders. Retrieval, filtering, sorting, and counting are performed in SQL.

## Part 1 demonstration

1. In `/docs`, execute `POST /upload` with `fixtures/sample_movies.csv`. The response should report 20 rows and 4 columns.
2. Execute `GET /movies` with `limit=2`. The first two movies should have ids 1 and 2; `total_rows` should be 20.
3. Execute `GET /movies/search` with `min_rating=8.5`, `limit=2`, and the default `columns` value of `title`. Expect Movie C (id 4), then Movie B (id 2).
4. Add `title` and `rating` as separate `columns` items and execute again. Expect ratings 9.0 and 8.5.
5. Stop Uvicorn with Ctrl+C, start it again using the same command, and call `GET /movies`. The 20 rows remain without uploading again.
6. Upload the sample again. The collection still contains 20 rows, rather than 40.
7. Upload a `.txt` file. The API returns 400, and `/health` still returns 200.

## Processing

Use the JSON in `fixtures/process_config.json` as the request body for `POST /movies/process`. The sample contains two duplicate rows, so default duplicate removal produces 18 rows. Enabling rating outlier removal with IQR and threshold 1.5 produces 16 rows.

The request accepts the same nested configuration as MP2: validation columns, duplicate removal, missing values (`rows` or `columns`), and outlier filtering (`iqr` or `zscore`). Processing an empty collection returns 400. Invalid processing settings return 400 without changing the stored collection. Invalid request types and out-of-range query values return 422.

The movie table always has four data columns. If the reused missing-value cleaning step drops a DataFrame column, the cleaning report describes that step and the corresponding SQL column is saved as NULL for every remaining row.

## Tests

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

On macOS/Linux, use `venv/bin/python -m pytest -q`.

Tests use temporary SQLite databases and cover the sample responses, upload replacement, persistence across storage instances, SQL NULL handling, rollback after a failed insert, search order and field validation, processing, and request logging/error handling.

## Structure

```text
mp3-movie-api/
  main.py
  requirements.txt
  src/
    __init__.py
    database.py
    storage.py
    models.py
    middleware.py
    utils.py
  data_pipeline/
    ... MP1 processing modules
  fixtures/
    sample_movies.csv
    process_config.json
  tests/
    conftest.py
    test_api.py
    test_storage.py
    test_processing.py
    test_middleware.py
  data/
    movies.db  (generated, ignored by Git)
```

Part 2 caching is not included in this Part 1 implementation.
