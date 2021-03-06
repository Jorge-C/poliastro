"""
=========
poliastro
=========

Utilities and Python wrappers for Orbital Mechanics

"""

from __future__ import absolute_import

__version__ = '0.2.0-dev'

from . import angles
from . import iod
from . import twobody
from .logging import logger

def test():
    import os.path
    import pytest
    pytest.main(os.path.dirname(os.path.abspath(__file__)))
