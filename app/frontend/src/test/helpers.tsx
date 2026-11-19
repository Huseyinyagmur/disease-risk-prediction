import { render } from '@testing-library/react';
import { vi } from 'vitest';
import type { Schema } from '../api/types';
import { App } from '../App';
import { SessionProvider, type Page } from '../state/session';
import eligEmpty from './fixtures/eligibility_empty.json';
import models from './fixtures/models.json';
import schemaJson from './fixtures/schema.json';

export const schema = schemaJson as unknown as Schema;

export type EligHandler = (fields: Record<string, unknown>) => unknown;

/** fetch sahtesi: /api/schema, /api/models fixture; /api/eligibility ve /api/predict işleyicilere gider. */
export function mockFetch(opts: { elig?: EligHandler; predict?: (fields: Record<string, unknown>) => { status: number; body: unknown } } = {}) {
  const calls: { path: string; fields?: Record<string, unknown> }[] = [];
  const fn = vi.fn(async (url: string, init?: RequestInit) => {
    const path = String(url).replace(/^\/api/, '');
    const fields = init?.body ? (JSON.parse(String(init.body)) as { fields: Record<string, unknown> }).fields : undefined;
    calls.push({ path, fields });
    const ok = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
    if (path === '/schema') return ok(schemaJson);
    if (path === '/models') return ok(models);
    if (path === '/eligibility') return ok(opts.elig ? opts.elig(fields ?? {}) : eligEmpty);
    if (path === '/predict' && opts.predict) {
      const r = opts.predict(fields ?? {});
      return ok(r.body, r.status);
    }
    return ok({ detail: 'yok' }, 404);
  });
  vi.stubGlobal('fetch', fn);
  return { fn, calls };
}

export function renderApp(page: Page = 'form') {
  return render(
    <SessionProvider initialPage={page}>
      <App />
    </SessionProvider>,
  );
}
