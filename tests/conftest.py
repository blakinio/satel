import sys
from pathlib import Path

import pytest

pytest_plugins = ("pytest_homeassistant_custom_component",)

# Ensure custom_components is on the path
sys.path.append(str(Path(__file__).resolve().parents[1]))
