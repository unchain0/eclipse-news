import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';

import type { PaginatedNews } from '../../../model/news.model';

@Component({
  selector: 'app-news-list',
  templateUrl: './news-list.component.html',
  imports: [DatePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsListComponent {
  readonly news = input<PaginatedNews | null>(null);
  readonly loading = input(false);
  readonly highlightIds = input<number[]>([]);

  readonly pageChange = output<number>();

  protected readonly hasNews = computed(() => {
    const value = this.news();
    return !!value && value.items.length > 0;
  });

  protected readonly currentPage = computed(() => this.news()?.page ?? 1);
  protected readonly totalPages = computed(() => this.news()?.pages ?? 1);

  protected isHighlighted(id: number): boolean {
    return this.highlightIds().includes(id);
  }

  protected getFaviconUrl(rawUrl: string): string {
    try {
      const url = new URL(rawUrl);
      const origin = url.origin;
      const encoded = encodeURIComponent(origin);
      return `https://www.google.com/s2/favicons?sz=64&domain_url=${encoded}`;
    } catch {
      return '';
    }
  }

  protected getFaviconAlt(rawUrl: string): string {
    try {
      const url = new URL(rawUrl);
      return `Ícone do site ${url.hostname}`;
    } catch {
      return 'Ícone do site';
    }
  }

  protected onPrevious(): void {
    const page = this.currentPage();
    if (page > 1) {
      this.pageChange.emit(page - 1);
    }
  }

  protected onNext(): void {
    const page = this.currentPage();
    const total = this.totalPages();
    if (page < total) {
      this.pageChange.emit(page + 1);
    }
  }
}
