// Uyarı metni: tek kaynak backend (/schema `disclaimer`). Frontend metni kendisi tutmaz.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import models from '../test/fixtures/models.json';
import { mockFetch, renderApp, schema } from '../test/helpers';

afterEach(() => vi.unstubAllGlobals());

const APPROVED =
  'Araştırma prototipidir; mevcut durum sınıflandırması yapar, gelecek risk tahmini değildir; negatif sonuç hastalığı dışlamaz; tanı ve tedavi için hekime başvurun.';

function srcFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((n) => {
    const p = path.join(dir, n);
    if (statSync(p).isDirectory()) return n === 'test' ? [] : srcFiles(p);
    return /\.(ts|tsx)$/.test(n) && !/\.test\.tsx?$/.test(n) ? [p] : [];
  });
}

describe('sabit uyarı — tek kaynak backend', () => {
  it('backend fixture onaylı metni taşır', () => {
    expect(schema.disclaimer).toBe(APPROVED);
  });

  it('arayüz backend ne gönderirse onu gösterir (her ekranda; Giriş ve Hakkında dahil)', async () => {
    const custom = 'TEST-UYARI-METNI: backend kaynaklı';
    const { fn } = mockFetch();
    fn.mockImplementation(async (url: string) => {
      const p = String(url).replace(/^\/api/, '');
      const body = p === '/schema' ? { ...schema, disclaimer: custom } : p === '/models' ? models : { models: [], field_errors: [], unit_conversion_notes: [], warnings: [] };
      return new Response(JSON.stringify(body), { status: 200 });
    });
    const u = userEvent.setup();
    renderApp('home');
    expect(await within(screen.getByTestId('disclaimer')).findByText(custom)).toBeInTheDocument();
    expect(screen.getAllByText(custom).length).toBe(2); // bant + Giriş kutusu
    for (const name of ['Veri girişi', 'Sonuçlar', 'EKG ile AF', 'Model kartları', 'Hakkında']) {
      await u.click(within(screen.getByRole('navigation', { name: 'Ana gezinme' })).getByRole('button', { name }));
      expect(screen.getByTestId('disclaimer')).toHaveTextContent(custom);
    }
    expect(screen.getAllByText(custom).length).toBe(2); // Hakkında: bant + sayfa sonu kutusu
    expect(document.body.textContent).not.toContain(APPROVED);
  });

  it('sunucuya ulaşılamazsa metin uydurulmaz; durum bildirilir', async () => {
    const { fn } = mockFetch();
    fn.mockImplementation(async () => {
      throw new TypeError('Failed to fetch');
    });
    renderApp('home');
    expect(await screen.findAllByText(/araştırma uyarısı yüklenemedi/)).toHaveLength(2);
    expect(document.body.textContent).not.toContain('Araştırma prototipidir');
  });

  it('kaynak kodda uyarı metni yok (src/, testler hariç)', () => {
    const root = path.resolve(__dirname, '..');
    for (const f of srcFiles(root)) {
      expect(readFileSync(f, 'utf8'), f).not.toContain('gelecek risk tahmini değildir');
    }
  });
});
