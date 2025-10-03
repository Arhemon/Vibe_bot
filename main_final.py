import os
import time
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
import json

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutoVisaChecker:
    def __init__(self):
        self.site_url = "https://services.vfsglobal.by/"
        self.recipient_email = "gannibal231@gmail.com"
        
        # Email настройки
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        
        # Интервал проверки (3 минуты чтобы токены не истекали)
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '180'))
        
        self.notification_sent = False
        self.driver = None
    
    def init_browser(self):
        """Инициализирует браузер с МАКСИМАЛЬНЫМ обходом Cloudflare"""
        try:
            logger.info("🔧 Настраиваю стелс-браузер...")
            
            options = uc.ChromeOptions()
            
            # Базовые параметры
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--window-size=1920,1080')
            
            # Антидетект параметры
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-features=IsolateOrigins,site-per-process')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument('--disable-webgl')
            options.add_argument('--disable-javascript-harmony-shipping')
            
            # User agent как у реального пользователя
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36')
            
            # Создаем драйвер
            logger.info("🚀 Запускаю undetected-chromedriver...")
            self.driver = uc.Chrome(
                options=options,
                headless=True,
                use_subprocess=False,
                version_main=141
            )
            
            # Применяем selenium-stealth для дополнительной маскировки
            logger.info("🎭 Применяю stealth плагин...")
            stealth(self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            
            # Устанавливаем дополнительные свойства через JavaScript
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
            })
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Браузер готов (FULL STEALTH MODE)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка браузера: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_fresh_tokens_and_check_slots(self):
        """ГЛАВНАЯ ФУНКЦИЯ: Обновляет токены И сразу проверяет слоты"""
        try:
            logger.info("🔄 Открываю браузер для получения токенов...")
            
            # Создаем новый браузер
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            
            if not self.init_browser():
                return []
            
            logger.info("🌐 Захожу на сайт...")
            self.driver.get(self.site_url)
            
            # Ждем прохождения Cloudflare challenge
            logger.info("⏳ Жду прохождения Cloudflare challenge...")
            time.sleep(10)
            
            # Проверяем прошли ли Cloudflare
            page_source = self.driver.page_source.lower()
            if "sorry, you have been blocked" in page_source or "cloudflare" in page_source:
                logger.warning("⚠️ Cloudflare блокирует, жду еще 10 сек...")
                time.sleep(10)
                
                # Проверяем снова
                page_source = self.driver.page_source.lower()
                if "sorry, you have been blocked" in page_source:
                    logger.error("❌ Cloudflare НЕ ПРОПУСТИЛ!")
                    logger.info("💡 Попробую обновить страницу...")
                    self.driver.refresh()
                    time.sleep(10)
            else:
                logger.info("✅ Cloudflare пройден!")
            
            time.sleep(3)
            
            # Закрываем popup
            try:
                btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                )
                btn.click()
                time.sleep(2)
            except:
                pass
            
            # Ждем Angular
            time.sleep(4)
            
            # Заполняем форму - пробуем несколько способов
            logger.info("📝 Заполняю форму...")
            wait = WebDriverWait(self.driver, 30)
            
            try:
                # Сохраняем HTML для отладки
                logger.info("DEBUG: Проверяю наличие элементов на странице...")
                page_source = self.driver.page_source
                if 'mat-select' in page_source:
                    logger.info("DEBUG: mat-select элементы найдены в HTML")
                else:
                    logger.warning("DEBUG: mat-select НЕ НАЙДЕНЫ в HTML!")
                    logger.info("DEBUG: Скорее всего Angular не загрузился, жду еще...")
                    time.sleep(10)
                
                # Используем JavaScript для заполнения (Angular не загружается в headless)
                logger.info("📝 Заполняю форму через JavaScript...")
                
                # Получаем cookies из браузера
                cookies_dict = {}
                for cookie in self.driver.get_cookies():
                    cookies_dict[cookie['name']] = cookie['value']
                
                cookies_str = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
                logger.info(f"✅ Получено {len(cookies_dict)} cookies")
                
                # Делаем запрос к API напрямую используя cookies браузера
                api_url = "https://lift-api.vfsglobal.by/appointment/CheckIsSlotAvailable"
                
                results = []
                
                # Проверяем оба типа виз
                for visa_info in [
                    {"code": "BLRVI", "name": "D - visa"},
                    {"code": "BLRVPL", "name": "D visa - Premium Lounge"}
                ]:
                    logger.info(f"\n📋 Проверяю {visa_info['name']}...")
                    
                    payload = {
                        "countryCode": "blr",
                        "loginUser": "Gannibal231@gmail.com",
                        "missionCode": "bgr",
                        "payCode": "",
                        "roleName": "Individual",
                        "vacCode": "BLRVIT",
                        "visaCategoryCode": visa_info['code']
                    }
                    
                    headers = {
                        'Content-Type': 'application/json;charset=UTF-8',
                        'Accept': 'application/json, text/plain, */*',
                        'Origin': 'https://services.vfsglobal.by',
                        'Referer': 'https://services.vfsglobal.by/',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Cookie': cookies_str
                    }
                    
                    # Делаем запрос через requests с cookies от браузера!
                    try:
                        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
                        logger.info(f"  API Статус: {response.status_code}")
                        
                        if response.status_code == 200:
                            data = response.json()
                            logger.info(f"  Ответ API: {data}")
                            
                            # Проверяем ответ
                            if 'error' in data and data['error'].get('code') == 1035:
                                logger.info(f"  ❌ {visa_info['name']}: Слотов нет (error 1035)")
                                results.append({'visa': visa_info['name'], 'available': False})
                            elif data.get('earliestDate') or (data.get('earliestSlotLists') and len(data['earliestSlotLists']) > 0):
                                logger.info(f"  🎉 {visa_info['name']}: СЛОТ НАЙДЕН!")
                                logger.info(f"  Данные: {data}")
                                results.append({'visa': visa_info['name'], 'available': True, 'data': data})
                            else:
                                logger.info(f"  ❓ {visa_info['name']}: Неясный ответ: {data}")
                                results.append({'visa': visa_info['name'], 'available': False})
                        else:
                            logger.warning(f"  ⚠️ Ошибка API: {response.status_code}")
                            results.append({'visa': visa_info['name'], 'available': False})
                    
                    except Exception as e:
                        logger.error(f"  ❌ Ошибка запроса: {e}")
                        results.append({'visa': visa_info['name'], 'available': False})
                    
                    time.sleep(2)
                
                logger.info("✅ Проверка через API завершена")
                return results
                
            except Exception as e:
                logger.error(f"❌ Ошибка заполнения формы: {e}")
                # Делаем скриншот для отладки
                try:
                    screenshot = f"error_{datetime.now().strftime('%H%M%S')}.png"
                    self.driver.save_screenshot(screenshot)
                    logger.info(f"📸 Скриншот: {screenshot}")
                except:
                    pass
                return []
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
            return []
        finally:
            # Закрываем браузер
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
    
    def send_email(self, visa_type):
        """Отправляет email"""
        if not self.sender_email or not self.sender_password:
            logger.error("Email не настроен!")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = f'🎉 СЛОТ ДОСТУПЕН: {visa_type}!'
            
            body = f"""
            <html><body>
                <h1 style="color: green;">СЛОТ НАЙДЕН!</h1>
                <p><strong>Время:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
                <p><strong>Виза:</strong> {visa_type}</p>
                <h2 style="color: red;">БЫСТРЕЕ ЗАПИСЫВАЙТЕСЬ!</h2>
                <p><a href="https://services.vfsglobal.by/" style="font-size: 20px; background: green; color: white; padding: 15px;">→ ЗАПИСАТЬСЯ СЕЙЧАС</a></p>
            </body></html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email отправлен на {self.recipient_email}!")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка email: {e}")
            return False
    
    def run(self):
        """Главный цикл - ВСЁ ЧЕРЕЗ БРАУЗЕР"""
        logger.info("=" * 70)
        logger.info("🤖 ПОЛНОСТЬЮ АВТОМАТИЧЕСКИЙ БОТ (ЧЕРЕЗ БРАУЗЕР)")
        logger.info("=" * 70)
        logger.info(f"Интервал: {self.check_interval} сек")
        logger.info(f"Email: {self.recipient_email}")
        logger.info("=" * 70)
        logger.info("")
        
        while True:
            try:
                current_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
                logger.info(f"\n{'='*70}")
                logger.info(f"🔍 ПРОВЕРКА [{current_time}]")
                logger.info(f"{'='*70}\n")
                
                # Получаем результаты через браузер (токены обновляются автоматически!)
                results = self.get_fresh_tokens_and_check_slots()
                
                slot_found = False
                
                for result in results:
                    if result.get('available'):
                        slot_found = True
                        logger.info(f"\n🎉🎉🎉 НАЙДЕН СЛОТ: {result['visa']} 🎉🎉🎉\n")
                        
                        if not self.notification_sent:
                            self.send_email(result['visa'])
                            self.notification_sent = True
                
                if not slot_found:
                    logger.info("\n❌ Слотов нет")
                    self.notification_sent = False
                
                logger.info(f"\n⏰ Следующая проверка через {self.check_interval} сек")
                logger.info(f"{'='*70}\n")
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("\n🛑 Остановлен")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле: {e}")
                logger.info("Пробую снова через 60 сек...")
                time.sleep(60)

if __name__ == "__main__":
    checker = AutoVisaChecker()
    checker.run()

