"""Factorial cell-means inference with HC3 covariance and global Holm correction."""
from itertools import combinations
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import scipy
import statsmodels
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

from analyze import ROOT, SEASONS, SECTIONS, OUTCOMES, load_data

ALPHA = 0.05
CELLS = [(section, season) for section in SECTIONS for season in SEASONS]


def weights(entries):
    result = np.zeros(20)
    for section, season, weight in entries:
        result[CELLS.index((section, season))] = weight
    return result


def evaluate(outcome, kind, label, contrast, means, covariance):
    contrast = np.atleast_2d(contrast)
    effect = contrast @ means
    variance = contrast @ covariance @ contrast.T
    rank = np.linalg.matrix_rank(contrast)
    wald = float(effect @ np.linalg.solve(variance, effect))
    result = {'outcome': outcome, 'kind': kind, 'contrast': label,
              'wald_chi2': wald, 'df': int(rank),
              'p_raw': float(stats.chi2.sf(wald, rank))}
    if rank == 1:
        estimate, se = float(effect[0]), float(np.sqrt(variance[0, 0]))
        critical = stats.norm.ppf(1 - ALPHA / 2)
        result.update(estimate=estimate, se=se, z=estimate / se,
                      ci_low=estimate - critical * se,
                      ci_high=estimate + critical * se)
    return result


def main():
    data = load_data()
    design = np.column_stack([
        ((data.river_section == section) & (data.saison == season)).astype(float)
        for section, season in CELLS])
    results, diagnostics, checks, sensitivity = [], [], [], []
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.4), layout='constrained')
    for row, outcome in enumerate(OUTCOMES):
        y = data[outcome].to_numpy()
        fit = sm.OLS(y, design).fit()
        robust = fit.get_robustcov_results(cov_type='HC3', use_t=False)
        means, covariance = np.asarray(robust.params), np.asarray(robust.cov_params())
        groups = [y[design[:, i] == 1] for i in range(20)]
        # Independent derivation: HC3 variance of a cell mean is s_g^2/(n_g-1).
        direct_means = np.array([g.mean() for g in groups])
        direct_cov = np.diag([g.var(ddof=1) / (len(g) - 1) for g in groups])
        np.testing.assert_allclose(means, direct_means, atol=1e-12)
        np.testing.assert_allclose(covariance, direct_cov, atol=1e-12)
        checks.append({'outcome': outcome, 'cell_means_max_abs_error': float(
            np.max(np.abs(means - direct_means))), 'HC3_max_abs_error': float(
                np.max(np.abs(covariance - direct_cov)))})
        seasonal = weights([(s, 'spring', .2) for s in SECTIONS] +
                           [(s, 'autumn', -.2) for s in SECTIONS])
        results.append(evaluate(outcome, 'season', 'spring - autumn', seasonal, means, covariance))
        section_contrasts = []
        for section in SECTIONS[1:]:
            section_contrasts.append(weights(
                [(section, t, .25) for t in SEASONS] +
                [(SECTIONS[0], t, -.25) for t in SEASONS]))
        results.append(evaluate(outcome, 'section_omnibus', 'equal section marginal means',
                                section_contrasts, means, covariance))
        interaction = []
        for section in SECTIONS[1:]:
            for season in SEASONS[1:]:
                interaction.append(weights([(section, season, 1), (section, 'spring', -1),
                    (SECTIONS[0], season, -1), (SECTIONS[0], 'spring', 1)]))
        results.append(evaluate(outcome, 'interaction', 'no section by season interaction',
                                interaction, means, covariance))
        for i, j in combinations(range(5), 2):
            contrast = weights([(SECTIONS[i], t, .25) for t in SEASONS] +
                               [(SECTIONS[j], t, -.25) for t in SEASONS])
            results.append(evaluate(outcome, 'section_pair', f'A{i+1} - A{j+1}',
                                    contrast, means, covariance))
        # Conventional pooled-variance covariance is a sensitivity analysis only.
        conventional = evaluate(outcome, 'season', 'spring - autumn', seasonal,
                                means, np.asarray(fit.cov_params()))
        sensitivity.append(conventional)
        cell_variances = np.array([g.var(ddof=1) for g in groups])
        residual = np.asarray(fit.resid)
        leverages = fit.get_influence().hat_matrix_diag
        standardized = residual / np.sqrt(fit.mse_resid * (1 - leverages))
        diagnostics.append({'outcome': outcome,
            'min_cell_sd': float(np.sqrt(cell_variances.min())),
            'max_cell_sd': float(np.sqrt(cell_variances.max())),
            'max_min_cell_variance_ratio': float(cell_variances.max()/cell_variances.min()),
            'residual_skewness': float(stats.skew(residual, bias=False)),
            'residual_excess_kurtosis': float(stats.kurtosis(residual, bias=False)),
            'max_abs_standardized_residual': float(np.max(np.abs(standardized))),
            'R_squared': float(fit.rsquared), 'residual_df': int(fit.df_resid)})
        axes[row, 0].scatter(fit.fittedvalues, residual, alpha=.35, s=10, color='#31816f')
        axes[row, 0].axhline(0, color='#333333', linewidth=.8)
        axes[row, 0].set(xlabel='Fitted concentration (mg/L)', ylabel='Residual (mg/L)',
                         title=outcome.replace('_mgL', '').title())
        stats.probplot(residual, dist='norm', plot=axes[row, 1])
        axes[row, 1].set(title='Residual normal Q-Q plot', ylabel='Ordered residual (mg/L)')
    fig.suptitle('Figure 3. Diagnostics for the full section-by-season models')
    fig.savefig(ROOT / 'outputs/figures/model_diagnostics.png', bbox_inches='tight')
    plt.close(fig)
    result = pd.DataFrame(results)
    assert len(result) == 26
    reject, adjusted, _, _ = multipletests(result.p_raw, alpha=ALPHA, method='holm')
    # Independently check the step-down implementation, including order restoration.
    order = np.argsort(result.p_raw.to_numpy())
    direct = np.minimum(1, np.maximum.accumulate(
        result.p_raw.to_numpy()[order] * np.arange(26, 0, -1)))
    np.testing.assert_allclose(adjusted[order], direct, atol=1e-14)
    result['p_holm'] = adjusted
    result['reject_005'] = reject
    result.to_csv(ROOT / 'outputs/tables/hypothesis_tests.csv', index=False)
    pd.DataFrame(diagnostics).to_csv(ROOT / 'outputs/tables/model_diagnostics.csv', index=False)
    pd.DataFrame(sensitivity).to_csv(ROOT / 'outputs/tables/pooled_variance_sensitivity.csv', index=False)
    # Test the 26 claims with HC2 as an additional covariance sensitivity analysis.
    # In this balanced design HC2 = (44/45) HC3 for every cell.
    hc2_p = stats.chi2.sf(result.wald_chi2.to_numpy() * 45/44, result.df.to_numpy())
    hc2_adj = multipletests(hc2_p, method='holm')[1]
    pd.DataFrame({'outcome': result.outcome, 'contrast': result.contrast,
                  'p_holm_HC2': hc2_adj, 'reject_005_HC2': hc2_adj < ALPHA}).to_csv(
                      ROOT / 'outputs/tables/hc2_sensitivity.csv', index=False)
    audit = {'alpha': ALPHA, 'covariance': 'HC3',
        'reference_distributions': 'normal for scalar contrasts; chi-square for joint Wald tests',
        'multiplicity': 'Holm over all 26 tests across both analytes',
        'confidence_intervals': '95% pointwise normal intervals; not multiplicity adjusted',
        'software': {'scipy': scipy.__version__, 'statsmodels': statsmodels.__version__},
        'cross_checks': checks, 'holm_independent_check': 'passed',
        'same_decisions_with_HC2': bool(np.array_equal(hc2_adj < ALPHA, reject))}
    (ROOT / 'outputs/inference_audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(result[['outcome', 'kind', 'contrast', 'estimate', 'p_holm', 'reject_005']].to_string(index=False))


if __name__ == '__main__':
    main()
