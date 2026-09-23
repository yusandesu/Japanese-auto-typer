#!/usr/bin/env python3
"""Entry point.

- No args:           launches the GUI.
- --cli plus flags:  runs headless from a file or stdin (see cli.py).
"""
import sys


def main():
    if "--cli" in sys.argv:
        sys.argv.remove("--cli")
        from auto_typer.cli import main as cli_main

        cli_main()
    else:
        from auto_typer.gui import main as gui_main

        gui_main()


if __name__ == "__main__":
    main()
