import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';

import type { Site } from '../core/models/site.model';

@Component({
  selector: 'app-site-filter',
  template: `
    <div class="space-y-2" role="group" aria-label="Filtrar por site">
      @if (loading()) {
      <p class="text-sm text-slate-400">Carregando sites...</p>
      } @else { @if (sites().length === 0) {
      <p class="text-sm text-slate-400">Nenhum site disponível.</p>
      } @else {
      <div class="flex flex-wrap gap-3">
        @for (site of sites(); track site.id) {
        <label class="inline-flex items-center gap-2 text-sm text-slate-100">
          <input
            type="checkbox"
            class="h-4 w-4 rounded border-slate-700 bg-slate-900 text-sky-500 focus-visible:outline-none focus-visible:ring focus-visible:ring-sky-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
            [checked]="isSelected(site.slug)"
            (change)="onCheckboxChange(site.slug, $event.target?.checked ?? false)"
          />
          <span>{{ site.name }}</span>
        </label>
        }
      </div>
      } }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SiteFilterComponent {
  readonly sites = input<Site[]>([]);
  readonly selectedSlugs = input<string[]>([]);
  readonly loading = input(false);

  readonly selectionChange = output<string[]>();

  protected isSelected(slug: string): boolean {
    return this.selectedSlugs().includes(slug);
  }

  protected onCheckboxChange(slug: string, checked: boolean): void {
    const current = this.selectedSlugs();
    const next = checked
      ? [...current, slug].filter((s, index, arr) => arr.indexOf(s) === index)
      : current.filter((s) => s !== slug);

    this.selectionChange.emit(next);
  }
}
