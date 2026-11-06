import pytest

from src.storage import MOVIE_COLUMNS


def test_empty_collection(client):
    assert client.get('/movies').json() == {'data': [], 'total_rows': 0}
    assert client.get('/movies/search').json() == []
    assert client.post('/movies/process', json={}).status_code == 400


def test_upload_and_retrieve(client, uploaded_movies):
    assert uploaded_movies == {'filename': 'sample_movies.csv', 'rows': 20,
                               'columns': 4, 'column_names': MOVIE_COLUMNS}
    assert client.get('/movies?limit=2').json() == {
        'data': [
            {'id': 1, 'title': 'Movie A', 'release_year': 2020, 'rating': 8.0, 'genre': 'Drama'},
            {'id': 2, 'title': 'Movie B', 'release_year': 2021, 'rating': 8.5, 'genre': 'Comedy'},
        ], 'total_rows': 20,
    }


def test_search_examples(client, uploaded_movies):
    assert client.get('/movies/search?min_rating=8.5&limit=2').json() == [
        {'id': 4, 'title': 'Movie C'}, {'id': 2, 'title': 'Movie B'},
    ]
    assert client.get('/movies/search?columns=title&columns=rating&min_rating=8.5&limit=2').json() == [
        {'id': 4, 'title': 'Movie C', 'rating': 9.0},
        {'id': 2, 'title': 'Movie B', 'rating': 8.5},
    ]
    assert client.get('/movies/search?min_rating=10').json() == []


def test_reupload_replaces(client, sample_csv_bytes, uploaded_movies):
    assert client.post('/upload', files={'file': ('again.csv', sample_csv_bytes)}).status_code == 200
    data = client.get('/movies').json()
    assert data['total_rows'] == 20
    assert data['data'][0]['id'] == 1


@pytest.mark.parametrize('filename,content', [
    ('bad.txt', b'hello'), ('empty.csv', b''), ('bad.csv', b'\xff'),
    ('header.csv', b'title,release_year,rating,genre\n'),
    ('missing.csv', b'title,rating\nMovie,8\n'),
    ('extra.csv', b'title,release_year,rating,genre,extra\nMovie,2020,8,Drama,x\n'),
    ('duplicate.csv', b'title,title,rating,genre\nMovie,2020,8,Drama\n'),
    ('broken.csv', b'title,release_year,rating,genre\n"unfinished'),
])
def test_bad_upload_preserves_collection(client, uploaded_movies, filename, content):
    before = client.get('/movies').json()
    assert client.post('/upload', files={'file': (filename, content)}).status_code == 400
    assert client.get('/movies').json() == before
    assert client.get('/health').status_code == 200


def test_reordered_columns_and_null(client):
    content = b'genre,rating,title,release_year\nDrama,,Movie A,2020\n'
    response = client.post('/upload', files={'file': ('MOVIES.CSV', content)})
    assert response.json()['column_names'] == MOVIE_COLUMNS
    assert client.get('/movies').json()['data'][0]['rating'] is None


@pytest.mark.parametrize('url', [
    '/movies?limit=0', '/movies?limit=abc', '/movies/search?limit=0',
    '/movies/search?min_rating=-1', '/movies/search?min_rating=11',
    '/movies/search?min_rating=abc',
])
def test_query_constraints(client, url):
    assert client.get(url).status_code == 422


@pytest.mark.parametrize('column', ['id', 'unknown', 'title; DROP TABLE movies; --', ''])
def test_invalid_search_columns(client, uploaded_movies, column):
    assert client.get('/movies/search', params={'columns': column}).status_code == 400
    assert client.get('/movies').json()['total_rows'] == 20
