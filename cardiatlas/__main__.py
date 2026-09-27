"""Allows `python -m cardiatlas ...` as an alternative to the installed `cardiatlas` console script."""
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
