# Пример конфигурационного файла
# Скопируйте этот файл как config.py и заполните своими ключами

# Coinbase API (стандартные ключи)
COINBASE_API_KEY = "your_coinbase_api_key_here"
COINBASE_API_SECRET = "your_coinbase_api_secret_here"

# Binance API
BINANCE_API_KEY = "your_binance_api_key_here"
BINANCE_API_SECRET = "your_binance_secret_key_here"

# CDP API (Cloud Data Platform)
CDP_ORGANIZATION_ID = "your_organization_id_here"
CDP_API_KEY_ID = "your_api_key_id_here"
CDP_PRIVATE_KEY = """-----BEGIN EC PRIVATE KEY-----
your_private_key_here
-----END EC PRIVATE KEY-----"""

# Настройки торгового робота
TRADING_ENABLED = False  # Установите True для включения автоматической торговли
MAX_SPREAD_PERCENT = 2.0  # Максимальный спред для торговли (%)
MIN_PROFIT_PERCENT = 0.5  # Минимальная прибыль для торговли (%)
MAX_TRADE_AMOUNT = 100  # Максимальная сумма для одной сделки (USD)

# Настройки логирования
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "trading_bot.log"

# Настройки API
REQUEST_TIMEOUT = 30  # Таймаут запросов в секундах
MAX_RETRIES = 3  # Максимальное количество повторных попыток 