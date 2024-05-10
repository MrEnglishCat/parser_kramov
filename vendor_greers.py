from dataclasses import dataclass
import json
import re
import os
import time

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
    def write_to_json(path, filename, data):
        __class__.check_folder(path)
        with open(f"{path}/{filename}", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @staticmethod
    def save_image(path, filename, data):
        __class__.check_folder(path)
        with open(f"{path}/{filename}", 'wb') as f:
            f.write(data)

    @staticmethod
    def read_from_json(path, issearch=True):
        if not __class__.check_file(path):
            print(f'[ALERT] Файл по пути: {path} не найден!')
            return
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if issearch:
                for item in data:
                    if 'urls' in item:
                        item['urls'].clear()
            return data

    def get_driver(self):
        # # CHROME
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument(
            "*/*")
        options.add_argument("--headless")
        # options.add_argument("headless")
        driver = webdriver.Chrome(options=options, keep_alive=True)

        return driver

    def get_all_goods_urls(self):
        result_json = {}
        urls = set()
        driver = self.get_driver()
        driver.get(self.URL)
        vendor_name = driver.find_element(By.XPATH, '//*[@id="pagetitle"]').text
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

        result_json.setdefault('urls', []).extend(urls)
        self.check_folder(f'data/{vendor_name}')
        self.write_to_json(f'data/{vendor_name}', filename='vendor_data.json', data=result_json)
        self.save_image(f'data/{vendor_name}', f"{vendor_name}.{image_url.split('.')[-1]}", requests.get(image_url, headers=self.HEADERS).content)

    def run(self):

        self.get_all_goods_urls()


parser = KramovParser()
parser.run()
