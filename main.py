from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


backend_path = Path(__file__).parent / "backend-mangga"
sys.path.insert(0, str(backend_path))
backend_spec = spec_from_file_location("backend_main", backend_path / "main.py")
if backend_spec is None or backend_spec.loader is None:
    raise RuntimeError("Cannot load backend application entrypoint")
backend_module = module_from_spec(backend_spec)
backend_spec.loader.exec_module(backend_module)
app = backend_module.app

__all__ = ["app"]