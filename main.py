import asyncio
import json
import os
import sys
import requests
from telethon import events, TelegramClient

# Константы
CONFIG_FILE = "config.json"
DEFAULT_TYPING_SPEED = 0.3
DEFAULT_CURSOR = "\u2588"  # Символ по умолчанию для анимации
GITHUB_RAW_URL = "https://raw.githubusercontent.com/mishkagoo/userbot/refs/heads/main/main.py"  # Укажите URL вашего скрипта
SCRIPT_VERSION = "1.4.31"

# Проверяем наличие файла конфигурации
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        API_ID = config.get("API_ID")
        API_HASH = config.get("API_HASH")
        PHONE_NUMBER = config.get("PHONE_NUMBER")
        typing_speed = config.get("typing_speed", DEFAULT_TYPING_SPEED)
        cursor_symbol = config.get("cursor_symbol", DEFAULT_CURSOR)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Ошибка чтения конфигурации: {e}. Удалите {CONFIG_FILE} и попробуйте снова.")
        exit(1)
else:
    # Запрашиваем данные у пользователя
    try:
        API_ID = int(input("Введите ваш API ID: "))
        API_HASH = input("Введите ваш API Hash: ").strip()
        PHONE_NUMBER = input("Введите ваш номер телефона (в формате +375XXXXXXXXX, +7XXXXXXXXXX): ").strip()
        typing_speed = DEFAULT_TYPING_SPEED
        cursor_symbol = DEFAULT_CURSOR

        # Сохраняем данные в файл конфигурации
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "API_ID": API_ID,
                "API_HASH": API_HASH,
                "PHONE_NUMBER": PHONE_NUMBER,
                "typing_speed": typing_speed,
                "cursor_symbol": cursor_symbol
            }, f)
    except Exception as e:
        print(f"Ошибка сохранения конфигурации: {e}")
        exit(1)

# Уникальное имя файла для сессии
SESSION_FILE = f'session_{PHONE_NUMBER.replace("+", "").replace("-", "")}'

# Инициализация клиента
client = TelegramClient(SESSION_FILE, API_ID, API_HASH)


def check_for_updates():
    """Проверка наличия обновлений скрипта на GitHub."""
    try:
        response = requests.get(GITHUB_RAW_URL)
        if response.status_code == 200:
            remote_script = response.text
            current_file = os.path.abspath(__file__)
            with open(current_file, 'r', encoding='utf-8') as f:
                current_script = f.read()

            if "SCRIPT_VERSION" in remote_script and "SCRIPT_VERSION" in current_script:
                remote_version = remote_script.split('SCRIPT_VERSION = "')[1].split('"')[0]
                if SCRIPT_VERSION != remote_version:
                    print(f"Доступна новая версия скрипта: {remote_version} (текущая: {SCRIPT_VERSION})")
                    choice = input("Хотите обновиться? (y/n): ").strip().lower()
                    if choice == 'y':
                        with open(current_file, 'w', encoding='utf-8') as f:
                            f.write(remote_script)
                        print("Скрипт обновлен. Перезапустите программу.")
                        exit()
                else:
                    print("У вас уже установлена последняя версия скрипта.")
            else:
                print("Не удалось определить версии для сравнения.")
        else:
            print("Не удалось проверить обновления. Проверьте соединение с GitHub.")
    except Exception as e:
        print(f"Ошибка при проверке обновлений: {e}")


@client.on(events.NewMessage(pattern=r'/p (.+)', func=lambda e: e.is_out))
async def animated_typing(event):
    """Команда для печатания текста с анимацией."""
    global typing_speed, cursor_symbol
    try:
        if not event.out:
            return

        # Захватываем весь текст, включая переносы строк
        text = event.pattern_match.group(1)
        typed_text = ""

        for char in text:
            typed_text += char
            await event.edit(typed_text + cursor_symbol)
            await asyncio.sleep(typing_speed)

        await event.edit(typed_text)
    except Exception as e:
        print(f"Ошибка анимации: {e}")
        await event.reply("<b>Произошла ошибка во время выполнения команды.</b>", parse_mode='html')


@client.on(events.NewMessage(pattern=r'/s (\d*\.?\d+)'))
async def set_typing_speed(event):
    """Команда для изменения скорости печатания."""
    global typing_speed
    try:
        if not event.out:
            return

        new_speed = float(event.pattern_match.group(1))

        if 0.1 <= new_speed <= 0.5:
            typing_speed = new_speed

            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            config["typing_speed"] = typing_speed
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f)

            await event.reply(f"<b>Скорость печатания изменена на {typing_speed} секунд.</b>", parse_mode='html')
        else:
            await event.reply("<b>Введите значение задержки в диапазоне от 0.1 до 0.5 секунд.</b>", parse_mode='html')

    except ValueError:
        await event.reply("<b>Некорректное значение. Укажите число в формате 0.1 - 0.5.</b>", parse_mode='html')
    except Exception as e:
        print(f"Ошибка при изменении скорости: {e}")
        await event.reply("<b>Произошла ошибка при изменении скорости.</b>", parse_mode='html')


@client.on(events.NewMessage(pattern=r'/c (.+)'))
async def change_cursor(event):
    """Команда для изменения символа курсора анимации."""
    global cursor_symbol
    try:
        if not event.out:
            return

        new_cursor = event.pattern_match.group(1).strip()

        if new_cursor:
            cursor_symbol = new_cursor

            # Обновление конфигурации
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            config["cursor_symbol"] = cursor_symbol
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f)

            await event.reply(f"<b>Символ курсора изменен на: {cursor_symbol}</b>", parse_mode='html')
        else:
            await event.reply("<b>Введите корректный символ для курсора.</b>", parse_mode='html')
    except Exception as e:
        print(f"Ошибка при изменении символа: {e}")
        await event.reply("<b>Произошла ошибка при изменении символа курсора.</b>", parse_mode='html')

@client.on(events.NewMessage(pattern=r'/sp (.+) (\d+) (\d*\.?\d+)'))
async def spam_message(event):
    """Команда для спама сообщений."""
    try:
        if not event.out:
            return

        message = event.pattern_match.group(1)
        count = int(event.pattern_match.group(2))
        speed = float(event.pattern_match.group(3))

        if count <= 0 or speed <= 0:
            await event.reply("<b>Количество сообщений и скорость должны быть положительными числами.</b>", parse_mode='html')
            return

        for _ in range(count):
            await event.reply(message)
            await asyncio.sleep(speed)

        
    except Exception as e:
        print(f"Ошибка при спаме: {e}")
        await event.reply("<b>Произошла ошибка при отправке сообщений.</b>", parse_mode='html')


@client.on(events.NewMessage(pattern="сердечки"))
async def heart(event):
     # Начальное сообщение
    stages = [
        "🤍", "🤍🤍", "🤍🤍🤍", "🤍🤍🤍🤍", "🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍", "🤍🤍🤍🤍🤍🤍🤍", "🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍❤️❤️🤍❤️❤️🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍❤️❤️🤍❤️❤️🤍🤍\n🤍❤️❤️❤️❤️❤️❤️❤️🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍❤️❤️🤍❤️❤️🤍🤍\n🤍❤️❤️❤️❤️❤️❤️❤️🤍\n🤍❤️❤️❤️❤️❤️❤️❤️🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍❤️❤️🤍❤️❤️🤍🤍\n🤍❤️❤️❤️❤️❤️❤️❤️🤍\n🤍❤️❤️❤️❤️❤️❤️❤️🤍\n🤍🤍❤️❤️❤️❤️❤️🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍❤️❤️🤍❤️❤️🤍🤍\n🤍❤️❤️❤️❤️❤️❤️❤️🤍\n🤍❤️❤️❤️❤️❤️❤️❤️🤍\n🤍🤍❤️❤️❤️❤️❤️🤍🤍\n🤍🤍🤍❤️❤️❤️🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍❤️❤️🤍❤️❤️🤍🤍\n🤍❤️❤️❤️❤️❤️❤️❤️🤍\n🤍❤️❤️❤️❤️❤️❤️❤️🤍\n🤍🤍❤️❤️❤️❤️❤️🤍🤍\n🤍🤍🤍❤️❤️❤️🤍🤍🤍\n🤍🤍🤍🤍❤️🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍💗💗🤍💗💗🤍🤍\n🤍❤️❤️❤️❤️❤️❤️❤️🤍\n🤍❤️❤️❤️❤️❤️❤️❤️🤍\n🤍🤍❤️❤️❤️❤️❤️🤍🤍\n🤍🤍🤍❤️❤️❤️🤍🤍🤍\n🤍🤍🤍🤍❤️🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍💗💗🤍💗💗🤍🤍\n🤍💗💗💗💗💗💗💗🤍\n🤍❤️❤️❤️❤️❤️❤️❤️🤍\n🤍🤍❤️❤️❤️❤️❤️🤍🤍\n🤍🤍🤍❤️❤️❤️🤍🤍🤍\n🤍🤍🤍🤍❤️🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍💗💗🤍💗💗🤍🤍\n🤍💗💗💗💗💗💗💗🤍\n🤍💗💗💗💗💗💗💗🤍\n🤍🤍❤️❤️❤️❤️❤️🤍🤍\n🤍🤍🤍❤️❤️❤️🤍🤍🤍\n🤍🤍🤍🤍❤️🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍💗💗🤍💗💗🤍🤍\n🤍💗💗💗💗💗💗💗🤍\n🤍💗💗💗💗💗💗💗🤍\n🤍🤍💗💗💗💗💗🤍🤍\n🤍🤍🤍❤️❤️❤️🤍🤍🤍\n🤍🤍🤍🤍❤️🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍💗💗🤍💗💗🤍🤍\n🤍💗💗💗💗💗💗💗🤍\n🤍💗💗💗💗💗💗💗🤍\n🤍🤍💗💗💗💗💗🤍🤍\n🤍🤍🤍💗💗💗🤍🤍🤍\n🤍🤍🤍🤍❤️🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍💗💗🤍💗💗🤍🤍\n🤍💗💗💗💗💗💗💗🤍\n🤍💗💗💗💗💗💗💗🤍\n🤍🤍💗💗💗💗💗🤍🤍\n🤍🤍🤍💗💗💗🤍🤍🤍\n🤍🤍🤍🤍💗🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍❤️‍🩹❤️‍🩹🤍❤️‍🩹❤️‍🩹🤍🤍\n🤍💗💗💗💗💗💗💗🤍\n🤍💗💗💗💗💗💗💗🤍\n🤍🤍💗💗💗💗💗🤍🤍\n🤍🤍🤍💗💗💗🤍🤍🤍\n🤍🤍🤍🤍💗🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍❤️‍🩹❤️‍🩹🤍❤️‍🩹❤️‍🩹🤍🤍\n🤍❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹🤍\n🤍💗💗💗💗💗💗💗🤍\n🤍🤍💗💗💗💗💗🤍🤍\n🤍🤍🤍💗💗💗🤍🤍🤍\n🤍🤍🤍🤍💗🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍❤️‍🩹❤️‍🩹🤍❤️‍🩹❤️‍🩹🤍🤍\n🤍❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹🤍\n🤍❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹🤍\n🤍🤍💗💗💗💗💗🤍🤍\n🤍🤍🤍💗💗💗🤍🤍🤍\n🤍🤍🤍🤍💗🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍❤️‍🩹❤️‍🩹🤍❤️‍🩹❤️‍🩹🤍🤍\n🤍❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹🤍\n🤍❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹🤍\n🤍🤍❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹🤍🤍\n🤍🤍🤍❤️‍🩹❤️‍🩹❤️‍🩹🤍🤍🤍\n🤍🤍🤍🤍💗🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍❤️‍🩹❤️‍🩹🤍❤️‍🩹❤️‍🩹🤍🤍\n🤍❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹🤍\n🤍❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹🤍\n🤍🤍❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹❤️‍🩹🤍🤍\n🤍🤍🤍❤️‍🩹❤️‍🩹❤️‍🩹🤍🤍🤍\n🤍🤍🤍🤍❤️‍🩹🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🍀🍀🍀🍀🍀🍀🍀🍀🍀\n🤍🤍💗💗🤍💗💗🤍🤍\n🤍💗💗💗💗💗💗💗🤍\n🤍💗💗💗💗💗💗💗🤍\n🤍🤍💗💗💗💗💗🤍🤍\n🤍🤍🤍💗💗💗🤍🤍🤍\n🤍🤍🤍🤍💗🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🍀🍀🍀🍀🍀🍀🍀🍀🍀\n🍀🍀💖💖🍀💖💖🍀🍀\n🤍💗💗💗💗💗💗💗🤍\n🤍💗💗💗💗💗💗💗🤍\n🤍🤍💗💗💗💗💗🤍🤍\n🤍🤍🤍💗💗💗🤍🤍🤍\n🤍🤍🤍🤍💗🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍", 
        "🍀🍀🍀🍀🍀🍀🍀🍀🍀\n🍀🍀💖💖🍀💖💖🍀🍀\n🍀💖💖💖💖💖💖💖🍀\n🤍💗💗💗💗💗💗💗🤍\n🤍🤍💗💗💗💗💗🤍🤍\n🤍🤍🤍💗💗💗🤍🤍🤍\n🤍🤍🤍🤍💗🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",  
        "🍀🍀🍀🍀🍀🍀🍀🍀🍀\n🍀🍀💖💖🍀💖💖🍀🍀\n🍀💖💖💖💖💖💖💖🍀\n🍀💖💖💖💖💖💖💖🍀\n🤍🤍💗💗💗💗💗🤍🤍\n🤍🤍🤍💗💗💗🤍🤍🤍\n🤍🤍🤍🤍💗🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🍀🍀🍀🍀🍀🍀🍀🍀🍀\n🍀🍀💖💖🍀💖💖🍀🍀\n🍀💖💖💖💖💖💖💖🍀\n🍀💖💖💖💖💖💖💖🍀\n🍀🍀💖💖💖💖💖🍀🍀\n🤍🤍🤍💗💗💗🤍🤍🤍\n🤍🤍🤍🤍💗🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",  
        "🍀🍀🍀🍀🍀🍀🍀🍀🍀\n🍀🍀💖💖🍀💖💖🍀🍀\n🍀💖💖💖💖💖💖💖🍀\n🍀💖💖💖💖💖💖💖🍀\n🍀🍀💖💖💖💖💖🍀🍀\n🍀🍀🍀💖💖💖🍀🍀🍀\n🤍🤍🤍🤍💗🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍",
        "🍀🍀🍀🍀🍀🍀🍀🍀🍀\n🍀🍀💖💖🍀💖💖🍀🍀\n🍀💖💖💖💖💖💖💖🍀\n🍀💖💖💖💖💖💖💖🍀\n🍀🍀💖💖💖💖💖🍀🍀\n🍀🍀🍀💖💖💖🍀🍀🍀\n🍀🍀🍀🍀💖🍀🍀🍀🍀\n🤍🤍🤍🤍🤍🤍🤍🤍🤍", 
        "🍀🍀🍀🍀🍀🍀🍀🍀🍀\n🍀🍀💖💖🍀💖💖🍀🍀\n🍀💖💖💖💖💖💖💖🍀\n🍀💖💖💖💖💖💖💖🍀\n🍀🍀💖💖💖💖💖🍀🍀\n🍀🍀🍀💖💖💖🍀🍀🍀\n🍀🍀🍀🍀💖🍀🍀🍀🍀\n🍀🍀🍀🍀🍀🍀🍀🍀🍀", 
        "🌴🌴🌴🌴🌴🌴🌴🌴🌴\n🍀🍀💖💖🍀💖💖🍀🍀\n🍀💖💖💖💖💖💖💖🍀\n🍀💖💖💖💖💖💖💖🍀\n🍀🍀💖💖💖💖💖🍀🍀\n🍀🍀🍀💖💖💖🍀🍀🍀\n🍀🍀🍀🍀💖🍀🍀🍀🍀\n🍀🍀🍀🍀🍀🍀🍀🍀🍀",  
        "🌴🌴🌴🌴🌴🌴🌴🌴🌴\n🌴🌴🐼🐼🌴🐼🐼🌴🌴\n🍀💖💖💖💖💖💖💖🍀\n🍀💖💖💖💖💖💖💖🍀\n🍀🍀💖💖💖💖💖🍀🍀\n🍀🍀🍀💖💖💖🍀🍀🍀\n🍀🍀🍀🍀💖🍀🍀🍀🍀\n🍀🍀🍀🍀🍀🍀🍀🍀🍀", 
        "🌴🌴🌴🌴🌴🌴🌴🌴🌴\n🌴🌴🐼🐼🌴🐼🐼🌴🌴\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🍀💖💖💖💖💖💖💖🍀\n🍀🍀💖💖💖💖💖🍀🍀\n🍀🍀🍀💖💖💖🍀🍀🍀\n🍀🍀🍀🍀💖🍀🍀🍀🍀\n🍀🍀🍀🍀🍀🍀🍀🍀🍀",  
        "🌴🌴🌴🌴🌴🌴🌴🌴🌴\n🌴🌴🐼🐼🌴🐼🐼🌴🌴\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🍀🍀💖💖💖💖💖🍀🍀\n🍀🍀🍀💖💖💖🍀🍀🍀\n🍀🍀🍀🍀💖🍀🍀🍀🍀\n🍀🍀🍀🍀🍀🍀🍀🍀🍀",  
        "🌴🌴🌴🌴🌴🌴🌴🌴🌴\n🌴🌴🐼🐼🌴🐼🐼🌴🌴\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🌴🌴🐼🐼🐼🐼🐼🌴🌴\n🍀🍀🍀💖💖💖🍀🍀🍀\n🍀🍀🍀🍀💖🍀🍀🍀🍀\n🍀🍀🍀🍀🍀🍀🍀🍀🍀",  
        "🌴🌴🌴🌴🌴🌴🌴🌴🌴\n🌴🌴🐼🐼🌴🐼🐼🌴🌴\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🌴🌴🐼🐼🐼🐼🐼🌴🌴\n🌴🌴🌴🐼🐼🐼🌴🌴🌴\n🍀🍀🍀🍀💖🍀🍀🍀🍀\n🍀🍀🍀🍀🍀🍀🍀🍀🍀",  
        "🌴🌴🌴🌴🌴🌴🌴🌴🌴\n🌴🌴🐼🐼🌴🐼🐼🌴🌴\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🌴🌴🐼🐼🐼🐼🐼🌴🌴\n🌴🌴🌴🐼🐼🐼🌴🌴🌴\n🌴🌴🌴🌴🐼🌴🌴🌴🌴\n🍀🍀🍀🍀🍀🍀🍀🍀🍀", 
        "🌴🌴🌴🌴🌴🌴🌴🌴🌴\n🌴🌴🐼🐼🌴🐼🐼🌴🌴\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🌴🌴🐼🐼🐼🐼🐼🌴🌴\n🌴🌴🌴🐼🐼🐼🌴🌴🌴\n🌴🌴🌴🌴🐼🌴🌴🌴🌴\n🌴🌴🌴🌴🌴🌴🌴🌴🌴",
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n🌴🌴🐼🐼🌴🐼🐼🌴🌴\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🌴🌴🌴🐼🐼🐼🌴🌴🌴\n🌴🌴🌴🌴🐼🌴🌴🌴🌴\n🌴🌴🌴🌴🌴🌴🌴🌴🌴",
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️💟💟☁️💟💟☁️☁️\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🌴🌴🌴🐼🐼🐼🌴🌴🌴\n🌴🌴🌴🌴🐼🌴🌴🌴🌴\n🌴🌴🌴🌴🌴🌴🌴🌴🌴", 
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️💟💟☁️💟💟☁️☁️\n☁️💟💟💟💟💟💟💟☁️\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🌴🌴🌴🐼🐼🐼🌴🌴🌴\n🌴🌴🌴🌴🐼🌴🌴🌴🌴\n🌴🌴🌴🌴🌴🌴🌴🌴🌴",  
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️💟💟☁️💟💟☁️☁️\n☁️💟💟💟💟💟💟💟☁️\n☁️💟💟💟💟💟💟💟☁️\n🌴🐼🐼🐼🐼🐼🐼🐼🌴\n🌴🌴🌴🐼🐼🐼🌴🌴🌴\n🌴🌴🌴🌴🐼🌴🌴🌴🌴\n🌴🌴🌴🌴🌴🌴🌴🌴🌴",   
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️💟💟☁️💟💟☁️☁️\n☁️💟💟💟💟💟💟💟☁️\n☁️💟💟💟💟💟💟💟☁️\n☁️☁️💟💟💟💟💟☁️☁️\n🌴🌴🌴🐼🐼🐼🌴🌴🌴\n🌴🌴🌴🌴🐼🌴🌴🌴🌴\n🌴🌴🌴🌴🌴🌴🌴🌴🌴",  
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️💟💟☁️💟💟☁️☁️\n☁️💟💟💟💟💟💟💟☁️\n☁️💟💟💟💟💟💟💟☁️\n☁️☁️💟💟💟💟💟☁️☁️\n☁️☁️☁️💟💟💟☁️☁️☁️\n🌴🌴🌴🌴🐼🌴🌴🌴🌴\n🌴🌴🌴🌴🌴🌴🌴🌴🌴",   
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️💟💟☁️💟💟☁️☁️\n☁️💟💟💟💟💟💟💟☁️\n☁️💟💟💟💟💟💟💟☁️\n☁️☁️💟💟💟💟💟☁️☁️\n☁️☁️☁️💟💟💟☁️☁️☁️\n☁️☁️☁️☁️💟☁️☁️☁️☁️\n🌴🌴🌴🌴🌴🌴🌴🌴🌴",   
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️💟💟☁️💟💟☁️☁️\n☁️💟💟💟💟💟💟💟☁️\n☁️💟💟💟💟💟💟💟☁️\n☁️☁️💟💟💟💟💟☁️☁️\n☁️☁️☁️💟💟💟☁️☁️☁️\n☁️☁️☁️☁️💟☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️",  
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️💟💟💟💟💟💟💟☁️\n☁️💟💟💟💟💟💟💟☁️\n☁️☁️💟💟💟💟💟☁️☁️\n☁️☁️☁️💟💟💟☁️☁️☁️\n☁️☁️☁️☁️💟☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️",  
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️💟💟💟💟💟💟💟☁️\n☁️☁️💟💟💟💟💟☁️☁️\n☁️☁️☁️💟💟💟☁️☁️☁️\n☁️☁️☁️☁️💟☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️",  
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️💟💟💟💟💟☁️☁️\n☁️☁️☁️💟💟💟☁️☁️☁️\n☁️☁️☁️☁️💟☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️",  
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️💟💟💟☁️☁️☁️\n☁️☁️☁️☁️💟☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️", 
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️💟☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️", 
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️",   
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️",
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️",
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️",
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️",
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️",
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️",
        "☁️☁️☁️☁️☁️☁️☁️☁️☁️",
        "❤️❤️i☁️☁️☁️☁️☁️☁️☁️☁️",
        "❤️❤️i❤️❤️love☁️☁️☁️☁️☁️☁️", 
        "❤️❤️i❤️❤️love❤️❤️you☁️☁️☁️☁️",   
        "❤️❤️i❤️❤️love❤️❤️you❤️❤️forever☁️☁️",  
        "❤️❤️i❤️❤️love❤️❤️you❤️❤️forever❤️❤️",







        # 
    ]

    for stage in stages:
        await event.edit(stage)  # Обновление текущего сообщения
        await asyncio.sleep(0.3)  # Задержка в 0.3 секунды между кадрами
        

   
    #await message.edit("Финальная стадия ❤️")  # Финальный текст

@client.on(events.NewMessage(pattern=r'/support'))
async def support_author(event):
    """Команда для поддержки автора (номер карты)."""
    try:
        if not event.out:
            return

        support_message = """
        Если вам понравился бот и вы хотите поддержать автора, вот номер карты:
        Номер карты: 9112 3800 5275 9059
        Благодарю за вашу поддержку!
        """
        await event.reply(support_message, parse_mode='html')
    except Exception as e:
        print(f"Ошибка при отправке информации для поддержки: {e}")
        await event.reply("<b>Произошла ошибка при отправке информации.</b>", parse_mode='html')


@client.on(events.NewMessage(pattern=r'/update'))
async def update_script(event):
    """Команда для обновления скрипта с GitHub и его автоматического перезапуска."""
    try:
        if not event.out:
            return

        response = requests.get(GITHUB_RAW_URL)

        if response.status_code == 200:
            current_file = os.path.abspath(__file__)
            with open(current_file, 'w', encoding='utf-8') as f:
                f.write(response.text)

            await event.reply("<b>Скрипт успешно обновлен. Перезапуск...</b>", parse_mode='html')

            # Перезапуск скрипта
            os.execv(sys.executable, [sys.executable, current_file])
        else:
            await event.reply("<b>Не удалось получить обновление. Проверьте URL и соединение с GitHub.</b>", parse_mode='html')

    except Exception as e:
        print(f"Ошибка при обновлении: {e}")
        await event.reply("<b>Произошла ошибка при обновлении скрипта.</b>", parse_mode='html')


async def main():
    print(f"Запуск main()\nВерсия скрипта: {SCRIPT_VERSION}")
    check_for_updates()
    await client.start(phone=PHONE_NUMBER)
    print("Скрипт успешно запущен! Автор @mshkago Для использования:")
    print("- Напишите в чате /p (текст) для анимации печатания.")
    print("- Используйте /s (задержка) для изменения скорости печатания.")
    print("- Используйте /c (символ) для изменения символа курсора анимации.")
    print("= Используйте /sp (текст) (количество) (скорость отправки).")
    print("- Используйте /update для обновления скрипта с GitHub.")
    print("- Используйте /support для поддержки автора.")
    print("- Используйте сердечки для создания анимация сердца")
    await client.run_until_disconnected()


if __name__ == "__main__":
    check_for_updates()
    asyncio.run(main())
