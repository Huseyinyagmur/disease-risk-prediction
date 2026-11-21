// Phase XLVII: terim sözlüğü ve sade dil. Metinlerin TEK kaynağı backend app_config.json (> ui, > form.field_ui_tr).
import { readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { Schema } from '../api/types';
import eligFull from '../test/fixtures/eligibility_full.json';
import models from '../test/fixtures/models.json';
import predictFull from '../test/fixtures/predict_full.json';
import { goStep, mockFetch, renderApp, schema, startAll } from '../test/helpers';
import { humanize, MISSING_MARK, nextStep, term } from './ui';

afterEach(() => vi.unstubAllGlobals());

const CODE_RE = /\b(NHANES|UCI|RIDRETH\w*|[A-Z]{3}\d{3}[A-Z]?|restecg|oldpeak|thalach|exang)\b/;

function srcFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((n) => {
    const p = path.join(dir, n);
    if (statSync(p).isDirectory()) return n === 'test' ? [] : srcFiles(p);
    return /\.(ts|tsx)$/.test(n) && !/\.test\.tsx?$/.test(n) ? [p] : [];
  });
}

describe('terim sözlüğü — tek kaynak app_config', () => {
  it('sözlük terimleri kaynak kodda sabit metin olarak yok', () => {
    const terms = [
      ...Object.values(schema.ui!.terms_tr.eligibility),
      ...Object.values(schema.ui!.terms_tr.result),
      ...Object.values(schema.ui!.terms_tr.decision),
      schema.ui!.text_tr.what_to_do,
      schema.ui!.text_tr.metrics,
    ];
    const src = srcFiles(path.resolve(__dirname, '..')).map((f) => readFileSync(f, 'utf8')).join('\n');
    for (const x of terms) expect(src, x).not.toContain(x);
    for (const old of ['Karar üretilmedi (ABSTAIN)', 'Kapsam dışı — karar üretilmedi', 'Karar verilemez', 'İleri değerlendirme önerilir']) {
      expect(src).not.toContain(old);
    }
  });

  it('sözlükteki terim değişirse arayüz değişir (panel ve sonuç kartı)', async () => {
    const custom = structuredClone(schema) as Schema;
    custom.ui!.terms_tr.result.ABSTAIN = 'TERIM-X-SONUC-YOK';
    custom.ui!.terms_tr.eligibility.READY = 'TERIM-Y-HAZIR';
    custom.ui!.next_steps_tr._default.ABSTAIN = 'YONLENDIRME-Z';
    const { fn } = mockFetch();
    fn.mockImplementation(async (url: string) => {
      const p = String(url).replace(/^\/api/, '');
      const body = p === '/schema' ? custom : p === '/models' ? models : p === '/predict' ? predictFull : eligFull;
      return new Response(JSON.stringify(body), { status: 200 });
    });
    const u = userEvent.setup();
    renderApp();
    await startAll(u);
    expect(await screen.findByTestId('panel-line-fibrosis_final')).toHaveTextContent('TERIM-Y-HAZIR');
    await u.click(screen.getByTestId('submit'));
    const copd = await screen.findByTestId('result-copd_S4_DEVICE');
    expect(within(copd).getByTestId('decision')).toHaveTextContent('TERIM-X-SONUC-YOK');
    expect(within(copd).getByTestId('next-step')).toHaveTextContent('YONLENDIRME-Z');
  });

  it('yardımcılar: term / nextStep / humanize', () => {
    expect(term(schema, 'result', 'NOT_APPLICABLE')).toBe('Bu analiz size uygun değil');
    expect(nextStep(schema, 'liver_fibrosis', 'ESIK_USTU')).toContain('FibroScan');
    expect(nextStep(schema, 'liver_fibrosis', 'ESIK_ALTI')).toBe(schema.ui!.next_steps_tr._default.ESIK_ALTI);
    expect(humanize(schema, 'albumin_gdl: 42 g/L -> 4.2 g/dL')).toBe('Albümin (kan): 42 g/L -> 4.2 g/dL');
    expect(humanize(schema, 'ırk/etnik köken yanıtsız: policy.optional_race gereği varsayılan sınıf atanmaz')).not.toContain('policy');
    expect(term(null, 'result', 'OK')).toContain(MISSING_MARK);
  });
});

describe('sade dil — form', () => {
  it('görünen etiket ve yardım metinlerinde kaynak değişken kodu yok; her alanda "?" teknik ayrıntı', async () => {
    mockFetch();
    const u = userEvent.setup();
    renderApp();
    await startAll(u);
    for (const s of ['temel', 'olcumler', 'oyku', 'laboratuvar', 'klinik']) {
      await goStep(u, s);
      for (const el of screen.getAllByTestId(/^field-/)) {
        const name = el.dataset.testid!.slice(6);
        const label = el.querySelector('label')!.textContent ?? '';
        expect(label, name).not.toMatch(CODE_RE);
        expect(label, name).not.toContain(name);
        const help = el.querySelector(`#help-${name}`)?.textContent ?? '';
        expect(help, name).not.toMatch(CODE_RE);
        expect(within(el).getByTestId(`tech-btn-${name}`)).toHaveAttribute('aria-expanded', 'false');
      }
    }
    await goStep(u, 'oyku');
    await u.click(screen.getByTestId('tech-btn-family_hx_diabetes'));
    expect(screen.getByTestId('tech-family_hx_diabetes')).toHaveTextContent('NHANES MCQ300C');
    await goStep(u, 'temel');
    expect(screen.getByTestId('help-age_years')).toHaveTextContent('Bazı analizler yalnız belirli yaş aralığında çalışır');
    expect(screen.getByTestId('field-age_years')).not.toHaveTextContent('models.json');
  });

  it('hiçbir ekranda eksik metin anahtarı (⟦…⟧) yok', async () => {
    mockFetch({ elig: () => eligFull, predict: () => ({ status: 200, body: predictFull }) });
    const u = userEvent.setup();
    renderApp();
    await startAll(u);
    for (const s of ['olcumler', 'oyku', 'laboratuvar', 'klinik', 'review', 'select']) {
      await goStep(u, s);
      expect(document.body.textContent).not.toContain(MISSING_MARK);
    }
    await u.click(screen.getByTestId('submit'));
    await screen.findByTestId('results-filtered');
    expect(document.body.textContent).not.toContain(MISSING_MARK);
    for (const name of ['EKG ile AF', 'Model kartları', 'Hakkında']) {
      await u.click(within(screen.getByRole('navigation', { name: 'Ana gezinme' })).getByRole('button', { name }));
      expect(document.body.textContent).not.toContain(MISSING_MARK);
    }
    expect(screen.getByTestId('glossary')).toHaveTextContent('Sonuç üretilmedi');
  });
});
