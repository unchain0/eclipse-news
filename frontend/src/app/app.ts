import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';

import type { PaginatedNews } from './core/models/news.model';
import type { Site } from './core/models/site.model';
import { NewsService } from './core/services/news.service';
import { NewsListComponent } from './news/news-list.component';
import { SiteFilterComponent } from './news/site-filter.component';

@Component({
  selector: 'app-root',
  templateUrl: './app.html',
  styleUrl: './app.css',
  imports: [SiteFilterComponent, NewsListComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App implements OnInit {
  private readonly newsService = inject(NewsService);

  protected readonly sites = signal<Site[]>([]);
  protected readonly loadingSites = signal(false);

  protected readonly selectedSlugs = signal<string[]>([]);
  protected readonly page = signal(1);
  protected readonly pageSize = 20;

  protected readonly loadingNews = signal(false);
  protected readonly paginatedNews = signal<PaginatedNews | null>(null);

  ngOnInit(): void {
    this.loadSitesAndInitialNews();
  }

  private loadSitesAndInitialNews(): void {
    this.loadingSites.set(true);

    this.newsService.getSites().subscribe({
      next: (sites) => {
        this.sites.set(sites);
        this.selectedSlugs.set(sites.map((site) => site.slug));
        this.loadingSites.set(false);
        this.loadNews();
      },
      error: (error) => {
        console.error('Failed to load sites', error);
        this.loadingSites.set(false);
      },
    });
  }

  protected onSelectionChange(slugs: string[]): void {
    this.selectedSlugs.set(slugs);
    this.page.set(1);
    this.loadNews();
  }

  protected onPageChange(newPage: number): void {
    this.page.set(newPage);
    this.loadNews();
  }

  private loadNews(): void {
    const slugs = this.selectedSlugs();

    if (slugs.length === 0) {
      this.paginatedNews.set({
        items: [],
        total: 0,
        page: 1,
        page_size: this.pageSize,
        pages: 0,
      });
      return;
    }

    this.loadingNews.set(true);

    this.newsService
      .getNews({
        sites: slugs,
        page: this.page(),
        pageSize: this.pageSize,
      })
      .subscribe({
        next: (response) => {
          this.paginatedNews.set(response);
        },
        error: (error) => {
          console.error('Failed to load news', error);
          this.loadingNews.set(false);
        },
        complete: () => {
          this.loadingNews.set(false);
        },
      });
  }
}
