"""PyInstaller entry script (kept outside the package so its folder never shadows package modules)."""
from caldera.app import main

raise SystemExit(main())
