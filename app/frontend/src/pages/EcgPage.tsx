import { useEffect, useRef, useState, type DragEvent } from 'react';
import { api, ApiError, errorsByField } from '../api/client';
import { EcgRrPanel } from '../components/EcgRrPanel';
import { ResultCard } from '../components/ResultCard';
import { PageTitle } from '../components/ui';
import { categoryLabel } from '../lib/form';
import { useSession } from '../state/session';

export const ECG_SAMPLES = [
  { id: '00691', label: 'PTB-XL 00691 — kayıt etiketi: AF', files: ['00691_hr.hea', '00691_hr.dat'] },
  { id: '00165', label: 'PTB-XL 00165 — kayıt etiketi: sinüs ritmi (SR)', files: ['00165_hr.hea', '00165_hr.dat'] },
];

type Stage = { kind: 'idle' } | { kind: 'upload'; frac: number } | { kind: 'processing'; since: number } | { kind: 'done' };

export function pickFiles(list: File[]): { header: File | null; signal: File | null; problems: string[] } {
  const header = list.filter((f) => f.name.toLowerCase().endsWith('.hea'));
  const signal = list.filter((f) => /\.(dat|mat)$/i.test(f.name));
  const problems: string[] = [];
  if (header.length !== 1) problems.push(header.length === 0 ? '.hea başlık dosyası yok' : 'birden fazla .hea dosyası');
  if (signal.length !== 1) problems.push(signal.length === 0 ? '.dat veya .mat sinyal dosyası yok' : 'birden fazla sinyal dosyası');
  const other = list.filter((f) => !header.includes(f) && !signal.includes(f));
  if (other.length) problems.push(`tanınmayan dosya: ${other.map((f) => f.name).join(', ')}`);
  return { header: header.length === 1 ? header[0] : null, signal: signal.length === 1 ? signal[0] : null, problems };
}

export function EcgPage() {
  const { schema, models, ecg, setEcg } = useSession();
  const [files, setFiles] = useState<File[]>([]);
  const [age, setAge] = useState('');
  const [sex, setSex] = useState('');
  const [sampleNote, setSampleNote] = useState<string | null>(null);
  const [stage, setStage] = useState<Stage>({ kind: 'idle' });
  const [error, setError] = useState<string | null>(null);
  const [now, setNow] = useState(Date.now());
  const [drag, setDrag] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (stage.kind !== 'processing') return;
    const t = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(t);
  }, [stage.kind]);

  const picked = pickFiles(files);
  const busy = stage.kind === 'upload' || stage.kind === 'processing';

  const addFiles = (fl: FileList | File[]) => {
    setFiles(Array.from(fl));
    setSampleNote(null);
    setError(null);
    setEcg(null);
  };

  const loadSample = async (id: string) => {
    const s = ECG_SAMPLES.find((x) => x.id === id)!;
    setError(null);
    try {
      const fs = await Promise.all(
        s.files.map(async (n) => {
          const r = await fetch(`/samples/${n}`, { cache: 'no-store' });
          if (!r.ok) throw new Error(`${n} yüklenemedi (HTTP ${r.status})`);
          return new File([await r.blob()], n);
        }),
      );
      setFiles(fs);
      setAge('60');
      setSex('male');
      setSampleNote(`${s.label}. Açık PhysioNet kaydı (geliştirme kümesinden; test kaydı değil). Yaş/cinsiyet SENTETİK (60, erkek).`);
      setEcg(null);
    } catch (e) {
      setError(String((e as Error).message));
    }
  };

  const run = async () => {
    if (!picked.header || !picked.signal) return;
    const fd = new FormData();
    fd.append('header_file', picked.header, picked.header.name);
    fd.append('signal_file', picked.signal, picked.signal.name);
    if (age.trim() !== '') fd.append('age_years', age.trim().replace(',', '.'));
    if (sex) fd.append('sex', sex);
    setError(null);
    setEcg(null);
    setStage({ kind: 'upload', frac: 0 });
    try {
      const r = await api.ecgAf(fd, (frac) => {
        setStage(frac >= 1 ? { kind: 'processing', since: Date.now() } : { kind: 'upload', frac });
      });
      setEcg(r);
      setStage({ kind: 'done' });
    } catch (e) {
      setStage({ kind: 'idle' });
      if (e instanceof ApiError) {
        const { byField, general } = errorsByField(e.detail);
        const msgs = [...general, ...Object.entries(byField).map(([k, v]) => `${k}: ${v.join(', ')}`)];
        setError(
          e.status === 429 ? 'AF pipeline meşgul (aynı anda tek kayıt işlenir); birkaç saniye sonra tekrar deneyin.'
            : e.status === 413 ? 'Dosya boyutu sınırı (2 MB) aşıldı.'
              : `${e.status ? `HTTP ${e.status}: ` : ''}${msgs.join(' · ') || e.message}`,
        );
      } else setError(String(e));
    }
  };

  const onDrop = (ev: DragEvent) => {
    ev.preventDefault();
    setDrag(false);
    if (ev.dataTransfer.files.length) addFiles(ev.dataTransfer.files);
  };

  const result = ecg?.result;
  const feats = result?.pipeline?.features_ms ?? null;
  const ageSpec = schema?.fields.age_years;
  const sexSpec = schema?.fields.sex;
  const info = models?.find((m) => m.model_id === 'af_S4_DEVICE');
  const cropped = !!result?.pipeline?.record_samples && (result.pipeline.record_samples ?? 0) > 5000;

  return (
    <div>
      <PageTitle sub="Kilitli AF-ECGDELI-OCTAVE-v1 pipeline'ı (Octave + ECGDeli) sunucuda çalışır; tarayıcı yalnız dosyaları gönderir ve sonucu gösterir.">
        EKG ile AF analizi
      </PageTitle>

      <div role="note" data-testid="first10s-note" className="mb-4 rounded border border-sky-300 bg-sky-50 p-3 text-sm text-sky-900">
        Kayıt 500 Hz, 12 derivasyonlu WFDB biçiminde olmalıdır. <strong>10 saniyeden uzun kayıtlarda yalnız ilk 10 saniye değerlendirilir</strong>;
        kaydın geri kalanındaki ritim görülmez. 10 sn'den kısa kayıtlar veya 500 Hz olmayan kayıtlar için karar üretilmez.
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-4" aria-label="EKG yükleme">
          <div
            data-testid="dropzone"
            onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={onDrop}
            className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 text-center text-sm ${drag ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300'}`}>
            <p className="font-medium text-slate-700">.hea + .dat veya .mat dosyalarını buraya sürükleyin</p>
            <p className="my-1 text-xs text-slate-500">veya</p>
            <button type="button" onClick={() => input.current?.click()} className="rounded border border-slate-300 px-3 py-1 text-xs hover:bg-slate-100">Dosya seç</button>
            <input ref={input} type="file" multiple accept=".hea,.dat,.mat" className="hidden" data-testid="file-input"
              onChange={(e) => e.target.files && addFiles(e.target.files)} />
          </div>
          {files.length > 0 && (
            <ul className="text-xs text-slate-700" data-testid="file-list">
              {files.map((f) => <li key={f.name}>{f.name} — {(f.size / 1024).toFixed(1)} KB</li>)}
            </ul>
          )}
          {files.length > 0 && picked.problems.length > 0 && (
            <p role="alert" className="text-xs text-rose-700">{picked.problems.join(' · ')}</p>
          )}
          <div className="flex flex-wrap gap-2">
            <span className="self-center text-xs text-slate-600">Örnek kayıt:</span>
            {ECG_SAMPLES.map((s) => (
              <button key={s.id} type="button" data-testid={`ecg-sample-${s.id}`} onClick={() => void loadSample(s.id)} disabled={busy}
                className="rounded border border-violet-300 bg-violet-50 px-2 py-1 text-xs text-violet-900 hover:bg-violet-100">
                {s.label}
              </button>
            ))}
          </div>
          {sampleNote && <p className="text-xs text-violet-900" data-testid="sample-note">{sampleNote}</p>}

          <div className="grid grid-cols-2 gap-3">
            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium">{ageSpec?.label_tr ?? 'Yaş'} ({ageSpec?.unit ?? 'yıl'})</span>
              <input data-testid="ecg-age" inputMode="decimal" autoComplete="off" value={age} onChange={(e) => setAge(e.target.value)}
                className="rounded border border-slate-300 px-2 py-1.5 text-sm" />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium">{sexSpec?.label_tr ?? 'Cinsiyet'}</span>
              <select data-testid="ecg-sex" value={sex} onChange={(e) => setSex(e.target.value)} className="rounded border border-slate-300 bg-white px-2 py-1.5 text-sm">
                <option value="">— yanıtlanmadı —</option>
                {schema && (sexSpec?.categories ?? []).map((c) => <option key={String(c)} value={String(c)}>{categoryLabel(schema, 'sex', c)}</option>)}
              </select>
            </label>
          </div>
          <p className="text-[11px] text-slate-500">AF modeli yaş ve cinsiyeti de kullanır; yanıtsızsa karar üretilmez (ABSTAIN). Yaş 18–89 dışında kapsam dışıdır.</p>

          <button type="button" data-testid="ecg-run" onClick={() => void run()} disabled={!picked.header || !picked.signal || busy}
            className="rounded bg-slate-800 px-4 py-2 text-sm font-medium text-white disabled:opacity-40">
            Analiz et
          </button>

          {busy && (
            <div data-testid="ecg-progress" aria-live="polite" className="space-y-1">
              <div className="h-2 w-full overflow-hidden rounded bg-slate-200">
                {stage.kind === 'upload' ? (
                  <div className="h-full bg-indigo-600 transition-all" style={{ width: `${Math.round(stage.frac * 100)}%` }} />
                ) : (
                  <div className="h-full w-1/3 animate-pulse bg-indigo-600" />
                )}
              </div>
              <p className="text-xs text-slate-600">
                {stage.kind === 'upload'
                  ? `Yükleniyor… %${Math.round(stage.frac * 100)}`
                  : `Sunucuda işleniyor (ilk 10 sn → ECGDeli delineasyonu → 10 feature → model)… ${((now - (stage.kind === 'processing' ? stage.since : now)) / 1000).toFixed(0)} sn (bu makinede ölçülen ≈ 7–30 sn, makine yüküne bağlı; üst sınır 60 sn)`}
              </p>
            </div>
          )}
          {error && <p role="alert" data-testid="ecg-error" className="rounded bg-rose-50 p-2 text-xs text-rose-800">{error}</p>}
        </section>

        <section className="space-y-3" aria-label="EKG sonucu">
          {result ? (
            <>
              <ResultCard r={{ ...result, warnings: result.warnings ?? [] }} info={info} schema={schema} />
              {result.pipeline && (
                <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-700" data-testid="pipeline-info">
                  <p><span className="font-medium">Pipeline:</span> {result.pipeline.version}</p>
                  {result.pipeline.window && (
                    <p className={cropped ? 'font-semibold text-sky-900' : ''} data-testid="window-info">
                      <span className="font-medium">Değerlendirilen pencere:</span> {result.pipeline.window}
                      {result.pipeline.record_samples ? ` (kayıt: ${result.pipeline.record_samples} örnek = ${(result.pipeline.record_samples / 500).toFixed(1)} sn)` : ''}
                    </p>
                  )}
                  {result.pipeline.wall_seconds != null && <p><span className="font-medium">Süre:</span> {result.pipeline.wall_seconds.toFixed(1)} sn</p>}
                </div>
              )}
            </>
          ) : (
            <p className="rounded-lg border border-dashed border-slate-300 p-6 text-sm text-slate-500">Sonuç burada görünecek.</p>
          )}
        </section>
      </div>

      {result && feats && schema && (
        <section className="mt-4 rounded-lg border border-slate-200 bg-white p-4" aria-label="EKG öznitelikleri">
          <h2 className="mb-2 text-base font-semibold text-slate-800">Çıkarılan 10 EKG özniteliği</h2>
          <table className="w-full text-left text-sm" data-testid="ecg-features">
            <thead className="text-xs text-slate-500">
              <tr><th className="py-1 font-medium">Öznitelik</th><th className="py-1 font-medium">Kod</th><th className="py-1 text-right font-medium">Değer (ms)</th></tr>
            </thead>
            <tbody>
              {Object.entries(feats).map(([k, v]) => (
                <tr key={k} className="border-t border-slate-100">
                  <td className="py-1">{schema.fields[`ecg_af_${k}`]?.label_tr ?? k}</td>
                  <td className="py-1 font-mono text-xs text-slate-500">{k}</td>
                  <td className="py-1 text-right tabular-nums">{v === null || Number.isNaN(v) ? 'üretilemedi' : v.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-1 text-[11px] text-slate-500">Öznitelikler (ms) şeffaflık içindir; olasılık değildir. Kaynak: kilitli pipeline (değiştirilmeden).</p>
        </section>
      )}
      {result?.display && <EcgRrPanel d={result.display} />}
    </div>
  );
}
