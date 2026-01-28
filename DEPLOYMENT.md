# 🚀 Deployment Guide - Fitness Bot AN_SPORT

Полное руководство по развертыванию Telegram бота для фитнес-студии с использованием Docker и CI/CD.

## 📋 Содержание

- [Требования](#требования)
- [Локальный запуск](#локальный-запуск)
- [Настройка GitHub Actions](#настройка-github-actions)
- [Настройка сервера](#настройка-сервера)
- [Мониторинг](#мониторинг)
- [Troubleshooting](#troubleshooting)

---

## 🛠 Требования

### Локальная разработка
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git

### Production сервер
- Ubuntu 20.04+ / Debian 11+
- Docker Engine 20.10+
- Docker Compose 2.0+
- SSH доступ
- Минимум 512 MB RAM
- Минимум 2 GB свободного места

---

## 💻 Локальный запуск

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-username/fitness-bot-ann-sport.git
cd fitness-bot-ann-sport
```

### 2. Настройка окружения

```bash
# Копировать пример конфигурации
cp .env.example .env

# Отредактировать файл .env
nano .env
```

Обязательные параметры в `.env`:
```env
BOT_TOKEN=your_bot_token_here
ADMIN_ID=1258139980
STUDIO_NAME=FitStudio
STUDIO_ADDRESS=пр. Комсомольский 3 (второй этаж)
CARD_NUMBER=2200700123456789
CARD_HOLDER=MARIA IVANOVA
```

### 3. Запуск контейнеров

```bash
# Сборка и запуск
docker compose up -d --build

# Просмотр логов
docker compose logs -f fitness-bot

# Остановка
docker compose down
```

**Dozzle** (веб-интерфейс для логов) будет доступен по адресу: `http://localhost:8080`

### 4. Проверка работоспособности

```bash
# Проверить статус контейнеров
docker compose ps

# Проверить логи бота
docker logs fitness-bot

# Проверить базу данных
docker exec -it fitness-bot ls -la /app/data/
```

---

## 🔧 Настройка GitHub Actions

### 1. Настройка GitHub Secrets

Перейдите в **Settings → Secrets and variables → Actions** вашего репозитория и добавьте следующий secret:

#### Обязательный секрет для деплоя

```
SSH_PRIVATE_KEY=your-private-ssh-key
```

Параметры сервера захардкожены в workflow:
- **SERVER_HOST:** 78.140.241.105
- **SERVER_USER:** root
- **DEPLOY_PATH:** /home/fitness-bot-ann-sport
- **SERVER_PORT:** 22

### 2. Генерация SSH ключа

```bash
# Генерация нового SSH ключа
ssh-keygen -t ed25519 -C "github-actions@fitness-bot" -f ~/.ssh/fitness-bot-deploy

# Копирование публичного ключа на сервер
ssh-copy-id -i ~/.ssh/fitness-bot-deploy.pub root@78.140.241.105

# Скопировать приватный ключ для GitHub Secret
cat ~/.ssh/fitness-bot-deploy
```

Скопируйте **весь вывод** (включая `-----BEGIN` и `-----END`) и вставьте в GitHub Secret `SSH_PRIVATE_KEY`.

### 3. Тестирование автоматического деплоя

```bash
# Push в main ветку запустит автоматический деплой
git add .
git commit -m "Initial deployment setup"
git push origin main
```

Или запустите вручную через **Actions → Deploy Bot → Run workflow**

### 4. Мониторинг деплоя

После push в main:
1. Перейдите в **Actions** на GitHub
2. Откройте последний запуск workflow
3. Следите за логами каждого шага
4. При успешном деплое бот автоматически перезапустится

---

## 🖥 Настройка сервера

### 1. Установка Docker

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Добавление Docker репозитория
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установка Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker

# Проверка установки
docker --version
docker compose version
```

### 2. Подготовка директории на сервере

```bash
# Создание директории для проекта (точный путь из workflow)
mkdir -p /home/fitness-bot-ann-sport
cd /home/fitness-bot-ann-sport

# Клонирование репозитория ИЛИ создание файлов вручную
git clone https://github.com/your-username/fitness-bot-ann-sport.git .
```

### 3. Настройка .env файла на сервере

```bash
nano .env
```

Заполните реальными данными:
```env
BOT_TOKEN=8380404463:AAHYJnUD5h19Ffc4v01x0m1mnBlzwKtNjpw
ADMIN_ID=1258139980
STUDIO_NAME=FitStudio
STUDIO_ADDRESS=пр. Комсомольский 3 (второй этаж)
CARD_NUMBER=2200700123456789
CARD_HOLDER=MARIA IVANOVA
CHANNEL_USERNAME=@OFFICIAL_AN_SPORT
```

### 4. Первый запуск на сервере

```bash
cd /home/fitness-bot-ann-sport
docker compose up -d
```

### 5. Проверка работы

```bash
# Статус контейнеров
docker compose ps

# Логи бота
docker logs -f fitness-bot

# Проверка базы данных
docker exec -it fitness-bot ls -la /app/data/
```

---

## 📊 Мониторинг

### Dozzle - веб-интерфейс для логов

**URL:** `http://78.140.241.105:8080`

Dozzle предоставляет:
- ✅ Просмотр логов в реальном времени
- ✅ Фильтрация по контейнерам
- ✅ Поиск в логах
- ✅ Статистика контейнеров
- ✅ Автоматическое обновление

### Полезные команды мониторинга

```bash
# Проверка статуса всех контейнеров
docker compose ps

# Просмотр логов бота
docker logs -f fitness-bot

# Просмотр логов Dozzle
docker logs -f dozzle

# Просмотр использования ресурсов
docker stats

# Проверка health check
docker inspect --format='{{.State.Health.Status}}' fitness-bot

# Просмотр последних 100 строк логов
docker logs --tail 100 fitness-bot

# Экспорт логов в файл
docker logs fitness-bot > bot-logs-$(date +%Y%m%d).txt
```

### Watchtower - автоматическое обновление

Watchtower автоматически:
- ✅ Проверяет обновления образов каждые 5 минут
- ✅ Обновляет контейнеры с новыми версиями
- ✅ Выполняет rolling restart для минимизации downtime
- ✅ Очищает старые образы

```bash
# Просмотр логов Watchtower
docker logs watchtower

# Остановить Watchtower (если нужно отключить автообновление)
docker stop watchtower

# Запустить обратно
docker start watchtower
```

---

## 🔥 Troubleshooting

### Контейнер не запускается

```bash
# Проверить логи
docker logs fitness-bot

# Проверить конфигурацию
docker compose config

# Пересобрать образ
docker compose up -d --build --force-recreate
```

### База данных не создается

```bash
# Проверить volume
docker volume ls
docker volume inspect fitness-bot-ann-sport_bot-data

# Проверить права доступа
docker exec -it fitness-bot ls -la /app/data/

# Пересоздать volume
docker compose down -v
docker compose up -d
```

### Бот не отвечает на команды

1. **Проверить токен бота:**
```bash
cat .env | grep BOT_TOKEN
```

2. **Проверить, что бот запущен через BotFather**

3. **Проверить логи на ошибки:**
```bash
docker logs --tail 200 fitness-bot
```

4. **Перезапустить бота:**
```bash
docker compose restart fitness-bot
```

### GitHub Actions не может подключиться к серверу

1. **Проверить SSH ключ в GitHub Secrets**
2. **Проверить доступность сервера:**
```bash
ssh -i ~/.ssh/your-key user@server-ip
```
3. **Проверить firewall:**
```bash
sudo ufw status
sudo ufw allow 22/tcp
```

### Недостаточно места на диске

```bash
# Очистка неиспользуемых образов
docker image prune -a

# Очистка volumes (осторожно! удалит данные)
docker volume prune

# Очистка всего (осторожно!)
docker system prune -a --volumes

# Проверка использования места
docker system df
```

### Высокое использование памяти

```bash
# Проверить использование ресурсов
docker stats

# Посмотреть лимиты в docker-compose.yml
docker inspect fitness-bot | grep -A 10 Memory
```

Лимиты уже установлены:
- **CPU:** до 1.0 (100% одного ядра)
- **Memory:** до 512 MB

### Проблемы с Dozzle

```bash
# Перезапуск Dozzle
docker restart dozzle

# Проверка логов Dozzle
docker logs dozzle

# Проверка прав доступа к Docker socket
ls -la /var/run/docker.sock
```

### Ошибка "Cannot connect to Docker daemon"

```bash
# Проверить, что Docker запущен
sudo systemctl status docker

# Запустить Docker
sudo systemctl start docker

# Добавить пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker
```

---

## 🔐 Безопасность

### Рекомендации по безопасности

1. **Защитите .env файл**
```bash
chmod 600 .env
```

2. **Используйте firewall**
```bash
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8080/tcp  # Dozzle (опционально, можно закрыть)
```

3. **Ограничьте доступ к Dozzle**

Если Dozzle нужен только вам:
```bash
# SSH туннель вместо открытого порта
ssh -L 8080:localhost:8080 user@your-server-ip
```

Затем откройте в браузере: `http://localhost:8080`

4. **Регулярно обновляйте образы**
```bash
docker compose pull
docker compose up -d
```

5. **Настройте автоматические бэкапы базы данных**

Добавьте в crontab:
```bash
# Открыть crontab
crontab -e

# Добавить строку (бэкап каждый день в 2:00)
0 2 * * * docker exec fitness-bot cp /app/data/bot.db /app/data/backup-$(date +\%Y\%m\%d).db
```

6. **Мониторинг логов на подозрительную активность**
```bash
# Поиск ошибок
docker logs fitness-bot | grep -i error

# Поиск исключений
docker logs fitness-bot | grep -i exception
```

---

## 📚 Структура проекта

```
fitness-bot-ann-sport/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions CI/CD
├── handlers/                   # Обработчики команд бота
├── keyboards/                  # Клавиатуры для бота
├── utils/                      # Утилиты
├── bot.py                      # Главный файл бота
├── config.py                   # Конфигурация
├── database.py                 # Работа с БД
├── Dockerfile                  # Docker образ
├── docker-compose.yml          # Docker Compose конфигурация
├── .env.example                # Пример переменных окружения
├── requirements.txt            # Python зависимости
└── DEPLOYMENT.md              # Эта документация
```

---

## 🚀 Быстрый старт (краткая версия)

### Локально

```bash
git clone <repo>
cd fitness-bot-ann-sport
cp .env.example .env
# Отредактировать .env
docker compose up -d
```

### На сервере

```bash
# Установить Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Клонировать и запустить
git clone <repo>
cd fitness-bot-ann-sport
cp .env.example .env
# Отредактировать .env
docker compose up -d
```

### GitHub Actions

1. Добавить secrets в GitHub
2. Push в main
3. Готово! 🎉

---

## 📞 Поддержка

При возникновении проблем:

1. Проверьте раздел [Troubleshooting](#troubleshooting)
2. Просмотрите логи: `docker logs fitness-bot`
3. Проверьте Dozzle: `http://your-server:8080`
4. Создайте issue в GitHub репозитории
5. Свяжитесь с администратором: @an_sport_

---

## 📄 Лицензия

Этот проект создан для фитнес-студии AN_SPORT.

**Создано с ❤️ для FitStudio (AN_SPORT)**
