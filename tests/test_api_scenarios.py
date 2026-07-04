import pytest
from httpx import Client
import re

BASE_URL = "http://localhost:8000"

@pytest.fixture
def client():
    with Client(base_url=BASE_URL, timeout=10.0) as c:
        yield c

# ДОСТУПНОСТь
def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_metrics_endpoint(client):
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    assert "f1_macro" in response.json()

# ЭВРИСТИКИ
@pytest.mark.parametrize("input_text, expected_pattern", [
    ("Описание: Начат процесс закрытия", "APP_ZOD"),
    ("Описание: Процедура выполняется успешно", "APP_ZOD"),
    ("Описание: Остановлен поток обработки данных", "APP_ZOD"),
    ("Описание: Отправить уведомление по почте", "EMAIL"),
    ("Email alert: system failure", "EMAIL"),
    ("Тестовое сообщение 123", "TEST"),
    ("т е с т системы", "TEST")
])

def test_heuristics(client, input_text, expected_pattern):
    payload = {"id": "test-h", "text": input_text}
    response = client.post("/api/v1/process", json=payload)
    data = response.json()
    assert data["pattern_name"] == expected_pattern
    assert data["confidence"] == 1.0
    
def test_numeric_description_rule(client):
    payload = {
        "id": "test-num",
        "text": "Описание: 404092"
    }
    response = client.post("/api/v1/process", json=payload)
    data = response.json()
    assert data["pattern_name"] == "APP_INTERNAL_ERROR_CODES"

# Confidence Threshold
def test_low_confidence_fallback(client):
    """Проверка, что при низкой уверенности модель честно говорит OTHER"""
    payload = {
        "id": "test-low-conf",
        "text": "Какое-то странное сообщение, которое нейронка точно не видела никогда"
    }
    response = client.post("/api/v1/process", json=payload)
    data = response.json()
    if data["confidence"] < 0.8:
        assert data["pattern_name"] is None
        assert data["pattern_found"] is False
        assert data["category"] == "Прочее"

# Валидация
def test_invalid_json(client):
    response = client.post("/api/v1/process", content="not a json")
    assert response.status_code == 422 # Unprocessable Entity

def test_missing_required_field(client):
    payload = {"text": "miss id field"}
    response = client.post("/api/v1/process", json=payload)
    assert response.status_code == 422
    assert "id" in response.text

def test_too_long_text(client):
    """Проверка ограничения длины Pydantic (max_length=2048)"""
    long_text = "a" * 3000
    payload = {"id": "1", "text": long_text}
    response = client.post("/api/v1/process", json=payload)
    assert response.status_code == 422

# Спецсимволы и инъекции
@pytest.mark.parametrize("tricky_text", [
    "DROP TABLE incident_logs;--",
    "<script>alert('xss')</script>",
    "🤔 🤔 🤔",
    "!!! %%% $$$ ^^^",
    ""
])
def test_robustness(client, tricky_text):
    payload = {"id": "robust", "text": tricky_text}
    response = client.post("/api/v1/process", json=payload)
    assert response.status_code in [200, 422]
    if response.status_code == 200:
        assert "pattern_found" in response.json()