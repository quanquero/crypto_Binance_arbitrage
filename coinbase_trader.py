from coinbase.rest import RESTClient
import time

class CoinbaseTrader:
    def __init__(self, api_key, api_secret):
        self.client = RESTClient(api_key=api_key, api_secret=api_secret)
        
    def get_account_balance(self, currency):
        """Получить баланс по конкретной валюте"""
        try:
            accounts = self.client.get_accounts()
            for account in accounts:
                if account['currency'] == currency:
                    return float(account['available_balance'])
            return 0.0
        except Exception as e:
            print(f"Ошибка при получении баланса: {e}")
            return 0.0
            
    def get_product_price(self, product_id):
        """Получить текущую цену торговой пары"""
        try:
            product = self.client.get_product(product_id)
            return float(product['price'])
        except Exception as e:
            print(f"Ошибка при получении цены: {e}")
            return None
            
    def place_market_buy(self, product_id, quote_size):
        """Разместить рыночный ордер на покупку"""
        try:
            order = self.client.create_market_order(
                product_id=product_id,
                side='BUY',
                quote_size=quote_size
            )
            print(f"Ордер создан: {order}")
            return order
        except Exception as e:
            print(f"Ошибка при создании ордера: {e}")
            return None
            
    def check_order_status(self, order_id):
        """Проверить статус ордера"""
        try:
            order = self.client.get_order(order_id)
            print(f"Статус ордера: {order['status']}")
            print(f"Заполнено: {order['filled_size']} {order['product_id']}")
            return order
        except Exception as e:
            print(f"Ошибка при проверке статуса ордера: {e}")
            return None

def buy_for_both_accounts(product_id, amount_usd):
    """Покупка для обоих аккаунтов"""
    # Первый аккаунт
    trader1 = CoinbaseTrader(
        api_key="o2",
        api_secret="""==
-----END EC PRIVATE KEY-----"""
    )
    
    # Второй аккаунт
    trader2 = CoinbaseTrader(
        api_key="",
        api_secret=""g==
-----END EC PRIVATE KEY-----"""
    )
    
    # Покупка для первого аккаунта
    print("\nПокупка для первого аккаунта:")
    print(f"Баланс USD: {trader1.get_account_balance('USD')}")
    order1 = trader1.place_market_buy(product_id, amount_usd)
    if order1:
        time.sleep(2)  # Ждем 2 секунды
        trader1.check_order_status(order1['order_id'])
    
    # Покупка для второго аккаунта
    print("\nПокупка для второго аккаунта:")
    print(f"Баланс USD: {trader2.get_account_balance('USD')}")
    order2 = trader2.place_market_buy(product_id, amount_usd)
    if order2:
        time.sleep(2)  # Ждем 2 секунды
        trader2.check_order_status(order2['order_id']) 
