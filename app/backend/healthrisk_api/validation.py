"""Kullanıcı alanlarının doğrulanması: birim dönüşümü (input_schema.unit_conversions) -> tür/aralık kontrolü.

Kurallar (Phase XLIV görev tanımı + input_schema.policy):
  * bilinmeyen alan adı, sayısal olmayan sayısal değer, desteklenmeyen birim, plausible_range dışı değer -> HTTP 422
  * EKG pipeline alanları (ecg_*) ve cihaz grupları formdan girilemez -> 422 (yalnız /ecg/af)
  * şemada olmayan KATEGORİ değeri 422 değildir: alan Invalid olarak işaretlenir, onu kullanan model ABSTAIN eder
  * tutarlılık: sbp_i > dbp_i, fev1_pre ≤ fvc_pre (aksi 422)
"""
import math
import re

from .transforms import Invalid


class ValidationError422(Exception):
    def __init__(self, errors):
        super().__init__('; '.join(e['msg'] for e in errors))
        self.errors = errors


_OP = re.compile(r'^\s*x\s*([*/])\s*([0-9]+(?:\.[0-9]+)?)(?:\s*\+\s*([0-9]+(?:\.[0-9]+)?))?')


def parse_unit_conversions(schema):
    """{(alan, kaynak_birim): fn} — şemadaki op metinlerinden. Tanınmayan op -> ValueError (sessiz geçilmez)."""
    table = {}
    for uc in schema['unit_conversions']:
        m = _OP.match(uc['op'])
        if not m:
            raise ValueError(f'tanınmayan birim dönüşümü: {uc["op"]!r}')
        op, k, b = m.group(1), float(m.group(2)), float(m.group(3) or 0.0)
        fn = (lambda x, k=k, b=b: x * k + b) if op == '*' else (lambda x, k=k, b=b: x / k + b)
        for f in [s.strip() for s in uc['field'].split('/')]:
            table[(f, uc['from_unit'])] = dict(fn=fn, op=uc['op'], to_unit=uc['to_unit'])
    return table


def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v))


def field_specs(schema, extra_fields):
    specs = dict(schema['fields'])
    specs.update(extra_fields)
    return specs


def validate_fields(raw, schema, extra_fields, conversions):
    """raw: {alan: değer | {"value": x, "unit": u} | None}. Döner: (F, notes). F model biriminde doğrulanmış alanlar."""
    specs = field_specs(schema, extra_fields)
    errors, F, notes = [], {}, []
    if not isinstance(raw, dict):
        raise ValidationError422([dict(loc=['fields'], msg='fields bir nesne olmalı')])
    for name, val in raw.items():
        spec = specs.get(name)
        if spec is None:
            errors.append(dict(loc=['fields', name], msg=f'bilinmeyen alan: {name}'))
            continue
        src = spec.get('input_source', '')
        if spec['type'] == 'device' or str(src).startswith('ecg_pipeline'):
            errors.append(dict(loc=['fields', name], msg=f'{name} formdan girilemez (yalnız kilitli EKG pipeline çıktısı; /ecg/af)'))
            continue
        unit = None
        if isinstance(val, dict):
            if set(val) - {'value', 'unit'}:
                errors.append(dict(loc=['fields', name], msg='nesne biçimi yalnız {value, unit} olabilir'))
                continue
            unit, val = val.get('unit'), val.get('value')
        if val is None:
            continue                                    # yanıtsız = eksik (tahminle doldurulmaz)
        if spec['type'] == 'numeric':
            if not _is_number(val):
                errors.append(dict(loc=['fields', name], msg=f'{name} sayısal olmalı'))
                continue
            x = float(val)
            if unit is not None and unit != spec.get('unit'):
                conv = conversions.get((name, unit))
                if conv is None:
                    errors.append(dict(loc=['fields', name], msg=f'{name}: desteklenmeyen birim {unit!r} (kayıtlı birim {spec.get("unit")!r})'))
                    continue
                x = conv['fn'](x)
                notes.append(f'{name}: {val} {unit} -> {x:.6g} {spec.get("unit")} ({conv["op"]})')
            lo, hi = spec['plausible_range']
            if not (lo <= x <= hi):
                errors.append(dict(loc=['fields', name], msg=f'{name}={x:.6g} {spec.get("unit")} makul aralık dışında [{lo}, {hi}]'))
                continue
            F[name] = x
        elif spec['type'] == 'boolean':
            if unit is not None:
                errors.append(dict(loc=['fields', name], msg=f'{name} birim almaz'))
                continue
            ok = isinstance(val, bool) or (not isinstance(val, (int, float)) and val in spec.get('categories', []))
            F[name] = val if ok else Invalid(val)        # ör. pregnant: true/false/"unknown"
        elif spec['type'] == 'categorical':
            if unit is not None:
                errors.append(dict(loc=['fields', name], msg=f'{name} birim almaz'))
                continue
            F[name] = val if (isinstance(val, str) and val in spec['categories']) else Invalid(val)
        else:
            errors.append(dict(loc=['fields', name], msg=f'{name}: desteklenmeyen alan tipi {spec["type"]}'))
    for i in (1, 2, 3):
        s, d = F.get(f'sbp_{i}_mmhg'), F.get(f'dbp_{i}_mmhg')
        if s is not None and d is not None and s <= d:
            errors.append(dict(loc=['fields', f'sbp_{i}_mmhg'], msg=f'tutarsız okuma {i}: sistolik ({s:g}) ≤ diyastolik ({d:g})'))
    if F.get('fev1_pre_ml') is not None and F.get('fvc_pre_ml') is not None and F['fev1_pre_ml'] > F['fvc_pre_ml']:
        errors.append(dict(loc=['fields', 'fev1_pre_ml'], msg='tutarsız spirometri: FEV1 > FVC'))
    if errors:
        raise ValidationError422(errors)
    return F, notes
