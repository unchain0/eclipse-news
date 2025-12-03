import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';

import type { PaginatedNews } from '../core/models/news.model';

@Component({
  selector: 'app-news-list',
  template: `
    <div class="space-y-4">
      @if (!hasNews()) {
      <p class="text-sm text-slate-400">Nenhuma notícia encontrada.</p>
      } @else {
      <ul class="space-y-3">
        @for (item of news()!.items; track item.id) {
        <li
          class="rounded-md border border-slate-800 bg-slate-900/60 px-4 py-3"
          [class.animate-news-enter]="isHighlighted(item.id)"
        >
          <div class="flex items-start gap-3">
            <img
              class="h-5 w-5 rounded-sm shrink-0"
              [src]="getFaviconUrl(item.url)"
              [attr.alt]="getFaviconAlt(item.url)"
              loading="lazy"
            />
            <div class="flex-1 min-w-0">
              <a
                class="text-sm font-medium text-sky-400 hover:text-sky-300 underline-offset-4 hover:underline"
                [href]="item.url"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ item.title }}
              </a>
              <p class="mt-1 text-xs text-slate-400">
                {{ item.scraped_at | date : 'short' }}
              </p>
            </div>
          </div>
        </li>
        }
      </ul>

      <nav
        class="mt-4 flex items-center justify-between text-xs text-slate-400"
        aria-label="Paginação de notícias"
      >
        <button
          type="button"
          class="rounded border border-slate-700 bg-slate-900 px-3 py-1 text-slate-100 disabled:opacity-50 disabled:cursor-not-allowed"
          (click)="onPrevious()"
          [disabled]="currentPage() <= 1"
        >
          Anterior
        </button>

        <span> Página {{ currentPage() }} de {{ totalPages() }} </span>

        <button
          type="button"
          class="rounded border border-slate-700 bg-slate-900 px-3 py-1 text-slate-100 disabled:opacity-50 disabled:cursor-not-allowed"
          (click)="onNext()"
          [disabled]="currentPage() >= totalPages()"
        >
          Próxima
        </button>
      </nav>

      @if (loading()) {
      <p class="text-xs text-slate-500">Atualizando notícias...</p>
      } }
    </div>
  `,
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
