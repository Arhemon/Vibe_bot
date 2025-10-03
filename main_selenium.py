import os
import time
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
from selenium.webdriver.support.ui import Select
import json

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VisaSlotCheckerSelenium:
    def __init__(self):
        self.url = "https://services.vfsglobal.by/"
        self.recipient_email = "gannibal231@gmail.com"
        
        # Email настройки из переменных окружения
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        
        # Интервал проверки в секундах (по умолчанию 5 минут)
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '300'))
        
        # Параметры для проверки
        self.visa_types = [
            {"code": "BLRVPL", "name": "Polish visa (национальная)"},
            {"code": "BLRVI", "name": "Visitor/Short-term visa"}
        ]
        
        # Флаг для отслеживания, было ли отправлено уведомление
        self.notification_sent = False
        
        # Браузер
        self.driver = None
    
    def init_browser(self):
        """Инициализирует браузер Chrome"""
        try:
            chrome_options = Options()
            
            # Для Railway и headless режима
            if os.getenv('HEADLESS', 'true').lower() == 'true':
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
            
            # Дополнительные настройки для стабильности
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')
            
            # Отключаем автоматическое обнаружение Selenium
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Браузер успешно инициализирован")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации браузера: {str(e)}")
            return False
    
    def check_slots(self, visa_type_code):
        """Проверяет доступность слотов через Selenium"""
        try:
            logger.info(f"🌐 Открываю сайт {self.url}")
            self.driver.get(self.url)
            
            # Ждем загрузки страницы
            time.sleep(5)
            
            # Закрываем cookie popup если есть
            try:
                logger.info("🍪 Закрываю cookie popup...")
                cookie_accept = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                )
                cookie_accept.click()
                time.sleep(2)
                logger.info("✅ Cookie popup закрыт")
            except:
                logger.info("ℹ️  Cookie popup не найден (возможно уже был закрыт)")
                pass
            
            # Ищем и заполняем форму
            wait = WebDriverWait(self.driver, 20)
            
            # Выбираем Country: Belarus
            logger.info("📝 Заполняю форму: Country = Belarus")
            try:
                country_select = wait.until(
                    EC.presence_of_element_located((By.ID, "mat-select-value-1"))
                )
                country_select.click()
                time.sleep(1)
                
                # Выбираем Belarus
                belarus_option = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Belarus')]"))
                )
                belarus_option.click()
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Попытка альтернативного способа выбора страны: {e}")
            
            # Выбираем Mission: Bulgaria
            logger.info("📝 Заполняю форму: Mission = Bulgaria")
            try:
                mission_select = self.driver.find_element(By.XPATH, "//mat-select[@formcontrolname='missionCode']")
                mission_select.click()
                time.sleep(1)
                
                bulgaria_option = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Bulgaria')]"))
                )
                bulgaria_option.click()
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Проблема с выбором миссии: {e}")
            
            # Выбираем VAC: BLRVIT
            logger.info("📝 Заполняю форму: VAC = BLRVIT")
            try:
                vac_select = self.driver.find_element(By.XPATH, "//mat-select[@formcontrolname='vacCode']")
                vac_select.click()
                time.sleep(1)
                
                vac_option = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'VIT')]"))
                )
                vac_option.click()
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Проблема с выбором VAC: {e}")
            
            # Выбираем Visa Category
            logger.info(f"📝 Заполняю форму: Visa Category = {visa_type_code}")
            try:
                visa_select = self.driver.find_element(By.XPATH, "//mat-select[@formcontrolname='visaCategoryCode']")
                visa_select.click()
                time.sleep(1)
                
                # Ищем нужный тип визы
                visa_option = wait.until(
                    EC.element_to_be_clickable((By.XPATH, f"//mat-option[contains(@id, '{visa_type_code}')]"))
                )
                visa_option.click()
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Проблема с выбором типа визы: {e}")
            
            # Нажимаем кнопку Continue/Check slots
            logger.info("🔍 Нажимаю кнопку проверки слотов")
            try:
                continue_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'mat-flat-button')]"))
                )
                continue_button.click()
                time.sleep(5)
            except Exception as e:
                logger.error(f"Не удалось нажать кнопку: {e}")
                return False, None
            
            # Проверяем результат
            page_source = self.driver.page_source.lower()
            
            # Ищем признаки отсутствия слотов
            if "no slots available" in page_source or "no appointments available" in page_source:
                logger.info("❌ Слоты недоступны")
                return False, None
            
            # Ищем признаки доступных слотов
            if "available" in page_source and "slot" in page_source:
                # Пытаемся найти конкретную информацию о слотах
                try:
                    slot_info = self.driver.find_element(By.XPATH, "//*[contains(text(), 'slot') or contains(text(), 'available')]").text
                    logger.info(f"🎉 НАЙДЕН СЛОТ! Информация: {slot_info}")
                    return True, {"info": slot_info, "timestamp": datetime.now().isoformat()}
                except:
                    logger.info("🎉 ВОЗМОЖНО НАЙДЕН СЛОТ! (нужна проверка)")
                    return True, {"info": "Slot possibly available", "timestamp": datetime.now().isoformat()}
            
            # Делаем скриншот для отладки
            try:
                screenshot_path = f"screenshot_{visa_type_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"📸 Скриншот сохранён: {screenshot_path}")
            except:
                pass
            
            return False, None
            
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке слотов: {str(e)}")
            try:
                screenshot_path = f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"📸 Скриншот ошибки: {screenshot_path}")
            except:
                pass
            return False, None
    
    def send_email_notification(self, slot_data, visa_type):
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
                <p><strong>Тип визы:</strong> {visa_type}</p>
                
                <h3>Детали:</h3>
                <pre>{json.dumps(slot_data, indent=2, ensure_ascii=False)}</pre>
                
                <p style="color: red; font-weight: bold; font-size: 18px;">
                    ⚡ БЫСТРЕЕ ПЕРЕХОДИТЕ НА САЙТ И ЗАПИСЫВАЙТЕСЬ! ⚡
                </p>
                <p><a href="https://services.vfsglobal.by/" style="background-color: #4CAF50; color: white; padding: 15px 32px; text-decoration: none; display: inline-block; font-size: 16px;">Перейти к записи</a></p>
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
            logger.error(f"❌ Ошибка при отправке email: {str(e)}")
            return False
    
    def run(self):
        """Основной цикл работы бота"""
        logger.info("=" * 70)
        logger.info("🤖 БОТ ЗАПУЩЕН (ВЕРСИЯ С SELENIUM)")
        logger.info("=" * 70)
        logger.info(f"Интервал проверки: {self.check_interval} секунд")
        logger.info(f"Email для уведомлений: {self.recipient_email}")
        
        if not self.sender_email or not self.sender_password:
            logger.warning("⚠️ Email настройки не заданы. Уведомления не будут отправляться!")
        
        # Инициализируем браузер один раз
        if not self.init_browser():
            logger.error("❌ Не удалось инициализировать браузер. Выход.")
            return
        
        try:
            while True:
                try:
                    current_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
                    logger.info(f"\n{'='*70}")
                    logger.info(f"🔍 ПРОВЕРКА СЛОТОВ... [{current_time}]")
                    logger.info(f"{'='*70}")
                    
                    slot_found = False
                    
                    # Проверяем оба типа виз
                    for visa_type in self.visa_types:
                        logger.info(f"\n📋 Проверка: {visa_type['name']} ({visa_type['code']})")
                        
                        is_available, slot_data = self.check_slots(visa_type['code'])
                        
                        if is_available:
                            slot_found = True
                            logger.info(f"🎉 НАЙДЕН СЛОТ для {visa_type['name']}!")
                            
                            # Отправляем уведомление только один раз
                            if not self.notification_sent:
                                self.send_email_notification(slot_data, visa_type['name'])
                                self.notification_sent = True
                                logger.info("📧 Уведомление отправлено. Бот продолжит работу...")
                            else:
                                logger.info("📧 Уведомление уже было отправлено ранее")
                        
                        # Небольшая задержка между проверками
                        time.sleep(3)
                    
                    if not slot_found:
                        logger.info("\n❌ Слоты пока недоступны")
                        # Сбрасываем флаг, если слоты снова стали недоступны
                        self.notification_sent = False
                    
                    logger.info(f"\n⏰ Следующая проверка через {self.check_interval} секунд")
                    logger.info(f"{'='*70}\n")
                    
                    time.sleep(self.check_interval)
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка в цикле: {str(e)}")
                    logger.info("🔄 Перезапускаю браузер...")
                    
                    # Закрываем старый браузер
                    try:
                        if self.driver:
                            self.driver.quit()
                    except:
                        pass
                    
                    # Инициализируем новый
                    time.sleep(5)
                    if not self.init_browser():
                        logger.error("❌ Не удалось перезапустить браузер. Жду 60 секунд...")
                        time.sleep(60)
                    
        except KeyboardInterrupt:
            logger.info("\n🛑 Бот остановлен пользователем")
        finally:
            # Закрываем браузер
            try:
                if self.driver:
                    self.driver.quit()
                    logger.info("✅ Браузер закрыт")
            except:
                pass

if __name__ == "__main__":
    checker = VisaSlotCheckerSelenium()
    checker.run()

