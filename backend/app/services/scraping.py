from __future__ import annotations

import time
from datetime import datetime, timezone

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
        slug_to_id = self.ensure_sites_exist(db)

        total_new = 0
        for slug in SUPPORTED_SITE_SLUGS:
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

        if total_new:
            db.commit()
        else:
            logger.info("No new articles found in this scraping cycle")

    def run_once(self) -> None:
        with SessionLocal() as db:
            self.scrape_all_sites_once(db)

    def loop(self) -> None:
        logger.info(
            "Starting scraping loop with interval {interval}s",
            interval=self.interval_seconds,
        )

        while True:
            start = time.time()
            try:
                self.run_once()
            except Exception as exc:
                logger.exception("Unexpected error in scraping loop: {exc}", exc=exc)

            duration = time.time() - start
            logger.debug(
                "Scraping cycle finished in {duration:.2f}s", duration=duration
            )
            time.sleep(self.interval_seconds)
