# Инструкция по загрузке проекта на GitHub

## Шаг 1: Подготовка проекта

1. Убедитесь, что все файлы готовы:
   - ✅ README.md
   - ✅ .gitignore
   - ✅ requirements.txt
   - ✅ LICENSE
   - ✅ config_example.py
   - ✅ Все Python файлы проекта

2. Удалите или переместите конфиденциальные файлы:
   - Переместите файлы с API ключами в безопасное место
   - Убедитесь, что .gitignore исключает конфиденциальные данные

## Шаг 2: Инициализация Git репозитория

```bash
# Инициализация Git
git init

# Добавление всех файлов
git add .

# Первый коммит
git commit -m "Initial commit: Trading bot for crypto exchanges"

# Проверка статуса
git status
```

## Шаг 3: Создание репозитория на GitHub

1. Перейдите на [GitHub.com](https://github.com)
2. Нажмите "New repository" (зеленая кнопка)
3. Заполните форму:
   - **Repository name**: `crypto-trading-bot`
   - **Description**: `Automated trading bot for Coinbase and Binance exchanges`
   - **Visibility**: Public или Private (на ваш выбор)
   - **Initialize with**: НЕ ставьте галочки (у вас уже есть файлы)
4. Нажмите "Create repository"

## Шаг 4: Подключение к GitHub

```bash
# Добавление удаленного репозитория
git remote add origin https://github.com/YOUR_USERNAME/crypto-trading-bot.git

# Переименование основной ветки (если нужно)
git branch -M main

# Отправка кода на GitHub
git push -u origin main
```

## Шаг 5: Настройка репозитория

### Добавление описания проекта

1. В репозитории на GitHub нажмите "About" (справа)
2. Добавьте описание: "Trading bot for crypto exchanges with spread analysis"
3. Добавьте теги: `python`, `trading-bot`, `cryptocurrency`, `coinbase`, `binance`

### Настройка веток

```bash
# Создание ветки для разработки
git checkout -b develop

# Отправка ветки на GitHub
git push -u origin develop
```

## Шаг 6: Дополнительные настройки

### Настройка GitHub Pages (опционально)

1. Перейдите в Settings → Pages
2. Source: Deploy from a branch
3. Branch: main, folder: / (root)
4. Save

### Настройка Issues и Projects

1. Создайте Issues для планирования функций
2. Создайте Project для управления задачами

## Шаг 7: Обновление кода

```bash
# Внесение изменений
git add .
git commit -m "Add new feature: improved spread analysis"
git push origin main
```

## Шаг 8: Создание релизов

1. Перейдите в Releases
2. Нажмите "Create a new release"
3. Заполните:
   - Tag version: v1.0.0
   - Release title: Initial Release
   - Description: Описание изменений
4. Publish release

## Полезные команды Git

```bash
# Проверка статуса
git status

# Просмотр истории коммитов
git log --oneline

# Создание новой ветки
git checkout -b feature/new-feature

# Слияние веток
git merge feature/new-feature

# Отмена последнего коммита
git reset --soft HEAD~1
```

## Безопасность

⚠️ **Важно**: Убедитесь, что конфиденциальные данные не попадут в репозиторий:

- Проверьте .gitignore файл
- Не коммитьте файлы с API ключами
- Используйте config_example.py как шаблон
- Добавьте предупреждение в README о безопасности

## Следующие шаги

1. Добавьте CI/CD (GitHub Actions)
2. Настройте автоматическое тестирование
3. Добавьте документацию API
4. Создайте Wiki для проекта 