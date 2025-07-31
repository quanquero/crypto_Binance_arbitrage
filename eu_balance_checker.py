import jwt  # используем PyJWT вместо jose
import base64
import time
import secrets
import requests
import json

class BalanceCheckerEU:
    def __init__(self):
        # EU API ключи
        self.API_KEY = "650178fe-dc79-4e01-8607-9a388ab387f2"
        self.API_SECRET = "uGybuFFiYIv2PFgSdr+/12ua+d4Je/xefW9qb2S9AkqvZEVw23uosY6bz+s+vG0yXfC1z8iSD99MibBAXUzgPQ=="
        self.API_URL = "https://api.coinbase.com"

    def sign_request(self, method, path, body=""):
        """
        Создание JWT токена в соответствии с документацией Coinbase Advanced Trade API
        https://docs.cdp.coinbase.com/advanced-trade/reference/retailbrokerageapi_postorder
        """
        try:
            # Декодируем секретный ключ из base64
            secret_bytes = base64.b64decode(self.API_SECRET)
            
            # Формируем сообщение для подписи
            timestamp = int(time.time())
            message = f"{timestamp}{method.upper()}{path}{body}"
            
            # Создаем HMAC-SHA256 подпись
            import hmac
            import hashlib
            signature = hmac.new(secret_bytes, message.encode(), hashlib.sha256).hexdigest()
            
            print(f"🔑 Подпись успешно создана")
            
            return {
                'signature': signature,
                'timestamp': timestamp
            }
            
        except Exception as e:
            print(f"❌ Ошибка создания подписи: {str(e)}")
            return None

    def show_balances(self):
        try:
            path = '/api/v3/brokerage/accounts'
            method = 'GET'
            
            # Создаем подпись
            auth = self.sign_request(method, path)
            if not auth:
                raise Exception("Не удалось создать подпись")
            
            # Формируем заголовки согласно документации
            headers = {
                'Content-Type': 'application/json',
                'CB-ACCESS-KEY': self.API_KEY,
                'CB-ACCESS-SIGN': auth['signature'],
                'CB-ACCESS-TIMESTAMP': str(auth['timestamp'])
            }
            
            print(f"\n🔄 Отправка запроса баланса...")
            print(f"URL: {self.API_URL}{path}")
            print(f"Заголовки: {json.dumps({k: headers[k] for k in headers if k != 'CB-ACCESS-SIGN'}, indent=2)}")
            
            response = requests.get(
                f'{self.API_URL}{path}',
                headers=headers
            )
            
            print(f"📡 Статус ответа: {response.status_code}")
            print(f"Ответ: {response.text[:200]}...")
            
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
            import traceback
            traceback.print_exc()
            return None

# Запуск проверки баланса
if __name__ == "__main__":
    checker = BalanceCheckerEU()
    checker.show_balances() 