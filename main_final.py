import os
import time
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
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
        """Инициализирует браузер с перехватом Network"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Включаем Performance logging для перехвата запросов
            chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Браузер готов")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка браузера: {e}")
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
            time.sleep(6)
            
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
                
                # 1. Application Centre (centerCode)
                logger.info("  1. Application Centre...")
                center = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "mat-select[formcontrolname='centerCode']")
                ))
                logger.info("  ✅ Поле найдено!")
                center.click()
                time.sleep(2)
                
                # Выбираем Vitebsk
                vitebsk = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//span[contains(text(), 'Vitebsk')]")
                ))
                vitebsk.click()
                logger.info("  ✅ Vitebsk выбран")
                time.sleep(3)
                
                # 2. Appointment category (selectedSubvisaCategory)
                logger.info("  2. Appointment category...")
                category = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "mat-select[formcontrolname='selectedSubvisaCategory']")
                ))
                category.click()
                time.sleep(2)
                
                # Выбираем Long Term Visa
                long_term = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//span[contains(text(), 'Long Term') or contains(text(), 'D- Visa') or contains(text(), 'D -')]")
                ))
                long_term.click()
                logger.info("  ✅ Long Term Visa выбрана")
                time.sleep(3)
                
                # 3. Sub-category (visaCategoryCode)
                logger.info("  3. Sub-category...")
                subcategory = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "mat-select[formcontrolname='visaCategoryCode']")
                ))
                subcategory.click()
                time.sleep(2)
                
                # Выбираем D - visa (первая опция)
                d_visa = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//span[contains(text(), 'D - visa') or contains(text(), 'D-visa')]")
                ))
                d_visa.click()
                logger.info("  ✅ D-visa выбрана")
                time.sleep(3)
                
                # Нажимаем Continue
                logger.info("  4. Нажимаю Continue...")
                btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(., 'Continue')]")
                ))
                btn.click()
                logger.info("  ✅ Кнопка нажата!")
                time.sleep(8)
                
                # Проверяем результат
                logger.info("📊 Читаю результат...")
                page_text = self.driver.page_source.lower()
                
                results = []
                
                if "no slots available" in page_text or "no appointments" in page_text:
                    logger.info("  ❌ Слотов нет")
                    results.append({'visa': 'D-visa', 'available': False})
                elif "available" in page_text and "slot" in page_text:
                    logger.info("  🎉 СЛОТ НАЙДЕН!")
                    results.append({'visa': 'D-visa', 'available': True, 'data': 'Slot found'})
                else:
                    # Проверяем наличие календаря или дат
                    if "calendar" in page_text or "date" in page_text or "appointment" in page_text:
                        logger.info("  🎉 ВОЗМОЖНО СЛОТ НАЙДЕН!")
                        results.append({'visa': 'D-visa', 'available': True, 'data': 'Possible slot'})
                    else:
                        logger.info("  ❓ Неизвестный статус")
                        results.append({'visa': 'D-visa', 'available': False})
                
                logger.info("✅ Проверка завершена")
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

