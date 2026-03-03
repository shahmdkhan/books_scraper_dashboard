
class SQLitePipeline:
    def __init__(self):
        super().__init__()
        self.seen_items = set()

    def process_item(self, item, spider):
        site_id = spider.site_id
        isbn = item.get('Search Term')
        url = item.get('Url')
        key = (site_id, isbn, url)

        if key not in self.seen_items:
            self.seen_items.add(key)

        history_id = spider.db.save_history_entry(site_id=spider.site_id, isbn=isbn)
        updated_row_id = spider.db.update_detail_entry(url=url, price=item.get("Price"), availability=True)

        if not updated_row_id:
            spider.db.save_detail_entry(item=item, history_id=history_id, site_id=spider.site_id)

        return item

    def close_spider(self, spider):
        spider.logger.info("Pipeline closing spider and updating availability")

        # Run-scoped availability update
        for isbn, expected_urls in spider.expected_urls.items():
            found_urls = spider.found_urls.get(isbn, set())
            missing_urls = expected_urls - found_urls

            if missing_urls:
                spider.logger.info(f"[Pipeline] ISBN {isbn} → {len(missing_urls)} products marked unavailable")
                spider.db.mark_urls_unavailable(site_id=spider.site_id, isbn=isbn, urls=missing_urls)

        # update history counts, delete old unavailable, close DB
        spider.db.update_history_counts(site_id=spider.site_id)
        spider.db.delete_old_unavailable_details(site_id=spider.site_id)
        spider.db.close()

