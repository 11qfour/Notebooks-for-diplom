import psutil
import os
import time
import numpy as np
from app.ml_logic import load_models, classify_message

def get_ram_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def run_performance_test():
    print("=== ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ И ПАМЯТИ ===")
    
    start_ram = get_ram_usage()
    print(f"INFO: RAM до загрузки: {start_ram:.2f} MB")

    start_load = time.time()
    load_models()
    load_duration = time.time() - start_load
    
    post_load_ram = get_ram_usage()
    model_ram = post_load_ram - start_ram
    
    print(f"INFO: Модель загружена за {load_duration:.2f} сек")
    print(f"INFO: RAM после загрузки: {post_load_ram:.2f} MB (Чистый вес модели в памяти: ~{model_ram:.2f} MB)")

    test_texts = [
        "Критическая загрузка CPU на сервере app-01",
        "Начат процесс закрытия операционного дня",
        "Ошибка подключения к базе данных ORA-12514",
        "Привет, как дела?",
        "Сбой в работе кластера k8s: поды в состоянии Pending"
    ] * 20

    print(f"INFO: Запуск инференса 100 сообщений...")
    latencies = []
    for text in test_texts:
        t0 = time.time()
        classify_message(text)
        latencies.append(time.time() - t0)

    avg_latency = np.mean(latencies) * 1000 
    print(f"INFO: Среднее время обработки: {avg_latency:.2f} ms")
    
    if post_load_ram < 1024:
        print("\nРЕЗУЛЬТАТ: УСПЕХ (Лимит 1 ГБ соблюден)")
    else:
        print("\nРЕЗУЛЬТАТ: ПРЕВЫШЕНИЕ ЛИМИТА")

if __name__ == "__main__":
    run_performance_test()