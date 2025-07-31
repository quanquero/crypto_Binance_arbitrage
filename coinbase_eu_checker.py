from jose import jwt
import base64
import time
import secrets
import requests
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import json

class CoinbaseEUChecker:
    def __init__(self, api_key, private_key_base64):
        self.api_key = api_key
        self.private_key_base64 = private_key_base64
        self.API_URL = "https://api.coinbase.com"
    
    def decode_private_key(self):
        """Декодирует приватный ключ из формата Base64"""
        try:
            private_key_bytes = base64.b64decode(self.private_key_base64)
            private_key = ec.derive_private_key(
                int.from_bytes(private_key_bytes, byteorder='big'), 
                ec.SECP256K1()
            )
            return private_key
        except Exception as e:
            print(f"❌ Ошибка декодирования приватного ключа: {str(e)}")
            return None
    
    def get_jwt_token(self, method, path):
        """Генерирует JWT токен для EU аккаунта"""
        try:
            private_key = self.decode_private_key()
            if not private_key:
                return None
                
            # Приватный ключ в формате PEM для библиотеки jose
            pem_private_key = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            uri = f"{method} api.coinbase.com{path}"
            timestamp = int(time.time())
            
            payload = {
                'sub': self.api_key,
                'iss': 'coinbase-cloud',
                'nbf': timestamp,
                'exp': timestamp + 120,
                'uri': uri
            }
            
            token = jwt.encode(
                payload,
                pem_private_key,
                algorithm='ES256',
                headers={
                    'kid': self.api_key,
                    'nonce': secrets.token_hex(16)
                }
            )
            
            print(f"🔑 JWT токен успешно создан")
            return token
            
        except Exception as e:
            print(f"❌ Ошибка создания JWT токена: {str(e)}")
            return None
    
    def show_balances(self):
        """Получает и отображает балансы аккаунта"""
        try:
            path = '/api/v3/brokerage/accounts'
            token = self.get_jwt_token('GET', path)
            
            if not token:
                raise Exception("Не удалось создать JWT токен")
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            print(f"\n🔄 Отправка запроса баланса...")
            response = requests.get(
                f'{self.API_URL}{path}',
                headers=headers
            )
            
            print(f"📡 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                accounts = response.json()
                
                print("\n=================== БАЛАНСЫ АККАУНТА EU ===================")
                print("Валюта  | Доступно         | В ордерах        | Всего")
                print("-" * 60)
                
                # Сортируем балансы по общей сумме
                sorted_accounts = sorted(
                    accounts.get('accounts', []),
                    key=lambda x: float(x['available_balance']['value']) + float(x['hold']['value']),
                    reverse=True
                )
                
                total_usd = 0
                
                for account in sorted_accounts:
                    currency = account['currency']
                    available = float(account['available_balance']['value'])
                    hold = float(account['hold']['value'])
                    total = available + hold
                    
                    # Показываем только ненулевые балансы
                    if total > 0:
                        print(f"{currency:<8}| {available:<15.8f} | {hold:<15.8f} | {total:<.8f}")
                        
                        # Если есть USD value, добавляем к общей сумме
                        if 'usd_value' in account:
                            total_usd += float(account['usd_value'])
                
                print("-" * 60)
                if total_usd > 0:
                    print(f"Общая стоимость портфеля: ${total_usd:.2f}")
                print("======================================================")
                
                return accounts
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                print(f"❌ Ответ: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка при получении балансов: {str(e)}")
            return None

# Пример использования
if __name__ == "__main__":
    # Ключи EU аккаунта
    api_key = "650178fe-dc79-4e01-8607-9a388ab387f2"
    private_key = "uGybuFFiYIv2PFgSdr+/12ua+d4Je/xefW9qb2S9AkqvZEVw23uosY6bz+s+vG0yXfC1z8iSD99MibBAXUzgPQ=="
    
    checker = CoinbaseEUChecker(api_key, private_key)
    checker.show_balances() 