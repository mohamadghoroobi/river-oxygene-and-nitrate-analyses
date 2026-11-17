"""Build the editable LaTeX report and package the project for Overleaf."""
import argparse
from pathlib import Path
import shutil
import subprocess
import zipfile

from export_latex_tables import PROJECT, main as export_tables
from analyze import ROOT


def package_project():
    archive = ROOT / 'report/saubach_overleaf.zip'
    archive.parent.mkdir(exist_ok=True)
    allowed = {'.tex', '.png', '.md', '.json'}
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as output:
        for path in sorted(PROJECT.rglob('*')):
            if path.is_file() and path.suffix in allowed:
                output.write(path, path.relative_to(PROJECT).as_posix())
    print(f'Overleaf upload archive: {archive}')


def main(compiler=None, source_only=False):
    export_tables()
    if not source_only:
        build = ROOT / 'tmp/latex-build'
        build.mkdir(parents=True, exist_ok=True)
        executable = compiler or shutil.which('tectonic') or shutil.which('latexmk') or shutil.which('pdflatex')
        if executable is None:
            raise SystemExit('No local TeX compiler found. Upload overleaf/ to Overleaf, or use --source-only to create the upload ZIP.')
        executable = str(Path(executable).resolve())
        name = Path(executable).stem.lower()
        if 'tectonic' in name:
            command = [executable, '--keep-logs', '--outdir', str(build), str(PROJECT / 'main.tex')]
            subprocess.run(command, cwd=PROJECT, check=True)
        elif 'latexmk' in name:
            command = [executable, '-pdf', '-interaction=nonstopmode', '-halt-on-error', f'-outdir={build}', 'main.tex']
            subprocess.run(command, cwd=PROJECT, check=True)
        else:
            command = [executable, '-interaction=nonstopmode', '-halt-on-error', f'-output-directory={build}', 'main.tex']
            for _ in range(3):
                subprocess.run(command, cwd=PROJECT, check=True)
        from pypdf import PdfReader
        pdf = build / 'main.pdf'
        reader = PdfReader(pdf)
        if len(reader.pages) != 10:
            raise RuntimeError(f'Expected exactly 10 pages, found {len(reader.pages)}. Inspect {pdf}')
        expected = {1: 'Contents', 2: 'Introduction', 3: 'Data and problem definition',
                    4: 'Statistical methods', 6: 'Evaluation', 9: 'Summary and discussion'}
        for index, title in expected.items():
            if title not in reader.pages[index].extract_text():
                raise RuntimeError(f'Unexpected pagination: {title} is not on page {index+1}.')
        text = '\n\n'.join(page.extract_text() for page in reader.pages)
        if 'References' in text or 'Bibliography' in text:
            raise RuntimeError('The requested GitHub-only report must not contain a bibliography.')
        target = ROOT / 'report/river_water_quality_report.pdf'
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(pdf, target)
        (target.parent / 'report_source.txt').write_text(text + '\n', encoding='utf-8')
        print(f'Verified ten-page report: {target}')
    package_project()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--compiler', help='Path to tectonic, latexmk, or pdflatex')
    parser.add_argument('--source-only', action='store_true', help='Package sources without compiling a PDF')
    args = parser.parse_args()
    main(args.compiler, args.source_only)
