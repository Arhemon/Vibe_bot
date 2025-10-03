import os
import time
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleVisaChecker:
    def __init__(self):
        self.api_url = "https://lift-api.vfsglobal.by/appointment/CheckIsSlotAvailable"
        self.recipient_email = "gannibal231@gmail.com"
        
        # Email настройки
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        
        # Интервал проверки
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '180'))
        
        # Токены из переменных окружения
        self.authorize = os.getenv('AUTHORIZE', '')
        self.clientsource = os.getenv('CLIENTSOURCE', '')
        self.cookies = os.getenv('COOKIES', '')
        self.route = os.getenv('ROUTE', 'blr/en/bgr')
        
        # Session
        self.session = requests.Session()
        
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
    
    def check_slots(self, payload):
        """Проверяет слоты"""
        try:
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Origin': 'https://services.vfsglobal.by',
                'Referer': 'https://services.vfsglobal.by/',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
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
            
            logger.info(f"Статус: {response.status_code}")
            
            if response.status_code == 401 or response.status_code == 403:
                logger.warning(f"⚠️ Токены устарели! Обновите их через Railway Variables")
                logger.warning(f"   1. Локально: python get_tokens_auto.py")
                logger.warning(f"   2. Скопируйте AUTHORIZE, CLIENTSOURCE, COOKIES")
                logger.warning(f"   3. Обновите в Railway Dashboard → Variables")
                return False, None
            
            if response.status_code == 200:
                data = response.json()
                
                if 'error' in data and data['error'].get('code') == 1035:
                    logger.info("❌ Слоты недоступны")
                    return False, None
                
                if data.get('earliestDate') or (data.get('earliestSlotLists') and len(data['earliestSlotLists']) > 0):
                    logger.info(f"🎉 СЛОТ НАЙДЕН! {data}")
                    return True, data
                
                if 'error' not in data or data['error'].get('code') != 1035:
                    logger.info(f"🎉 Возможно слот найден! {data}")
                    return True, data
            
            return False, None
            
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return False, None
    
    def send_email(self, slot_data, visa_type):
        """Отправляет email"""
        if not self.sender_email or not self.sender_password:
            logger.error("Email не настроен!")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = '🎉 ДОСТУПЕН СЛОТ ДЛЯ ВИЗЫ!'
            
            body = f"""
            <html><body>
                <h2>Найден слот!</h2>
                <p><strong>Время:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
                <p><strong>Виза:</strong> {visa_type}</p>
                <p style="color: red; font-size: 20px;"><strong>БЫСТРЕЕ ЗАПИСЫВАЙТЕСЬ!</strong></p>
                <p><a href="https://services.vfsglobal.by/">Перейти к записи</a></p>
            </body></html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email отправлен!")
            return True
        except Exception as e:
            logger.error(f"❌ Email error: {e}")
            return False
    
    def run(self):
        """Главный цикл"""
        logger.info("=" * 70)
        logger.info("🤖 VISA SLOT CHECKER - ПРОСТАЯ ВЕРСИЯ")
        logger.info("=" * 70)
        logger.info(f"Интервал: {self.check_interval} сек")
        logger.info(f"Email: {self.recipient_email}")
        
        if not self.authorize or not self.clientsource:
            logger.warning("⚠️ ТОКЕНЫ НЕ ЗАДАНЫ!")
            logger.warning("   Добавьте в Railway Variables:")
            logger.warning("   - AUTHORIZE")
            logger.warning("   - CLIENTSOURCE")
            logger.warning("   - COOKIES")
        
        logger.info("")
        
        while True:
            try:
                current_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
                logger.info(f"\n{'='*70}")
                logger.info(f"🔍 ПРОВЕРКА [{current_time}]")
                logger.info(f"{'='*70}\n")
                
                slot_found = False
                
                for i, payload in enumerate(self.payloads, 1):
                    visa_type = payload['visaCategoryCode']
                    logger.info(f"📋 {i}. {visa_type}")
                    
                    is_available, data = self.check_slots(payload)
                    
                    if is_available:
                        slot_found = True
                        logger.info(f"🎉 СЛОТ!")
                        
                        if not self.notification_sent:
                            self.send_email(data, visa_type)
                            self.notification_sent = True
                    
                    time.sleep(2)
                
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
                logger.error(f"❌ Ошибка: {e}")
                time.sleep(60)

if __name__ == "__main__":
    checker = SimpleVisaChecker()
    checker.run()

