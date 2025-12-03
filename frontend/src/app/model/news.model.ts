export interface News {
  id: number;
  site_id: number;
  title: string;
  url: string;
  scraped_at: string;
}

export interface PaginatedNews {
  items: News[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
