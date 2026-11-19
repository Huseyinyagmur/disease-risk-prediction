import { describe, expect, it } from 'vitest';
import { schema } from '../test/helpers';
import { unitOptions } from '../lib/form';
import { DEMO_PROFILES } from './profiles';

describe('sentetik demo profilleri', () => {
  it('dört profil: çalışabilir, eksik, kapsam dışı, birim hatalı', () => {
    expect(DEMO_PROFILES.map((p) => p.id)).toEqual(['fibrosis_ready', 'missing', 'out_of_scope', 'unit_error']);
  });
  it.each(DEMO_PROFILES.map((p) => [p.id, p] as const))('%s: tüm alanlar şemada form alanı; birimler seçenekler içinde; kategoriler geçerli', (_id, p) => {
    for (const [name, v] of Object.entries(p.values)) {
      const spec = schema.fields[name];
      expect(spec, name).toBeDefined();
      expect(spec.form_input, name).toBe(true);
      if (v.unit) expect(unitOptions(schema, name), name).toContain(v.unit);
      if (spec.type !== 'numeric') expect(spec.categories, name).toContain(v.value);
    }
  });
});
