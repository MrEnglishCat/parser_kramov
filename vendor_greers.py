from copy import deepcopy
from dataclasses import dataclass
import json
import re
import os
import time
from pprint import pprint

import fake_useragent
import requests
from itertools import product
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

    @staticmethod
    def get_data_from_url(url, headers):
        return requests.get(url, headers=headers).content

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
                print('[ALARM] Ошибка при поиске ссылки на товар или товары не найдены')
                continue

        result_json.setdefault('vendor_name', vendor_name)
        result_json.setdefault('vendor_url_image', image_url)
        result_json.setdefault('vendor_description', vendor_description)
        result_json.setdefault('urls', []).extend(sorted(urls))
        result_json.setdefault('products_data', [])
        self.check_folder(f'data/{vendor_name}')
        self.write_to_file(f'data/{vendor_name}', filename='vendor_data.json', data=result_json)
        self.save_image(f'data/{vendor_name}', f"{vendor_name}.{image_url.split('.')[-1]}",
                        self.get_data_from_url(image_url, headers=self.HEADERS))
        self.write_to_file(f'data', 'DIR_LISTS.txt', self.DIR_LISTS, istxt=True)

    def get_characteristics(self, driver, general_path, vendor_name, product_name):
        # сбор данных на каждую модель
        products_data = {}
        # general_block_data = driver.find_element(By.XPATH, '/html/body/div[5]/div[7]/div[2]/div/div/div/div/div/div[1]/div/div/div[3]/div[1]/div[1]/div[2]')
        general_block_data = driver.find_element(By.XPATH,
                                                 '//*[@id="content"]/div[2]/div/div/div/div/div/div[1]/div/div/div[3]/div[1]/div[1]/div[2]')
        characteristics = {"description": {}, "images": {}}
        characteristics_image_path = f"{general_path}"
        try:
            general_block = general_block_data.find_element(By.ID, 'props')
            soup = BeautifulSoup(general_block.get_attribute('outerHTML'), 'lxml')
            characteristics["description"] = general_block.get_attribute('outerHTML')
            for tag_a in soup.find_all('a'):
                url = f"{self.BASE_URL}{tag_a.get('href')}"
                url_name = tag_a.find_previous('h3').text.strip()
                characteristics["images"].setdefault(url_name, []).append(url)
            for dir_name, url_list in characteristics["images"].items():
                for index, u in enumerate(url_list, 1):
                    self.save_image(
                        characteristics_image_path,
                        f"image_{vendor_name}_{product_name}_{str(dir_name.replace(':', '').replace('+', 'и').replace('|', 'или'))}_{index}.{u.split('.')[-1]}",
                        self.get_data_from_url(f"{u}", headers=self.HEADERS))
        except Exception as e:
            print("[ALARM] Ошибка при сборе данных или раздела характеристики нету")
            # print(e)
        # Получение отзывов


        products_data.setdefault('characteristics_image_path', characteristics_image_path)
        products_data.setdefault('characteristics', characteristics)

        return products_data

    def get_data_from_one_product(self, driver, json_data, url, DIR):
        driver.get(url)
        products_data = {}

        product_name = driver.find_element(By.ID, "pagetitle").text.strip()
        general_path = f"{DIR}/files/{product_name}"
        # Получение и сохранение фото товара
        photo_path = f"{general_path}/photo"
        tags_all_photo_urls = driver.find_element(By.XPATH,
                                                  '/html/body/div[5]/div[7]/div[2]/div/div/div/div/div/div[1]/div/div/div[2]/div/div/div[1]/div').find_elements(
            By.TAG_NAME, 'a')
        all_photo_urls = [item_url.get_attribute('href') for item_url in tags_all_photo_urls]
        for index, photo in enumerate(all_photo_urls, 1):
            self.save_image(photo_path,
                            f"photo_{json_data['vendor_name']}_{product_name}_{index}.{photo.split('.')[-1]}",
                            self.get_data_from_url(photo, headers=self.HEADERS))

        # Получение общих параметров
        general_attrs = driver.find_element(By.XPATH,
                                            '/html/body/div[5]/div[7]/div[2]/div/div/div/div/div/div[1]/div/div/div[2]/div/div/div[2]/div[2]/div[1]').text
        # Получение и загрузка документов
        try:
            docs_urls = {tag_a.get_attribute('href'): tag_a.text for tag_a in driver.find_element(By.XPATH,
                                                                                                  '/html/body/div[5]/div[7]/div[2]/div/div/div/div/div/div[1]/div/div/div[2]/div/div/div[3]/div[2]/div').find_elements(
                By.TAG_NAME, 'a')}
        except:
            print('[ALARM] Ошибка при поиске или загрузке документа или документы не найдены')
            docs_urls = {}

        doc_path = f"{general_path}/docs"
        for docs_url, docs_name in docs_urls.items():
            self.write_to_file(doc_path, f'{docs_name}.{docs_url.split(".")[-1]}',
                               self.get_data_from_url(docs_url, headers=self.HEADERS), isfile=True, mode='wb')

        # Получение цены или варианта заказа
        price = driver.find_element(By.CLASS_NAME, 'item-stock').text

        # Получение ссылок на видео
        try:
            source_video_urls = driver.find_element(By.XPATH,
                                                    '/html/body/div[5]/div[7]/div[2]/div/div/div/div/div/div[1]/div/div/div[3]/div[1]/div[1]/div[2]/div[3]/div/div').find_elements(
                By.TAG_NAME, 'iframe')
            video_urls = [tag_iframe.get_attribute('src') for tag_iframe in source_video_urls]
        except:
            print("[ALARM] Ошибка при поиске ссылки на видео или видео не найдено")
            video_urls = []

        # Получение описания позиции
        # source_description = driver.find_element(By.XPATH, '//*[@id="desc"]/div[1]').find_elements(By.TAG_NAME, 'div')
        source_description = (driver.find_element(By.XPATH, '//*[@id="desc"]/div[1]'),)
        description = {
            "description": [],
            "image_url": [],
        }
        description_image_path = f"{general_path}/desctiption_image"
        for desc in source_description:
            # soup = BeautifulSoup(desc.get_attribute('outerHTML'))
            # description.setdefault(desc.find_element(By.TAG_NAME, 'h3').text, soup.fin)
            description["description"].append(desc.get_attribute('outerHTML'))

            # получение изображений из описания если они есть
            for index, link in enumerate(desc.find_elements(By.TAG_NAME, 'a'), 1):
                link = link.get_attribute('href')
                description["image_url"].append(link)
                self.save_image(description_image_path,
                                f"description_image_path_{json_data['vendor_name']}_{product_name}_{index}.{link.split('.')[-1]}",
                                self.get_data_from_url(link, self.HEADERS))

        description["description"] = ''.join(description["description"])

        # Проверка наличия чертежей
        blueprints_urls = []
        blueprints_path = f"{general_path}/Чертежи"
        try:
            blueprints = driver.find_element(By.XPATH,
                                             '//*[@id="desc"]/div[2]/div/div[3]/div/div[1]/div')
            if (a := blueprints.find_elements(By.TAG_NAME, 'a')):
                for index, link in enumerate(a, 1):
                    link = link.get_attribute('href')
                    self.save_image(blueprints_path,
                                    f"blueprints_{json_data['vendor_name']}_{product_name}_{index}.{link.split('.')[-1]}",
                                    self.get_data_from_url(link, headers=self.HEADERS))
        except:
            print('[ALARM] Ошибка поиска чертежей или чертежи не найдены')

        # Получение объектов по моделям, размерам, типам двигателя и прочему
        # varieties - заносит все уровни(модель, тип, размер и тп)
        _varieties = driver.find_element(By.CLASS_NAME, 'offer-props-wrapper').find_elements(By.CLASS_NAME,
                                                                                             'bx_item_detail_size')
        reviews = driver.find_element(By.XPATH,

                                                 '//*[@id="content"]/div[2]/div/div/div/div/div/div[1]/div/div/div[3]/div[1]/div[1]/div[2]').find_element(By.ID, 'reviews').get_attribute('outerHTML')

        products_data.setdefault('product_name', product_name)
        products_data.setdefault('price', price)
        products_data.setdefault('general_attrs', general_attrs)
        products_data.setdefault('doc_path', doc_path)
        products_data.setdefault('photo_path', photo_path)
        products_data.setdefault('description_image_path', description_image_path)
        products_data.setdefault('blueprints_path', blueprints_path)
        products_data.setdefault('video_urls', video_urls)
        products_data.setdefault('product_description', description)
        products_data.setdefault('blueprints', blueprints_urls)


        varietes = []

        keys = []
        for item in _varieties:
            varietes.append(item.find_elements(By.TAG_NAME, 'li'))
        for item in product(*varietes):
            buffer = []
            try:
                for click_item in item:
                    try:
                        click_item.click()
                        buffer.append(click_item.text)
                    except:
                        raise
            except:
                continue

            keys = '_'.join(buffer)

            data = self.get_characteristics(
                driver,
                f"{general_path}/characteristics_image/{keys}",
                json_data['vendor_name'],
                product_name
            )
            # products_data.setdefault(keys, data)


            products_data.setdefault('characteristics_data', {}).setdefault(keys, data)
        products_data.setdefault('reviews', reviews)

        return products_data
        ###############################################

    def run(self):
        driver = self.get_driver()
        # self.get_all_goods_urls(driver)

        if not self.DIR_LISTS:
            self.DIR_LISTS = self.read_from_file('data/DIR_LISTS.txt', istxt=True)
        # Если сохраняются данные различных производителей
        for DIR in self.DIR_LISTS:

            json_data = self.read_from_file(f"{DIR}/vendor_data.json")
            vendor_urls = json_data.get('urls', '')
            total_urls = len(vendor_urls)
            try:
                for index, url in enumerate(vendor_urls, 1):
                # for url in ['https://kramov.by/catalog/ventilyatory/2282/',
                #             'https://kramov.by/catalog/ventilyatory/2754/',
                #             'https://kramov.by/catalog/otopitelnoe_oborudovanie/vozdushnye_zavesy/2324/?oid=2325'][
                #            ::-1]:
                    print('Начата обработка URL:', url)
                    product_data = self.get_data_from_one_product(driver, json_data, url, DIR)
                    json_data.get("products_data").append(product_data)
                    print(f"[INFO] {index}/{total_urls}")
                    # print(f"[INFO] 1/{total_urls}")
                    # break
            except Exception as e:
                print(e)
                raise
            finally:
                self.write_to_file(DIR, 'vendor_data.json', json_data)
        driver.quit()


parser = KramovParser()
parser.run()
