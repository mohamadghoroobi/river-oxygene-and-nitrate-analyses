# Editing in Overleaf

1. In Overleaf, choose **New Project > Upload Project** and select `saubach_overleaf.zip` from the repository's `report` folder.
2. Open `main.tex` and use **pdfLaTeX** as the compiler. No shell escape or external bibliography program is needed.
3. Compile twice so that the automatic contents and cross-references have current page numbers.

Edit the applicant name and date in `main.tex`. Edit prose in `sections/`. Mathematical expressions and tables are LaTeX text, not screenshots. Figures are in `figures/`; tables are in `tables/`.

The delivered layout targets exactly 10 pages with a title page on page 1 and a separate contents page on page 2. Text uses 12-point Times-style fonts and 1.5 line spacing. Longer edits can change the page count; inspect the final PDF before submission.

The analysis uses the task's assumed river name, Saubach, and alpha = 0.075. Pointwise confidence intervals have 92.5% coverage and are not simultaneous intervals corresponding to the Holm decisions.

The bibliography and external literature citations were omitted at the author's request. The university guidelines require them, so this version does not satisfy that part of the assignment. The GitHub repository link supplies project materials; it does not replace book references for statistical methods.

Regenerate tables after changing the Python analysis by running `python src/export_latex_tables.py` from the repository root, then upload the changed tables and figures into Overleaf. Prose is never overwritten by that exporter.
