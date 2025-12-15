import { bootstrapApplication } from '@angular/platform-browser';
import { registerLocaleData } from '@angular/common';
import { appConfig } from './app/app.config';
import { App } from './app/app';
import localePt from '@angular/common/locales/pt';

registerLocaleData(localePt);

bootstrapApplication(App, appConfig).catch((err) => console.error(err));
