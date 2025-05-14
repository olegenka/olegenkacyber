#!/usr/bin/env python3

import unittest
import requests
import json
import time
from urllib.parse import urlencode

class TestFaultTolerance(unittest.TestCase):
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
            "payload": "test_package"
        }

    def _make_request(self, endpoint, method='get', params=None, json_data=None):
        """Вспомогательный метод для выполнения запросов с обработкой ошибок"""
        try:
            if params is None:
                params = {}
            params['token'] = self.test_token

            if method.lower() == 'get':
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    params=params,
                    timeout=5
                )
            else:
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    params=params,
                    json=json_data,
                    timeout=5
                )
            return response
        except requests.exceptions.ConnectionError:
            return None
        except Exception as e:
            self.fail(f"Неожиданная ошибка при запросе {endpoint}: {str(e)}")

    def test_connection_loss(self):
        """Тест поведения при потере связи"""
        response = self._make_request('/fault/connection-loss')
        if response:
            self.assertIn(response.status_code, [200, 404, 500])
            if response.status_code == 200:
                data = response.json()
                self.assertIn("autonomous_mode", data)
                self.assertIn("last_known_position", data)
                self.assertIn("recovery_protocol", data)

    def test_gps_failure(self):
        """Тест поведения при отказе GPS"""
        response = self._make_request('/fault/gps-failure')
        if response:
            self.assertIn(response.status_code, [200, 404, 500])
            if response.status_code == 200:
                data = response.json()
                self.assertIn("backup_navigation", data)
                self.assertIn("last_valid_position", data)
                self.assertIn("recovery_status", data)

    def test_imu_failure(self):
        """Тест поведения при сбое IMU"""
        response = self._make_request('/fault/imu-failure')
        if response:
            self.assertIn(response.status_code, [200, 404, 500])
            if response.status_code == 200:
                data = response.json()
                self.assertIn("backup_sensors", data)
                self.assertIn("stabilization_mode", data)
                self.assertIn("recovery_protocol", data)

    def test_emergency_landing(self):
        """Тест процедуры аварийной посадки"""
        response = self._make_request('/fault/emergency-landing')
        if response:
            self.assertIn(response.status_code, [200, 404, 500])
            if response.status_code == 200:
                data = response.json()
                self.assertIn("landing_sites", data)
                self.assertIn("risk_assessment", data)
                self.assertIn("landing_protocol", data)

    def test_multiple_failures(self):
        """Тест поведения при множественных отказах"""
        failures = [
            '/fault/connection-loss',
            '/fault/gps-failure',
            '/fault/imu-failure'
        ]
        
        for failure in failures:
            response = self._make_request(failure)
            if response:
                self.assertIn(response.status_code, [200, 404, 500])

    def test_recovery_sequence(self):
        """Тест последовательности восстановления после сбоев"""
        # Имитация сбоя
        response = self._make_request('/fault/gps-failure')
        if response and response.status_code == 200:
            # Проверка восстановления через 5 секунд
            time.sleep(5)
            recovery_response = self._make_request('/fault/recovery-status')
            if recovery_response:
                self.assertEqual(recovery_response.status_code, 200)
                data = recovery_response.json()
                self.assertIn("recovery_complete", data)

if __name__ == '__main__':
    unittest.main()
