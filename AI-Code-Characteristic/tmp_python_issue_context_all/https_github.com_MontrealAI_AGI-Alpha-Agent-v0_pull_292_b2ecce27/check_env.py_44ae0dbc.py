import importlib.util
import sys

REQUIRED = [
    'pytest',
    'prometheus_client',
]

def main() -> int:
    missing = []
    for pkg in REQUIRED:
        if importlib.util.find_spec(pkg) is None:
            missing.append(pkg)
    if missing:
        print('Missing packages:', ', '.join(missing))
        print('Install with: pip install -r requirements.txt')
        return 1
    print('Environment OK')
    return 0

if __name__ == '__main__':
    sys.exit(main())
