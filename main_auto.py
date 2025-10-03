import os
import time
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutoTokenVisaChecker:
    def __init__(self):
        self.api_url = "https://lift-api.vfsglobal.by/appointment/CheckIsSlotAvailable"
        self.site_url = "https://services.vfsglobal.by/"
        self.recipient_email = "gannibal231@gmail.com"
        
        # Email настройки
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        
        # Интервал проверки
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '300'))
        
        # Токены (будут обновляться автоматически)
        self.authorize = ''
        self.clientsource = ''
        self.cookies = ''
        self.route = 'blr/en/bgr'
        
        # Session для запросов
        self.session = requests.Session()
        
        # Варианты виз для проверки
        self.visa_configs = [
            {"code": "BLRVPL", "name": "Polish visa (национальная)"},
            {"code": "BLRVI", "name": "Visitor/Short-term visa"}
        ]
        
        self.payloads = [
            {
                "countryCode": "blr",
                "loginUser": "Gannibal231@gmail.com",
                "missionCode": "bgr",
                "payCode": "",
                "roleName": "Individual",
                "vacCode": "BLRVIT",
                "visaCategoryCode": "BLRVPL"
            },
            {
                "countryCode": "blr",
                "loginUser": "Gannibal231@gmail.com",
                "missionCode": "bgr",
                "payCode": "",
                "roleName": "Individual",
                "vacCode": "BLRVIT",
                "visaCategoryCode": "BLRVI"
            }
        ]
        
        self.notification_sent = False
        self.driver = None
    
    def init_browser(self):
        """Инициализирует headless браузер Chrome"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Включаем логирование Network для перехвата токенов
            chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Браузер инициализирован")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации браузера: {e}")
            return False
    
    def refresh_tokens_via_browser(self):
        """Обновляет токены через браузер (автоматически)"""
        try:
            logger.info("🔄 Обновляю токены через браузер...")
            
            if not self.driver:
                if not self.init_browser():
                    return False
            
            # Открываем сайт
            self.driver.get(self.site_url)
            time.sleep(5)
            
            # Закрываем cookie popup
            try:
                cookie_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                )
                cookie_btn.click()
                time.sleep(2)
            except:
                pass
            
            # Заполняем форму автоматически через JavaScript
            logger.info("📝 Заполняю форму автоматически...")
            
            # Скрипт для автоматического заполнения Angular Material формы
            fill_script = """
            // Функция для клика и выбора опции в mat-select
            function selectMatOption(selectId, optionText) {
                const select = document.querySelector(selectId);
                if (select) {
                    select.click();
                    setTimeout(() => {
                        const options = document.querySelectorAll('mat-option');
                        for (let opt of options) {
                            if (opt.innerText.includes(optionText)) {
                                opt.click();
                                break;
                            }
                        }
                    }, 500);
                }
            }
            
            setTimeout(() => selectMatOption('[formcontrolname="countryCode"]', 'Belarus'), 1000);
            setTimeout(() => selectMatOption('[formcontrolname="missionCode"]', 'Bulgaria'), 2000);
            setTimeout(() => selectMatOption('[formcontrolname="vacCode"]', 'VIT'), 3000);
            setTimeout(() => selectMatOption('[formcontrolname="visaCategoryCode"]', 'PL'), 4000);
            
            // Нажимаем кнопку Continue
            setTimeout(() => {
                const btn = document.querySelector('button[type="submit"]');
                if (btn) btn.click();
            }, 5000);
            """
            
            self.driver.execute_script(fill_script)
            time.sleep(8)
            
            # Извлекаем токены из Network logs
            logger.info("🔍 Извлекаю токены из логов браузера...")
            
            logs = self.driver.get_log('performance')
            
            for entry in logs:
                try:
                    log = json.loads(entry['message'])
                    message = log.get('message', {})
                    
                    if message.get('method') == 'Network.requestWillBeSent':
                        params = message.get('params', {})
                        request = params.get('request', {})
                        url = request.get('url', '')
                        
                        if 'CheckIsSlotAvailable' in url:
                            headers = request.get('headers', {})
                            
                            if 'authorize' in headers:
                                self.authorize = headers['authorize']
                                logger.info(f"✅ authorize получен ({len(self.authorize)} символов)")
                            
                            if 'clientsource' in headers:
                                self.clientsource = headers['clientsource']
                                logger.info(f"✅ clientsource получен ({len(self.clientsource)} символов)")
                            
                            if 'cookie' in headers or 'Cookie' in headers:
                                self.cookies = headers.get('cookie') or headers.get('Cookie')
                                logger.info(f"✅ cookies получены ({len(self.cookies)} символов)")
                            
                            if self.authorize and self.clientsource:
                                logger.info("✅ Токены успешно обновлены!")
                                return True
                except:
                    continue
            
            logger.warning("⚠️ Токены не найдены в логах, используем cookies из session")
            
            # Получаем cookies из драйвера
            cookies_list = []
            for cookie in self.driver.get_cookies():
                cookies_list.append(f"{cookie['name']}={cookie['value']}")
            self.cookies = "; ".join(cookies_list)
            
            if self.cookies:
                logger.info(f"✅ Cookies получены из session ({len(self.cookies)} символов)")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления токенов: {e}")
            return False
    
    def check_slots(self, payload):
        """Проверяет слоты через API"""
        try:
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Origin': 'https://services.vfsglobal.by',
                'Referer': 'https://services.vfsglobal.by/',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            if self.authorize:
                headers['authorize'] = self.authorize
            if self.clientsource:
                headers['clientsource'] = self.clientsource
            if self.route:
                headers['route'] = self.route
            if self.cookies:
                headers['Cookie'] = self.cookies
            
            response = self.session.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"Запрос отправлен. Статус: {response.status_code}")
            
            if response.status_code == 401 or response.status_code == 403:
                logger.warning("⚠️ Токены устарели")
                return None, 'AUTH_REQUIRED'
            
            if response.status_code == 200:
                data = response.json()
                
                if 'error' in data and data['error'].get('code') == 1035:
                    return False, None
                
                if data.get('earliestDate') or (data.get('earliestSlotLists') and len(data['earliestSlotLists']) > 0):
                    return True, data
                
                if 'error' not in data or data['error'].get('code') != 1035:
                    return True, data
            
            return False, None
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки: {e}")
            return False, None
    
    def send_email_notification(self, slot_data, visa_type):
        """Отправляет email уведомление"""
        if not self.sender_email or not self.sender_password:
            logger.error("Email настройки не заданы!")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = '🎉 ДОСТУПЕН СЛОТ ДЛЯ ВИЗЫ!'
            
            body = f"""
            <html>
            <body>
                <h2>Отличные новости! Появился свободный слот!</h2>
                <p><strong>Время:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
                <p><strong>Тип визы:</strong> {visa_type}</p>
                <h3>Детали:</h3>
                <pre>{json.dumps(slot_data, indent=2, ensure_ascii=False)}</pre>
                <p style="color: red; font-weight: bold; font-size: 18px;">
                    ⚡ БЫСТРЕЕ ПЕРЕХОДИТЕ И ЗАПИСЫВАЙТЕСЬ! ⚡
                </p>
                <p><a href="https://services.vfsglobal.by/">Перейти к записи</a></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email отправлен на {self.recipient_email}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка отправки email: {e}")
            return False
    
    def run(self):
        """Основной цикл с автоматическим обновлением токенов"""
        logger.info("=" * 70)
        logger.info("🤖 БОТ С АВТОМАТИЧЕСКИМ ОБНОВЛЕНИЕМ ТОКЕНОВ")
        logger.info("=" * 70)
        logger.info(f"Интервал проверки: {self.check_interval} сек")
        logger.info(f"Email: {self.recipient_email}")
        
        try:
            while True:
                current_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
                logger.info(f"\n{'='*70}")
                logger.info(f"🔍 ПРОВЕРКА СЛОТОВ [{current_time}]")
                logger.info(f"{'='*70}")
                
                # Обновляем токены перед проверкой
                logger.info("⏰ Обновление токенов за 5 секунд до проверки...")
                time.sleep(5)
                
                if not self.refresh_tokens_via_browser():
                    logger.warning("⚠️ Не удалось обновить токены, пробую с текущими...")
                
                slot_found = False
                
                for i, payload in enumerate(self.payloads, 1):
                    visa_type = payload['visaCategoryCode']
                    logger.info(f"\n📋 Проверка {i}: {visa_type}")
                    
                    is_available, slot_data = self.check_slots(payload)
                    
                    if is_available:
                        slot_found = True
                        logger.info(f"🎉 НАЙДЕН СЛОТ для {visa_type}!")
                        
                        if not self.notification_sent:
                            self.send_email_notification(slot_data, visa_type)
                            self.notification_sent = True
                        else:
                            logger.info("📧 Уведомление уже отправлено")
                    
                    time.sleep(2)
                
                if not slot_found:
                    logger.info("\n❌ Слоты недоступны")
                    self.notification_sent = False
                
                logger.info(f"\n⏰ Следующая проверка через {self.check_interval} сек")
                logger.info(f"{'='*70}\n")
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Бот остановлен")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("✅ Браузер закрыт")

if __name__ == "__main__":
    checker = AutoTokenVisaChecker()
    checker.run()

