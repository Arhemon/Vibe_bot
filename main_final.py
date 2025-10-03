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
        """Инициализирует браузер с обходом Cloudflare"""
        try:
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--window-size=1920,1080')
            
            # undetected-chromedriver автоматически обходит Cloudflare!
            self.driver = uc.Chrome(
                options=options,
                headless=True,
                use_subprocess=False,
                version_main=141  # Версия Chrome
            )
            
            logger.info("✅ Браузер готов (undetected mode)")
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
                
                # Используем JavaScript для заполнения (Angular не загружается в headless)
                logger.info("📝 Заполняю форму через JavaScript...")
                
                # Скрипт для клика по опциям через их ID
                fill_form_script = """
                console.log('==> Начинаю заполнение формы');
                
                // Функция для клика по mat-select и выбора опции по ID
                function selectOption(selectId, optionId) {
                    return new Promise((resolve) => {
                        const select = document.getElementById(selectId);
                        if (select) {
                            select.click();
                            setTimeout(() => {
                                const option = document.getElementById(optionId);
                                if (option) {
                                    option.click();
                                    console.log('Clicked:', optionId);
                                    setTimeout(resolve, 1000);
                                } else {
                                    console.error('Option not found:', optionId);
                                    resolve();
                                }
                            }, 1000);
                        } else {
                            console.error('Select not found:', selectId);
                            resolve();
                        }
                    });
                }
                
                // Последовательно заполняем форму
                async function fillForm() {
                    console.log('1. Выбираю Application Centre - Vitebsk');
                    await selectOption('mat-select-0', 'BLRVIT');
                    
                    console.log('2. Выбираю Long Term Visa');
                    await selectOption('mat-select-2', 'BLRLTV');
                    
                    console.log('3. Выбираю D - visa');
                    await selectOption('mat-select-1', 'BLRVI');
                    
                    console.log('4. Нажимаю Continue');
                    setTimeout(() => {
                        const btn = document.querySelector('button[type="submit"], button.btn-brand-orange');
                        if (btn && !btn.disabled) {
                            btn.click();
                            console.log('Button clicked!');
                        } else {
                            console.error('Button not found or disabled');
                        }
                    }, 2000);
                }
                
                fillForm();
                return 'started';
                """
                
                self.driver.execute_script(fill_form_script)
                logger.info("✅ JavaScript запущен")
                time.sleep(15)  # Даем время на заполнение и отправку
                
                # Проверяем результат - вариант 1
                logger.info("📊 Проверяю результат для D - visa...")
                page_text = self.driver.page_source
                page_lower = page_text.lower()
                
                # DEBUG: Показываем что видим на странице
                logger.info("DEBUG: Проверяю ключевые слова на странице:")
                logger.info(f"  'no slots available': {'ДА' if 'no slots available' in page_lower else 'НЕТ'}")
                logger.info(f"  'no appointments': {'ДА' if 'no appointments' in page_lower else 'НЕТ'}")
                logger.info(f"  'earliest': {'ДА' if 'earliest' in page_lower else 'НЕТ'}")
                logger.info(f"  'calendar': {'ДА' if 'calendar' in page_lower else 'НЕТ'}")
                logger.info(f"  'select date': {'ДА' if 'select date' in page_lower else 'НЕТ'}")
                logger.info(f"  'book appointment': {'ДА' if 'book appointment' in page_lower else 'НЕТ'}")
                
                # Сохраняем часть текста для анализа
                visible_text = self.driver.find_element(By.TAG_NAME, "body").text
                logger.info(f"DEBUG: Видимый текст (первые 500 символов):")
                logger.info(f"{visible_text[:500]}...")
                
                results = []
                
                if "no slots available" in page_lower or "no appointments" in page_lower:
                    logger.info("  ❌ D - visa: Слотов нет")
                    results.append({'visa': 'D - visa', 'available': False})
                elif "earliest" in page_lower or "calendar" in page_lower or "select date" in page_lower or "book appointment" in page_lower:
                    logger.info("  🎉 D - visa: СЛОТ НАЙДЕН!")
                    results.append({'visa': 'D - visa', 'available': True})
                else:
                    logger.info("  ❓ D - visa: Неясный результат")
                    results.append({'visa': 'D - visa', 'available': False})
                
                # Проверяем вариант 2 - Premium Lounge
                logger.info("📋 Проверяю D visa - Premium Lounge...")
                
                # Возвращаемся и выбираем Premium
                self.driver.back()
                time.sleep(3)
                
                select_premium_script = """
                setTimeout(() => {
                    const select = document.getElementById('mat-select-1');
                    if (select) {
                        select.click();
                        setTimeout(() => {
                            const option = document.getElementById('BLRVPL');
                            if (option) {
                                option.click();
                                console.log('Premium selected');
                                setTimeout(() => {
                                    const btn = document.querySelector('button.btn-brand-orange');
                                    if (btn) btn.click();
                                }, 2000);
                            }
                        }, 1000);
                    }
                }, 1000);
                """
                
                self.driver.execute_script(select_premium_script)
                time.sleep(15)
                
                page_text = self.driver.page_source.lower()
                
                if "no slots available" in page_text or "no appointments" in page_text:
                    logger.info("  ❌ Premium: Слотов нет")
                    results.append({'visa': 'D visa - Premium', 'available': False})
                elif "earliest" in page_text or "calendar" in page_text:
                    logger.info("  🎉 Premium: СЛОТ НАЙДЕН!")
                    results.append({'visa': 'D visa - Premium', 'available': True})
                else:
                    logger.info("  ❓ Premium: Проверьте вручную")
                    results.append({'visa': 'D visa - Premium', 'available': False})
                
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

