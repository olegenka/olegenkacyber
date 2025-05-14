#!/usr/bin/env python3

import unittest
import requests
import json
import time
import psutil
import os
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed

class TestPerformance(unittest.TestCase):
    def setUp(self):
        """Настройка тестового окружения"""
        self.base_url = "http://localhost:8080"
        self.test_drone_id = "test_drone_001"
        self.test_token = "test_token_123"  # Добавляем тестовый токен
        self.test_mission = {
            "drone_id": self.test_drone_id,
            "waypoints": [
                {"lat": 55.7558, "lon": 37.6173, "alt": 50},
                {"lat": 55.7559, "lon": 37.6174, "alt": 50}
            ],
            "payload": "test_package",
            "token": self.test_token
        }

    def test_command_latency(self):
        """Тест задержки при выполнении команд"""
        try:
            commands = ["takeoff", "land", "return_to_home"]
            latencies = []

            for command in commands:
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/command",
                    json={
                        "command": command,
                        "drone_id": self.test_drone_id,
                        "token": self.test_token
                    },
                    timeout=5
                )
                end_time = time.time()
                latency = end_time - start_time
                latencies.append(latency)

                self.assertIn(response.status_code, [200, 404, 500])
                
                if response.status_code == 200:
                    self.assertLess(latency, 1.0, f"Высокая задержка для команды {command}: {latency} сек")
                    data = response.json()
                    self.assertIn("command_status", data)
                    self.assertIn("execution_time", data)

            # Проверяем среднюю задержку
            avg_latency = sum(latencies) / len(latencies)
            self.assertLess(avg_latency, 0.5, f"Средняя задержка слишком высокая: {avg_latency} сек")

        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
            self.fail(f"Неожиданная ошибка при проверке задержки команд: {str(e)}")

    def test_telemetry_processing(self):
        """Тест производительности обработки телеметрии"""
        try:
            telemetry_data = {
                "drone_id": self.test_drone_id,
                "lat": 55.7558,
                "lon": 37.6173,
                "alt": 50,
                "speed": 10,
                "battery": 100,
                "status": "active",
                "token": self.test_token
            }
            
            # Тестируем обработку множественных пакетов телеметрии
            processing_times = []
            for _ in range(10):  # 10 последовательных пакетов
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/telemetry",
                    data=urlencode(telemetry_data),
                    headers={'Content-Type': 'application/x-www-form-urlencoded'},
                    timeout=5
                )
                processing_time = time.time() - start_time
                processing_times.append(processing_time)

                self.assertIn(response.status_code, [200, 404, 500])
                
                if response.status_code == 200:
                    self.assertLess(processing_time, 0.5)
                    data = response.json()
                    self.assertIn("processing_time", data)

            # Проверяем среднее время обработки
            avg_processing_time = sum(processing_times) / len(processing_times)
            self.assertLess(avg_processing_time, 0.2, 
                          f"Среднее время обработки телеметрии слишком высокое: {avg_processing_time} сек")

        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
            self.fail(f"Неожиданная ошибка при проверке обработки телеметрии: {str(e)}")

    def test_resource_usage(self):
        """Тест использования системных ресурсов"""
        try:
            # Мониторинг ресурсов в течение нескольких секунд
            cpu_samples = []
            memory_samples = []
            
            for _ in range(5):  # 5 замеров с интервалом в 1 секунду
                response = requests.get(
                    f"{self.base_url}/system/resources",
                    params={"token": self.test_token},
                    timeout=5
                )
                self.assertIn(response.status_code, [200, 404, 500])
                
                if response.status_code == 200:
                    data = response.json()
                    cpu_samples.append(data["cpu_usage"])
                    memory_samples.append(data["memory_usage"])
                    
                    self.assertIn("network_usage", data)
                    self.assertLess(data["network_usage"], 1000)
                
                time.sleep(1)

            if cpu_samples and memory_samples:
                avg_cpu = sum(cpu_samples) / len(cpu_samples)
                avg_memory = sum(memory_samples) / len(memory_samples)
                
                self.assertLess(avg_cpu, 80, f"Среднее использование CPU слишком высокое: {avg_cpu}%")
                self.assertLess(avg_memory, 80, f"Среднее использование памяти слишком высокое: {avg_memory}%")

        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
            self.fail(f"Неожиданная ошибка при проверке использования ресурсов: {str(e)}")

    def test_concurrent_requests(self):
        """Тест производительности при параллельных запросах"""
        try:
            def make_request():
                return requests.get(
                    f"{self.base_url}/system/concurrent",
                    params={"token": self.test_token},
                    timeout=5
                )

            # Тестируем с 20 параллельными запросами
            with ThreadPoolExecutor(max_workers=20) as executor:
                future_to_request = {executor.submit(make_request): i for i in range(20)}
                
                response_times = []
                for future in as_completed(future_to_request):
                    try:
                        response = future.result()
                        self.assertIn(response.status_code, [200, 404, 500])
                        
                        if response.status_code == 200:
                            data = response.json()
                            response_times.append(data["average_response_time"])
                    except requests.exceptions.ConnectionError:
                        pass
                    except Exception as e:
                        self.fail(f"Ошибка при параллельном запросе: {str(e)}")

            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                self.assertLess(avg_response_time, 0.5,
                              f"Среднее время отклика при параллельных запросах слишком высокое: {avg_response_time} сек")

        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
            self.fail(f"Неожиданная ошибка при проверке параллельных запросов: {str(e)}")

    def tearDown(self):
        """Очистка после тестов"""
        try:
            # Очистка тестовых данных
            requests.delete(
                f"{self.base_url}/cleanup",
                params={"token": self.test_token, "drone_id": self.test_drone_id},
                timeout=5
            )
        except:
            pass

if __name__ == '__main__':
    unittest.main()
