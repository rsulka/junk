"""Entry point dla uruchamiania jako moduł: python -m dsmonitor."""

import sys

from dsmonitor.cli import main

if __name__ == "__main__":
    sys.exit(main())
