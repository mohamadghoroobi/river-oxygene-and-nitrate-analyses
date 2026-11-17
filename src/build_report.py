"""Build the ten-page report from the verified analysis outputs."""
import argparse
from html import escape
from pathlib import Path
import platform

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import nbformat
import numpy as np
import pandas as pd
import reportlab
import scipy
import statsmodels
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                               Table, TableStyle, Image, KeepTogether)

ROOT = Path(__file__).resolve().parents[1]
WIDTH = A4[0] - 108
BLUE = colors.HexColor('#214f63')


def pvalue(value):
    if value < 1e-99:
        return '&lt;1e-99'
    return f'{value:.2e}' if value < .001 else f'{value:.4f}'


def main(author):
    out = ROOT / 'report'
    out.mkdir(exist_ok=True)
    # Prefer embedded Times New Roman; use built-in Times on non-Windows systems.
    fonts = Path('C:/Windows/Fonts')
    regular, bold, italic = 'Times-Roman', 'Times-Bold', 'Times-Italic'
    if (fonts / 'times.ttf').exists():
        for name, filename in [('ReportTimes', 'times.ttf'), ('ReportTimesBold', 'timesbd.ttf'),
                               ('ReportTimesItalic', 'timesi.ttf')]:
            pdfmetrics.registerFont(TTFont(name, str(fonts / filename)))
        pdfmetrics.registerFontFamily('ReportTimes', normal='ReportTimes',
                                      bold='ReportTimesBold', italic='ReportTimesItalic')
        regular, bold, italic = 'ReportTimes', 'ReportTimesBold', 'ReportTimesItalic'
    body = ParagraphStyle('Body', fontName=regular, fontSize=11.5, leading=16.5,
                          spaceAfter=8, textColor=colors.HexColor('#18232a'))
    heading = ParagraphStyle('Heading', parent=body, fontName=bold, fontSize=17,
                             leading=21, textColor=BLUE, spaceAfter=14)
    sub = ParagraphStyle('Sub', parent=body, fontName=bold, fontSize=12.5,
                         leading=16, spaceBefore=5, spaceAfter=7)
    small = ParagraphStyle('Small', parent=body, fontSize=9.5, leading=12.5, spaceAfter=7)
    caption = ParagraphStyle('Caption', parent=small, fontName=italic, spaceBefore=5)
    center = ParagraphStyle('Center', parent=body, alignment=TA_CENTER)
    title = ParagraphStyle('Title', parent=center, fontName=bold, fontSize=29,
                           leading=35, textColor=BLUE, spaceAfter=20)
    story, source = [], []
    def para(text, style=body):
        story.append(Paragraph(text, style))
        source.append(text)
    def section(text):
        para(text, heading)
    def subsection(text):
        para(text, sub)
    def page():
        story.append(PageBreak())
        source.append('\n--- PAGE BREAK ---\n')
    def table(rows, widths=None, size=9.6):
        style = ParagraphStyle('Cell', parent=small, fontSize=size, leading=size+3,
                               spaceAfter=0)
        entries = [[Paragraph(str(v), style) for v in row] for row in rows]
        t = Table(entries, colWidths=widths, repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e7eff2')),
            ('LINEBELOW', (0, 0), (-1, 0), .7, BLUE),
            ('LINEBELOW', (0, -1), (-1, -1), .5, colors.HexColor('#aabac2')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t)
        story.append(Spacer(1, 9))
        source.extend([' | '.join(str(v) for v in row) for row in rows])
    def figure(name, height=None):
        path = ROOT / 'outputs/figures' / name
        from PIL import Image as PILImage
        with PILImage.open(path) as im:
            w, h = im.size
        image_width = WIDTH if height is None else min(WIDTH, height*w/h)
        story.append(Image(str(path), width=image_width, height=image_width*h/w))
        source.append(f'[Figure: outputs/figures/{name}]')
    def equation(name, expression, height=.46):
        target = out / 'equations'
        target.mkdir(exist_ok=True)
        fig = plt.figure(figsize=(6.8, height))
        fig.text(.5, .5, expression, fontsize=13, ha='center', va='center')
        dest = target / f'{name}.png'
        fig.savefig(dest, dpi=220, transparent=True, bbox_inches='tight', pad_inches=.08)
        plt.close(fig)
        from PIL import Image as PILImage
        with PILImage.open(dest) as im:
            w, h = im.size
        story.append(Image(str(dest), width=min(WIDTH, w*72/220),
                           height=min(WIDTH, w*72/220)*h/w))
        story.append(Spacer(1, 6))
        source.append(expression)

    tests = pd.read_csv(ROOT / 'outputs/tables/hypothesis_tests.csv')
    diag = pd.read_csv(ROOT / 'outputs/tables/model_diagnostics.csv')
    seasons = pd.read_csv(ROOT / 'outputs/tables/by_season.csv')
    sections = pd.read_csv(ROOT / 'outputs/tables/by_section.csv')
    seasonal = tests[tests.kind == 'season'].set_index('outcome')
    oxygen, nitrate = seasonal.loc['oxygen_mgL'], seasonal.loc['nitrate_mgL']

    # Page 1
    story.append(Spacer(1, 65))
    para('Seasonal and spatial patterns<br/>in river water quality', title)
    para('Oxygen and nitrate concentrations across five river sections', center)
    story.append(Spacer(1, 35))
    para(escape(author), ParagraphStyle('Author', parent=center, fontName=bold, fontSize=16))
    para('17 November 2026', center)
    story.append(Spacer(1, 45))
    para('Application Report<br/>M.Sc. Data Science<br/>TU Dortmund University<br/>Summer Semester 2027', center)
    story.append(Spacer(1, 50))
    para('Abstract', sub)
    para('This report examines 900 measurements of oxygen and nitrate in a balanced design of five river sections and four seasons. A factorial cell-means model with heteroskedasticity-robust inference compares spring with autumn and evaluates section differences. After Holm adjustment across 26 tests, nitrate differs between spring and autumn and between every section pair. Oxygen shows section differences and a section-by-season interaction, but no statistically significant averaged spring-autumn difference. All inference is conditional on independent sampling, which cannot be verified from the supplied data.')
    page()

    # Page 2
    section('Contents')
    toc = [
        ('1. Introduction and data', 3), ('2. Statistical model and estimands', 4),
        ('3. Testing, multiplicity and diagnostics', 5), ('4. Descriptive seasonal results', 6),
        ('5. Descriptive section results', 7), ('6. Hypothesis tests and pairwise comparisons', 8),
        ('7. Discussion and conclusions', 9), ('References', 10)]
    table([['Section', 'Page']] + [[label, str(number)] for label, number in toc], [WIDTH-45, 45], 11)
    subsection('Research questions')
    para('First, do spring and autumn differ in their mean oxygen and nitrate concentrations? Second, do mean concentrations differ between river sections, and which pairs differ? Both questions concern concentrations measured in milligrams per liter (mg/L).')
    subsection('Reading the results')
    para('Seasonal contrasts average equally over the five sections. Section contrasts average equally over the four seasons. The model retains interactions, so these averages do not imply a common effect in every season or section. Two-sided tests use a familywise significance level of 0.05. All reported adjusted p-values belong to one family of 26 tests.')
    para('The report includes two statistical figures and seven tables. The repository also supplies cell-level descriptive statistics, all pointwise confidence intervals, model diagnostics, provenance records, and executable analysis and report-generation code. These materials support reproduction without extending the ten-page report.')
    page()

    # Page 3
    section('1. Introduction and data')
    para('A comparison of water-quality measurements should distinguish spatial patterns from seasonal variation. Pooling all observations can obscure differences that change across the year. Here, oxygen and nitrate are analyzed separately while preserving the same section-season structure. The aim is to quantify observed differences and their statistical uncertainty, without attributing them to an unmeasured physical or biological cause.')
    para('TU Dortmund University provides the application task and the data file <i>waterquality.csv</i> (TU Dortmund University, 2026a, 2026b). The dataset contains 900 rows. Each of five ordered sections has 180 observations: 45 in spring, summer, autumn, and winter. The section labels run from headwaters (A1) through upper course (A2), middle course (A3), and lower course (A4) to the mouth (A5).')
    para('Table 1 describes the variables. Oxygen and nitrate are quantitative concentrations in mg/L. Season is treated as a categorical factor rather than a numeric trend. River section is ordered geographically, but is modeled categorically because no distances are supplied. ID is excluded from the statistical model.')
    table([['Variable', 'Meaning', 'Treatment'], ['ID', 'Row identifier', 'Validation only'],
           ['river_section', 'Five river sections', 'Categorical factor'],
           ['saison', 'Four seasons', 'Categorical factor'],
           ['oxygen_mgL', 'Oxygen concentration', 'Numeric outcome, mg/L'],
           ['nitrate_mgL', 'Nitrate concentration', 'Numeric outcome, mg/L']],
          [100, 195, WIDTH-295], 10)
    para('Table 1. Variables in the original semicolon-separated CSV.', caption)
    para('Validation found no missing values, duplicate IDs, duplicate complete rows, negative concentrations, or nonfinite values. All 20 section-season cells contain exactly 45 observations. No measurements were removed or imputed. These checks establish consistency with the task description; they do not verify the measurement process.')
    para('The file contains no sampling dates, repeated-site identifiers, collection protocol, or confirmed river name. The analysis therefore assumes independent observations conditionally within the design. This assumption is a limitation, not a conclusion from the IDs. The principal findings are a spring-autumn nitrate difference, a downstream nitrate gradient, and a season-dependent oxygen pattern. Sections 2-3 define the methods, Sections 4-6 present results, and Section 7 discusses their limits.')
    page()

    # Page 4
    section('2. Statistical model and estimands')
    subsection('2.1 A factorial model without additive restrictions')
    para('For each outcome separately, let Y<sub>ijk</sub> be observation k in section i and season j, with i = 1,...,5, j = 1,...,4, and k = 1,...,45. The full factorial model is written in cell-means form:')
    equation('model', r'$Y_{ijk}=\mu_{ij}+\varepsilon_{ijk},\qquad E(\varepsilon_{ijk})=0,\quad \mathrm{Var}(\varepsilon_{ijk})=\sigma_{ij}^{2}.$')
    para('This is equivalent to an intercept, section effects, season effects, and their interaction under suitable identifying constraints (Faraway, 2014, Chapters 14-16). In matrix form Y = X beta + epsilon, X has one indicator column for each of the 20 cells. The least-squares estimate is beta-hat = (X\u2032X)<super>-1</super>X\u2032Y, which equals the vector of sample cell means. There are 900 - 20 = 880 residual degrees of freedom.')
    subsection('2.2 Contrasts that answer the questions')
    para('The seasonal estimand is the equally weighted spring-autumn difference. The section estimand is the difference between two section means, each averaged over all seasons:')
    equation('estimands', r'$\Delta=\frac{1}{5}\sum_{i=1}^{5}(\mu_{i,\mathrm{spring}}-\mu_{i,\mathrm{autumn}}),\qquad D_{ab}=\frac{1}{4}\sum_{j=1}^{4}(\mu_{aj}-\mu_{bj}).$', .65)
    para('Because the dataset is balanced, these equal-weight averages also equal the corresponding pooled sample means. Explicit contrasts retain the intended weights if the implementation is reviewed. A positive Delta means a higher spring concentration; a positive D<sub>ab</sub> means a higher concentration in section a. Effect estimates remain in the original mg/L units.')
    subsection('2.3 Covariance estimation')
    para('Errors may have different variances across cells. HC3 covariance uses residuals e<sub>r</sub> and diagonal leverages h<sub>r</sub> of X(X\u2032X)<super>-1</super>X\u2032 (Davidson and MacKinnon, 2004, Section 5.5):')
    equation('hc3', r'$\widehat V_{\mathrm{HC3}}=(X^\top X)^{-1}X^\top\mathrm{diag}\!\left(\frac{e_r^2}{(1-h_r)^2}\right)X(X^\top X)^{-1}.$', .65)
    para('Here h<sub>r</sub> = 1/45, and the HC3 variance of cell mean ij simplifies to s<sub>ij</sub><super>2</super>/44, where s<sub>ij</sub><super>2</super> is the usual sample variance. The covariance matrix is diagonal under independent sampling. A direct cell-based calculation reproduces the software covariance to numerical precision. HC3 addresses heteroskedasticity; it does not correct dependence between observations.')
    page()

    # Page 5
    section('3. Testing, multiplicity and diagnostics')
    subsection('3.1 Null hypotheses and reference distributions')
    para('For each analyte, the seasonal null is H<sub>0</sub>: Delta = 0 against Delta unequal to 0. The omnibus section null states that all five equally weighted section means are equal; four linearly independent contrasts test it. Each of ten section-pair nulls states D<sub>ab</sub> = 0. Finally, 12 independent difference-in-differences contrasts test the absence of interaction: (mu<sub>ij</sub> - mu<sub>i1</sub>) - (mu<sub>1j</sub> - mu<sub>11</sub>) = 0 for i &gt; 1 and j &gt; 1.')
    equation('wald', r'$W=(L\hat\beta)^\top(L\widehat V_{\mathrm{HC3}}L^\top)^{-1}(L\hat\beta),\qquad W\ \dot\sim\ \chi_q^2.$', .6)
    para('L contains the q independent contrast rows. For q = 1, z = (c\u2032 beta-hat)/sqrt(c\u2032 V-hat c) is compared with a standard normal distribution; W = z<super>2</super>. These are large-sample approximations rather than exact finite-sample tests. Pointwise 95% confidence intervals are estimate plus or minus 1.96 times the HC3 standard error. Robust Wald inference is described by Davidson and MacKinnon (2004); the implementation uses statsmodels (2026).')
    subsection('3.2 A single multiplicity family')
    para('The family comprises 26 tests: two seasonal, two omnibus section, twenty pairwise section, and two interaction tests. Holm adjustment controls the probability of at least one false rejection at alpha = 0.05 when the individual p-values are valid. For ordered p-values p<sub>(1)</sub> through p<sub>(26)</sub>, define:')
    equation('holm', r'$p^{\mathrm{adj}}_{(k)}=\min\!\left\{1,\ \max_{1\leq r\leq k}(26-r+1)p_{(r)}\right\}. $', .6)
    para('Reject when the adjusted p-value is at most 0.05. The procedure permits arbitrary dependence between tests (Holm, 1979; Hochberg and Tamhane, 1987). Including both analytes in one family avoids treating their related conclusions as separate opportunities for rejection. The 95% intervals remain pointwise and should not be read as simultaneous intervals corresponding to the adjusted decisions.')
    subsection('3.3 Descriptive methods and diagnostic checks')
    para('Tables report means, sample SDs with denominator n - 1, medians, quartiles, and ranges. A boxplot spans quartiles Q1 to Q3, marks the median, and extends whiskers to the furthest observations within 1.5(Q3 - Q1) of the box. Remaining points are displayed and retained. Quartiles use linear interpolation. Residual-versus-fitted and normal Q-Q plots inspect spread and shape; diagnostics follow the approach in Faraway (2014, Chapter 6). HC2 covariance provides a sensitivity check. No outcome-based observation deletion or model selection is used.')
    page()

    # Page 6
    section('4. Descriptive seasonal results')
    para('Table 2 summarizes the seasonal concentrations. Oxygen has its lowest mean in summer (7.040 mg/L) and its highest mean in winter (9.935 mg/L). Nitrate has its highest mean in summer (10.342 mg/L) and its lowest mean in winter (7.198 mg/L). Each season contributes the same number of observations from each river section.')
    rows = [['Season', 'n', 'Oxygen: mean (SD)', 'Nitrate: mean (SD)']]
    for season in ['spring', 'summer', 'autumn', 'winter']:
        a = seasons[(seasons.saison == season) & (seasons.outcome == 'oxygen_mgL')].iloc[0]
        b = seasons[(seasons.saison == season) & (seasons.outcome == 'nitrate_mgL')].iloc[0]
        rows.append([season.title(), '225', f'{a["mean"]:.3f} ({a.sd:.3f})', f'{b["mean"]:.3f} ({b.sd:.3f})'])
    table(rows, [75, 35, (WIDTH-110)/2, (WIDTH-110)/2], 10)
    para('Table 2. Seasonal mean and sample SD, in mg/L, pooling all five sections.', caption)
    para('Figure 1 displays the distributions rather than means alone. The spring and autumn oxygen distributions overlap substantially. Their nitrate distributions also overlap, despite a larger difference in their means. Overlap does not itself decide a hypothesis test; Section 6 quantifies uncertainty using the factorial model.')
    figure('seasonal_distributions.png')
    para('Figure 1. Seasonal boxplots, 225 observations per season. Boxes show Q1, median, and Q3; whiskers follow the 1.5-IQR rule. Points beyond whiskers are retained measurements.', caption)
    para('Spring oxygen has mean 9.531 mg/L and median 9.550 mg/L; autumn has mean 9.379 mg/L and median 9.514 mg/L. Spring nitrate has mean 9.289 mg/L and median 9.652 mg/L; autumn has mean 8.418 mg/L and median 8.568 mg/L. The observed mean differences are therefore +0.152 and +0.871 mg/L, respectively. These descriptive numbers do not yet incorporate multiplicity.')
    page()

    # Page 7
    section('5. Descriptive section results')
    para('Table 3 gives section summaries averaged over all four seasons. Mean nitrate increases from 5.350 mg/L at the headwaters to 11.467 mg/L at the mouth. Mean oxygen varies less between sections, from 8.694 mg/L in the lower course to 9.231 mg/L at the headwaters. The mouth has a higher oxygen mean than the lower course, so its pooled spatial pattern is not monotonic.')
    rows = [['Section', 'n', 'Oxygen: mean (SD)', 'Nitrate: mean (SD)']]
    labels = ['A1: Headwaters', 'A2: Upper course', 'A3: Middle course', 'A4: Lower course', 'A5: Mouth']
    for label, code in zip(labels, ['A1_headwaters','A2_upper_course','A3_middle_course','A4_lower_course','A5_mouth']):
        a = sections[(sections.river_section == code) & (sections.outcome == 'oxygen_mgL')].iloc[0]
        b = sections[(sections.river_section == code) & (sections.outcome == 'nitrate_mgL')].iloc[0]
        rows.append([label, '180', f'{a["mean"]:.3f} ({a.sd:.3f})', f'{b["mean"]:.3f} ({b.sd:.3f})'])
    table(rows, [112, 30, (WIDTH-142)/2, (WIDTH-142)/2], 10)
    para('Table 3. Section means and sample SDs in mg/L, pooling the four seasons.', caption)
    para('Figure 2 separates these profiles by season. Nitrate rises downstream in all four seasons. Summer oxygen decreases toward the mouth, whereas winter oxygen changes relatively little. Autumn oxygen falls in the lower course and rises again at the mouth. These unequal profiles motivate retaining the interaction rather than assuming an identical section effect throughout the year.')
    figure('section_season_means.png')
    para('Figure 2. Mean concentration by section and season; each point averages 45 observations. Lines connect ordered categories and do not imply continuous spatial interpolation. Uncertainty is evaluated by the tests in Section 6.', caption)
    para('Pooled section SDs include variation between seasons as well as variation within a season. They should therefore not be substituted for within-cell variability when assessing the factorial contrasts. The model uses residual variation within all 20 cells.')
    page()

    # Page 8
    section('6. Hypothesis tests and pairwise comparisons')
    para('Table 4 answers the seasonal question. Nitrate is higher in spring by 0.871 mg/L; its adjusted p-value is below 0.05. Oxygen has an estimated difference of 0.152 mg/L, but its interval includes zero and its adjusted p-value is 0.324. This does not establish equivalence of the seasons.', small)
    rows = [['Outcome', 'Difference', '95% pointwise CI', 'Raw p', 'Holm p']]
    for label, r in [('Oxygen', oxygen), ('Nitrate', nitrate)]:
        rows.append([label, f'{r.estimate:.3f}', f'[{r.ci_low:.3f}, {r.ci_high:.3f}]', pvalue(r.p_raw), pvalue(r.p_holm)])
    table(rows, [65, 65, 137, 105, WIDTH-372], 9)
    para('Table 4. Spring minus autumn contrasts, averaged over sections. Differences and intervals are in mg/L.', caption)
    rows = [['Outcome / null hypothesis', 'W', 'df', 'Holm p']]
    for _, r in tests[tests.kind.isin(['section_omnibus', 'interaction'])].iterrows():
        label = ('Oxygen' if r.outcome == 'oxygen_mgL' else 'Nitrate') + (' / equal section means' if r.kind == 'section_omnibus' else ' / no interaction')
        rows.append([label, f'{r.wald_chi2:.2f}', str(int(r.df)), pvalue(r.p_holm)])
    table(rows, [WIDTH-195, 60, 35, 100], 9)
    para('Table 5. Robust joint Wald tests. Both section tests and the oxygen interaction test reject their nulls. The nitrate interaction test does not reject.', caption)
    rows = [['Pair', 'Oxygen difference', 'Oxygen Holm p', 'Nitrate difference', 'Nitrate Holm p']]
    pairs = tests[tests.kind == 'section_pair']
    for name in pairs.contrast.unique():
        a = pairs[(pairs.contrast == name) & (pairs.outcome == 'oxygen_mgL')].iloc[0]
        b = pairs[(pairs.contrast == name) & (pairs.outcome == 'nitrate_mgL')].iloc[0]
        rows.append([name, f'{a.estimate:.3f}', pvalue(a.p_holm), f'{b.estimate:.3f}', pvalue(b.p_holm)])
    table(rows, [55, 100, 105, 105, WIDTH-365], 8.7)
    para('Table 6. Section-pair contrasts (first section minus second), averaged equally over seasons. Differences are in mg/L. Tables 4-6 share one 26-test Holm adjustment. Very small p-values are displayed as &lt;1e-99; numerical underflow in the CSV does not imply zero probability.', caption)
    para('All ten nitrate pairs differ. Five oxygen pairs differ: A1-A4, A1-A5, A2-A4, A3-A4, and A4-A5. The remaining pairs do not reject at 0.05. Oxygen comparisons describe seasonal averages and must be read alongside its interaction.', small)
    page()

    # Page 9
    section('7. Discussion and conclusions')
    subsection('7.1 Diagnostics and robustness')
    para('Table 7 summarizes within-cell variability and residual shape. Cell SDs vary, supporting the use of a covariance estimator that allows unequal variances. Residual skewness is close to zero for both outcomes. The residual Q-Q and fitted-value plots are supplied as Figure 3 in the repository; they show no pronounced overall curvature in the Q-Q relationship. This visual check cannot prove normality or independence.', small)
    rows = [['Diagnostic', 'Oxygen', 'Nitrate'],
        ['Within-cell SD range (mg/L)', f'{diag.iloc[0].min_cell_sd:.3f}-{diag.iloc[0].max_cell_sd:.3f}', f'{diag.iloc[1].min_cell_sd:.3f}-{diag.iloc[1].max_cell_sd:.3f}'],
        ['Largest/smallest cell variance', f'{diag.iloc[0].max_min_cell_variance_ratio:.3f}', f'{diag.iloc[1].max_min_cell_variance_ratio:.3f}'],
        ['Residual skewness', f'{diag.iloc[0].residual_skewness:.3f}', f'{diag.iloc[1].residual_skewness:.3f}'],
        ['Maximum |standardized residual|', f'{diag.iloc[0].max_abs_standardized_residual:.3f}', f'{diag.iloc[1].max_abs_standardized_residual:.3f}']]
    table(rows, [WIDTH-180, 90, 90], 9.5)
    para('Table 7. Model diagnostics. Standardized residuals use the model residual mean square and leverage; all measurements remain in the analysis.', caption)
    para('Replacing HC3 by HC2 scales each cell-mean variance by 44/45 and leaves all 26 adjusted decisions unchanged. A pooled-variance seasonal calculation also leaves oxygen nonsignificant and nitrate significant. These checks address covariance choice, not errors in the sampling protocol. Tests remain asymptotic, and HC3 alone cannot correct spatial or temporal correlation.', small)
    subsection('7.2 Answers and interpretation')
    para('For spring versus autumn, the analysis finds higher mean nitrate in spring, averaged across sections, but insufficient evidence of an oxygen difference after correction. For river sections, both analytes show differences in their marginal means. Every nitrate pair differs, with higher means progressively downstream. The oxygen pairs identified in Table 6 differ on average over seasons, while its significant interaction indicates that spatial differences vary through the year. Failure to reject any other pair does not show that its means are equal.')
    para('The nitrate gradient and the low summer oxygen values identify patterns worth investigating, but the dataset contains no covariates that explain them. There is no basis here for attributing changes to agriculture, discharge, temperature, or another mechanism. Statistical significance does not establish environmental harm or regulatory noncompliance; that would require applicable standards and additional contextual measurements.')
    subsection('7.3 Limits and reproducibility')
    para('The main limitation is the unknown sampling design. Repeated samples from the same site or sampling occasion could invalidate the assumed covariance structure. Future analysis should obtain dates, site identifiers, hydrological information, and measurement protocols, then use a suitable dependence model. The present conclusions apply conditionally to the supplied design, without a claim of representativeness for other rivers or years.', small)
    para('Python (Python Software Foundation, 2026), NumPy (2026), pandas (2026), Matplotlib (2026), SciPy (Virtanen et al., 2020), and statsmodels (2026) produce the analysis. ReportLab (2026) generates this PDF; nbformat (Jupyter, 2026) supports the notebook. Raw-data hashes, software versions, scripts, and all numerical outputs are retained for reproduction.', small)
    page()

    # Page 10
    section('References')
    references = [
        'Davidson, R. and MacKinnon, J. G. (2004). <i>Econometric Theory and Methods.</i> Oxford University Press, New York. Section 5.5. Author-hosted edition: https://econ.queensu.ca/ETM/ (accessed 17 November 2026).',
        'Faraway, J. J. (2014). <i>Linear Models with R.</i> 2nd ed. Chapman &amp; Hall/CRC, Boca Raton. Chapters 1-3, 6, 14-16. Author materials: https://julianfaraway.github.io/faraway/LMR/ (accessed 17 November 2026).',
        'Hochberg, Y. and Tamhane, A. C. (1987). <i>Multiple Comparison Procedures.</i> John Wiley &amp; Sons, New York. https://doi.org/10.1002/9780470316672.',
        'Holm, S. (1979). A simple sequentially rejective multiple test procedure. <i>Scandinavian Journal of Statistics</i>, 6(2), 65-70.',
        'TU Dortmund University (2026a). <i>Application Report Master Data Science: Sommersemester 2027.</i> Department of Statistics. Application brief supplied as a local PDF; accessed 17 November 2026. Publication year is not specified; 2026 denotes access year.',
        'TU Dortmund University (2026b). <i>waterquality.csv.</i> Application dataset. https://statistik.tu-dortmund.de/storages/statistik/r/Downloads/Studium/Studiengaenge-Infos/Data_Science/waterquality.csv (downloaded 17 November 2026). Publication year is not specified; 2026 denotes access year.',
        f'Python Software Foundation (2026). <i>Python</i>, version {platform.python_version()}. https://www.python.org/. NumPy developers (2026). <i>NumPy</i>, version {np.__version__}. https://numpy.org/. Software; accessed 17 November 2026.',
        f'pandas development team (2026). <i>pandas</i>, version {pd.__version__}. https://pandas.pydata.org/. Matplotlib development team (2026). <i>Matplotlib</i>, version {matplotlib.__version__}. https://matplotlib.org/. Software; accessed 17 November 2026.',
        f'Virtanen, P., Gommers, R., Oliphant, T. E., et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. <i>Nature Methods</i>, 17, 261-272. https://doi.org/10.1038/s41592-019-0686-2. SciPy version used: {scipy.__version__}.',
        f'statsmodels developers (2026). <i>statsmodels</i>, version {statsmodels.__version__}. HC3 covariance and multiple-testing documentation. https://www.statsmodels.org/stable/ (accessed 17 November 2026).',
        f'ReportLab (2026). <i>ReportLab Toolkit</i>, version {reportlab.Version}. https://www.reportlab.com/. Jupyter developers (2026). <i>nbformat</i>, version {nbformat.__version__}. https://nbformat.readthedocs.io/. Software; accessed 17 November 2026.',
    ]
    for ref in references:
        para(ref, small)
    def footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#b5c7cf'))
        canvas.line(54, 43, A4[0]-54, 43)
        canvas.setFont(regular, 9)
        canvas.setFillColor(colors.HexColor('#526773'))
        canvas.drawString(54, 29, 'River water quality | TU Dortmund application report')
        canvas.drawRightString(A4[0]-54, 29, str(document.page))
        canvas.restoreState()
    pdf = out / 'river_water_quality_report.pdf'
    doc = SimpleDocTemplate(str(pdf), pagesize=A4, rightMargin=54, leftMargin=54,
        topMargin=48, bottomMargin=55, title='Seasonal and spatial patterns in river water quality',
        author=author, subject='Oxygen and nitrate analysis across five river sections')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    if doc.page != 10:
        raise RuntimeError(f'Report must have exactly 10 pages; generated {doc.page}.')
    (out / 'report_source.txt').write_text('\n\n'.join(source) + '\n', encoding='utf-8')
    print(f'Built {pdf}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--author', default='Mohamad Ghoroobi')
    main(parser.parse_args().author)
