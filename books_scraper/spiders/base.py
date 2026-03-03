import os, csv
from typing import Iterable, Any
from urllib.parse import urlparse
from collections import OrderedDict

from scrapy import Spider, Request
from collections import defaultdict

from .database import DatabaseManager


class BaseSpider(Spider):
    name = 'base'
    start_url = 'https://example.com'
    headers = {}

    custom_settings = {
        'CONCURRENT_REQUESTS': 5,

        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2.5,
        'AUTOTHROTTLE_MAX_DELAY': 5,

        'DOWNLOAD_DELAY': 1,
        'RANDOMIZE_DOWNLOAD_DELAY': True,

        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408, 429, 401],

        'URLLENGTH_LIMIT': 10000
    }

    def __init__(self, list_name: str=None, search_terms: str= None, **kwargs):
        super().__init__(**kwargs)
        self.recent_scraped_urls = set()
        self.spider_name = f'{self.name}_{list_name}'
        self.spider_domain = urlparse(self.start_url).netloc
        self.search_keys = set(search_terms.split(',')) if search_terms else set()

        # Database manager
        self.db = DatabaseManager()
        self.site_id = self.db.save_spider_info(spider_name=self.spider_name, spider_domain=self.spider_domain)
        os.makedirs(name='utils', exist_ok=True)
        self.unrelated_file_name = f'utils/{self.name}_unrelated_urls.csv'
        self.unrelated_data = self.read_csv(filename=self.unrelated_file_name)
        self.expected_urls = {}
        self.found_urls = defaultdict(set)


    def start_requests(self) -> Iterable[Any]:
        yield Request(url=self.start_url, callback=self.parse, meta={'handle_httpstatus_all': True})

    def get_item(self, html_response=None, json_response=None):
        json_response = {} if not json_response else json_response
        item = OrderedDict()

        item['Search Term'] = self.get_search_term(html_response, json_response)
        item['Name'] = self.get_name(html_response, json_response)
        item['Price'] = self.get_price(html_response, json_response)
        item['Seller'] = self.get_seller(html_response, json_response)
        item['Condition'] = self.get_condition(html_response, json_response)
        item['Editorial'] = self.get_editorial(html_response, json_response)
        item['Image'] = self.get_images(html_response, json_response)
        item['Url'] = self.get_url(html_response, json_response)

        return item

    # ---------------- Getters (to override) ----------------
    def get_search_term(self, html_response, json_response):
        return ''

    def get_name(self, html_response, json_response):
        return ''

    def get_price(self, html_response, json_response):
        return ''

    def get_seller(self, html_response, json_response):
        return ''

    def get_condition(self, html_response, json_response):
        return ''

    def get_editorial(self, html_response, json_response):
        return ''

    def get_images(self, html_response, json_response):
        return ''

    def get_url(self, html_response, json_response):
        return ''


    # Using these functions as the vinted site show unrelated urls that didn't match the search term
    def read_csv(self, filename: str) -> list:
        data = []
        try:
            with open(filename, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data.append(row)

        except Exception as e:
            self.logger.info(str(e))

        return data

    def get_all_urls_against_search_term(self, search_term: str) -> list[str]:
        return [item.get('Url') for item in self.unrelated_data if item.get('Search Term') == search_term]

    @staticmethod
    def write_to_csv(data, mode: str = 'a', output_filename=None) -> None:
        headers = data.keys() if isinstance(data, OrderedDict) else data[0].keys()
        with open(output_filename, mode, newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)

            if csvfile.tell() == 0:
                writer.writeheader()

            if isinstance(data, OrderedDict):
                writer.writerow(data)
            else:
                for row in data:
                    writer.writerow(row)