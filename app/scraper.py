import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

class IvaSmsScraper:
    def __init__(self, email, password, notification_callback=None):
        self.email = email
        self.password = password
        self.driver = None
        self.base_url = "https://www.ivasms.com"
        self.login_url = f"{self.base_url}/login"
        self.otp_page_url = f"{self.base_url}/portal/sms/received"
        self.sent_otps = set() # To keep track of sent OTPs and avoid duplicates
        self.notification_callback = notification_callback

    def _send_notification(self, message):
        if self.notification_callback:
            self.notification_callback(message)
        print(message) # Also print to console for debugging

    def _initialize_driver(self):
        if self.driver:
            self.driver.quit()
        options = webdriver.ChromeOptions()
        options.add_argument(\'--headless\')
        options.add_argument(\'--no-sandbox\')
        options.add_argument(\'--disable-dev-shm-usage\')
        options.add_argument(\'--window-size=1920,1080\') # Ensure a large enough window size
        options.add_argument(\'--log-level=3\') # Suppress verbose logging
        options.add_argument(\'--disable-gpu\')
        options.add_argument(\'--disable-extensions\')
        options.add_argument(\'--start-maximized\')
        options.add_argument(\'--disable-infobars\')
        options.add_argument(\'--disable-browser-side-navigation\')
        options.add_argument(\'--disable-features=VizDisplayCompositor\')
        self.driver = webdriver.Chrome(service=Service(\'/usr/bin/chromedriver\'), options=options)
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(10) # Implicit wait for elements

    def login(self):
        try:
            if not self.driver:
                self._initialize_driver()

            self.driver.get(self.login_url)
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.NAME, "email")))
            
            email_field = self.driver.find_element(By.NAME, "email")
            password_field = self.driver.find_element(By.NAME, "password")
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), \'Log in\')]")

            email_field.send_keys(self.email)
            password_field.send_keys(self.password)
            login_button.click()

            WebDriverWait(self.driver, 20).until(
                EC.url_contains("/portal") or EC.presence_of_element_located((By.CLASS_NAME, "sidebar-menu"))
            )
            self._send_notification("Login successful.")
            return True
        except (TimeoutException, NoSuchElementException, WebDriverException) as e:
            self._send_notification(f"Login failed: {e}")
            return False
        except Exception as e:
            self._send_notification(f"An unexpected error occurred during login: {e}")
            return False

    def handle_popup(self):
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".modal-content")))
            self._send_notification("Pop-up detected. Attempting to close.")

            try:
                next_button = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), \'Next\')]")))
                next_button.click()
                WebDriverWait(self.driver, 3).until(EC.invisibility_of_element_located((By.XPATH, "//button[contains(text(), \'Next\')]")))
                self._send_notification("Clicked Next on pop-up.")
            except TimeoutException:
                pass 

            done_button = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), \'Done\')]")))
            done_button.click()
            WebDriverWait(self.driver, 5).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".modal-content")))
            self._send_notification("Pop-up closed successfully.")
            return True
        except TimeoutException:
            self._send_notification("No pop-up or pop-up closed automatically.")
            return False
        except (NoSuchElementException, WebDriverException) as e:
            self._send_notification(f"Error handling pop-up: {e}")
            return False
        except Exception as e:
            self._send_notification(f"An unexpected error occurred during pop-up handling: {e}")
            return False

    def navigate_to_otp_page(self):
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "sidebar-menu")))

            client_system_menu = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, \'#\') and contains(., \'Client System\')]"))
            )
            client_system_menu.click()
            time.sleep(1) # Give a moment for sub-menu to appear

            my_sms_statistics_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, \'/portal/sms/received\') and contains(., \'My SMS Statistics\')]"))
            )
            my_sms_statistics_link.click()

            WebDriverWait(self.driver, 15).until(EC.url_to_be(self.otp_page_url))
            self._send_notification("Successfully navigated to My SMS Statistics page.")
            return True
        except (TimeoutException, NoSuchElementException, WebDriverException) as e:
            self._send_notification(f"Navigation to OTP page failed: {e}")
            return False
        except Exception as e:
            self._send_notification(f"An unexpected error occurred during navigation: {e}")
            return False

    def _extract_otps_from_table(self):
        otps = []
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table#datatable-sms-received tbody tr")) or
                EC.presence_of_element_located((By.XPATH, "//td[contains(text(), \'No data available in table\')]"))
            )
            
            if self.driver.find_elements(By.XPATH, "//td[contains(text(), \'No data available in table\')]"):
                self._send_notification("No data available in the SMS statistics table.")
                return []

            rows = self.driver.find_elements(By.CSS_SELECTOR, "table#datatable-sms-received tbody tr")
            for row in rows:
                try:
                    message_text = row.find_element(By.XPATH, ".//td[3]").text
                    otps.append(message_text.strip())
                except NoSuchElementException:
                    self._send_notification("Could not find message text in a row. Skipping.")
                    continue
        except (TimeoutException, NoSuchElementException, WebDriverException) as e:
            self._send_notification(f"Error extracting OTPs from table: {e}")
        return otps

    def fetch_new_otps(self):
        try:
            self.driver.get(self.otp_page_url) # Ensure we are on the correct page
            current_otps = self._extract_otps_from_table()
            new_messages = []
            for otp in current_otps:
                if otp and otp not in self.sent_otps:
                    new_messages.append(otp)
                    self.sent_otps.add(otp)
            return new_messages
        except WebDriverException as e:
            self._send_notification(f"WebDriver error during new OTP fetch: {e}")
            return []
        except Exception as e:
            self._send_notification(f"An unexpected error occurred during new OTP fetch: {e}")
            return []

    def get_historical_otps(self, start_date, end_date):
        try:
            self.driver.get(self.otp_page_url) # Ensure we are on the correct page
            historical_messages = []
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "date_from")))
            date_from_field = self.driver.find_element(By.ID, "date_from")
            date_to_field = self.driver.find_element(By.ID, "date_to")
            get_sms_button = self.driver.find_element(By.XPATH, "//button[contains(text(), \'Get SMS\')]")

            date_from_field.clear()
            date_from_field.send_keys(start_date)
            date_to_field.clear()
            date_to_field.send_keys(end_date)
            get_sms_button.click()

            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table#datatable-sms-received tbody tr")) or
                EC.presence_of_element_located((By.XPATH, "//td[contains(text(), \'No data available in table\')]"))
            )

            historical_messages = self._extract_otps_from_table()
            return historical_messages
        except (TimeoutException, NoSuchElementException, WebDriverException) as e:
            self._send_notification(f"Error fetching historical OTPs: {e}")
            return []
        except Exception as e:
            self._send_notification(f"An unexpected error occurred during historical OTP fetch: {e}")
            return []

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

if __name__ == \'__main__\':
    from app.config import Config
    Config.validate()

    TEST_EMAIL = Config.IVASMS_EMAIL
    TEST_PASSWORD = Config.IVASMS_PASSWORD

    def test_notification_callback(message):
        print(f"[TEST NOTIFICATION]: {message}")

    scraper = IvaSmsScraper(TEST_EMAIL, TEST_PASSWORD, notification_callback=test_notification_callback)
    try:
        if scraper.login():
            scraper.handle_popup()
            if scraper.navigate_to_otp_page():
                print("Fetching new OTPs...")
                new_otps = scraper.fetch_new_otps()
                if new_otps:
                    for otp in new_otps:
                        print(f"New OTP: {otp}")
                else:
                    print("No new OTPs found.")

                print("Fetching historical OTPs (e.g., 2025-09-01 to 2025-09-30)...")
                historical_otps = scraper.get_historical_otps("2025-09-01", "2025-09-30")
                if historical_otps:
                    for otp in historical_otps:
                        print(f"Historical OTP: {otp}")
                else:
                    print("No historical OTPs found for the given range.")

    finally:
        scraper.close()

