import logging
import re

import main


def test_request_ids_and_log_levels(client, caplog):
    with caplog.at_level(logging.INFO, logger="src.middleware"):
        responses = [
            client.get("/health"),
            client.post("/upload", files={"file": ("bad.txt", b"data")}),
            client.get("/datasets/999"),
            client.get("/movies?limit=0"),
        ]
    assert [response.status_code for response in responses] == [200, 400, 404, 422]
    ids = [response.headers["X-Request-ID"] for response in responses]
    assert len(set(ids)) == 4
    assert all(re.fullmatch(r"[0-9a-f]{8}", request_id) for request_id in ids)
    records = [record for record in caplog.records if record.name == "src.middleware"]
    assert [record.levelno for record in records] == [
        logging.INFO, logging.WARNING, logging.WARNING, logging.WARNING,
    ]
    for response, request_id, record in zip(responses, ids, records):
        message = record.getMessage()
        assert f"request_id={request_id}" in message
        assert response.request.method in message
        assert response.request.url.path in message
        assert f"status={response.status_code}" in message
        assert re.search(r"duration=\d+\.\d+ms", message)


def test_unexpected_error_returns_generic_500_and_logs_traceback(
    client, uploaded_movies, processing_body, monkeypatch, caplog
):
    before = client.get("/movies").json()

    def broken_processing(*args):
        raise RuntimeError("private internal details")

    monkeypatch.setattr(main, "process_data", broken_processing)
    caplog.clear()
    with caplog.at_level(logging.ERROR, logger="src.middleware"):
        response = client.post(
            "/movies/process", json=processing_body
        )
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    request_id = response.headers["X-Request-ID"]
    assert re.fullmatch(r"[0-9a-f]{8}", request_id)
    records = [record for record in caplog.records if record.name == "src.middleware"]
    assert all(record.levelno == logging.ERROR for record in records)
    assert any(record.exc_info is not None for record in records)
    assert any(f"request_id={request_id}" in record.getMessage() for record in records)
    assert any("status=500" in record.getMessage() for record in records)
    assert "private internal details" not in response.text
    assert client.get("/movies").json() == before
    assert client.get("/health").status_code == 200
