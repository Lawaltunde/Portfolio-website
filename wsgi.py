import sys
from pathlib import Path
import importlib.util

# Project root and the unconventional package directory (with a dot in the name)
ROOT = Path(__file__).resolve().parent
PKG_DIR = ROOT / "com.hammed"

# Ensure ROOT is on sys.path so submodules can be found under PKG_DIR
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load the package as a proper package named 'com_hammed' so relative imports work
spec = importlib.util.spec_from_file_location(
    "com_hammed", PKG_DIR / "__init__.py", submodule_search_locations=[str(PKG_DIR)]
)
module = importlib.util.module_from_spec(spec)
sys.modules["com_hammed"] = module
assert spec.loader is not None
spec.loader.exec_module(module)  # type: ignore[attr-defined]

# Create the Flask app via the factory inside the loaded package
app = module.create_app()
