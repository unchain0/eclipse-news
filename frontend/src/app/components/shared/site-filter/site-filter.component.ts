import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';

import type { Site } from '../../../model/site.model';

@Component({
  selector: 'app-site-filter',
  templateUrl: './site-filter.component.html',
  styleUrl: './site-filter.component.css',
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
