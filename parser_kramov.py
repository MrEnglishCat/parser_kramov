from dataclasses import dataclass
import json
import re
import os
import time

import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup


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
    URL = 'https://kramov.by/catalog'
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
    def write_to_json(path, data):
        __class__.check_folder('data/json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

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

    def get_categories(self):
        result = []  # {'category_name':'', 'category_url':''}
        response = requests.get(type(self).URL,
                                headers=self.HEADERS)
        soup = BeautifulSoup(response.content, 'lxml')

        categories = soup.find('div', class_='section-content-wrapper').find_all('div',
                                                                                 class_='item_block lg col-lg-20 col-md-4 col-xs-6')

        for index, category in enumerate(categories, 1):
            url = re.search(r"(?<=\/catalog).*", category.find('a', class_='dark_link')['href']).group()
            title = category.find('span', class_='font_md').get_text()
            amount_of_goods = category.find('span', class_='element-count2 muted font_xs').get_text()
            result.append(
                {
                    'category_name': title,
                    'category_url': url,
                    'amount_of_goods': amount_of_goods
                }
            )
            print(f"[INFO {index} of {len(categories)}] ({amount_of_goods}) {title} - {url}")

        return result

    def get_all_data_from_url(self, url):
        response = requests.get(url, headers=self.HEADERS)
        soup = BeautifulSoup(response.content, 'lxml')
        position = KramovDataClass()
        position.brand_name = soup.find('a', class_='brand__picture').get('title')
        position.brand_url = self.BASE_URL + soup.find('a', class_='brand__picture').get('href')
        response_brand = requests.get(position.brand_url, self.HEADERS)
        print(response_brand.status_code, position.brand_url)
        position.brand_description = BeautifulSoup(response_brand.content, 'lxml').find('div', class_='inner_wrapper_text').find_all('p')
        # position.brand_img = soup.find('a', class_='brand__picture').find('img').get('')
        # position.brand_img_url =
        position.preview = [''.join(filter(lambda char: char not in ('\n', '\t', '\r'), item.text.strip())) for item in soup.find('div', class_='preview-text').find_all('tr')]

        print(position)

    def get_data(self, json_data):
        print(json_data)
        for row in json_data:
            for url in row['urls']:
                self.get_all_data_from_url(self.BASE_URL + url)

                break
            break

    def get_next_page(self, soup):
        return soup.find('div', class_='nums').find('a', class_='flex-next').get('href')

    def get_all_items_from_pages(self, soup, index, categories: json):
        elements = soup.find_all('div',
                                 class_='col-lg-3 col-md-4 col-sm-6 col-xs-6 col-xxs-12 item item-parent item_block')
        categories[index].setdefault('urls', [])
        # categories[index].setdefault('urls', set())
        for element in elements:
            url = element.find('a').get('href')
            categories[index]['urls'].append(url)
            # categories[index]['urls'].

    def get_items_url_from_category(self, categories: json):
        for index, category in enumerate(categories):
            category_url = category.get('category_url')
            url = self.URL + category_url
            start_pagination = True
            while start_pagination:
                response = requests.get(url, headers=self.HEADERS)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'lxml')
                    self.get_all_items_from_pages(soup, index, categories)
                    try:
                        pagination = self.get_next_page(soup)
                        url = self.BASE_URL + pagination
                    except Exception as e:
                        start_pagination = False



                else:
                    print(f"[ALERT {response.status_code}] {url}")
            print(f"[INFO {index} of {len(categories)}] обработан ({category_url})")

    def run(self):
        # categories = self.get_categories()
        # self.write_to_json(f'{self.BASE_FILE_PATH}/json/kramov_categories.json', categories)
        # json_data = self.read_from_json(f'{self.BASE_FILE_PATH}/json/kramov_categories.json')
        # self.get_items_url_from_category(json_data)
        # self.write_to_json(f'{self.BASE_FILE_PATH}/json/kramov_categories.json', json_data)
        json_data = self.read_from_json(f'{self.BASE_FILE_PATH}/json/kramov_categories.json', issearch=False)
        self.get_data(json_data)


parser = KramovParser()
parser.run()
