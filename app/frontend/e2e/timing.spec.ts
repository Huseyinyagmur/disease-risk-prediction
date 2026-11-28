// @timing: AF arayüz süresinin ayrıştırılması (teşhis; normal test koşusuna dahil değil: --grep-invert "@screenshots|@timing").
// Tarayıcı Resource Timing (XHR /api/ecg/af) + sunucunun bildirdiği wall/octave süresi + grafik çizimi.
import { expect, test } from '@playwright/test';
import { writeFileSync } from 'node:fs';
import { loadEcgSample, openEcg } from './helpers';

const OUT = process.env.TIMING_OUT ?? '../../phase_l2/results/af_timing_browser.json';

test.describe('@timing', () => {
  test('AF arayüz süre ayrıştırması', async ({ page }) => {
    test.setTimeout(600_000);
    const rows: Record<string, unknown>[] = [];
    await openEcg(page);
    for (let i = 0; i < 3; i++) {
      for (const id of ['00691', '00165']) {
        await loadEcgSample(page, id);
        await page.evaluate(() => {
          performance.clearResourceTimings();
          const w = window as unknown as { __t: Record<string, number> };
          w.__t = {};
          new MutationObserver((_m, obs) => {
            if (document.querySelector('[data-testid="ecg-trace"] .recharts-line path')) {
              w.__t.trace_rendered = performance.now();
              obs.disconnect();
            }
          }).observe(document.body, { childList: true, subtree: true });
        });
        const respP = page.waitForResponse((r) => r.url().endsWith('/api/ecg/af'), { timeout: 120_000 });
        const tClick = await page.evaluate(() => performance.now());
        await page.getByTestId('ecg-run').click();
        const resp = await respP;
        const body = await resp.json();
        await expect(page.getByTestId('ecg-trace')).toBeVisible({ timeout: 30_000 });
        await page.waitForFunction(() => (window as unknown as { __t: Record<string, number> }).__t.trace_rendered !== undefined);
        const t = await page.evaluate(() => {
          const e = performance.getEntriesByType('resource').find((x) => x.name.endsWith('/api/ecg/af')) as PerformanceResourceTiming;
          const w = window as unknown as { __t: Record<string, number> };
          return { start: e.startTime, reqStart: e.requestStart, respStart: e.responseStart, respEnd: e.responseEnd,
            encoded: e.encodedBodySize, decoded: e.decodedBodySize, rendered: w.__t.trace_rendered };
        });
        const p = body.result.pipeline;
        rows.push({
          run: i, record: id, status: body.result.status,
          click_to_request_s: +((t.start - tClick) / 1000).toFixed(3),
          request_to_first_byte_s: +((t.respStart - t.start) / 1000).toFixed(3),
          server_wall_s: +p.wall_seconds.toFixed(3), octave_s: +p.octave_seconds.toFixed(3),
          upload_and_queue_minus_server_s: +((t.respStart - t.start) / 1000 - p.wall_seconds).toFixed(3),
          download_s: +((t.respEnd - t.respStart) / 1000).toFixed(4),
          response_bytes: t.decoded,
          render_after_response_s: +((t.rendered - t.respEnd) / 1000).toFixed(3),
          click_to_chart_s: +((t.rendered - tClick) / 1000).toFixed(3),
        });
        console.log(JSON.stringify(rows[rows.length - 1]));
      }
    }
    writeFileSync(OUT, JSON.stringify({ rows, note: 'Teşhis ölçümü; aynı makine, canlı backend + vite preview + Chromium.' }, null, 1));
  });
});
