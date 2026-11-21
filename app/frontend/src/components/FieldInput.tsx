import { useState } from 'react';
import type { FieldSpec, Schema } from '../api/types';
import { categoryLabel, fieldLabel, unitOptions, type FieldValue } from '../lib/form';
import { t } from '../lib/ui';

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

/** Form alanı. Görünen etiket ve yardım sade dildedir (app_config > form.field_ui_tr); kaynak değişken (NHANES/UCI kodu),
 * şemadaki araştırma tanımı ve not yalnız "?" ile açılan teknik ayrıntıda gösterilir. */
export function FieldInput({ name, spec, schema, value, required, errors, onChange }: Props) {
  const [techOpen, setTechOpen] = useState(false);
  const id = `f-${name}`;
  const errId = `err-${name}`;
  const helpId = `help-${name}`;
  const techId = `tech-${name}`;
  const hasErr = errors.length > 0;
  const units = spec.type === 'numeric' ? unitOptions(schema, name) : [];
  const unit = value?.unit ?? spec.unit;
  const optionalRace = name === 'race_ethnicity';
  const ui = schema.form.field_ui_tr?.[name];
  const label = fieldLabel(schema, name);
  const hasHelp = !!ui?.help || (spec.type === 'numeric' && !!spec.plausible_range);
  const describedBy = [hasHelp ? helpId : null, hasErr ? errId : null].filter(Boolean).join(' ') || undefined;

  return (
    <div className="flex min-w-0 flex-col gap-1" data-testid={`field-${name}`}>
      <div className="flex items-start justify-between gap-2">
        <label htmlFor={id} className="text-sm font-medium text-slate-800">
          {label}
          {required && <span className="ml-1 text-rose-700"> * {t(schema, 'required_mark')}</span>}
          {optionalRace && <span className="ml-1 font-normal text-slate-600">({t(schema, 'optional')})</span>}
        </label>
        <button type="button" data-testid={`tech-btn-${name}`} aria-expanded={techOpen} aria-controls={techId}
          aria-label={`${t(schema, 'tech_toggle')}: ${label}`} title={t(schema, 'tech_toggle')}
          onClick={() => setTechOpen((o) => !o)}
          className="h-6 w-6 shrink-0 rounded-full border border-slate-400 text-xs font-semibold text-slate-700 hover:bg-slate-100">
          ?
        </button>
      </div>
      {spec.type === 'numeric' ? (
        <div className="flex gap-2">
          <input id={id} type="text" inputMode="decimal" autoComplete="off" spellCheck={false}
            aria-invalid={hasErr} aria-describedby={describedBy}
            className={`w-full min-w-0 rounded border px-2 py-1.5 text-sm ${hasErr ? 'border-rose-600 bg-rose-50' : 'border-slate-400'}`}
            value={encode(value?.value)}
            onChange={(e) => onChange({ value: e.target.value, unit })} />
          {units.length > 1 ? (
            <select aria-label={t(schema, 'unit_of', { label })} data-testid={`unit-${name}`}
              className="rounded border border-slate-400 bg-white px-1 text-sm"
              value={unit} onChange={(e) => onChange({ value: value?.value ?? '', unit: e.target.value })}>
              {units.map((u) => <option key={u} value={u}>{u}</option>)}
            </select>
          ) : (
            <span className="self-center whitespace-nowrap text-sm text-slate-600">{spec.unit}</span>
          )}
        </div>
      ) : (
        <select id={id} autoComplete="off" aria-invalid={hasErr} aria-describedby={describedBy}
          className={`w-full min-w-0 rounded border bg-white px-2 py-1.5 text-sm ${hasErr ? 'border-rose-600' : 'border-slate-400'}`}
          value={encode(value?.value)}
          onChange={(e) => onChange({ value: decode(e.target.value, spec.categories ?? []) })}>
          <option value="">{optionalRace ? t(schema, 'race_no_answer') : t(schema, 'no_answer')}</option>
          {(spec.categories ?? []).map((c) => (
            <option key={String(c)} value={String(c)}>{categoryLabel(schema, name, c)}</option>
          ))}
        </select>
      )}
      {hasHelp && (
        <div id={helpId} className="text-[11px] leading-snug text-slate-600">
          {spec.type === 'numeric' && spec.plausible_range && (
            <p>
              {t(schema, 'range', { lo: spec.plausible_range[0], hi: spec.plausible_range[1], unit: spec.unit ?? '' })}
              {units.length > 1 && ` ${t(schema, 'range_units')}`}
            </p>
          )}
          {ui?.help && <p data-testid={`help-${name}`}>{ui.help}</p>}
        </div>
      )}
      {techOpen && (
        <dl id={techId} data-testid={techId} className="rounded border border-slate-200 bg-slate-50 p-2 text-[11px] text-slate-700">
          {ui?.source && <div><dt className="inline font-medium">{t(schema, 'tech_source')}: </dt><dd className="inline">{ui.source}</dd></div>}
          <div><dt className="inline font-medium">{t(schema, 'tech_definition')}: </dt><dd className="inline">{spec.label_tr}</dd></div>
          {spec.note && <div><dt className="inline font-medium">{t(schema, 'tech_note')}: </dt><dd className="inline">{spec.note}</dd></div>}
          <div><dt className="inline font-medium">{t(schema, 'tech_field')}: </dt><dd className="inline font-mono">{name}</dd></div>
        </dl>
      )}
      {hasErr && (
        <p id={errId} role="alert" data-testid={errId} className="text-xs text-rose-700">{errors.join(' · ')}</p>
      )}
    </div>
  );
}
