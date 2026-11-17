# Review against the university requirements

Reviewed 17 November 2026 against the local application brief and the writing guidelines supplied by the author.

| Requirement | Revised report / project |
|---|---|
| Exactly 10 PDF pages | Enforced by the report builder; final compilation must pass before delivery. |
| River name Saubach and alpha = 0.075 | Used throughout the revised report and inference. The river name is stated as the task's assumption. |
| Spring-autumn comparison for oxygen and nitrate | Two explicit mean contrasts with estimates, pointwise 92.5% intervals, raw p-values, and Holm-adjusted p-values. |
| Differences between five sections and identification of pairs | Two omnibus tests and all 20 section-pair tests, averaged equally across seasons. |
| Four seasons, 180 observations per section, 45 per cell | Confirmed by schema and group-size checks; 900 rows retained. |
| Detailed descriptive analysis | Means, SDs, medians, IQRs, quartiles, ranges, group summaries, and two labeled graphics. Full cell summaries are exported in the project. |
| Justified tests and mathematical methods | Full factorial model, mean contrasts, HC3 covariance, Wald tests, Holm correction, and assumptions are defined and connected to the research questions. |
| Title page with author, title and date | Page 1. |
| Contents on a separate second page | Automatic table of contents on page 2; includes subsections. |
| Introduction with motivation, aims, approach and main result | Page 3. |
| Detailed problem/data description | Page 4, including source, variables, missingness and unobserved sampling protocol. |
| Methods | Pages 5-6. |
| Evaluation with descriptive and inferential subsections | Pages 7-9. |
| Summary and discussion readable independently | Page 10; includes all question answers, limitations and further work. |
| Numbered, captioned and cited figures/tables | Automatic LaTeX numbering, labels and cross-references. |
| Consistent font, readable margins and 1.5 spacing | 12-point Times-style body text, 22 mm side margins, 1.5 line spacing; compact single-spaced tables and captions. |
| No unused methods or unrelated narrative | Methods are limited to the analyses and diagnostics actually run. |
| Bibliography, book citations and software citations | **Not met:** omitted at the author's explicit request. The report links only to the GitHub project. GitHub does not replace method references required by the guidelines. |
| Appendix optional, discouraged | None. |

## Corrections from the previous version

The previous report used alpha = 0.05, did not use the assumed river name, and had a manually written contents list without subsections. The revised version changes alpha to 0.075, uses Saubach as the specified assumption, and generates contents automatically on its own page. Alpha changes add A1-A2 and A1-A3 to the significant oxygen pairs; seasonal decisions do not change. Pointwise intervals are now 92.5%, rather than 95%, and are explicitly distinguished from globally adjusted tests.

The earlier literature entries were checked against author or publisher records; they were not fabricated. Removing them is an author preference and creates the stated exception to the university's requirements. This review does not certify the GitHub-only version as fully compliant with those requirements.
