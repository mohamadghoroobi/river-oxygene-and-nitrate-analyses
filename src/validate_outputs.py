"""Check generated results against the original observations and provenance."""
import hashlib
import json
import numpy as np
import pandas as pd
from analyze import ROOT, OUTCOMES, SECTIONS, load_data
from inference import ALPHA


def main():
    data = load_data()
    raw = ROOT / 'data/raw/waterquality.csv'
    digest = hashlib.sha256(raw.read_bytes()).hexdigest()
    metadata = json.loads(raw.with_suffix('.metadata.json').read_text())
    audit = json.loads((ROOT / 'outputs/data_audit.json').read_text())
    assert metadata['sha256'] == audit['raw_sha256'] == digest, 'Raw data changed.'
    tests = pd.read_csv(ROOT / 'outputs/tables/hypothesis_tests.csv')
    assert len(tests) == 26 and not tests[['outcome', 'kind', 'contrast']].duplicated().any()
    assert tests.p_raw.between(0, 1).all() and tests.p_holm.between(0, 1).all()
    assert (tests.p_holm >= tests.p_raw).all()
    assert np.allclose(tests.alpha, ALPHA)
    assert np.array_equal(tests.reject, tests.p_holm <= ALPHA)
    for outcome in OUTCOMES:
        rows = tests[tests.outcome == outcome]
        seasonal = rows[rows.kind == 'season'].iloc[0]
        expected = (data.loc[data.saison == 'spring', outcome].mean() -
                    data.loc[data.saison == 'autumn', outcome].mean())
        np.testing.assert_allclose(seasonal.estimate, expected, atol=1e-12)
        for _, pair in rows[rows.kind == 'section_pair'].iterrows():
            first, second = pair.contrast.split(' - ')
            a, b = SECTIONS[int(first[1:])-1], SECTIONS[int(second[1:])-1]
            expected = (data.loc[data.river_section == a, outcome].mean() -
                        data.loc[data.river_section == b, outcome].mean())
            np.testing.assert_allclose(pair.estimate, expected, atol=1e-12)
        scalar = rows[rows.kind.isin(['season', 'section_pair'])]
        assert (scalar.ci_low < scalar.estimate).all()
        assert (scalar.ci_high > scalar.estimate).all()
    inference = json.loads((ROOT / 'outputs/inference_audit.json').read_text())
    assert inference['holm_independent_check'] == 'passed'
    assert inference['same_decisions_with_HC2']
    for filename in ['seasonal_distributions.png', 'section_season_means.png', 'model_diagnostics.png']:
        assert (ROOT / 'outputs/figures' / filename).stat().st_size > 1000
    assert (ROOT / 'report/river_water_quality_report.pdf').stat().st_size > 1000
    print('Validated provenance, all 22 scalar estimates, p-values, decisions, and deliverables.')


if __name__ == '__main__':
    main()
