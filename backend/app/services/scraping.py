from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import NewsModel, SiteModel
from app.services.scraping_core import (
    SITE_DISPLAY_NAMES,
    SUPPORTED_SITE_SLUGS,
    scrape_site,
)


class Scraping:
    def __init__(self, interval_seconds: int) -> None:
        self.interval_seconds = interval_seconds if interval_seconds > 0 else 60
        self._last_run_per_site: dict[str, float] = {}
        self._shutdown_event = threading.Event()
        self._current_thread: Optional[threading.Thread] = None
        self._db_session: Optional[Session] = None

    def ensure_sites_exist(self, db: Session) -> dict[str, int]:
        existing_sites = (
            db.query(SiteModel).filter(SiteModel.slug.in_(SUPPORTED_SITE_SLUGS)).all()
        )
        slug_to_site: dict[str, SiteModel] = {
            site.slug: site for site in existing_sites
        }

        for slug in SUPPORTED_SITE_SLUGS:
            desired_name = SITE_DISPLAY_NAMES.get(slug, slug.upper())

            site = slug_to_site.get(slug)
            if site is None:
                site = SiteModel(
                    slug=slug,
                    name=desired_name,
                )
                db.add(site)
                slug_to_site[slug] = site
            elif site.name != desired_name:
                site.name = desired_name

        db.commit()

        for site in slug_to_site.values():
            if site.id is None:
                db.refresh(site)

        return {
            slug: site.id for slug, site in slug_to_site.items() if site.id is not None
        }

    def scrape_all_sites_once(self, db: Session) -> None:
        self._db_session = db

        try:
            slug_to_id = self.ensure_sites_exist(db)

            total_new = 0
            for slug in SUPPORTED_SITE_SLUGS:
                if self._shutdown_event.is_set():
                    logger.info("Shutdown signal received, stopping scraping")
                    break

                site_id = slug_to_id.get(slug)
                if site_id is None:
                    continue

                now = time.time()
                last_run = self._last_run_per_site.get(slug)
                if last_run is not None and now - last_run < self.interval_seconds:
                    remaining = int(self.interval_seconds - (now - last_run))
                    logger.info(
                        "Skipping site {slug} due to cooldown ({remaining}s remaining)",
                        slug=slug,
                        remaining=remaining,
                    )
                    continue

                self._last_run_per_site[slug] = now

                articles = scrape_site(slug)
                if not articles:
                    continue

                existing_urls: set[str] = {
                    url
                    for (url,) in db.query(NewsModel.url)
                    .filter(NewsModel.site_id == site_id)
                    .all()
                }

                new_for_site = 0
                for article in articles:
                    if self._shutdown_event.is_set():
                        logger.info(
                            "Shutdown signal received during article processing"
                        )
                        break

                    if not article.url or not article.title:
                        continue

                    if article.url in existing_urls:
                        continue

                    news = NewsModel(
                        site_id=site_id,
                        title=article.title,
                        url=article.url,
                        scraped_at=datetime.now(timezone.utc),
                    )
                    db.add(news)
                    existing_urls.add(article.url)
                    new_for_site += 1

                if new_for_site:
                    logger.info(
                        "Inserted {count} new articles for site {slug}",
                        count=new_for_site,
                        slug=slug,
                    )
                    total_new += new_for_site

                if self._shutdown_event.is_set():
                    break

            if total_new:
                db.commit()
            else:
                logger.info("No new articles found in this scraping cycle")

        finally:
            self._db_session = None

    def run_once(self) -> None:
        with SessionLocal() as db:
            self.scrape_all_sites_once(db)

    def loop(self) -> None:
        logger.info(
            "Starting scraping loop with interval {interval}s",
            interval=self.interval_seconds,
        )

        self._current_thread = threading.current_thread()

        try:
            while not self._shutdown_event.is_set():
                start = time.time()
                try:
                    self.run_once()
                except Exception as exc:
                    logger.exception(
                        "Unexpected error in scraping loop: {exc}", exc=exc
                    )

                duration = time.time() - start
                logger.debug(
                    "Scraping cycle finished in {duration:.2f}s", duration=duration
                )

                self._shutdown_event.wait(timeout=self.interval_seconds)

        except Exception as exc:
            logger.exception("Fatal error in scraping loop: {exc}", exc=exc)
        finally:
            logger.info("Scraping loop terminated")
            self._current_thread = None

    def shutdown(self, timeout: float = 10.0) -> None:
        """Initiate graceful shutdown of the scraping loop."""
        logger.info(
            "Initiating scraping shutdown with {timeout}s timeout", timeout=timeout
        )

        self._shutdown_event.set()

        if self._current_thread and self._current_thread.is_alive():
            pass

        if self._current_thread and self._current_thread.is_alive():
            self._current_thread.join(timeout=timeout)

            if self._current_thread.is_alive():
                logger.warning(
                    "Scraping thread did not terminate gracefully within timeout"
                )
            else:
                logger.info("Scraping thread terminated gracefully")

        if self._db_session:
            try:
                self._db_session.rollback()
                self._db_session.close()
            except Exception as exc:
                logger.error(
                    "Error cleaning up database session during shutdown: {exc}", exc=exc
                )
            finally:
                self._db_session = None
