# -*- coding: utf-8 -*-

"""
Main function for vagrant-debian program
"""

import sys
from .pid_tune import main

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
