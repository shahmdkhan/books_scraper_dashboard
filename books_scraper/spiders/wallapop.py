from json import loads
from typing import Any
from urllib.parse import urlencode

import requests
from scrapy import Request
from scrapy.http import Response

from .base import BaseSpider


class WallapopSpider(BaseSpider):
    name = "wallapop"
    start_url = 'https://es.wallapop.com/'

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'es,en-US;q=0.9',
        'Connection': 'keep-alive',
        'DeviceOS': '0',
        'Origin': 'https://es.wallapop.com',
        'Referer': 'https://es.wallapop.com/',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'X-DeviceOS': '0',
    }

    def __init__(self, list_name: str=None, search_terms: str= None, **kwargs):
        super().__init__(list_name, search_terms, **kwargs)


    def parse(self, response, **kwargs):
        for isbn in self.search_keys:
            self.expected_urls[isbn] = self.db.fetch_urls_by_site_and_isbn(site_id=self.site_id, isbn=isbn)
            yield self.build_request(isbn=isbn)


    def parse_listing(self, response):
        try:
            products = loads(response.text).get('data', {}).get('section', {}).get('payload', {}).get('items', [])
        except Exception as e:
            self.logger.error(f"Error parsing response: {e}")
            products = []

        isbn = response.meta.get('isbn')

        # Initialize found_urls for this ISBN if not already
        if isbn not in self.found_urls:
            self.found_urls[isbn] = set()

        for product in products:
            url = f"https://www.wallapop.com/item/{product.get('web_slug')}"
            price = product.get('price', {}).get('amount', 0) or 0

            # Track this URL as found in this run
            self.found_urls[isbn].add(url)

            # Check if product exists in DB
            if self.db.update_detail_entry(url=url, price=price, availability=True):
                # Already exists: skip detail page
                print(f"Updated existing product: {url}, skipped detail page.\n")

            else:
                # New product: request detail page
                yield Request(url=url, headers=self.headers, callback=self.parse_details, meta={'isbn': isbn})
                print(f'Insert New Record: {url}\n')


    def parse_details(self, response: Response) -> Any:
        json_data = loads(response.css('script[id="__NEXT_DATA__"]::text').extract_first('{}')) or {}
        json_item = json_data.get('props', {}).get('pageProps', {}).get('item', {})
        json_item['isbn'] = response.meta.get('isbn', '')
        json_item['Url'] = response.url

        yield self.get_item(json_response=json_item)


    # ---------------- Getter methods (stubs to override) ----------------
    def get_search_term(self, html_response, json_response):
        return json_response.get('isbn', '')

    def get_name(self, html_response, json_response):
        return json_response.get('title', {}).get('original', '')

    def get_price(self, html_response, json_response):
        return str(json_response.get('price', {}).get('cash', {}).get('amount', ''))

    def get_condition(self, html_response, json_response):
        return json_response.get('condition', {}).get('text', 'Unknown') or 'Unknown'

    def get_seller(self, html_response, json_response):
        seller_url = f"https://api.wallapop.com/api/v3/users/{json_response.get('userId', '')}"
        seller_response = requests.get(url=seller_url, headers=self.headers)

        return self.load_json_data(response=seller_response).get('micro_name', '')

    def get_images(self, html_response, json_response):
        return [row.get('urls', {}).get('big', '') for row in json_response.get('images', [])]

    def get_url(self, html_response, json_response):
        return json_response.get('Url', '')

    def build_request(self, isbn: str, next_page_token: str = None) -> Request:
        params = {
            'source': 'search_box',
            'keywords': isbn,
            'latitude': '40.41956',
            'longitude': '-3.69196',
        }

        if next_page_token:
            params['next_page'] = next_page_token

        return Request(url=f'https://api.wallapop.com/api/v3/search?{urlencode(params)}', headers=self.headers,
                       callback=self.parse_listing, meta={'isbn': isbn})

    def load_json_data(self, response):
        try:
            json_data = loads(response.text)
        except Exception as e:
            self.logger.error(e)
            json_data = {}

        return json_data
