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
                   'recorded leader commands'):
        # Case-insensitive: prose checks concern disclosures, not typography.
        assert phrase.lower() in flat.lower(), f'missing disclosure/input: {phrase}'
    expected = [(20, 5, 9, 6, 2), (20, 1, 14, 14, 1), (6, 0, 0, 0, 0)]
    table = (generated / 'hardware_table_all.tex').read_text()
    for r, target in zip(actual['hardware'], expected):
        assert (r['pairs'], r['base'], r['delta'], r['delta_only'], r['base_only']) == target, 'hardware changed; revise prose'
        assert f"{r['base']}/{r['pairs']} & {r['delta']}/{r['pairs']}" in table
    completed_table = (generated / 'hardware_table.tex').read_text()
    assert '0/6' not in completed_table and '0/6' in table
    assert 'generated/hardware_table_all.tex' in tex
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
    print('PASS: hardware outcomes, paired tables, simulation means, corpus counts, guard and scale disclosures, citations, and LaTeX checks')


if __name__ == '__main__':
    main()
