// Backend istemcisi. Tüm istekler aynı kökenden /api önekiyle gider (Vite vekili -> 127.0.0.1 backend).
// Hiçbir yanıt veya girdi tarayıcı depolamasına yazılmaz; önbellek kapalı (cache: 'no-store').
import type { AssistantResponse, AssistantResultLabel, EcgResponse, EligibilityResponse, ModelInfo, PredictResponse, Schema } from './types';

export const API_BASE = '/api';

export type FieldPayload = Record<string, unknown>;

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown, message?: string) {
    super(message ?? `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let resp: Response;
  try {
    resp = await fetch(API_BASE + path, { cache: 'no-store', credentials: 'omit', ...init });
  } catch (e) {
    if ((e as Error).name === 'AbortError') throw e;
    throw new ApiError(0, null, 'Sunucuya ulaşılamadı (backend 127.0.0.1 üzerinde çalışıyor mu?)');
  }
  let body: unknown = null;
  try {
    body = await resp.json();
  } catch {
    body = null;
  }
  if (!resp.ok) {
    const detail = (body as { detail?: unknown } | null)?.detail ?? null;
    throw new ApiError(resp.status, detail);
  }
  return body as T;
}

const json = (fields: FieldPayload, signal?: AbortSignal): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ fields }),
  signal,
});

export const api = {
  schema: () => request<Schema>('/schema'),
  models: () => request<{ models: ModelInfo[] }>('/models'),
  health: () => request<Record<string, unknown>>('/health'),
  eligibility: (fields: FieldPayload, signal?: AbortSignal) =>
    request<EligibilityResponse>('/eligibility', json(fields, signal)),
  predict: (fields: FieldPayload) => request<PredictResponse>('/predict', json(fields)),
  /** Phase XLVIII: yalnız soru + sonuç ETİKETLERİ (ham değer yok). */
  assistantAsk: (question: string, results: AssistantResultLabel[], signal?: AbortSignal) =>
    request<AssistantResponse>('/assistant/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, results }),
      signal,
    }),
  ecgAf: (form: FormData, onUpload?: (fraction: number) => void) =>
    new Promise<EcgResponse>((resolve, reject) => {
      // XHR: yükleme ilerlemesi için (fetch yükleme ilerlemesi vermez)
      const xhr = new XMLHttpRequest();
      xhr.open('POST', API_BASE + '/ecg/af');
      xhr.responseType = 'json';
      xhr.upload.onprogress = (ev) => {
        if (ev.lengthComputable && onUpload) onUpload(ev.loaded / ev.total);
      };
      xhr.upload.onload = () => onUpload?.(1);
      xhr.onload = () => {
        const body = xhr.response as { detail?: unknown } | null;
        if (xhr.status >= 200 && xhr.status < 300) resolve(body as unknown as EcgResponse);
        else reject(new ApiError(xhr.status, body?.detail ?? null));
      };
      xhr.onerror = () => reject(new ApiError(0, null, 'Sunucuya ulaşılamadı'));
      xhr.send(form);
    }),
};

/** 422 ayrıntısını {alan: mesaj[]} biçimine çevirir (backend loc = ['fields', alan]). */
export function errorsByField(detail: unknown): { byField: Record<string, string[]>; general: string[] } {
  const byField: Record<string, string[]> = {};
  const general: string[] = [];
  if (Array.isArray(detail)) {
    for (const d of detail as { loc?: unknown[]; msg?: string; field?: string | null }[]) {
      const name = d.field ?? (Array.isArray(d.loc) && d.loc.length > 1 ? String(d.loc[1]) : null);
      const msg = d.msg ?? String(d);
      if (name) (byField[name] ??= []).push(msg);
      else general.push(msg);
    }
  } else if (typeof detail === 'string') general.push(detail);
  else if (detail != null) general.push(JSON.stringify(detail));
  return { byField, general };
}
