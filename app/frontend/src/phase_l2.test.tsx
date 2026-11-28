// Phase L2: tasarım revizyonu — kompakt durum paneli, sohbet görünümlü çekmece asistan, tek seferlik uyarı.
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import eligEmpty from './test/fixtures/eligibility_empty.json';
import eligFull from './test/fixtures/eligibility_full.json';
import { mockFetch, renderApp, schema } from './test/helpers';

afterEach(() => vi.unstubAllGlobals());
const tx = schema.ui!.text_tr;
const count = (hay: string, needle: string) => hay.split(needle).length - 1;

describe('durum paneli (kompakt)', () => {
  it('hiç bilgi girilmemişken nötr "Henüz bilgi girilmedi"; sarı "Eksik bilgi" yok; ortak gerekçe bir kez', async () => {
    mockFetch({ elig: () => eligEmpty });
    renderApp();
    const panel = await screen.findByTestId('routing-panel');
    await waitFor(() => expect(within(panel).getByTestId('panel-fibrosis_final')).toBeInTheDocument());
    for (const id of ['af_S4_DEVICE', 'fibrosis_final', 'osteo_final']) {
      const row = within(panel).getByTestId(`panel-${id}`);
      expect(row).toHaveAttribute('data-state', 'MISSING'); // sunucu durumu değişmez
      expect(row).toHaveAttribute('data-display', 'NOT_STARTED');
      expect(within(row).getByTestId('state-badge')).toHaveTextContent(tx.panel_not_started);
      expect(within(row).getByTestId('state-badge')).not.toHaveTextContent(schema.ui!.terms_tr.eligibility.MISSING);
      expect(within(row).getByTestId(`panel-progress-${id}`)).toHaveTextContent(/^0\/\d+ bilgi girildi$/);
    }
    // "Yaş girilmediği için …" üç analizde ortak → panelde tek satır
    const yas = 'Yaş girilmediği için bu analizin size uygun olup olmadığı belirlenemiyor.';
    expect(count(panel.textContent ?? '', yas)).toBe(1);
    expect(within(panel).getByTestId('panel-common')).toHaveTextContent(yas);
  });

  it('eksik alan listesi varsayılan katlı ("Eksikleri göster"); ilerleme x/y', async () => {
    mockFetch({ elig: () => eligFull });
    const u = userEvent.setup();
    renderApp();
    await u.click(await screen.findByTestId('select-all'));
    const copd = await screen.findByTestId('panel-copd_S4_DEVICE');
    await waitFor(() => expect(copd).toHaveAttribute('data-state', 'MISSING'));
    const det = within(copd).getByTestId('panel-missing-copd_S4_DEVICE') as HTMLDetailsElement;
    expect(det.tagName).toBe('DETAILS');
    expect(det.open).toBe(false);
    expect(det.querySelector('summary')).toHaveTextContent(tx.panel_show_missing);
    expect(det).toHaveTextContent('FEV1');
    const fib = screen.getByTestId('panel-fibrosis_final');
    expect(fib).toHaveAttribute('data-state', 'READY');
    expect(within(fib).queryByTestId('panel-missing-fibrosis_final')).toBeNull();
  });
});

describe('asistan (sohbet görünümü, çekmece)', () => {
  it('masaüstünde çekmece + karartma; içerik daralmaz ve inert; boş durumda karşılama + chip; uyarı tek satır', async () => {
    vi.stubGlobal('matchMedia', (q: string) => ({ matches: q.includes('1024'), addEventListener() {}, removeEventListener() {} }));
    mockFetch();
    const u = userEvent.setup();
    renderApp();
    await u.click(await screen.findByTestId('assistant-open'));
    const panel = screen.getByTestId('assistant-panel');
    expect(panel).toHaveAttribute('data-layout', 'drawer');
    expect(panel).toHaveAttribute('aria-modal', 'true');
    expect(screen.getByTestId('assistant-backdrop')).toBeInTheDocument();
    expect(screen.getByTestId('app-shell').style.marginRight).toBe('');
    expect(screen.getByTestId('app-shell')).toHaveAttribute('inert');
    expect(within(panel).getByTestId('assistant-welcome')).toHaveTextContent(tx.asst_welcome);
    const chips = within(panel).getAllByTestId('assistant-chip');
    expect(chips.length).toBeGreaterThanOrEqual(3);
    expect(chips.length).toBeLessThanOrEqual(4);
    expect(within(panel).getByTestId('assistant-disclaimer')).toHaveTextContent(tx.asst_disclaimer_short);
    await u.click(within(panel).getByTestId('assistant-expand'));
    expect(panel).toHaveAttribute('data-layout', 'centered');
    await u.click(screen.getByTestId('assistant-backdrop'));
    expect(screen.queryByTestId('assistant-panel')).toBeNull();
    expect(screen.getByTestId('app-shell')).not.toHaveAttribute('inert');
  });
});
