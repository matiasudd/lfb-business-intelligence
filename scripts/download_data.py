"""Download original LFB evidence and retain immutable checksums."""
from pathlib import Path
from urllib.request import urlopen, Request
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'mobilisations_2021_2024.csv': 'https://data.london.gov.uk/download/24r65/3ff29fb5-3935-41b2-89f1-38571059237e/LFB%20Mobilisation%20data%20from%202021%20-%202024.csv',
    'mobilisations_metadata.xlsx': 'https://data.london.gov.uk/download/24r65/0eaaa520-1f54-4c33-9008-f394b78206be/Mobilisations%20Metadata.xlsx',
}

def main():
    manifest_path = ROOT / 'data/source_manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for name, url in SOURCES.items():
        destination = ROOT / 'data/raw' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            temporary = destination.with_suffix(destination.suffix + '.tmp')
            with urlopen(Request(url, headers={'User-Agent': 'LFB-C1-academic-project'}), timeout=120) as response, temporary.open('wb') as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            temporary.replace(destination)
            retrieved = datetime.now(timezone.utc).isoformat()
        else:
            retrieved = manifest.get(name, {}).get('retrieved_utc', 'unknown: existing local file')
        with destination.open('rb') as handle:
            digest = hashlib.file_digest(handle, 'sha256').hexdigest()
        previous = manifest.get(name, {}).get('sha256')
        if previous and previous != digest:
            raise ValueError(f'Original file changed: {name}')
        manifest[name] = {'url': url, 'retrieved_utc': retrieved, 'bytes': destination.stat().st_size, 'sha256': digest,
                          'publisher': 'London Fire Brigade / London Datastore', 'license_as_listed': 'Open Government Licence v2'}
        print(name, destination.stat().st_size, digest, flush=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
