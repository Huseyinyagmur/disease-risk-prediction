"""AF süre ölçümlerinin özeti (yalnız ölçüm JSON'larını okur) -> results/af_timing_summary.json.
Girdiler: af_timing_api.json (doğrudan API), af_timing_browser.json (tarayıcı ayrıştırması),
af_timing_octave.json (sunucusuz kilitli pipeline + BLAS=1 deneyi), af_timing_octave_pcores.json (P-çekirdek benzeşimi deneyi)."""
import json
import statistics as st
from pathlib import Path

R = Path(__file__).resolve().parents[1] / 'results'
load = lambda n: json.loads((R / n).read_text(encoding='utf8'))


def rng(xs):
    xs = [x for x in xs if x is not None]
    return dict(n=len(xs), median=round(st.median(xs), 3), min=round(min(xs), 3), max=round(max(xs), 3)) if xs else None


api = load('af_timing_api.json')
br = load('af_timing_browser.json')['rows']
oc = load('af_timing_octave.json')['rows']
pc = load('af_timing_octave_pcores.json')['rows']
recs = ('00691_hr', '00165_hr')
summ = dict(
    api_direct=dict(roundtrip_s=rng([r['roundtrip_s'] for r in api]), server_wall_s=rng([r['server_wall_s'] for r in api]),
                    octave_toc_s=rng([r['octave_s'] for r in api]),
                    client_overhead_s=rng([r['roundtrip_s'] - r['server_wall_s'] for r in api]),
                    json_parse_s=rng([r['json_parse_s'] for r in api]), response_bytes=rng([r['response_bytes'] for r in api]),
                    display_bytes=rng([r['display_bytes'] for r in api]), upload_bytes=rng([r['upload_bytes'] for r in api])),
    browser=dict(click_to_chart_s=rng([r['click_to_chart_s'] for r in br]), server_wall_s=rng([r['server_wall_s'] for r in br]),
                 octave_toc_s=rng([r['octave_s'] for r in br]),
                 click_to_request_s=rng([r['click_to_request_s'] for r in br]),
                 upload_and_queue_minus_server_s=rng([r['upload_and_queue_minus_server_s'] for r in br]),
                 download_s=rng([r['download_s'] for r in br]), render_after_response_s=rng([r['render_after_response_s'] for r in br]),
                 non_server_total_s=rng([r['click_to_chart_s'] - r['server_wall_s'] for r in br]),
                 response_bytes=rng([r['response_bytes'] for r in br])),
    standalone={m: dict(octave_bare_s=rng([r['octave_bare_s'] for r in oc if r['mode'] == m]),
                        octave_pkgload_s=rng([r['octave_pkgload_s'] for r in oc if r['mode'] == m]),
                        ecgdeli_wall_s=rng([r[s]['ecgdeli_wall_s'] for r in oc if r['mode'] == m for s in recs]),
                        octave_toc_s=rng([r[s]['octave_toc_s'] for r in oc if r['mode'] == m for s in recs]),
                        features_identical_to_default=all(r[s]['features_equal_default'] for r in oc if r['mode'] == m for s in recs))
                for m in ('default', 'blas_1thread')},
    pcores_affinity={r['mode']: dict(ecgdeli_wall_s=[r[s]['ecgdeli_wall_s'] for s in recs], octave_toc_s=[r[s]['octave_toc_s'] for s in recs],
                                     octave_pkgload_s=r['octave_pkgload_s']) for r in pc},
    phase_xliv_reference='phase_xliv/results/af_e2e.json: octave_seconds ≈ 4,3–4,5, wall_seconds ≈ 6,9–7,1 (aynı makine, farklı zaman)',
)
(R / 'af_timing_summary.json').write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding='utf8')
print(json.dumps(summ, ensure_ascii=False, indent=1))
