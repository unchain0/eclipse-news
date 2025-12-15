#!/usr/bin/env python3
"""
Standalone scraper process.

This script runs the web scraper as a separate, independent process.
It can be run manually, via cron job, or by a process manager.

Usage:
    python run_scraper.py

Environment variables:
    SCRAPE_INTERVAL_SECONDS: Interval between scraping cycles (default: 60)
    DATABASE_URL: PostgreSQL connection string
    ALLOWED_DOMAINS: Comma-separated list of allowed domains
"""

import argparse
import signal
import sys
import time
from contextlib import contextmanager

from loguru import logger

from app.config import settings
from app.services.scraping import Scraping


class ScraperProcess:
    """Manages the scraper process lifecycle."""

    def __init__(self):
        self.scraping = Scraping(settings.scrape_interval_seconds)
        self._running = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown")
            self._running = False
            self.scraping.shutdown(timeout=10.0)
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    @contextmanager
    def managed_session(self):
        """Context manager for scraping session with error handling."""
        try:
            yield
        except KeyboardInterrupt:
            logger.info("Scraping interrupted by user")
        except Exception as exc:
            logger.exception("Unexpected error in scraping process: {exc}", exc=exc)
        finally:
            logger.info("Scraping session ended")

    def run_single_cycle(self):
        """Run a single scraping cycle."""
        logger.info("Starting single scraping cycle")
        try:
            self.scraping.run_once()
            logger.info("Single scraping cycle completed")
        except Exception as exc:
            logger.exception("Error during scraping cycle: {exc}", exc=exc)

    def run_continuous(self):
        """Run scraping continuously with the configured interval."""
        logger.info(
            f"Starting continuous scraping with {self.scraping.interval_seconds}s interval"
        )

        self._running = True

        with self.managed_session():
            while self._running:
                start_time = time.time()

                try:
                    self.scraping.run_once()
                except Exception as exc:
                    logger.exception("Error during scraping cycle: {exc}", exc=exc)

                cycle_duration = time.time() - start_time
                sleep_time = max(0, self.scraping.interval_seconds - cycle_duration)

                if sleep_time > 0:
                    logger.debug(f"Sleeping for {sleep_time:.2f}s until next cycle")
                    time.sleep(sleep_time)
                else:
                    logger.warning(
                        f"Scraping cycle took {cycle_duration:.2f}s, "
                        f"longer than interval {self.scraping.interval_seconds}s"
                    )

    def run(self, mode: str = "continuous"):
        """Run the scraper in the specified mode."""
        logger.info(f"Starting scraper process in '{mode}' mode")

        if mode == "single":
            self.run_single_cycle()
        elif mode == "continuous":
            self.run_continuous()
        else:
            logger.error(f"Invalid mode: {mode}. Use 'single' or 'continuous'")
            sys.exit(1)


def main():
    """Main entry point for the scraper process."""
    parser = argparse.ArgumentParser(description="Run the web scraper")
    parser.add_argument(
        "--mode",
        choices=["single", "continuous"],
        default="continuous",
        help="Scraping mode: single (one cycle) or continuous (default)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        help=f"Scraping interval in seconds (default: {settings.scrape_interval_seconds})",
    )

    args = parser.parse_args()
    if args.interval:
        if args.interval <= 0:
            logger.error("Interval must be greater than 0")
            sys.exit(1)
        settings.scrape_interval_seconds = args.interval

    if not settings.database_url:
        logger.error("DATABASE_URL environment variable is required")
        sys.exit(1)

    logger.info(
        f"Database URL configured: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'localhost'}"
    )
    logger.info(f"Scraping interval: {settings.scrape_interval_seconds} seconds")

    scraper = ScraperProcess()
    scraper.run(mode=args.mode)


if __name__ == "__main__":
    main()
