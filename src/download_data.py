"""Download the original university data without silently replacing a local copy."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
URL = ('https://statistik.tu-dortmund.de/storages/statistik/r/Downloads/'
       'Studium/Studiengaenge-Infos/Data_Science/waterquality.csv')
TARGET = ROOT / 'data/raw/waterquality.csv'


def main():
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if TARGET.exists():
        print(f'Keeping existing raw data: {TARGET}')
        return
    with urlopen(URL, timeout=60) as response:
        content = response.read()
    if not content.startswith(b'"ID";"river_section";"saison";'):
        raise ValueError('Unexpected response: expected the university CSV header.')
    temporary = TARGET.with_suffix('.download')
    temporary.write_bytes(content)
    temporary.replace(TARGET)
    metadata = {
        'source_url': URL,
        'downloaded_at_utc': datetime.now(timezone.utc).isoformat(),
        'sha256': hashlib.sha256(content).hexdigest(),
        'size_bytes': len(content),
    }
    TARGET.with_suffix('.metadata.json').write_text(
        json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    print(f'Downloaded {TARGET}')


if __name__ == '__main__':
    main()
