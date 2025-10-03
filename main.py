import os
import time
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VisaSlotChecker:
    def __init__(self):
        self.api_url = "https://lift-api.vfsglobal.by/appointment/CheckIsSlotAvailable"
        self.login_url = "https://lift-api.vfsglobal.by/user/login"
        self.recipient_email = "gannibal231@gmail.com"
        
        # Email настройки из переменных окружения
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        
        # Интервал проверки в секундах (по умолчанию 5 минут)
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '300'))
        
        # Данные для автоматического логина
        self.vfs_email = os.getenv('VFS_EMAIL', 'gannibal231@gmail.com')
        self.vfs_password = os.getenv('VFS_PASSWORD', 'ZzamlXFvYj52Q+0Inao1QR/qf2gYFmgZuwYqFW0x9RP0XV/LALE+TSL68jaHLZTkRD0mGzB8wpmsHLRkzDgMxyUxpNRXqP5c5V/L5DersWqlnAz5Dj7kmbsy6iOk/1uzOBO0WZyrwlPRren0VHBurcOjge7ma5SD2yFOkgvML72JLJcYhMQc2olXDk8lZPDMlArFQb/fbx4399W56Oulkm1kVEOllQHYXXNkzp4EX0Q/9T0hQeOSgWKslkxTTUYDX9DsAQjWxO3xfsN12QaLdIhtUk2/Or7r600guxJQ3IwSsHTAur0ANelnvPy9pVH2CI9sbBsm1OBdfTQ96TbAYA==')
        self.vfs_captcha = os.getenv('VFS_CAPTCHA', '0.z5rs79DYQtvRu45yZDSEQjp9O6cyYNavh_UIzO6yYIBE2HCBcHuL23INX7gLSCOH7vbg3CmQ9be42IVH3hnfEp2KvZZS7vfG9S-2PshbuIGK4nlpI_blUUTS-Y6hG1VBxwvHLY0p95ETFHnKhk-BfzVxLq8hlgAVeskuVpzbxgGy4zCTR9NsxQVWFjYTi9LYMgdHl0Vx9NW-LOP_X9uNxVqkA2X4M5JXSwSUvRlnC6nOC1p38tHbkX2O5yi4gRUFT_Kmfvwbr17zDwh-xONDpUHnD9LVUkijjAVxFFqkh_H9rHYskU9czdaG_e1417kb5OlAp1Ue7J9fs_DCEL5__CpGtV6ap2RQbGepLWJPq0yMId3ZR8QO-hYGdDMRVobQIPjUMYZKYsBGIDznUdmGbDF77afUjpT7G12qJFHV1bPEzpcWZtTIFlF9mSy0nRkMRTwgq2b37ULawZZqOcg3mjJ6yQr3jvOJ-IFHfSypv17h4yYsSdUQmDYtDRtcUjuj4lu8PuUfZcdrE2xaMmcGpDHMnPm8DoGh6sJf-MoEfgXRjSteU9rMoot7JXFbFkZMzW9mOUL2q-tJ6CRPo50_aTjK1F0hXDbme_NsdSHzCrfSI0co2WhvzgoqQPIF06CqRRR8HOGiKWw_6686E5CpoaRrAD2raVyO7ffwYbrPcfFgUVZXpVvZhXotjBn3s4xnIi0VPL-uuRhlbAvFPEY8Su4ifOiFO2IE-x7rPlZHoCCSWGm4oq_CCFE_si_PCSzXWj_9jk6NPA1Jh3NyfwXcBvESqRm_0IdKsQzHL2FNqbd3Wqeiux_-ahIul6mqxcqvofPzXvr1kzqy-iS87EPGp4zpwmRCRN7VjO_CgbondeNuhzcXqVXGIaxabbrTAChztcmWk7rylEGX-_j3trIBa9Hk8eRXsCmD4NPf-cx_X9U.Kzbs0HjG-jAJIeWmGh_EcA.be600d9c25a939c7d8103dca8e38491b30c616e30f05a48e9dc13a151ff9e5ce')
        
        # Токены авторизации (будут получены после логина)
        self.authorize = ''
        self.clientsource = ''
        self.cookies = ''
        self.route = 'blr/en/bgr'
        
        # Session для сохранения cookies между запросами
        self.session = requests.Session()
        
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
    
    def login(self):
        """Автоматический логин для получения токенов"""
        try:
            logger.info("🔐 Выполняю автоматический логин...")
            
            # Пробуем разные варианты payload
            login_payloads = [
                # Вариант 1: с captcha
                {
                    "username": self.vfs_email,
                    "password": self.vfs_password,
                    "missioncode": "bgr",
                    "countrycode": "blr",
                    "languageCode": "en-US",
                    "captcha_version": "cloudflare-v1",
                    "captcha_api_key": self.vfs_captcha
                },
                # Вариант 2: без captcha
                {
                    "username": self.vfs_email,
                    "password": self.vfs_password,
                    "missioncode": "bgr",
                    "countrycode": "blr",
                    "languageCode": "en-US"
                },
                # Вариант 3: минимальный
                {
                    "username": self.vfs_email,
                    "password": self.vfs_password
                }
            ]
            
            for attempt, login_payload in enumerate(login_payloads, 1):
                logger.info(f"Попытка логина вариант {attempt}...")
                
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Origin': 'https://services.vfsglobal.by',
                    'Referer': 'https://services.vfsglobal.by/',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
                }
                
                response = self.session.post(
                    self.login_url,
                    json=login_payload,
                    headers=headers,
                    timeout=30
                )
                
                logger.info(f"Ответ логина: Статус {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Логин успешен!")
                    
                    # Извлекаем токены из ответа
                    if 'authorize' in data or 'token' in data:
                        self.authorize = data.get('authorize', data.get('token', ''))
                        logger.info(f"✅ Токен authorize получен ({len(self.authorize)} символов)")
                    
                    if 'clientsource' in data:
                        self.clientsource = data.get('clientsource', '')
                        logger.info(f"✅ Токен clientsource получен ({len(self.clientsource)} символов)")
                    
                    # Сохраняем cookies из session
                    cookies_list = []
                    for cookie in self.session.cookies:
                        cookies_list.append(f"{cookie.name}={cookie.value}")
                    self.cookies = "; ".join(cookies_list)
                    
                    if self.cookies:
                        logger.info(f"✅ Cookies получены ({len(self.cookies)} символов)")
                    
                    # Проверяем что получили нужные данные
                    if self.authorize or self.cookies:
                        logger.info("✅ Автоматический логин выполнен успешно!")
                        return True
                    else:
                        logger.warning("⚠️ Токены не найдены в ответе логина")
                        logger.debug(f"Ответ: {data}")
                else:
                    logger.warning(f"❌ Вариант {attempt} не сработал: {response.status_code}")
                    try:
                        logger.debug(f"Ответ: {response.text[:200]}")
                    except:
                        pass
                    
                    # Пробуем следующий вариант
                    time.sleep(1)
                    continue
            
            # Если все варианты не сработали
            logger.error("❌ Все варианты логина не сработали")
            return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при логине: {str(e)}")
            return False
    
    def check_slots(self, payload):
        """Проверяет доступность слотов через API"""
        try:
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Origin': 'https://services.vfsglobal.by',
                'Referer': 'https://services.vfsglobal.by/',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'Sec-Ch-Ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"macOS"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Priority': 'u=1, i'
            }
            
            # Добавляем обязательные заголовки VFS Global
            if self.authorize:
                headers['authorize'] = self.authorize
            
            if self.clientsource:
                headers['clientsource'] = self.clientsource
            
            if self.route:
                headers['route'] = self.route
            
            # Добавляем cookies
            if self.cookies:
                headers['Cookie'] = self.cookies
            
            response = self.session.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"Запрос отправлен. Статус: {response.status_code}")
            
            # Логируем тело ответа для отладки
            try:
                response_text = response.text
                logger.debug(f"Ответ API: {response_text[:500]}")
            except:
                pass
            
            if response.status_code == 401:
                logger.warning("⚠️ Ошибка 401: Токены устарели, требуется повторный логин")
                return None, 'AUTH_REQUIRED'
            
            if response.status_code == 403:
                logger.warning("⚠️ Ошибка 403: Доступ запрещен")
                return None, 'AUTH_REQUIRED'
            
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
        logger.info("=" * 70)
        logger.info("🤖 БОТ ЗАПУЩЕН С АВТОМАТИЧЕСКИМ ОБНОВЛЕНИЕМ ТОКЕНОВ")
        logger.info("=" * 70)
        logger.info(f"Интервал проверки: {self.check_interval} секунд")
        logger.info(f"Email для уведомлений: {self.recipient_email}")
        logger.info(f"VFS аккаунт: {self.vfs_email}")
        
        if not self.sender_email or not self.sender_password:
            logger.warning("⚠️ Email настройки не заданы. Уведомления не будут отправляться!")
        
        # Выполняем первый логин
        logger.info("")
        if not self.login():
            logger.error("❌ Не удалось выполнить первоначальный логин. Выход.")
            return
        
        logger.info("")
        logger.info("✅ Готов к мониторингу!")
        
        login_retry_count = 0
        max_login_retries = 3
        
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
                    
                    # Проверяем нужно ли перелогиниться
                    if is_available is None and slot_data == 'AUTH_REQUIRED':
                        logger.warning("⚠️ Токены устарели, выполняю повторный логин...")
                        if self.login():
                            logger.info("✅ Логин выполнен, повторяю проверку...")
                            is_available, slot_data = self.check_slots(payload)
                            login_retry_count = 0  # Сброс счетчика
                        else:
                            login_retry_count += 1
                            logger.error(f"❌ Не удалось выполнить логин (попытка {login_retry_count}/{max_login_retries})")
                            if login_retry_count >= max_login_retries:
                                logger.error("❌ Превышено количество попыток логина. Выход.")
                                return
                            time.sleep(60)  # Ждем минуту перед следующей попыткой
                            continue
                    
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

