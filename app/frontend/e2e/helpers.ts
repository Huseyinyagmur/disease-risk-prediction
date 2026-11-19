import { expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

export const SAMPLES = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../public/samples');
export const sample = (n: string) => path.join(SAMPLES, n);
export const sampleBytes = (n: string) => readFileSync(sample(n));

export async function openForm(page: Page) {
  await page.goto('/');
  await page.getByTestId('start').click();
  await expect(page.getByTestId('section-temel')).toBeVisible();
}

export async function loadProfile(page: Page, id: string) {
  await page.getByTestId(`profile-${id}`).click();
  await expect(page.getByTestId('profile-loaded')).toBeVisible();
}

/** Panelde modelin durumu beklenen değere gelene dek bekler (debounce + sunucu). */
export async function expectPanel(page: Page, modelId: string, state: string, text?: string | RegExp) {
  const item = page.getByTestId(`panel-${modelId}`);
  await expect(item).toHaveAttribute('data-state', state);
  if (text) await expect(page.getByTestId(`panel-line-${modelId}`)).toContainText(text);
}

export async function submit(page: Page) {
  await page.getByTestId('submit').click();
  await expect(page.getByText('Ana modüller ve araştırma modülü')).toBeVisible();
}

export async function openEcg(page: Page) {
  await page.goto('/');
  await page.getByTestId('start-ecg').click();
  await expect(page.getByTestId('dropzone')).toBeVisible();
}

/** Analizi başlatır; sonuç kartı veya hata görünene dek bekler. Başlık ön kontrolünde anında ABSTAIN olan kayıtlarda
 * ilerleme göstergesi çok kısa görünür; bu yüzden gösterge yalnız expectProgress=true iken (Octave çalışan kayıt) sınanır. */
export async function runEcg(page: Page, opts: { expectProgress?: boolean } = {}) {
  await page.getByTestId('ecg-run').click();
  if (opts.expectProgress) await expect(page.getByTestId('ecg-progress')).toBeVisible();
  await expect(page.getByTestId('result-af_S4_DEVICE').or(page.getByTestId('ecg-error'))).toBeVisible({ timeout: 90_000 });
  await expect(page.getByTestId('ecg-progress')).toBeHidden();
}

export async function loadEcgSample(page: Page, id: string) {
  await page.getByTestId(`ecg-sample-${id}`).click();
  await expect(page.getByTestId('sample-note')).toContainText(id);
  await expect(page.getByTestId('ecg-age')).toHaveValue('60');
}
