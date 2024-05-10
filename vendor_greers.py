from dataclasses import dataclass
import json
import re
import os
import time

import fake_useragent
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from lxml.html import fromstring
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


@dataclass
class KramovDataClass:
    brand_name: str = None
    brand_url: str = None
    brand_img: str = None
    brand_description: str = None
    preview: str = None

    # def __str__(self):
    #     return f"{self.brand_name}\n\t{self.brand_url}\n\t\t{self.brand_img}\n\t\t\t{self.brand_description}"


class KramovParser:
    BASE_URL = 'https://kramov.by'
    URL = 'https://kramov.by/info/brands/greers/'
    BASE_FILE_PATH = 'data'
    HEADERS = {'Accept': '*/*', 'User-Agent': UserAgent().random, 'Bx-Ajax': 'true'}
    DIR_LISTS = []

    @staticmethod
    def check_folder(path):
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def check_file(path):
        if os.path.isfile(path):
            return True
        else:
            return False

    @staticmethod
    def write_to_file(path, filename, data, istxt=False, isfile=False, mode='w'):
        __class__.check_folder(path)
        with open(f"{path}/{filename}", mode, encoding='utf-8' if 'b' not in mode else None) as f:
            if istxt:
                f.writelines(data)
            elif isfile:
                f.write(data)
            else:
                json.dump(data, f, ensure_ascii=False, indent=4)

    @staticmethod
    def save_image(path, filename, data):
        __class__.check_folder(path)
        with open(f"{path}/{filename}", 'wb') as f:
            f.write(data)

    @staticmethod
    def read_from_file(path, issearch=True, istxt=False):
        if not __class__.check_file(path):
            print(f'[ALERT] Файл по пути: {path} не найден!')
            return
        with open(path, 'r', encoding='utf-8') as f:
            if istxt:
                return f.readlines()
            return json.load(f)

    def get_driver(self):
        # # CHROME
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(
            f"user-agent={fake_useragent.UserAgent()}")
        options.add_argument(
            "*/*")
        options.add_argument("--headless")
        # options.add_argument("headless")
        driver = webdriver.Chrome(options=options, keep_alive=True)

        return driver

    def get_all_goods_urls(self, driver):
        result_json = {}
        urls = set()

        driver.get(self.URL)
        vendor_name = driver.find_element(By.XPATH, '//*[@id="pagetitle"]').text
        self.DIR_LISTS.append(f'data/{vendor_name}')
        vendor_description = driver.find_element(By.XPATH,
                                                 '//*[@id="content"]/div[2]/div/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div').text
        image_url = driver.find_element(By.CLASS_NAME, 'detailimage').find_element(By.TAG_NAME,
                                                                                   'a').get_attribute(
            'href')
        vendor_description = ' '.join(vendor_description.split())
        all_goods_items = driver.find_element(By.XPATH,
                                              '//*[@id="content"]/div[2]/div/div[1]/div/div/div[1]/div[1]/div[3]/div[3]/div[1]/div[2]/div[1]/div').find_elements(
            By.TAG_NAME, 'div')

        for item in all_goods_items:
            try:
                url = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
                urls.add(url)
            except:
                continue

        result_json.setdefault('vendor_name', vendor_name)
        result_json.setdefault('vendor_url_image', image_url)
        result_json.setdefault('vendor_description', vendor_description)
        result_json.setdefault('products_data', [])
        result_json.setdefault('urls', []).extend(sorted(urls))
        self.check_folder(f'data/{vendor_name}')
        self.write_to_file(f'data/{vendor_name}', filename='vendor_data.json', data=result_json)
        self.save_image(f'data/{vendor_name}', f"{vendor_name}.{image_url.split('.')[-1]}",
                        requests.get(image_url, headers=self.HEADERS).content)
        self.write_to_file(f'data', 'DIR_LISTS.txt', self.DIR_LISTS, istxt=True)

    def get_data_from_one_product(self, driver, json_data, url, DIR):
        driver.get(url)
        general_path = f"{DIR}/files"
        # Получение и сохранение фото товара
        photo_path = f"{general_path}/photo"
        tags_all_photo_urls =  driver.find_element(By.XPATH, '/html/body/div[5]/div[7]/div[2]/div/div/div/div/div/div[1]/div/div/div[2]/div/div/div[1]/div/div[1]/div[1]').find_elements(By.TAG_NAME, 'a')
        all_photo_urls = [item_url.get_attribute('href') for item_url in tags_all_photo_urls]
        for index, photo in enumerate(all_photo_urls, 1):
            self.save_image(photo_path, f"{index}.{photo.split('.')[-1]}", requests.get(photo, headers=self.HEADERS).content)

        # Получение общих параметров
        general_attrs = driver.find_element(By.XPATH,
                                            '/html/body/div[5]/div[7]/div[2]/div/div/div/div/div/div[1]/div/div/div[2]/div/div/div[2]/div[2]/div[1]').text
        # Получение и загрузка документов
        docs_urls = {tag_a.get_attribute('href'): tag_a.text for tag_a in driver.find_element(By.XPATH,
                                                                                              '/html/body/div[5]/div[7]/div[2]/div/div/div/div/div/div[1]/div/div/div[2]/div/div/div[3]/div[2]/div').find_elements(
            By.TAG_NAME, 'a')}

        doc_path = f"{general_path}/docs"
        for docs_url, docs_name in docs_urls.items():
            self.write_to_file(doc_path, f'{docs_name}.{docs_url.split(".")[-1]}',
                               requests.get(docs_url, headers=self.HEADERS).content, isfile=True, mode='wb')

        # Получение цены или варианта заказа
        price = driver.find_element(By.XPATH,
                                    '/html/body/div[5]/div[7]/div[2]/div/div/div/div/div/div[1]/div/div/div[2]/div/div/div[2]/div[4]/div[1]/div/div[1]/div/div[1]/div[2]/div[1]/div/span[2]').text

        # Получение ссылок на видео
        try:
            source_video_urls = driver.find_element(By.XPATH, '/html/body/div[5]/div[7]/div[2]/div/div/div/div/div/div[1]/div/div/div[3]/div[1]/div[1]/div[2]/div[3]/div/div').find_elements(By.TAG_NAME, 'iframe')
            video_urls = [tag_iframe.get_attribute('src') for tag_iframe in source_video_urls]
        except:
            video_urls = []

        # Получение описания позиции
        source_description = driver.find_element(By.XPATH, '//*[@id="desc"]/div[1]').find_elements(By.TAG_NAME, 'div')
        description = {}
        for desc in source_description:
            description.setdefault(desc.find_element(By.TAG_NAME, 'h3').text, desc.find_element(By.TAG_NAME, 'p').text)

        # Получение объектов по моделям, размерам, типам двигателя и прочему
        varieties_of_goods = {} # словарь для размещения объектов по разновидностями товаров каждый со своими данными
        # general_block = driver.find_element(By.XPATH, '/html/body/div[5]/div[7]/div[2]/div/div/div/div/div/div[1]/div/div/div[2]/div/div/div[2]/div[4]/div[1]/div/div[1]/div/div[2]')
        general_block = driver.find_element(By.XPATH, '/html/body/div[5]/div[7]/div[2]/div/div/div/div/div/div[1]/div/div/div[3]/div[1]/div[1]/div[2]/div[2]/div/div')
        self.write_to_file('TEST', 'TEST_HTML.html', general_block.get_attribute('outerHTML'), istxt=True)
        print(general_block.get_attribute('outerHTML'))
        # for item in general_block:
        #
        #     all_elements = item.find_elements(By.TAG_NAME, 'li')
        #
        #     for el in all_elements:
        #         el.click()
        #         print(driver.find_element(By.XPATH, '/html/body/div[5]/div[7]/div[2]/div/div/div/div/div/div[1]/div/div/div[3]/div[1]/div[1]/div[2]/div[2]/div/div').text)
        #         print('='*100)



    def run(self):
        driver = self.get_driver()
        # self.get_all_goods_urls(driver)

        if not self.DIR_LISTS:
            self.DIR_LISTS = self.read_from_file('data/DIR_LISTS.txt', istxt=True)
        # Если сохраняются данные различных производителей
        for DIR in self.DIR_LISTS:
            json_data = self.read_from_file(f"{DIR}/vendor_data.json")
            vendor_urls = json_data.get('urls', '')
            for url in vendor_urls:
                self.get_data_from_one_product(driver, json_data, url, DIR)

                break


parser = KramovParser()
parser.run()
