import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import type { Site } from '../models/site.model';
import type { PaginatedNews } from '../models/news.model';

@Injectable({ providedIn: 'root' })
export class NewsService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiBaseUrl;

  getSites(): Observable<Site[]> {
    return this.http.get<Site[]>(`${this.baseUrl}/sites`);
  }

  getNews(options?: {
    sites?: string[];
    page?: number;
    pageSize?: number;
    search?: string | null;
    timeRange?: string | null;
  }): Observable<PaginatedNews> {
    let params = new HttpParams();

    if (options?.sites && options.sites.length > 0) {
      params = params.set('sites', options.sites.join(','));
    }

    if (options?.page != null) {
      params = params.set('page', String(options.page));
    }

    if (options?.pageSize != null) {
      params = params.set('page_size', String(options.pageSize));
    }

    if (options?.search != null && options.search.trim() !== '') {
      params = params.set('search', options.search.trim());
    }

    if (options?.timeRange != null && options.timeRange.trim() !== '') {
      params = params.set('time_range', options.timeRange.trim());
    }

    return this.http.get<PaginatedNews>(`${this.baseUrl}/news`, { params });
  }
}
