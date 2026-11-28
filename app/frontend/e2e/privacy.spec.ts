// @gizlilik: sağlık verisi tarayıcıda kalıcı saklanmaz; yenilenince silinir; istekler yalnız localhost'a gider.
import { expect, test, type Page } from '@playwright/test';
import { gotoStep, loadEcgSample, loadProfile, mainNav, openEcg, openForm, runEcg, submit } from './helpers';

async function storageSnapshot(page: Page) {
  return page.evaluate(async () => {
    const idb = 'databases' in indexedDB ? (await indexedDB.databases()).map((d) => d.name) : ['(desteklenmiyor)'];
    const caches_ = 'caches' in window ? await caches.keys() : [];
    return { local: localStorage.length, session: sessionStorage.length, idb, cookie: document.cookie, caches: caches_ };
  });
}

test.describe('@gizlilik tarayıcı depolaması ve yenileme', () => {
  test('form + sonuç + EKG sonrası depolama boş; yenilemede tüm veri silinir; dış istek yok', async ({ page, context }) => {
    const hosts = new Set<string>();
    page.on('request', (r) => hosts.add(new URL(r.url()).host));
    // depolamaya yazma girişimlerini de yakala (okuma dahil sayılmaz)
    await page.addInitScript(() => {
      const w = window as unknown as { __storageWrites: string[] };
      w.__storageWrites = [];
      for (const s of [Storage.prototype]) {
        const orig = s.setItem;
        s.setItem = function (k: string, v: string) {
          w.__storageWrites.push(k);
          return orig.call(this, k, v);
        };
      }
      const openOrig = indexedDB.open.bind(indexedDB);
      indexedDB.open = ((name: string, v?: number) => {
        w.__storageWrites.push('idb:' + name);
        return openOrig(name, v);
      }) as typeof indexedDB.open;
    });

    await openForm(page);
    await loadProfile(page, 'fibrosis_ready');
    await submit(page);
    await expect(page.getByTestId('result-fibrosis_final')).toBeVisible();

    await openEcg(page); // aynı sekmede yeniden yükleme (page.goto) — aşağıda ayrıca yenileme sınanır
    await loadEcgSample(page, '00165');
    await runEcg(page);
    await expect(page.getByTestId('result-af_S4_DEVICE')).toBeVisible();

    const snap = await storageSnapshot(page);
    expect(snap).toEqual({ local: 0, session: 0, idb: [], cookie: '', caches: [] });
    expect(await page.evaluate(() => (window as unknown as { __storageWrites: string[] }).__storageWrites)).toEqual([]);
    expect(await context.cookies()).toEqual([]);

    // Formu doldur, sonra yenile: hiçbir değer kalmamalı
    await mainNav(page).getByRole('button', { name: 'Veri girişi', exact: true }).click();
    await loadProfile(page, 'fibrosis_ready'); // seçim openForm'dan: Tümü
    await gotoStep(page, 'temel');
    await expect(page.locator('#f-age_years')).toHaveValue('58');
    await page.reload();
    await mainNav(page).getByRole('button', { name: 'Veri girişi', exact: true }).click();
    await expect(page.getByTestId('selected-count')).toContainText('3 analiz'); // Phase L: seçim bellekte tutulmaz; yenilenince varsayılana (3) döner
    await expect(page.getByTestId('profile-loaded')).toHaveCount(0);
    await page.getByTestId('select-all').click();
    await gotoStep(page, 'temel');
    await expect(page.locator('#f-age_years')).toHaveValue('');
    await mainNav(page).getByRole('button', { name: 'Sonuçlar', exact: true }).click();
    await expect(page.getByText('Henüz sonuç yok')).toBeVisible();
    await mainNav(page).getByRole('button', { name: 'EKG ile AF', exact: true }).click();
    await expect(page.getByText('Sonuç burada görünecek.')).toBeVisible();

    const snap2 = await storageSnapshot(page);
    expect(snap2).toEqual({ local: 0, session: 0, idb: [], cookie: '', caches: [] });
    expect([...hosts].every((h) => h === '127.0.0.1:4173')).toBe(true);
  });

  test('sabit uyarı her ekranda görünür', async ({ page }) => {
    await page.goto('/');
    const text = 'Araştırma prototipidir; mevcut durum sınıflandırması yapar, gelecek risk tahmini değildir; negatif sonuç hastalığı dışlamaz; tanı ve tedavi için hekime başvurun.';
    for (const name of ['Giriş', 'Veri girişi', 'Sonuçlar', 'EKG ile AF', 'Model kartları', 'Hakkında']) {
      await mainNav(page).getByRole('button', { name, exact: true }).click();
      await expect(page.getByTestId('disclaimer')).toContainText(text);
    }
  });
});
