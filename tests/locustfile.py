from locust import HttpUser, task, between
import random

class IncidentClassifierUser(HttpUser):
    # один запрос в 1-3 секунды от пользователя
    wait_time = between(1, 3)

    # Список данных, покрывающий все типы логики (Regex + ML + Новые классы)
    SAMPLE_DATA = [
        # Инфраструктурные (Нейросеть)
        {"text": "Monitoring: High CPU Load. На хосте srv-app-01 загрузка 98%"},
        {"text": "Авария: EM-99999. Сервис postgresql перешел в состояние failed на db-node"},
        {"text": "Критическая проблема: Свободное место на диске /backup < 5%"},
        {"text": "ORA-12514: TNS listener could not resolve service name"},
        {"text": "Connection refused to database on port 5432 на узле etl-01"},
        {"text": "Потеря heartbeat от гипервизора esxi-prod-04. Виртуальные машины падают"},
        {"text": "Ошибка TLS handshake на шлюзе внешних запросов port 443"},
        {"text": "Отклонение метрики RTT > 200ms на магистральном канале связи"},
        {"text": "Заполнение /pg_walarchive достигло лимита, репликация стоп"},
        {"text": "Массовое падение подов Kubernetes в namespace prod-bank"},
        
        # Прикладные (Нейросеть)
        {"text": "ИС: Mobile API. Массовые ошибки HTTP 500 при вызове /auth/login"},
        {"text": "Бизнес-ошибка: Отказ в авторизации по картам. Превышено время ожидания"},
        {"text": "Внутренняя ошибка приложения: Получен код ошибки 0xCC125"},
        {"text": "ФинБанк: Зафиксирована частичная недоступность системы транзакций"},
        
        # Регламентные (Regex-эвристики)
        {"text": "Начат: Запуск процедур закрытия реестров."},
        {"text": "Процесс резервного копирования выполняется по расписанию."},
        {"text": "Требуется отправить email уведомление в службу рассылок."},
        
        # Тестовые и Прочие
        {"text": "Это просто Т Е С Т системы мониторинга, игнор."},
        {"text": "Нужна помощь по другому вопросу."},
    ]

    @task(10)
    def post_incident(self):
        payload = random.choice(self.SAMPLE_DATA).copy()
        # уникальный ID, чтобы в БД не было дублей
        payload["id"] = f"load-{random.randint(100000, 999999)}"
        
        with self.client.post("/api/v1/process", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Error {response.status_code}: {response.text}")

    @task(1)
    def check_health(self):
        self.client.get("/health")
        
    @task(1)
    def check_metrics(self):
        self.client.get("/api/v1/metrics")