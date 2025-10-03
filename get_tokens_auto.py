#!/usr/bin/env python3
"""
Автоматическое извлечение токенов из браузера с помощью Selenium
"""
import os
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

def update_env_token(key, value):
    """Обновляет значение переменной в .env файле"""
    env_path = '.env'
    
    if not os.path.exists(env_path):
        print(f"❌ Файл {env_path} не найден!")
        return False
    
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем строку с ключом
    pattern = f'^{key}=.*$'
    replacement = f'{key}={value}'
    
    if re.search(pattern, content, re.MULTILINE):
        # Заменяем существующее значение
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    else:
        print(f"❌ Ключ {key} не найден в .env")
        return False

def extract_tokens():
    """Извлекает токены из браузера"""
    print("=" * 70)
    print("🔐 АВТОМАТИЧЕСКОЕ ИЗВЛЕЧЕНИЕ ТОКЕНОВ")
    print("=" * 70)
    print()
    
    # Включаем логирование Network в Chrome
    caps = DesiredCapabilities.CHROME
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}
    
    chrome_options = Options()
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = None
    
    try:
        print("🌐 Открываю браузер...")
        driver = webdriver.Chrome(options=chrome_options)
        
        print("📝 Открываю сайт VFS Global...")
        driver.get("https://services.vfsglobal.by/")
        
        print()
        print("=" * 70)
        print("⏸️  ПАУЗА ДЛЯ РУЧНОЙ ПРОВЕРКИ СЛОТОВ")
        print("=" * 70)
        print()
        print("ИНСТРУКЦИЯ:")
        print("1. В открывшемся браузере заполните форму:")
        print("   - Country: Belarus")
        print("   - Mission: Bulgaria")
        print("   - VAC: BLRVIT")
        print("   - Visa Category: BLRVPL или BLRVI")
        print()
        print("2. Нажмите кнопку 'Continue' или 'Check Slots'")
        print()
        print("3. Дождитесь ответа от сервера")
        print()
        print("4. Вернитесь в терминал и нажмите Enter")
        print()
        input("👉 Нажмите Enter когда выполните запрос... ")
        
        print()
        print("🔍 Ищу токены в логах браузера...")
        
        # Получаем логи производительности
        logs = driver.get_log('performance')
        
        authorize_token = None
        clientsource_token = None
        cookies_str = None
        
        # Ищем запрос к CheckIsSlotAvailable
        for entry in logs:
            try:
                import json
                log = json.loads(entry['message'])
                message = log.get('message', {})
                method = message.get('method', '')
                
                # Ищем запрос
                if method == 'Network.requestWillBeSent':
                    params = message.get('params', {})
                    request = params.get('request', {})
                    url = request.get('url', '')
                    
                    if 'CheckIsSlotAvailable' in url:
                        headers = request.get('headers', {})
                        
                        # Извлекаем токены
                        if 'authorize' in headers:
                            authorize_token = headers['authorize']
                        
                        if 'clientsource' in headers:
                            clientsource_token = headers['clientsource']
                        
                        if 'cookie' in headers or 'Cookie' in headers:
                            cookies_str = headers.get('cookie') or headers.get('Cookie')
                        
                        if authorize_token and clientsource_token:
                            break
            except:
                continue
        
        print()
        print("=" * 70)
        print("📊 РЕЗУЛЬТАТЫ")
        print("=" * 70)
        
        if authorize_token:
            print(f"✅ AUTHORIZE найден ({len(authorize_token)} символов)")
        else:
            print("❌ AUTHORIZE не найден")
        
        if clientsource_token:
            print(f"✅ CLIENTSOURCE найден ({len(clientsource_token)} символов)")
        else:
            print("❌ CLIENTSOURCE не найден")
        
        if cookies_str:
            print(f"✅ COOKIES найдены ({len(cookies_str)} символов)")
        else:
            print("❌ COOKIES не найдены")
        
        if authorize_token and clientsource_token and cookies_str:
            print()
            print("=" * 70)
            print("💾 ОБНОВЛЯЮ .ENV ФАЙЛ")
            print("=" * 70)
            
            update_env_token('AUTHORIZE', authorize_token)
            update_env_token('CLIENTSOURCE', clientsource_token)
            update_env_token('COOKIES', cookies_str)
            
            print()
            print("🎉 Токены успешно обновлены в .env!")
            print()
            print("Теперь запустите бота:")
            print("  python main.py")
            return True
        else:
            print()
            print("❌ Не все токены найдены.")
            print()
            print("Возможные причины:")
            print("- Запрос к CheckIsSlotAvailable не был выполнен")
            print("- Нужно подождать дольше после нажатия кнопки")
            print("- Попробуйте запустить скрипт еще раз")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if driver:
            print()
            input("👉 Нажмите Enter чтобы закрыть браузер... ")
            driver.quit()
            print("✅ Браузер закрыт")

if __name__ == "__main__":
    extract_tokens()

