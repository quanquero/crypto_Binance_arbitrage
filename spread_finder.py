import requests
import time
from datetime import datetime
import pandas as pd
import os
import asyncio
import aiohttp
import json
import websockets
from typing import List, Dict, Optional, Set
from collections import defaultdict

class SpreadFinder:
    def __init__(self):
        """Инициализация класса для поиска спредов"""
        self.PUBLIC_API_URL = "https://api.exchange.coinbase.com"
        self.WS_URL = "wss://ws-feed.exchange.coinbase.com"
        self.MIN_VOLUME_USD = 50  # Минимальный объем в USD для фильтрации
        self.CACHE_FILE = "spreads_cache.json"
        self.CACHE_DURATION = 300  # 5 минут в секундах
        self.spreads_data = defaultdict(dict)
        self.active_pairs = set()
        self.ws_connection = None
        self.ws_task = None

    async def connect_websocket(self):
        """Установка WebSocket соединения"""
        try:
            self.ws_connection = await websockets.connect(self.WS_URL)
            print("WebSocket соединение установлено")
            
            # Подписываемся на обновления
            subscribe_message = {
                "type": "subscribe",
                "product_ids": list(self.active_pairs),
                "channels": ["ticker", "level2"]
            }
            
            await self.ws_connection.send(json.dumps(subscribe_message))
            print(f"Подписка на {len(self.active_pairs)} пар установлена")
            
        except Exception as e:
            print(f"Ошибка подключения WebSocket: {str(e)}")
            raise

    async def process_websocket_message(self, message: str):
        """Обработка входящих сообщений WebSocket"""
        try:
            data = json.loads(message)
            
            if data.get("type") == "ticker":
                pair = data.get("product_id")
                if pair in self.active_pairs:
                    self.spreads_data[pair].update({
                        'Пара': pair,
                        'Бид': float(data.get("bid", 0)),
                        'Аск': float(data.get("ask", 0)),
                        'Объем бида': float(data.get("bid_size", 0)),
                        'Объем аска': float(data.get("ask_size", 0)),
                        'timestamp': time.time()
                    })
                    
                    # Пересчитываем спред
                    bid = self.spreads_data[pair]['Бид']
                    ask = self.spreads_data[pair]['Аск']
                    if bid > 0:
                        self.spreads_data[pair]['Спред %'] = ((ask - bid) / bid) * 100
                        self.spreads_data[pair]['Объем USD'] = min(
                            self.spreads_data[pair]['Объем бида'] * bid,
                            self.spreads_data[pair]['Объем аска'] * ask
                        )
            
            elif data.get("type") == "l2update":
                pair = data.get("product_id")
                if pair in self.active_pairs:
                    # Обновляем стакан
                    changes = data.get("changes", [])
                    for change in changes:
                        side, price, size = change
                        if side == "buy":
                            self.spreads_data[pair]['Бид'] = float(price)
                            self.spreads_data[pair]['Объем бида'] = float(size)
                        elif side == "sell":
                            self.spreads_data[pair]['Аск'] = float(price)
                            self.spreads_data[pair]['Объем аска'] = float(size)
                    
                    # Пересчитываем спред
                    bid = self.spreads_data[pair]['Бид']
                    ask = self.spreads_data[pair]['Аск']
                    if bid > 0:
                        self.spreads_data[pair]['Спред %'] = ((ask - bid) / bid) * 100
                        self.spreads_data[pair]['Объем USD'] = min(
                            self.spreads_data[pair]['Объем бида'] * bid,
                            self.spreads_data[pair]['Объем аска'] * ask
                        )
            
        except Exception as e:
            print(f"Ошибка обработки сообщения: {str(e)}")

    async def websocket_listener(self):
        """Слушатель WebSocket сообщений"""
        while True:
            try:
                if self.ws_connection is None:
                    await self.connect_websocket()
                
                message = await self.ws_connection.recv()
                await self.process_websocket_message(message)
                
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket соединение закрыто, переподключаемся...")
                await asyncio.sleep(5)
                self.ws_connection = None
                
            except Exception as e:
                print(f"Ошибка в WebSocket листенере: {str(e)}")
                await asyncio.sleep(5)

    async def start_websocket(self):
        """Запуск WebSocket соединения"""
        if self.ws_task is None:
            self.ws_task = asyncio.create_task(self.websocket_listener())

    async def stop_websocket(self):
        """Остановка WebSocket соединения"""
        if self.ws_task:
            self.ws_task.cancel()
            self.ws_task = None
        if self.ws_connection:
            await self.ws_connection.close()
            self.ws_connection = None

    async def update_active_pairs(self):
        """Обновление списка активных пар"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.PUBLIC_API_URL}/products") as response:
                if response.status != 200:
                    raise Exception(f"Ошибка получения списка пар: {response.status}")
                
                products = await response.json()
                new_pairs = {p['id'] for p in products if p.get('status') == 'online'}
                
                # Если список пар изменился, переподписываемся
                if new_pairs != self.active_pairs:
                    self.active_pairs = new_pairs
                    if self.ws_connection:
                        await self.stop_websocket()
                        await self.start_websocket()

    def _process_spreads(self, spreads: List[Dict], limit: int, start_time: float) -> List[Dict]:
        """Обработка и вывод результатов"""
        if spreads:
            # Сортируем по спреду
            sorted_spreads = sorted(spreads, key=lambda x: x['Спред %'], reverse=True)
            top_spreads = sorted_spreads[:limit]
            
            print("\n\n🏆 ТОП ПАРЫ ПО СПРЕДУ:")
            print("-" * 65)
            print("Пара      | Спред %  | Бид        | Аск        | Объем USD")
            print("-" * 65)
            
            for spread in top_spreads:
                print(f"{spread['Пара']:<9} | {spread['Спред %']:8.2f} | {spread['Бид']:10.8f} | {spread['Аск']:10.8f} | {spread['Объем USD']:10.2f}")
            
            execution_time = time.time() - start_time
            print("\n⏱️ Время выполнения: {:.2f} сек".format(execution_time))
            print(f"📊 Найдено {len(spreads)} пар со спредом >= {min_spread}%")
            
            return top_spreads
        else:
            print(f"\nНе найдено пар со спредом больше {min_spread}%")
            return []

    async def find_top_spreads(self, min_spread=0.5, limit=10) -> List[Dict]:
        """Поиск пар с лучшими спредами"""
        try:
            print(f"\n{'='*20} ПОИСК СПРЕДОВ {'='*20}")
            print(f"Минимальный спред: {min_spread}%")
            start_time = time.time()

            # Запускаем WebSocket если еще не запущен
            await self.start_websocket()
            
            # Обновляем список пар
            await self.update_active_pairs()
            
            # Ждем накопления данных
            await asyncio.sleep(2)
            
            # Фильтруем и сортируем данные
            spreads = [
                data for data in self.spreads_data.values()
                if data.get('Спред %', 0) >= min_spread and data.get('Объем USD', 0) >= self.MIN_VOLUME_USD
            ]
            
            return self._process_spreads(spreads, limit, start_time)

        except Exception as e:
            print(f"\nОшибка при поиске спредов: {str(e)}")
            return []

    async def analyze_pair(self, pair_id: str) -> Dict:
        """Анализ конкретной торговой пары"""
        try:
            print(f"\n{'='*20} АНАЛИЗ ПАРЫ {pair_id} {'='*20}")
            
            # Запускаем WebSocket если еще не запущен
            await self.start_websocket()
            
            # Ждем накопления данных
            await asyncio.sleep(2)
            
            if pair_id in self.spreads_data:
                data = self.spreads_data[pair_id]
                
                print("\n📊 ТЕКУЩИЕ ЦЕНЫ")
                print(f"Лучшая цена покупки (bid): {data['Бид']:.8f}")
                print(f"Лучшая цена продажи (ask): {data['Аск']:.8f}")
                print(f"Текущий спред: {data['Спред %']:.2f}%")
                print(f"Объем бида: {data['Объем бида']:.8f}")
                print(f"Объем аска: {data['Объем аска']:.8f}")
                print(f"Объем USD: {data['Объем USD']:.2f}")
                
                return data
            else:
                print(f"Пара {pair_id} не найдена или нет данных")
                return {}
                
        except Exception as e:
            print(f"Ошибка при анализе пары: {str(e)}")
            return {}

async def main():
    """Основная функция"""
    finder = SpreadFinder()
    
    while True:
        print("\nВыберите действие:")
        print("1. Найти лучшие спреды")
        print("2. Проанализировать пару")
        print("3. Выход")
        
        choice = input("Ваш выбор (1-3): ")
        
        if choice == "1":
            min_spread = float(input("Введите минимальный спред (%): ") or "0.5")
            limit = int(input("Введите количество пар для отображения: ") or "10")
            await finder.find_top_spreads(min_spread, limit)
            
        elif choice == "2":
            pair = input("Введите пару (например, BTC-USD): ")
            await finder.analyze_pair(pair)
            
        elif choice == "3":
            await finder.stop_websocket()
            break
            
        else:
            print("Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    asyncio.run(main()) 