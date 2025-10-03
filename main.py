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

class VisaSlotChecker:
    def __init__(self):
        self.api_url = "https://lift-api.vfsglobal.by/appointment/CheckIsSlotAvailable"
        self.recipient_email = "gannibal231@gmail.com"
        
        # Email настройки из переменных окружения
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        
        # Интервал проверки в секундах (по умолчанию 5 минут)
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '300'))
        
        # Варианты payload для проверки
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
        
        # Флаг для отслеживания, было ли отправлено уведомление
        self.notification_sent = False
    
    def check_slots(self, payload):
        """Проверяет доступность слотов через API"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"Запрос отправлен. Статус: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Ответ API: {data}")
                
                # Проверяем наличие ошибки "No slots available"
                if 'error' in data and data['error'].get('code') == 1035:
                    logger.info("Слоты недоступны")
                    return False, None
                
                # Если нет ошибки или есть earliestDate, значит слот доступен
                if data.get('earliestDate') or (data.get('earliestSlotLists') and len(data['earliestSlotLists']) > 0):
                    logger.info("🎉 СЛОТ НАЙДЕН!")
                    return True, data
                
                # Если в ответе нет ошибки 1035, считаем что слот доступен
                if 'error' not in data or data['error'].get('code') != 1035:
                    logger.info("🎉 Возможно, слот доступен (нет ошибки 1035)")
                    return True, data
                
            return False, None
            
        except Exception as e:
            logger.error(f"Ошибка при проверке слотов: {str(e)}")
            return False, None
    
    def send_email_notification(self, slot_data, payload_type):
        """Отправляет email уведомление о доступном слоте"""
        if not self.sender_email or not self.sender_password:
            logger.error("Email настройки не заданы! Установите SENDER_EMAIL и SENDER_PASSWORD")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = '🎉 ДОСТУПЕН СЛОТ ДЛЯ ВИЗЫ!'
            
            # Форматируем информацию о слоте
            body = f"""
            <html>
            <body>
                <h2>Отличные новости! Появился свободный слот для записи!</h2>
                <p><strong>Время проверки:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
                <p><strong>Тип визы:</strong> {payload_type}</p>
                
                <h3>Детали:</h3>
                <pre>{slot_data}</pre>
                
                <p><strong>Быстрее переходите на сайт и записывайтесь!</strong></p>
                <p><a href="https://lift.vfsglobal.com/appointment">Перейти к записи</a></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Отправка email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email успешно отправлен на {self.recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке email: {str(e)}")
            return False
    
    def run(self):
        """Основной цикл работы бота"""
        logger.info("🤖 Бот запущен и начинает мониторинг слотов...")
        logger.info(f"Интервал проверки: {self.check_interval} секунд")
        logger.info(f"Email для уведомлений: {self.recipient_email}")
        
        if not self.sender_email or not self.sender_password:
            logger.warning("⚠️ Email настройки не заданы. Уведомления не будут отправляться!")
        
        while True:
            try:
                current_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
                logger.info(f"\n{'='*50}")
                logger.info(f"🔍 Проверка слотов... [{current_time}]")
                
                slot_found = False
                
                # Проверяем оба варианта payload
                for i, payload in enumerate(self.payloads, 1):
                    visa_type = payload['visaCategoryCode']
                    logger.info(f"Проверка варианта {i}: {visa_type}")
                    
                    is_available, slot_data = self.check_slots(payload)
                    
                    if is_available:
                        slot_found = True
                        logger.info(f"🎉 НАЙДЕН СЛОТ для визы {visa_type}!")
                        
                        # Отправляем уведомление только один раз
                        if not self.notification_sent:
                            self.send_email_notification(slot_data, visa_type)
                            self.notification_sent = True
                            logger.info("Уведомление отправлено. Бот продолжит работу...")
                        else:
                            logger.info("Уведомление уже было отправлено ранее")
                    
                    # Небольшая задержка между запросами
                    time.sleep(2)
                
                if not slot_found:
                    logger.info("❌ Слоты пока недоступны")
                    # Сбрасываем флаг, если слоты снова стали недоступны
                    self.notification_sent = False
                
                logger.info(f"⏰ Следующая проверка через {self.check_interval} секунд")
                logger.info(f"{'='*50}\n")
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("\n🛑 Бот остановлен пользователем")
                break
            except Exception as e:
                logger.error(f"Непредвиденная ошибка: {str(e)}")
                logger.info("Продолжаю работу через 60 секунд...")
                time.sleep(60)

if __name__ == "__main__":
    checker = VisaSlotChecker()
    checker.run()

