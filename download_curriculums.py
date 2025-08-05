import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

def download_pdf_from_button(url, download_dir, button_text="Скачать учебный план"):
    # Создаем директорию для загрузок, если она не существует
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        print(f"Создана директория: {download_dir}")
    
    # Получаем абсолютный путь к директории загрузки
    abs_download_dir = os.path.abspath(download_dir)
    print(f"Файлы будут сохраняться в: {abs_download_dir}")
    
    # Настраиваем опции Chrome
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": abs_download_dir,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True,
        "download.directory_upgrade": True
    })
    
    # Инициализируем браузер
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Открываем страницу
        driver.get(url)
        print(f"Страница {url} открыта")
        
        # Ждем загрузки страницы
        time.sleep(3)
        
        # Ищем кнопку по тексту
        buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "button"))
        )
        
        target_button = None
        for button in buttons:
            if button_text.lower() in button.text.lower():
                target_button = button
                print(f"Найдена кнопка: {button.text}")
                break
        
        # Если кнопка не найдена по тексту, ищем по классу
        if not target_button:
            try:
                target_button = driver.find_element(By.CLASS_NAME, "ButtonSimple_button__JbIQ5.ButtonSimple_button_masterProgram__JK8b_")
                print("Найдена кнопка по классу")
            except:
                pass
        
        # Если кнопка не найдена, пробуем найти любые ссылки, содержащие pdf
        if not target_button:
            pdf_links = []
            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href")
                if href and (".pdf" in href.lower() or "download" in href.lower() or "plan" in href.lower()):
                    pdf_links.append(href)
            
            if pdf_links:
                print(f"Найдены возможные PDF-ссылки: {pdf_links}")
                # Скачиваем первую найденную PDF-ссылку напрямую
                response = requests.get(pdf_links[0])
                filename = os.path.join(abs_download_dir, "study_plan.pdf")
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"Файл скачан и сохранен как {filename}")
                return filename
            else:
                print("Не найдены PDF-ссылки на странице")
                return None
        
        # Кликаем по кнопке
        driver.execute_script("arguments[0].click();", target_button)
        print("Кнопка нажата")
        
        # Запоминаем список файлов до загрузки
        before_download = set(os.listdir(abs_download_dir))
        
        # Ждем, пока файл загрузится
        time.sleep(10)  # Увеличил время ожидания для надежности
        
        # Проверяем, появился ли новый файл
        after_download = set(os.listdir(abs_download_dir))
        new_files = after_download - before_download
        
        pdf_files = [f for f in new_files if f.endswith('.pdf')]
        
        if pdf_files:
            downloaded_file = os.path.join(abs_download_dir, pdf_files[0])
            print(f"Файл скачан и сохранен как {downloaded_file}")
            return downloaded_file
        else:
            # Если PDF не обнаружен, проверяем наличие файла с расширением .crdownload
            # (Chrome использует это расширение для незавершенных загрузок)
            crdownload_files = [f for f in new_files if f.endswith('.crdownload')]
            if crdownload_files:
                print("Загрузка файла не завершена. Ожидаем...")
                time.sleep(20)  # Ждем еще немного
                
                # Проверяем снова
                current_files = set(os.listdir(abs_download_dir))
                completed_files = [f for f in current_files if f.endswith('.pdf') and f not in before_download]
                
                if completed_files:
                    downloaded_file = os.path.join(abs_download_dir, completed_files[0])
                    print(f"Файл скачан и сохранен как {downloaded_file}")
                    return downloaded_file
            
            print("Файл не был загружен или это не PDF-файл")
            return None
            
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None
    finally:
        # Закрываем браузер
        driver.quit()

if __name__ == "__main__":
    download_directory = "./pdf_curriculum"  # Директория для скачивания по умолчанию
    for url in ["https://abit.itmo.ru/program/master/ai", "https://abit.itmo.ru/program/master/ai_product"]:
        result = download_pdf_from_button(url, download_directory + '_' + url.split('/')[-1])
        
        if result:
            print(f"Успешно скачан файл: {result}")
        else:
            print("Не удалось скачать файл")