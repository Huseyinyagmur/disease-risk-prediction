import type { FieldSpec, Schema } from '../api/types';
import { categoryLabel, unitOptions, type FieldValue } from '../lib/form';

interface Props {
  name: string;
  spec: FieldSpec;
  schema: Schema;
  value: FieldValue | undefined;
  required: boolean;
  errors: string[];
  onChange: (v: FieldValue) => void;
}

const encode = (v: unknown) => (v === null || v === undefined ? '' : String(v));
const decode = (s: string, cats: (string | boolean)[]): string | boolean | null => {
  if (s === '') return null;
  const hit = cats.find((c) => String(c) === s);
  return hit === undefined ? s : hit;
};

export function FieldInput({ name, spec, schema, value, required, errors, onChange }: Props) {
  const id = `f-${name}`;
  const errId = `err-${name}`;
  const hasErr = errors.length > 0;
  const units = spec.type === 'numeric' ? unitOptions(schema, name) : [];
  const unit = value?.unit ?? spec.unit;
  const optionalRace = name === 'race_ethnicity';

  return (
    <div className="flex flex-col gap-1" data-testid={`field-${name}`}>
      <label htmlFor={id} className="text-sm font-medium text-slate-800">
        {spec.label_tr}
        {required && <span className="ml-1 text-rose-700" title="Bu durumda zorunlu"> * zorunlu</span>}
        {optionalRace && <span className="ml-1 font-normal text-slate-500">(isteğe bağlı)</span>}
      </label>
      {spec.type === 'numeric' ? (
        <div className="flex gap-2">
          <input id={id} type="text" inputMode="decimal" autoComplete="off" spellCheck={false}
            aria-invalid={hasErr} aria-describedby={hasErr ? errId : undefined}
            className={`w-full rounded border px-2 py-1.5 text-sm ${hasErr ? 'border-rose-500 bg-rose-50' : 'border-slate-300'}`}
            value={encode(value?.value)}
            onChange={(e) => onChange({ value: e.target.value, unit })} />
          {units.length > 1 ? (
            <select aria-label={`${spec.label_tr} birimi`} data-testid={`unit-${name}`}
              className="rounded border border-slate-300 bg-white px-1 text-sm"
              value={unit} onChange={(e) => onChange({ value: value?.value ?? '', unit: e.target.value })}>
              {units.map((u) => <option key={u} value={u}>{u}</option>)}
            </select>
          ) : (
            <span className="self-center whitespace-nowrap text-sm text-slate-500">{spec.unit}</span>
          )}
        </div>
      ) : (
        <select id={id} autoComplete="off" aria-invalid={hasErr} aria-describedby={hasErr ? errId : undefined}
          className={`rounded border bg-white px-2 py-1.5 text-sm ${hasErr ? 'border-rose-500' : 'border-slate-300'}`}
          value={encode(value?.value)}
          onChange={(e) => onChange({ value: decode(e.target.value, spec.categories ?? []) })}>
          <option value="">{optionalRace ? 'Belirtmek istemiyorum (yanıtsız)' : '— yanıtlanmadı —'}</option>
          {(spec.categories ?? []).map((c) => (
            <option key={String(c)} value={String(c)}>{categoryLabel(schema, name, c)}</option>
          ))}
        </select>
      )}
      {spec.type === 'numeric' && spec.plausible_range && (
        <p className="text-[11px] text-slate-500">
          Makul aralık: {spec.plausible_range[0]}–{spec.plausible_range[1]} {spec.unit}
          {units.length > 1 && ' (başka birim seçilirse dönüşüm ve denetim sunucuda yapılır)'}
        </p>
      )}
      {spec.note && <p className="text-[11px] leading-snug text-slate-500">{spec.note}</p>}
      {hasErr && (
        <p id={errId} role="alert" data-testid={errId} className="text-xs text-rose-700">{errors.join(' · ')}</p>
      )}
    </div>
  );
}
