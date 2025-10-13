import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load the app and alias package via WSGI loader
import wsgi  # noqa: F401

import com_hammed.migrate_to_supabase as mig  # type: ignore[attr-defined]

if __name__ == "__main__":
    raise SystemExit(mig.main())
