import os
from typing import Any
from urllib.parse import urlencode
from collections import OrderedDict

from scrapy import Request
from scrapy.http import Response

from .base import BaseSpider


class VintedSpider(BaseSpider):
    name = "vinted"
    start_url = 'https://www.vinted.es/'

    SCRAPEOPS_API_KEY = os.environ.get("SCRAPEOPS_API_KEY", "")
    custom_settings = {
        'CONCURRENT_REQUESTS': 2,

        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408, 429, 401],

        'SCRAPEOPS_PROXY_ENABLED': True,
        # todo: replace with your key
        'SCRAPEOPS_API_KEY': SCRAPEOPS_API_KEY,
        'SCRAPEOPS_PROXY_SETTINGS': {
            'country': 'es',
            'keep_headers': 'true'
        },

        'DOWNLOADER_MIDDLEWARES': {
            'scrapeops_scrapy_proxy_sdk.scrapeops_scrapy_proxy_sdk.ScrapeOpsScrapyProxySdk': 725,
        },

    }

    def __init__(self, list_name: str = None, search_terms: str = None, **kwargs):
        super().__init__(list_name, search_terms, **kwargs)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for isbn in self.search_keys:
            isbn = str(isbn).strip()
            url = f"https://www.vinted.es/catalog?{urlencode({'search_text': isbn})}"
            yield Request(url=url, callback=self.parse_listing, meta={'search_key': isbn}, dont_filter=True)


    def parse_listing(self, response: Response) -> Any:
        search_key = response.meta.get('search_key')
        unrelated_urls = self.get_all_urls_against_search_term(search_term=search_key)

        products_list = response.css('.feed-grid__item-content')

        for product in products_list:
            product_url = product.css('a::attr(href)').get()
            if not product_url:
                continue

            url = product_url.replace('?referrer=catalog', '')
            price_text = product.css('.new-item-box__title p ::text').re_first(r'(\d+,\d+|\d+)')
            price = float(price_text.strip().replace('.', '').replace(',', '.')) if price_text else None

            if url in unrelated_urls:
                print(f'Skipping unrelated item: {url}')
                continue

            if self.db.update_detail_entry(url=url, price=price, availability=True):
                # Product exists: update price & availability, skip detail page
                self.recent_scraped_urls.add(url)
                print(f"Updated existing product: {url}, skipped detail page.\n")
            else:
                yield Request(url=url, callback=self.parse_detail_pages, meta={'url': url, 'search_key': search_key},
                              dont_filter=True)
                print(f'Insert New Record: {url}\n')

        if next_url:=(response.css('[data-testid="catalog-pagination--next-page"][aria-disabled="false"]::attr(href)').
                extract_first('').strip()):
            yield Request(url=self.start_url+next_url, callback=self.parse_listing, meta={'search_key': search_key},
                          dont_filter=True)

    def parse_detail_pages(self, response: Response):
        # Checking the ISBN no.
        search_key = response.meta.get('search_key').strip()
        if response.css('[data-testid="item-attributes-isbn_nav-link"] ::text').extract_first('').strip() == search_key:
            yield self.get_item(html_response=response)

        else:
            self.logger.debug(f"ISBN didn\'t match with {search_key}")
            new_item = OrderedDict()

            new_item['Search Term'] = search_key
            new_item['Url'] = response.meta.get('url')

            self.write_to_csv(data=new_item, output_filename=self.unrelated_file_name)
            print(new_item)

    def get_search_term(self, html_response, json_response):
        return html_response.meta.get('search_key')

    def get_name(self, html_response, json_response):
        return (html_response.css('[data-testid="item-page-summary-plugin"] .web_ui__Text__title ::text').
                extract_first('').strip())

    def get_price(self, html_response, json_response):
        return float(html_response.css('[data-testid="item-price"] p ::text').re_first(r'(\d+,\d+|\d+)').strip().replace('.', '').replace(',', '.'))

    def get_seller(self, html_response, json_response):
        return html_response.css('[data-testid="profile-username"] ::text').extract_first('').strip()

    def get_condition(self, html_response, json_response):
        return next(reversed(html_response.css('.summary-max-lines-4 span ::text').getall()), '')

    def get_editorial(self, html_response, json_response):
        return html_response.css('.details-list__item-value:contains(Marca) + div a ::text').extract_first('').strip()

    def get_images(self, html_response, json_response):
        return html_response.css('[data-photoid] img ::attr(src)').getall()

    def get_url(self, html_response, json_response):
        return html_response.meta.get('url')
