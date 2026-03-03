from os import listdir
from collections import deque

from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from spiders.vinted import VintedSpider
from spiders.wallapop import WallapopSpider


def read_txt_file(file_name='search_terms.txt') -> str:
    try:
        with open(f'search_lists/{file_name}', 'r', encoding='utf-8') as f:
            return ','.join([line.strip() for line in f.readlines() if line.strip()])
    except Exception as e:
        return ''

class SequentialRunner:
    def __init__(self):
        self.process = CrawlerProcess(get_project_settings())
        self.queue = deque()

    def add_job(self, spider_cls, **kwargs):
        self.queue.append((spider_cls, kwargs))

    def _crawl_next(self):
        if not self.queue:
            print('🎉 All spiders finished')
            self.process.stop()
            return

        spider_cls, kwargs = self.queue.popleft()

        print(f'🚀 Starting {spider_cls.name} with {kwargs}')

        crawler = self.process.create_crawler(spider_cls)

        crawler.signals.connect(self.spider_closed, signal=signals.spider_closed)

        self.process.crawl(crawler, **kwargs)

    def spider_closed(self, spider, reason):
        print(f'✅ Finished {spider.name}')
        self._crawl_next()

    def start(self):
        self._crawl_next()
        self.process.start()


def main():
    runner = SequentialRunner()

    spiders = [WallapopSpider]  #[VintedSpider ,WallapopSpider]

    for file_name in listdir('search_lists'):
        if not file_name.endswith('.txt'):
            continue

        list_name = file_name.split('.')[0]
        search_terms = read_txt_file(file_name)

        for spider_cls in spiders:
            runner.add_job(spider_cls, list_name=list_name, search_terms=search_terms)

    runner.start()


if __name__ == "__main__":
    main()
