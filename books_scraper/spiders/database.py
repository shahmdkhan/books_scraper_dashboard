import os
from datetime import date, timedelta
from collections import OrderedDict
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, select, update, func, delete
from sqlalchemy.orm import sessionmaker

from .models import Base, Source, History, Detail


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class DatabaseManager:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        db_path = os.environ.get("DATABASE_URL")
        self.engine = create_engine(db_path, echo=False, future=True)
        Session = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.session = Session()

    # ── SOURCE ─────────────────────────────────────────────────────────────
    def save_spider_info(self, spider_name: str, spider_domain: str) -> int:
        row = (
            self.session.query(Source)
            .filter(Source.spider_name == spider_name, Source.spider_domain == spider_domain)
            .first()
        )
        if not row:
            row = Source(spider_name=spider_name, spider_domain=spider_domain)
            self.session.add(row)
            self.session.commit()
        return row.spider_id

    # ── FETCH HELPERS ──────────────────────────────────────────────────────
    def fetch_scraped_urls(self, site_id: int, availability: bool = True) -> list[str]:
        return (
            self.session.execute(
                select(Detail.url).where(
                    Detail.site_id == site_id,
                    Detail.availability == availability,
                )
            )
            .scalars()
            .all()
        )

    def fetch_urls_by_site_and_isbn(self, site_id: int, isbn: str) -> set[str]:
        rows = (
            self.session.execute(
                select(Detail.url).where(
                    Detail.site_id == site_id,
                    Detail.isbn == isbn,
                    Detail.availability.is_(True),
                )
            )
            .scalars()
            .all()
        )
        return set(rows)

    # ── HISTORY ────────────────────────────────────────────────────────────
    def save_history_entry(self, site_id: int, isbn: str) -> int:
        row = (
            self.session.query(History)
            .filter(History.site_id == site_id, History.isbn == isbn)
            .first()
        )
        if row:
            return row.history_id

        new_row = History(site_id=site_id, isbn=isbn)
        self.session.add(new_row)
        self.session.commit()
        return new_row.history_id

    # ── DETAIL UPDATE ──────────────────────────────────────────────────────
    def update_detail_keep_newest(self, url: str, updates: dict) -> int | None:
        if not url:
            return None
        detail = (
            self.session.query(Detail)
            .filter(Detail.url == url)
            .order_by(Detail.detail_id.desc())
            .first()
        )
        if not detail:
            return None
        for key, value in updates.items():
            setattr(detail, key, value)
        self.session.commit()
        return detail.detail_id

    def update_detail_entry(self, url: str, price: float, availability: bool):
        updates = {"price": price, "availability": availability, "date_scraped": date.today()}
        return self.update_detail_keep_newest(url, updates)

    # ── DETAIL INSERT ──────────────────────────────────────────────────────
    def save_detail_entry(self, item: OrderedDict, history_id: int, site_id: int) -> int:
        new_detail = Detail(
            history_id   = history_id,
            isbn         = item.get("Search Term"),
            name         = item.get("Name"),
            price        = float(item.get("Price") or 0),
            seller       = item.get("Seller"),
            condition    = item.get("Condition"),
            editorial    = item.get("Editorial"),
            images       = item.get("Image"),
            url          = item.get("Url"),
            site_id      = site_id,
            availability = True,
            date_scraped = date.today(),
            first_seen   = date.today(),
            # interest defaults to "pending" via column default
        )
        self.session.add(new_detail)
        self.session.commit()
        return new_detail.detail_id

    # ── AVAILABILITY CONTROL ───────────────────────────────────────────────
    def mark_urls_unavailable(self, site_id: int, isbn: str, urls: set[str]) -> None:
        if not urls:
            return
        self.session.execute(
            update(Detail)
            .where(Detail.site_id == site_id, Detail.isbn == isbn, Detail.url.in_(urls))
            .values(availability=False, date_scraped=date.today())
        )
        self.session.commit()

    def mark_item_availability(self, site_id: int, url: str, availability: bool = False):
        self.session.execute(
            update(Detail)
            .where(Detail.site_id == site_id, Detail.url == url)
            .values(availability=availability)
        )
        self.session.commit()

    # ── HISTORY COUNTS ─────────────────────────────────────────────────────
    def update_history_counts(self, site_id: int):
        history_ids = (
            self.session.execute(select(History.history_id).where(History.site_id == site_id))
            .scalars()
            .all()
        )
        for history_id in history_ids:
            available_count = (
                self.session.query(func.count(Detail.detail_id))
                .filter(Detail.history_id == history_id, Detail.availability.is_(True))
                .scalar()
            )
            sold_count = (
                self.session.query(func.count(Detail.detail_id))
                .filter(Detail.history_id == history_id, Detail.availability.is_(False))
                .scalar()
            )
            self.session.execute(
                update(History)
                .where(History.history_id == history_id)
                .values(available_books=available_count, sold_books=sold_count)
            )
        self.session.commit()

    # ── CLEANUP ────────────────────────────────────────────────────────────
    def delete_old_unavailable_details(self, site_id: int):
        cutoff_date = date.today() - timedelta(days=30)
        history_ids = select(History.history_id).where(History.site_id == site_id)
        self.session.execute(
            delete(Detail).where(
                Detail.availability.is_(False),
                Detail.date_scraped < cutoff_date,
                Detail.history_id.in_(history_ids),
            )
        )
        self.session.commit()

    # ── DELETE SPIDER ──────────────────────────────────────────────────────
    def delete_spider_records(self, spider_name: str):
        try:
            spider = self.session.query(Source).filter(Source.spider_name == spider_name).first()
            if not spider:
                return

            spider_id   = spider.spider_id
            history_ids = [
                h[0]
                for h in self.session.query(History.history_id)
                .filter(History.site_id == spider_id)
                .all()
            ]
            if history_ids:
                self.session.query(Detail).filter(Detail.history_id.in_(history_ids)).delete(
                    synchronize_session=False
                )
                self.session.query(History).filter(History.history_id.in_(history_ids)).delete(
                    synchronize_session=False
                )
            self.session.query(Source).filter(Source.spider_id == spider_id).delete(
                synchronize_session=False
            )
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def close(self):
        self.session.close()