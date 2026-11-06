import sqlite3

import pandas as pd
import pytest

from src import MovieStorage
from src.database import get_connection
from src.storage import MOVIE_COLUMNS


def test_empty_schema(movie_storage):
    assert list(movie_storage.get().columns) == MOVIE_COLUMNS
    assert movie_storage.get().empty
    assert movie_storage.count_movies() == 0


def test_persistence_and_sql_null(movie_storage):
    df = pd.DataFrame([['A', 2020, 8.5, None], ['B', None, None, 'Drama']], columns=MOVIE_COLUMNS)
    movie_storage.save(df)
    reopened = MovieStorage(movie_storage.db_path)
    assert reopened.count_movies() == 2
    rows = reopened.select_columns(MOVIE_COLUMNS)
    assert rows[0]['genre'] is None
    assert rows[1]['release_year'] is None
    assert rows[1]['rating'] is None
    assert reopened.query_movies(['title'], 0, 10) == [{'id': 1, 'title': 'A'}]


def test_rollback_restores_deleted_rows(movie_storage):
    original = pd.DataFrame([['A', 2020, 8, 'Drama']], columns=MOVIE_COLUMNS)
    movie_storage.save(original)
    invalid = pd.DataFrame([['B', 2021, 9, 'Comedy'], [['unbound'], 2022, 7, 'Drama']], columns=MOVIE_COLUMNS)
    with pytest.raises(sqlite3.Error):
        movie_storage.save(invalid)
    pd.testing.assert_frame_equal(movie_storage.get(), original, check_dtype=False)


def test_query_order_and_limit(movie_storage):
    movie_storage.save(pd.DataFrame([
        ['A', 2020, 8, 'Drama'], ['B', 2021, 9, 'Drama'], ['C', 2022, 9, 'Comedy'],
    ], columns=MOVIE_COLUMNS))
    assert movie_storage.query_movies(['title'], 8, 2) == [
        {'id': 2, 'title': 'B'}, {'id': 3, 'title': 'C'},
    ]
    assert movie_storage.select_columns(['genre'], 1) == [{'id': 1, 'genre': 'Drama'}]
    movie_storage.save(pd.DataFrame(columns=MOVIE_COLUMNS))
    assert movie_storage.count_movies() == 0


@pytest.mark.parametrize('columns', [[], ['id'], ['bad'], ['title; DROP TABLE movies']])
def test_column_allowlist(movie_storage, columns):
    with pytest.raises(ValueError):
        movie_storage.select_columns(columns)
    with pytest.raises(ValueError):
        movie_storage.query_movies(columns, 0, 5)


def test_database_schema(movie_storage):
    connection = get_connection(movie_storage.db_path)
    try:
        schema = connection.execute('PRAGMA table_info(movies)').fetchall()
        assert [row['name'] for row in schema] == ['id'] + MOVIE_COLUMNS
        assert schema[0]['pk'] == 1
        assert all(row['notnull'] == 0 for row in schema[1:])
    finally:
        connection.close()
