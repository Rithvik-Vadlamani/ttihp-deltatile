"""Run Cocotb from a temporary path without spaces, retaining test evidence."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--venv", type=Path, required=True,
                    help="Virtual environment without spaces, containing test/requirements.txt")
args = parser.parse_args()
venv = args.venv.resolve()
if " " in str(venv):
    parser.error("Cocotb's Makefiles require a virtual environment path without spaces")
env = dict(os.environ, PATH=str(venv / "bin") + os.pathsep + os.environ["PATH"])
evidence = root / "artifacts" / "local-tests"
evidence.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix="deltatile-") as tmp:
    build = Path(tmp)
    for name in ("src", "test", "model", "host"):
        shutil.copytree(root / name, build / name,
                        ignore=shutil.ignore_patterns("sim_build", "__pycache__", "*.fst", "results.xml"))
    env["PWD"] = str(build / "test")
    result = subprocess.run(["make"], cwd=build / "test", env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout)
    (evidence / "simulation.log").write_text(result.stdout)
    for name in ("results.xml", "tb.fst"):
        if (build / "test" / name).exists():
            shutil.copy2(build / "test" / name, evidence / name)
    if result.returncode:
        raise SystemExit(result.returncode)
    if not (build / "test" / "results.xml").exists():
        raise SystemExit("Simulation produced no result XML")
    xml = ET.parse(build / "test" / "results.xml")
    if list(xml.iter("failure")) or list(xml.iter("error")) or not list(xml.iter("testcase")):
        raise SystemExit("Simulation did not produce a clean test result")
print(f"Verification evidence: {evidence}")
