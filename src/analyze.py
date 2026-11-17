"""Validate and describe the water-quality data. No inferential claims are made."""
import hashlib
import json
import platform
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SEASONS = ['spring', 'summer', 'autumn', 'winter']
SECTIONS = ['A1_headwaters', 'A2_upper_course', 'A3_middle_course',
            'A4_lower_course', 'A5_mouth']
LABELS = ['Headwaters', 'Upper course', 'Middle course', 'Lower course', 'Mouth']
OUTCOMES = ['oxygen_mgL', 'nitrate_mgL']
COLORS = ['#31816f', '#d39435', '#ba6349', '#567eb0']


def load_data():
    data = pd.read_csv(ROOT / 'data/raw/waterquality.csv', sep=';')
    expected = ['ID', 'river_section', 'saison', 'nitrate_mgL', 'oxygen_mgL']
    if data.columns.tolist() != expected:
        raise ValueError(f'Unexpected columns: {data.columns.tolist()}')
    if len(data) != 900 or data.isna().any().any() or data.ID.duplicated().any():
        raise ValueError('Unexpected row count, missing values, or duplicate IDs.')
    if set(data.river_section) != set(SECTIONS) or set(data.saison) != set(SEASONS):
        raise ValueError('Unexpected section or season labels.')
    for outcome in OUTCOMES:
        values = pd.to_numeric(data[outcome], errors='raise')
        if not np.isfinite(values).all() or (values < 0).any():
            raise ValueError(f'Invalid concentrations: {outcome}')
    counts = data.groupby(['river_section', 'saison']).size()
    if len(counts) != 20 or not counts.eq(45).all():
        raise ValueError('Expected 45 observations in each of 20 cells.')
    data['river_section'] = pd.Categorical(data.river_section, SECTIONS, ordered=True)
    data['saison'] = pd.Categorical(data.saison, SEASONS, ordered=True)
    return data


def describe(data, groups):
    long = data.melt(id_vars=['ID', 'river_section', 'saison'],
                     value_vars=OUTCOMES, var_name='outcome', value_name='mg_L')
    result = long.groupby(groups + ['outcome'], observed=True)['mg_L'].agg(
        n='count', mean='mean', sd='std', median='median',
        q1=lambda s: s.quantile(.25), q3=lambda s: s.quantile(.75),
        minimum='min', maximum='max')
    result['iqr'] = result.q3 - result.q1
    return result.reset_index()


def main():
    data = load_data()
    tables = ROOT / 'outputs/tables'
    figures = ROOT / 'outputs/figures'
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    for name, groups in [('overall', []), ('by_season', ['saison']),
                         ('by_section', ['river_section']),
                         ('by_section_season', ['river_section', 'saison'])]:
        describe(data, groups).to_csv(tables / f'{name}.csv', index=False)
    counts = data.groupby(['river_section', 'saison'], observed=True).size()
    counts.rename('n').to_csv(tables / 'cell_counts.csv')
    means = data.groupby('saison', observed=True)[OUTCOMES].mean()
    (means.loc['spring'] - means.loc['autumn']).rename(
        'spring_minus_autumn_mg_L').to_csv(tables / 'season_mean_differences.csv')

    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'figure.dpi': 140})
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), layout='constrained')
    for ax, outcome, title in zip(axes, OUTCOMES, ['Oxygen', 'Nitrate']):
        values = [data.loc[data.saison == season, outcome] for season in SEASONS]
        boxes = ax.boxplot(values, tick_labels=[s.title() for s in SEASONS],
                           patch_artist=True, widths=.55)
        for patch, color in zip(boxes['boxes'], COLORS):
            patch.set_facecolor(color)
            patch.set_alpha(.7)
        ax.set(title=title, xlabel='Season (225 observations each)',
               ylabel='Concentration (mg/L)')
        ax.grid(axis='y', alpha=.18)
    fig.suptitle('Figure 1. Seasonal distributions pooled over five river sections')
    fig.savefig(figures / 'seasonal_distributions.png', bbox_inches='tight')
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout='constrained')
    for ax, outcome, title in zip(axes, OUTCOMES, ['Oxygen', 'Nitrate']):
        grouped = data.groupby(['river_section', 'saison'], observed=True)[outcome].mean()
        for season, color in zip(SEASONS, COLORS):
            values = [grouped.loc[section, season] for section in SECTIONS]
            ax.plot(range(5), values, marker='o', color=color, label=season.title())
        ax.set_xticks(range(5), LABELS, rotation=20, ha='right')
        ax.set(title=title, xlabel='River section (headwaters to mouth)',
               ylabel='Mean concentration (mg/L)')
        ax.grid(axis='y', alpha=.18)
    axes[1].legend(frameon=False)
    fig.suptitle('Figure 2. Section means by season (45 observations per point)')
    fig.savefig(figures / 'section_season_means.png', bbox_inches='tight')
    plt.close(fig)

    audit = {
        'rows': len(data), 'columns': data.columns.tolist(),
        'missing_values': {k: int(v) for k, v in data.isna().sum().items()},
        'duplicate_ids': int(data.ID.duplicated().sum()),
        'duplicate_rows': int(data.duplicated().sum()),
        'section_season_cells': len(counts), 'observations_per_cell': 45,
        'raw_sha256': hashlib.sha256((ROOT / 'data/raw/waterquality.csv').read_bytes()).hexdigest(),
        'software': {'python': platform.python_version(), 'pandas': pd.__version__,
                     'numpy': np.__version__, 'matplotlib': matplotlib.__version__},
        'scope': 'Descriptive analysis only; no hypothesis tests performed.',
    }
    (ROOT / 'outputs/data_audit.json').write_text(
        json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    print(f'Validated {len(data)} rows; saved descriptive tables and two figures.')
    print('Spring minus autumn means (mg/L):')
    print((means.loc['spring'] - means.loc['autumn']).round(4).to_string())
    return data


if __name__ == '__main__':
    main()
