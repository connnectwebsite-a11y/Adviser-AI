
import sys
import importlib.util
from pathlib import Path


def load_module(name, path):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Required module missing: {path}"
        )

    sys.modules.pop(name, None)

    spec = importlib.util.spec_from_file_location(
        name,
        path
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not load module: {name}"
        )

    module = importlib.util.module_from_spec(spec)

    sys.modules[name] = module

    spec.loader.exec_module(module)

    return module


def recover_large_book_system(
    project_dir="/content/AdviserAI-Portfolio"
):
    project_dir = Path(project_dir)

    book_engine = load_module(
        "book_engine",
        project_dir / "book_engine.py"
    )

    mind = load_module(
        "mind",
        project_dir / "mind.py"
    )

    processor = load_module(
        "large_book_processor",
        project_dir / "large_book_processor.py"
    )

    batch_runner = load_module(
        "batch_runner",
        project_dir / "batch_runner.py"
    )

    sampled_processor = load_module(
        "sampled_book_processor",
        project_dir / "sampled_book_processor.py"
    )

    sampled_batch_runner = load_module(
        "sampled_batch_runner",
        project_dir / "sampled_batch_runner.py"
    )

    return {
        "book_engine": book_engine,
        "mind": mind,
        "processor": processor,
        "batch_runner": batch_runner,
        "sampled_processor": sampled_processor,
        "sampled_batch_runner": sampled_batch_runner,
    }
