from jose import jwt
from cryptography.hazmat.primitives.serialization import load_pem_private_key
import time
import requests
import statistics
import secrets
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import socket

class CoinbasePingChecker:
    def __init__(self):
        # USA API ключи (формат с organizations/...)
        self.KEY_NAME = ""
        self.KEY_SECRET = """"""
        self.API_URL = "https://api.coinbase.com"
        self.PUBLIC_API_URL = "https://api.exchange.coinbase.com"
        
        # Создаем сессию с настройками повторных попыток
        self.session = self._create_robust_session()
        
        # Известные DNS-серверы и их провайдеры
        self.dns_servers = {
            "Google DNS": "8.8.8.8",
            "Cloudflare DNS": "1.1.1.1",
            "OpenDNS": "208.67.222.222",
            "Quad9": "9.9.9.9",
            "Local Default": None  # Использует DNS по умолчанию
        }
        
    def _create_robust_session(self):
        """Создает сессию с настройками повторных попыток"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,  # максимальное количество повторных попыток
            backoff_factor=1,  # фактор экспоненциального откладывания
            status_forcelist=[429, 500, 502, 503, 504],  # статусы для повторных попыток
            allowed_methods=["GET"]  # только для GET запросов
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
        
    def get_jwt_token(self, method, path, body=""):
        """Создание JWT токена для авторизации (USA формат)"""
        try:
            private_key = load_pem_private_key(
                self.KEY_SECRET.encode(),
                password=None
            )
            uri = f"{method} api.coinbase.com{path}"
            timestamp = int(time.time())
            
            payload = {
                'sub': self.KEY_NAME,
                'iss': 'coinbase-cloud',
                'nbf': timestamp,
                'exp': timestamp + 120,
                'uri': uri
            }
            
            token = jwt.encode(
                payload,
                private_key,
                algorithm='ES256',
                headers={
                    'kid': self.KEY_NAME,
                    'nonce': secrets.token_hex(16)
                }
            )
            
            return token
            
        except Exception as e:
            print(f"❌ Ошибка создания JWT токена: {str(e)}")
            return None
    
    def check_dns_connectivity(self, hostname="api.coinbase.com", timeout=5):
        """
        Проверяет соединение с хостом через различные DNS-серверы
        
        Args:
            hostname: имя хоста для проверки
            timeout: таймаут в секундах
        
        Returns:
            dict: результаты DNS-проверки для каждого DNS-сервера
        """
        print(f"\n🔎 Проверка DNS-соединения с {hostname}...")
        results = {}
        
        # Сохраняем текущий DNS-сервер
        original_nameserver = socket.getaddrinfo(hostname, None)[0][4][0]
        print(f"Текущий IP адрес для {hostname}: {original_nameserver}")
        
        for dns_name, dns_server in self.dns_servers.items():
            print(f"\nПроверка через {dns_name} {'(' + dns_server + ')' if dns_server else ''}")
            
            if dns_server:
                # Этот код работает только теоретически, 
                # в Windows изменение DNS требует прав администратора
                print(f"⚠️ Для полной проверки DNS запустите этот скрипт с правами администратора")
                print(f"⚠️ Текущая проверка будет использовать системный DNS для всех запросов")
            
            try:
                # Пытаемся получить IP-адрес с помощью DNS
                start_time = time.time()
                # В реальной реализации здесь был бы код для изменения DNS-сервера
                # Но это требует прав администратора
                try:
                    ip_address = socket.gethostbyname(hostname)
                    resolve_time = (time.time() - start_time) * 1000
                    print(f"✅ Разрешение DNS: {hostname} -> {ip_address} (за {resolve_time:.2f} мс)")
                    
                    # TCP-проверка: пытаемся подключиться к порту 443 (HTTPS)
                    start_tcp = time.time()
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(timeout)
                    
                    try:
                        s.connect((ip_address, 443))
                        tcp_time = (time.time() - start_tcp) * 1000
                        print(f"✅ TCP-соединение (порт 443): Успешно (за {tcp_time:.2f} мс)")
                        results[dns_name] = {
                            "resolved_ip": ip_address,
                            "dns_resolve_time_ms": resolve_time,
                            "tcp_connect_time_ms": tcp_time,
                            "status": "success"
                        }
                    except socket.timeout:
                        print(f"❌ TCP-соединение: Таймаут (>{timeout} сек)")
                        results[dns_name] = {
                            "resolved_ip": ip_address,
                            "dns_resolve_time_ms": resolve_time,
                            "status": "tcp_timeout"
                        }
                    except socket.error as e:
                        print(f"❌ TCP-соединение: Ошибка {str(e)}")
                        results[dns_name] = {
                            "resolved_ip": ip_address,
                            "dns_resolve_time_ms": resolve_time,
                            "status": "tcp_error",
                            "error": str(e)
                        }
                    finally:
                        s.close()
                        
                except socket.gaierror as e:
                    print(f"❌ Ошибка разрешения DNS: {str(e)}")
                    results[dns_name] = {
                        "status": "dns_error",
                        "error": str(e)
                    }
            except Exception as e:
                print(f"❌ Неожиданная ошибка при DNS-проверке: {str(e)}")
                results[dns_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return results
    
    def check_ping(self, endpoint="/api/v3/brokerage/accounts", num_requests=3, timeout=10):
        """
        Проверяет пинг до API Coinbase с использованием USA формата ключей
        
        Args:
            endpoint: эндпоинт для проверки
            num_requests: количество запросов для усреднения
            timeout: таймаут запроса в секундах
        
        Returns:
            dict: результаты измерения пинга
        """
        print(f"Проверка пинга на {self.API_URL}{endpoint}")
        print(f"Настройки: {num_requests} запросов, таймаут {timeout} сек")
        
        times = []
        status_codes = []
        errors = []
        
        for i in range(num_requests):
            try:
                # Получаем JWT токен для каждого запроса
                token = self.get_jwt_token("GET", endpoint)
                
                if not token:
                    print(f"❌ Запрос {i+1}/{num_requests}: Не удалось создать JWT токен")
                    errors.append("JWT token error")
                    continue
                
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                print(f"Запрос {i+1}/{num_requests}: отправка запроса...")
                start_time = time.time()
                
                try:
                    response = self.session.get(
                        f"{self.API_URL}{endpoint}", 
                        headers=headers, 
                        timeout=timeout
                    )
                    end_time = time.time()
                    
                    response_time_ms = (end_time - start_time) * 1000
                    times.append(response_time_ms)
                    status_codes.append(response.status_code)
                    
                    status = "✅" if response.status_code == 200 else "❌"
                    print(f"Запрос {i+1}/{num_requests}: {status} Код: {response.status_code}, Время: {response_time_ms:.2f} мс")
                
                except requests.exceptions.Timeout:
                    print(f"❌ Запрос {i+1}/{num_requests}: Таймаут соединения (>{timeout} сек)")
                    errors.append("Timeout")
                    
                except requests.exceptions.ConnectionError:
                    print(f"❌ Запрос {i+1}/{num_requests}: Ошибка соединения")
                    errors.append("Connection Error")
                    
                except Exception as e:
                    print(f"❌ Запрос {i+1}/{num_requests}: {str(e)}")
                    errors.append(str(e))
                
            except Exception as e:
                print(f"❌ Запрос {i+1}/{num_requests}: Неожиданная ошибка: {str(e)}")
                errors.append(str(e))
            
            # Небольшая пауза между запросами
            print(f"Ожидание 2 секунды перед следующим запросом...")
            time.sleep(2)
        
        # Проверка публичного API без авторизации
        print("\nПроверка публичного API без авторизации...")
        public_times = []
        public_status = []
        public_errors = []
        public_endpoint = "/products"
        
        for i in range(num_requests):
            try:
                print(f"Публичный запрос {i+1}/{num_requests}: отправка...")
                start_time = time.time()
                
                try:
                    response = self.session.get(
                        f"{self.PUBLIC_API_URL}{public_endpoint}",
                        timeout=timeout
                    )
                    end_time = time.time()
                    
                    response_time_ms = (end_time - start_time) * 1000
                    public_times.append(response_time_ms)
                    public_status.append(response.status_code)
                    
                    status = "✅" if response.status_code == 200 else "❌"
                    print(f"Публичный запрос {i+1}/{num_requests}: {status} Время: {response_time_ms:.2f} мс")
                    
                except requests.exceptions.Timeout:
                    print(f"❌ Публичный запрос {i+1}/{num_requests}: Таймаут соединения (>{timeout} сек)")
                    public_errors.append("Timeout")
                    
                except requests.exceptions.ConnectionError:
                    print(f"❌ Публичный запрос {i+1}/{num_requests}: Ошибка соединения")
                    public_errors.append("Connection Error")
                    
                except Exception as e:
                    print(f"❌ Публичный запрос {i+1}/{num_requests}: {str(e)}")
                    public_errors.append(str(e))
                
            except Exception as e:
                print(f"❌ Публичный запрос {i+1}/{num_requests}: Неожиданная ошибка: {str(e)}")
                public_errors.append(str(e))
            
            time.sleep(2)
        
        # Результаты
        print("\n📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ ПИНГА:")
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            median_time = statistics.median(times) if len(times) > 0 else None
            
            print("\n📊 Результаты приватного API (USA ключи):")
            print(f"Успешных запросов: {len(times)}/{num_requests}")
            print(f"Среднее время: {avg_time:.2f} мс")
            print(f"Минимальное время: {min_time:.2f} мс")
            print(f"Максимальное время: {max_time:.2f} мс")
            print(f"Медианное время: {median_time:.2f} мс" if median_time else "Медианное время: N/A")
            print(f"Статус коды: {status_codes}")
            if errors:
                print(f"Ошибки: {errors}")
        else:
            print("\n❌ Не удалось выполнить ни один запрос к приватному API")
            print(f"Ошибки: {errors}")
        
        if public_times:
            avg_public = sum(public_times) / len(public_times)
            min_public = min(public_times)
            max_public = max(public_times)
            median_public = statistics.median(public_times) if len(public_times) > 0 else None
            
            print("\n📊 Результаты публичного API:")
            print(f"Успешных запросов: {len(public_times)}/{num_requests}")
            print(f"Среднее время: {avg_public:.2f} мс")
            print(f"Минимальное время: {min_public:.2f} мс")
            print(f"Максимальное время: {max_public:.2f} мс")
            print(f"Медианное время: {median_public:.2f} мс" if median_public else "Медианное время: N/A")
            print(f"Статус коды: {public_status}")
            if public_errors:
                print(f"Ошибки: {public_errors}")
        else:
            print("\n❌ Не удалось выполнить ни один запрос к публичному API")
            print(f"Ошибки: {public_errors}")
        
        return {
            "private_api": {
                "success_count": len(times),
                "total_requests": num_requests,
                "average": avg_time if times else None,
                "min": min_time if times else None,
                "max": max_time if times else None,
                "median": median_time if times else None,
                "status_codes": status_codes,
                "errors": errors,
                "all_times": times
            },
            "public_api": {
                "success_count": len(public_times),
                "total_requests": num_requests,
                "average": avg_public if public_times else None,
                "min": min_public if public_times else None,
                "max": max_public if public_times else None,
                "median": median_public if public_times else None,
                "status_codes": public_status,
                "errors": public_errors,
                "all_times": public_times
            }
        }
    
    def run_full_diagnostics(self):
        """
        Выполняет полную диагностику соединения с Coinbase API
        """
        print("🔄 Запуск полной диагностики соединения с Coinbase API\n")
        
        # 1. Проверка DNS-соединения
        dns_results = self.check_dns_connectivity()
        
        # 2. Проверка пинга до API
        ping_results = self.check_ping(num_requests=2, timeout=15)
        
        # 3. Обобщение результатов
        print("\n📋 СВОДНЫЙ ОТЧЕТ О СОЕДИНЕНИИ:")
        
        # Проверка успешности DNS
        dns_success = any(result.get("status") == "success" for result in dns_results.values())
        print(f"DNS-соединение: {'✅ Доступно' if dns_success else '❌ Проблемы с соединением'}")
        
        # Проверка успешности приватного API
        private_success = ping_results["private_api"]["success_count"] > 0
        print(f"Приватный API: {'✅ Доступен' if private_success else '❌ Недоступен'}")
        
        # Проверка успешности публичного API
        public_success = ping_results["public_api"]["success_count"] > 0
        print(f"Публичный API: {'✅ Доступен' if public_success else '❌ Недоступен'}")
        
        # Рекомендации
        print("\n🔧 РЕКОМЕНДАЦИИ:")
        if not dns_success:
            print("1️⃣ Проблемы с DNS-разрешением имен. Рекомендации:")
            print("   - Проверьте работу интернет-соединения")
            print("   - Попробуйте изменить DNS на 1.1.1.1 (Cloudflare) или 8.8.8.8 (Google)")
            print("   - Проверьте, не блокируется ли доступ к Coinbase вашим провайдером")
        elif not public_success:
            print("2️⃣ Публичный API недоступен. Рекомендации:")
            print("   - Проверьте, не блокируется ли доступ к Coinbase в вашем регионе")
            print("   - Попробуйте использовать VPN-сервис из США или Европы")
            print("   - Проверьте настройки брандмауэра и антивируса")
        elif not private_success:
            print("3️⃣ Приватный API недоступен, но публичный работает. Рекомендации:")
            print("   - Проверьте корректность API-ключей")
            print("   - Убедитесь, что у ключа есть необходимые разрешения")
            print("   - Проверьте, не истек ли срок действия ключа")
        else:
            print("✅ Все проверки пройдены успешно!")
            
        return {
            "dns_results": dns_results,
            "ping_results": ping_results,
            "summary": {
                "dns_success": dns_success,
                "private_api_success": private_success,
                "public_api_success": public_success
            }
        }

# Запуск полной диагностики
if __name__ == "__main__":
    checker = CoinbasePingChecker()
    results = checker.run_full_diagnostics() 
