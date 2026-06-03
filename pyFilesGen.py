import os
import sys
from pathlib import Path
import subprocess

result_dir = Path(os.environ.get("PYSF_RESULT_DIR", "output/result"))
pysf_dir = result_dir / "pysf"
sys.path.insert(0, str(pysf_dir.resolve()))

if sys.platform == "win32":
    import pysf as sf
elif sys.platform == "darwin":
    import pysf as sf
else:
    print("Unsupported operating system")
    sys.exit(1)


def collect_pyi_paths(target_dir_name):
    cwd = Path.cwd()
    target_path = cwd / target_dir_name

    if not target_path.exists():
        raise FileNotFoundError(f"Directory not found: {target_path}")

    pyi_files = []

    for file_path in target_path.rglob("*.pyi"):
        if file_path.is_file():
            relative_path = file_path.relative_to(cwd)
            pyi_files.append(str(relative_path))

    return pyi_files


def replace_pyi(pyi_path):
    with open(pyi_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
    with open(pyi_path, "w", encoding="utf-8") as file:
        for line in lines:
            line = line.replace("pysf.", "")
            file.write(line)


if __name__ == "__main__":
    attrs = [attr for attr in dir(sf) if not (attr.startswith("__") and attr.endswith("__"))]
    with open(pysf_dir / "__init__.py", "w") as file:
        file.write("from . import pysf as _pysf\n")
        file.write("from .pysf import (\n")
        for attr in attrs:
            file.write(f"   {attr},\n")
        file.write(")\n")
        file.write("__doc__ = _pysf.__doc__\n")
    print("Successfully generated __init__.py")

    subprocess.run([sys.executable, "-m", "pybind11_stubgen", "--output-dir=.", "pysf"], cwd=pysf_dir)
    for path in collect_pyi_paths(pysf_dir / "pysf"):
        replace_pyi(path)
    print("Successfully generated pyi")
