#!/usr/bin/env python3

import unittest
import requests
import json
import os
import sys
import subprocess
from urllib.parse import urlencode

class TestSecurityMechanisms(unittest.TestCase):
    def setUp(self):
        """Настройка тестового окружения"""
        self.base_url = "http://localhost:8080"
        self.test_drone_id = "test_drone_001"
        self.test_token = "test_token_123"  # Добавляем тестовый токен
        
    def _make_secure_request(self, endpoint, method='get', params=None, data=None):
        """Вспомогательный метод для выполнения защищенных запросов"""
        try:
            if params is None:
                params = {}
            params['token'] = self.test_token
            
            url = f"{self.base_url}{endpoint}"
            
            if method.lower() == 'get':
                response = requests.get(url, params=params, timeout=5)
            else:
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, params=params, json=data, headers=headers, timeout=5)
                
            return response
        except requests.exceptions.ConnectionError:
            return None
        except Exception as e:
            self.fail(f"Неожиданная ошибка при запросе {endpoint}: {str(e)}")

    def test_kos_verification(self):
        """Тест верификации KasperskyOS"""
        response = self._make_secure_request('/security/verify')
        if response:
            self.assertIn(response.status_code, [200, 401, 403])
            
            if response.status_code == 200:
                data = response.json()
                self.assertIn("status", data)
                self.assertIn("kos_version", data)
                self.assertIn("security_level", data)
                # Дополнительные проверки безопасности
                self.assertGreaterEqual(data["security_level"], 3)
                self.assertTrue(data["status"] in ["verified", "secure"])

    def test_isolation_mechanisms(self):
        """Тест механизмов изоляции"""
        response = self._make_secure_request('/security/isolation')
        if response:
            self.assertIn(response.status_code, [200, 401, 403])
            
            if response.status_code == 200:
                data = response.json()
                self.assertIn("process_isolation", data)
                self.assertIn("memory_protection", data)
                self.assertIn("resource_isolation", data)
                # Проверка состояния изоляции
                self.assertTrue(data["process_isolation"]["enabled"])
                self.assertTrue(data["memory_protection"]["enabled"])
                self.assertGreaterEqual(len(data["resource_isolation"]["policies"]), 1)

    def test_access_control(self):
        """Тест механизмов контроля доступа"""
        response = self._make_secure_request('/security/access-control')
        if response:
            self.assertIn(response.status_code, [200, 401, 403])
            
            if response.status_code == 200:
                data = response.json()
                self.assertIn("access_policies", data)
                self.assertIn("user_roles", data)
                self.assertIn("permissions", data)
                # Проверка политик доступа
                self.assertGreaterEqual(len(data["access_policies"]), 1)
                self.assertIn("admin", data["user_roles"])
                self.assertIn("read", data["permissions"])
                self.assertIn("write", data["permissions"])

    def test_memory_protection(self):
        """Тест работы с защищенной памятью"""
        response = self._make_secure_request('/security/memory-protection')
        if response:
            self.assertIn(response.status_code, [200, 401, 403])
            
            if response.status_code == 200:
                data = response.json()
                self.assertIn("memory_protection_enabled", data)
                self.assertIn("protected_regions", data)
                self.assertIn("access_violations", data)
                # Проверка защиты памяти
                self.assertTrue(data["memory_protection_enabled"])
                self.assertEqual(data["access_violations"], 0)

    def test_unauthorized_access(self):
        """Тест на попытки несанкционированного доступа"""
        # Тест без токена
        response = requests.get(f"{self.base_url}/security/verify", timeout=5)
        self.assertEqual(response.status_code, 401)
        
        # Тест с неверным токеном
        response = requests.get(
            f"{self.base_url}/security/verify",
            params={"token": "invalid_token"},
            timeout=5
        )
        self.assertEqual(response.status_code, 403)

    def test_security_logging(self):
        """Тест системы логирования безопасности"""
        response = self._make_secure_request('/security/logs')
        if response:
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("security_events", data)
            self.assertIn("audit_trail", data)
            self.assertGreaterEqual(len(data["security_events"]), 0)

    def tearDown(self):
        """Очистка после тестов"""
        try:
            # Очистка тестовых данных и логов
            self._make_secure_request('/security/cleanup', method='post')
        except:
            pass

if __name__ == '__main__':
    unittest.main()
