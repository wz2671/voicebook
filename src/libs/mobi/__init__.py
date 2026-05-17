import os

os.environ["LOGURU_AUTOINIT"] = "False"
from .extract import extract as extract  # explicit re-export

__version__ = "0.4.1"
