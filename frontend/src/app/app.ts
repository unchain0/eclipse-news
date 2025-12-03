import { ChangeDetectionStrategy, Component } from '@angular/core';

import { Home } from './screens/home/home';

@Component({
  selector: 'app-root',
  templateUrl: './app.html',
  styleUrls: ['./app.css'],
  imports: [Home],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {}
