# # Scrapy-Playwright settings
# import logging
# logging.getLogger("scrapy-playwright").setLevel(logging.WARNING)
#
# # Enable Scrapy-Playwright
# DOWNLOAD_HANDLERS = {
#     "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
#     "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
# }
# PLAYWRIGHT_LOGGING_LEVEL = "DEBUG"
# PLAYWRIGHT_CLOSE_PAGE_ON_ERROR = True
# PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 170000  # Timeout in ms (170s)
# PLAYWRIGHT_BROWSER_TYPE = "chromium"
# # PLAYWRIGHT_LAUNCH_OPTIONS = {
# #     "headless": False,
# #     # "executable_path":  r"C:\Users\dell\AppData\Local\Programs\Opera GX\opera.exe",
# #     # "executable_path":  r"C:\Users\dell\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe",
# #     # "executable_path":  r"C:\Users\dell\AppData\Local\camoufox\camoufox\Cache\camoufox.exe",
# # }
#
# def should_abort_request(request):
#     return request.resource_type == "image" or ".jpg" in request.url
#
# PLAYWRIGHT_ABORT_REQUEST = should_abort_request
# # Needed for scrapy-playwright
# TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

BOT_NAME = "books_scraper"

SPIDER_MODULES = ["books_scraper.spiders"]
NEWSPIDER_MODULE = "books_scraper.spiders"

ADDONS = {}

ITEM_PIPELINES = {
    'books_scraper.pipelines.SQLitePipeline': 300,
}


# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "books_scraper.middlewares.BooksScraperSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "books_scraper.middlewares.BooksScraperDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    "books_scraper.pipelines.BooksScraperPipeline": 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"