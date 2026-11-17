"""Export numerical tables and figures for the editable Overleaf project."""
from pathlib import Path
import json
import shutil

import pandas as pd

from analyze import ROOT
from inference import ALPHA

PROJECT = ROOT / 'overleaf'


def pvalue(value):
    if value < 1e-99:
        return r'$<10^{-99}$'
    if value < .001:
        mantissa, exponent = f'{value:.2e}'.split('e')
        return f'${mantissa}\\times10^{{{int(exponent)}}}$'
    return f'{value:.4f}'


def tabular(name, columns, rows):
    path = PROJECT / 'tables' / f'{name}.tex'
    text = [r'\begin{tabular}{' + columns + '}', r'\toprule']
    for i, row in enumerate(rows):
        text.append(' & '.join(row) + r' \\')
        if i == 0:
            text.append(r'\midrule')
    text += [r'\bottomrule', r'\end{tabular}', '']
    path.write_text('\n'.join(text), encoding='utf-8')


def main():
    (PROJECT / 'tables').mkdir(parents=True, exist_ok=True)
    (PROJECT / 'figures').mkdir(exist_ok=True)
    seasons = pd.read_csv(ROOT / 'outputs/tables/by_season.csv')
    sections = pd.read_csv(ROOT / 'outputs/tables/by_section.csv')
    tests = pd.read_csv(ROOT / 'outputs/tables/hypothesis_tests.csv')
    if not (tests.alpha == ALPHA).all():
        raise ValueError('Run inference.py before exporting the LaTeX tables.')
    rows = [['Season', '$n$', 'Oxygen: mean (SD)', 'Nitrate: mean (SD)']]
    for season in ['spring', 'summer', 'autumn', 'winter']:
        selected = seasons[seasons.saison == season].set_index('outcome')
        rows.append([season.title(), '225'] + [f'{selected.loc[o, "mean"]:.3f} ({selected.loc[o, "sd"]:.3f})'
            for o in ['oxygen_mgL', 'nitrate_mgL']])
    tabular('seasonal', 'lrrr', rows)
    rows = [['Section', '$n$', 'Oxygen: mean (SD)', 'Nitrate: mean (SD)']]
    labels = ['A1: Headwaters', 'A2: Upper course', 'A3: Middle course', 'A4: Lower course', 'A5: Mouth']
    for code, label in zip(sections.river_section.unique(), labels):
        selected = sections[sections.river_section == code].set_index('outcome')
        rows.append([label, '180'] + [f'{selected.loc[o, "mean"]:.3f} ({selected.loc[o, "sd"]:.3f})'
            for o in ['oxygen_mgL', 'nitrate_mgL']])
    tabular('sections', 'lrrr', rows)
    rows = [['Outcome', 'Difference', r'92.5\% pointwise CI', 'Raw $p$', 'Holm $p$']]
    for _, r in tests[tests.kind == 'season'].iterrows():
        label = 'Oxygen' if r.outcome == 'oxygen_mgL' else 'Nitrate'
        rows.append([label, f'{r.estimate:.3f}', f'[{r.ci_low:.3f}, {r.ci_high:.3f}]',
                     pvalue(r.p_raw), pvalue(r.p_holm)])
    tabular('season_tests', 'lrrrr', rows)
    rows = [['Outcome / null hypothesis', '$W$', 'df', 'Holm $p$']]
    for _, r in tests[tests.kind.isin(['section_omnibus', 'interaction'])].iterrows():
        label = ('Oxygen' if r.outcome == 'oxygen_mgL' else 'Nitrate')
        label += ' / equal section means' if r.kind == 'section_omnibus' else ' / no interaction'
        rows.append([label, f'{r.wald_chi2:.2f}', str(int(r.df)), pvalue(r.p_holm)])
    tabular('omnibus', 'lrrr', rows)
    rows = [['Pair', r'$D_{ab}$: oxygen', 'Holm $p$', r'$D_{ab}$: nitrate', 'Holm $p$']]
    pairs = tests[tests.kind == 'section_pair']
    for name in pairs.contrast.unique():
        selected = pairs[pairs.contrast == name].set_index('outcome')
        a, b = selected.loc['oxygen_mgL'], selected.loc['nitrate_mgL']
        rows.append([name.replace(' - ', '--'), f'{a.estimate:.3f}', pvalue(a.p_holm),
                     f'{b.estimate:.3f}', pvalue(b.p_holm)])
    tabular('pairs', 'lrrrr', rows)
    for filename in ['seasonal_distributions.png', 'section_season_means.png', 'model_diagnostics.png']:
        shutil.copyfile(ROOT / 'outputs/figures' / filename, PROJECT / 'figures' / filename)
    manifest = {'alpha': ALPHA, 'confidence_level': 1-ALPHA,
        'expected_pages': 10, 'main_document': 'main.tex', 'compiler': 'pdfLaTeX',
        'bibliography': 'Omitted at the author request; university literature requirements remain unmet.'}
    (PROJECT / 'analysis_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Exported LaTeX tables and figures for alpha =', ALPHA)


if __name__ == '__main__':
    main()
