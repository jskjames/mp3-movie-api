import pytest

from src import ProcessConfig


@pytest.mark.parametrize('failure', ['required', 'numeric', 'axis', 'method'])
def test_processing_error_preserves_data(client, uploaded_movies, processing_body, failure):
    before = client.get('/movies').json()
    if failure == 'required':
        processing_body['validation']['required_columns'].append('missing')
    elif failure == 'numeric':
        processing_body['validation']['numeric_columns'].append('missing')
    elif failure == 'axis':
        processing_body['processing']['missing']['axis'] = 'invalid'
    else:
        processing_body['processing']['outliers'].update(enabled=True, method='invalid')
    assert client.post('/movies/process', json=processing_body).status_code == 400
    assert client.get('/movies').json() == before


def test_process_and_repeat(client, uploaded_movies, processing_body):
    response = client.post('/movies/process', json=processing_body)
    assert response.status_code == 200
    assert response.json() == {
        'validation_rows_removed': 0,
        'cleaning_report': {'rows_before': 20, 'rows_after': 18, 'rows_removed': 2,
                            'columns_before': 4, 'columns_after': 4, 'columns_removed': 0},
    }
    assert client.get('/movies').json()['total_rows'] == 18
    assert client.post('/movies/process', json=processing_body).json()['cleaning_report']['rows_removed'] == 0


@pytest.mark.parametrize('body', [None, [], {'validation': {'numeric_columns': 12}}])
def test_invalid_body(client, uploaded_movies, body):
    before = client.get('/movies').json()
    assert client.post('/movies/process', json=body).status_code == 422
    assert client.get('/movies').json() == before


def test_numeric_validation_and_nulls(client, processing_body):
    csv = b'title,release_year,rating,genre\nA,2020,8,Drama\nB,2021,unknown,Comedy\nC,2022,,Action\n'
    client.post('/upload', files={'file': ('movies.csv', csv)})
    processing_body['processing']['missing']['enabled'] = False
    response = client.post('/movies/process', json=processing_body)
    assert response.json()['validation_rows_removed'] == 1
    rows = client.get('/movies').json()['data']
    assert len(rows) == 2
    assert rows[1]['rating'] is None


def test_drop_missing_column_keeps_sql_schema(client, processing_body):
    csv = b'title,release_year,rating,genre\nA,2020,8,Drama\nB,2021,,Comedy\n'
    client.post('/upload', files={'file': ('movies.csv', csv)})
    processing_body['processing']['missing']['axis'] = 'columns'
    response = client.post('/movies/process', json=processing_body)
    assert response.status_code == 200
    assert response.json()['cleaning_report']['columns_removed'] == 1
    assert all(row['rating'] is None for row in client.get('/movies').json()['data'])


@pytest.mark.parametrize('method', ['iqr', 'zscore'])
def test_outlier_processing(client, uploaded_movies, processing_body, method):
    processing_body['processing']['outliers'].update(enabled=True, method=method, threshold=1.5)
    response = client.post('/movies/process', json=processing_body)
    assert response.status_code == 200
    assert response.json()['cleaning_report']['rows_after'] == 16


def test_model_defaults_are_independent():
    first, second = ProcessConfig(), ProcessConfig()
    first.validation.numeric_columns.append('rating')
    assert second.validation.numeric_columns == []
