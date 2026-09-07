"""Check the publication rewrite against saved results and generated evidence.

The pre-rewrite checker is preserved as check_legacy_paper_numbers.py.
Run after build_paper_evidence.py and latexmk from the repository root.
"""
import json
import re
from pathlib import Path

from build_paper_evidence import collect

ROOT = Path(__file__).resolve().parents[2]


def main():
    actual = collect()
    generated = ROOT / 'paper/generated'
    assert json.loads((generated / 'evidence.json').read_text()) == actual, 'regenerate paper evidence'
    tex = (ROOT / 'paper/main.tex').read_text()
    flat = re.sub(r'\s+', ' ', tex)
    for phrase in ('generated/hardware_table.tex', 'fig_observation_evidence.pdf',
                   'third evaluation was interrupted', 'its outcome was not entered', 'not variation over training seeds',
                   'fig_real_quantitative.pdf', 'not included in any count',
                   'recorded leader commands', 'a third evaluation was', 'stratified exact test', 'power 0.17'):
        # Case-insensitive: prose checks concern disclosures, not typography.
        assert phrase.lower() in flat.lower(), f'missing disclosure/input: {phrase}'
    expected = [(20, 5, 9, 6, 2), (20, 1, 14, 14, 1), (6, 0, 0, 0, 0)]
    table = (generated / 'hardware_table_all.tex').read_text()
    for r, target in zip(actual['hardware'], expected):
        assert (r['pairs'], r['base'], r['delta'], r['delta_only'], r['base_only']) == target, 'hardware changed; revise prose'
        assert f"{r['base']}/{r['pairs']} & {r['delta']}/{r['pairs']}" in table
    completed_table = (generated / 'hardware_table.tex').read_text()
    assert '0/6' not in completed_table and '0/6' in table
    assert 'generated/hardware_table_ci.tex' in tex
    for name in ('power_table.tex', 'trace_taxonomy.tex', 'sim_contrasts.tex'):
        assert f'generated/{name}' in tex and (generated / name).exists(), name
    for fig in ('fig_hardware_traces.pdf', 'fig_corpus.pdf', 'fig_measurement.pdf'):
        assert fig in tex and (ROOT / 'figures/paper' / fig).exists(), fig
    supp = json.loads((generated / 'supplementary.json').read_text())
    st = supp['hardware']['stratified']
    assert (st['delta_only'], st['base_only']) == (20, 3) and f"{st['exact_p']:.4f}" == '0.0005'
    orr = st['conditional_odds_ratio']
    assert f"{orr['estimate']:.1f}" == '6.7' and f"{orr['ci'][0]:.1f}" == '2.0' and round(orr['ci'][1]) == 35
    assert f"{st['heterogeneity_fisher_p']:.2f}" == '0.27'
    power = supp['power']['at_observed_structure']
    assert f"{power['seed0']:.2f}" == '0.17' and f"{power['seed1']:.2f}" == '0.97'
    tax = supp['hardware']['taxonomy']
    assert tax['seed0_delta_success']['closed_and_held'] == 9 == tax['seed0_delta_success']['n']
    assert tax['seed1_delta_success']['closed_and_held'] == 14 == tax['seed1_delta_success']['n']
    fails = [tax[k] for k in ('seed0_delta_failure', 'seed1_delta_failure')]
    assert sum(f['n'] for f in fails) == 16 and sum(f['never_closed'] + f['closed_then_reopened'] for f in fails) == 15
    for key, never in (('seed2_base_failure', 5), ('seed2_delta_failure', 3), ('seed0_base_failure', 3),
                       ('seed0_delta_failure', 1), ('seed1_base_failure', 2), ('seed1_delta_failure', 0)):
        assert tax[key]['never_closed'] == never, key
    for key, step in (('seed0_delta_success', 165), ('seed1_delta_success', 206), ('seed0_delta_failure', 83),
                      ('seed1_delta_failure', 115)):
        assert round(tax[key]['median_first_close_step']) == step, key
    lim = supp['hardware']['limiter']
    for key, frac in (('seed0_delta', .09), ('seed0_base', .32), ('seed1_delta', .32), ('seed1_base', .35)):
        assert round(lim[key]['median_clipped_frame_fraction'], 2) == frac, key
    con = {(c['b'], c['a']): c for c in supp['simulation']['contrasts']}
    for pair, diff, lo, hi in ((('Tracking error', 'Position'), 15.6, 3.5, 27.7),
                               (('Position history', 'Position'), 14.1, 4.5, 23.8),
                               (('Tracking error', 'Position history'), 1.5, -11.1, 14.0)):
        r = con[pair]
        assert (round(r['diff'], 1), round(r['ci'][0], 1), round(r['ci'][1], 1)) == (diff, lo, hi), pair
    assert all(r['holm_p'] >= .05 for r in con.values()) and len(con) == 28
    assert [c for c in con.values() if c['resolved'] and c['a'] == 'Position'] and \
        {c['b'] for c in con.values() if c['resolved'] and c['a'] == 'Position'} == {'Tracking error', 'Compensated residual', 'Seat token'}
    corp = supp['corpus']
    assert (corp['negative_point_estimates'], corp['ci_excludes_zero_negative'], corp['ci_excludes_zero_positive']) == (11, 7, 2)
    meas = supp['measurement']['demonstrations']
    assert f"{100*meas['saturated_fraction']:.1f}" == '16.5' and f"{meas['corr_load_delta_jaw']:.2f}" == '-0.92'
    assert f"{supp['measurement']['static']['r2']:.3f}" == '0.976'
    assert actual['hardware'][1]['shutdown_errors'] == 2
    assert actual['hardware'][1]['missing_trajectories'] == 1
    assert actual['hardware'][2]['shutdown_errors'] == 3
    assert actual['hardware'][0]['bootstrap_ci'] == [-.05, .45]
    assert actual['hardware'][1]['bootstrap_ci'] == [.4, .9]
    for name, expected_mean, seeds in (
        ('Position', 6.2, 5), ('Action history', 13.8, 5), ('Tracking error', 21.8, 5),
        ('Lag excess', 26.6, 5), ('Auxiliary target', 6.6, 5), ('Position history', 20.3, 3)):
        vals = actual['simulation'][name]
        assert len(vals) == seeds and round(sum(vals)/len(vals), 1) == expected_mean
        assert f'{expected_mean:.1f}\\%' in tex, f'missing simulation value: {name}'
    corpus = [r for r in json.loads((ROOT/'results/corpus/corpus_delta_outcome.json').read_text()) if r.get('cohen_d') is not None]
    assert len(corpus) == 16 and sum(r['episodes'] for r in corpus) == 546
    assert sum(r['cohen_d'] > .5 for r in corpus) == 2
    assert '546 episodes' in flat and '$d=-0.39$' in tex
    pending = json.loads((ROOT/'results/hardware/real_delta_v3_s2_trials_pending.json').read_text())
    assert pending['trial'] == 12 and pending['rollout_complete']
    assert (ROOT / 'results/hardware/real_trial_traj' / Path(pending['trajectory']).name).exists()
    guards = json.loads((ROOT/'results/simulation/guard_ab.json').read_text())
    assert sum(r['crushed'] for r in guards if r['crush']>0 and not r['guarded']) == 85
    assert sum(r['crushed'] for r in guards if r['crush']>0 and r['guarded']) == 3
    assert sum(r['success'] for r in guards if not r['guarded']) == 12
    assert sum(r['success'] for r in guards if r['guarded']) == 0
    for arm, n in (('P_base', 3), ('Q_excess', 3)):
        files = list((ROOT/'results/simulation').glob(f'grid600_{arm}_s*.json'))
        assert len(files) == n, 'scale screen changed; update appendix'
        for p in files:
            record = json.loads(p.read_text())
            assert record['steps'] == 26000
            assert all(r['success'] == 0 and r['episodes'] == 100 for r in record['results'])
    bib = (ROOT/'paper/refs.bib').read_text()
    for cites in re.findall(r'\\cite\w*\{([^}]+)\}', tex):
        for key in cites.split(','):
            assert re.search(r'@\w+\{' + re.escape(key.strip()) + ',', bib), key
    log = (ROOT/'paper/main.log').read_text()
    assert not re.search(r'undefined|Overfull|^!', log, re.M), 'LaTeX references/layout need attention'
    assert '[URL]' not in tex and 'TODO' not in tex
    print('PASS: hardware outcomes, paired and stratified tables, trace classes, power, simulation means and contrasts, corpus counts and figure, measurement context, guard and scale disclosures, citations, and LaTeX checks')


if __name__ == '__main__':
    main()
