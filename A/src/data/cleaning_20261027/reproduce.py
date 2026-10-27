"""Reproduce the fixed-version audit and twelve authorized formula corrections."""
import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from context import HERE, check_paths, file_hash, validate_input

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Read-only official attachment directory")
    parser.add_argument("--run-dir", required=True, type=Path, help="New diagnostic directory")
    parser.add_argument("--output-dir", required=True, type=Path, help="New directory for exactly three deliverables")
    parser.add_argument("--node", required=True, type=Path, help="Bundled Node executable")
    parser.add_argument("--node-modules", required=True, type=Path, help="Bundled node_modules containing @oai/artifact-tool")
    parser.add_argument("--render", action="store_true", help="Also render the original and saved result for visual review")
    args = parser.parse_args()
    if sys.flags.optimize:
        parser.error("Python -O is unsupported; verification assertions must be enabled")
    raw, run, out = (p.resolve() for p in (args.input, args.run_dir, args.output_dir))
    check_paths(raw, run, out)
    if run.exists() or out.exists():
        parser.error("run-dir and output-dir must both be new; existing artifacts are never overwritten")
    if not run.parent.is_dir() or not out.parent.is_dir():
        parser.error("Create the parent run/output folders first")
    input_hashes = validate_input(raw)
    node, modules = args.node.resolve(), args.node_modules.resolve()
    package = modules / "@oai" / "artifact-tool" / "package.json"
    if not node.is_file() or not package.is_file():
        parser.error("A bundled Node executable and @oai/artifact-tool are required; see README")
    versions = {name: importlib.metadata.version(name) for name in ("numpy", "pandas", "openpyxl")}
    versions.update(python=platform.python_version(),
                    node=subprocess.check_output([str(node), "--version"], text=True).strip(),
                    artifact_tool=json.loads(package.read_text(encoding="utf-8"))["version"])
    run.mkdir()
    config = {"input": raw.as_posix(), "run": run.as_posix(), "output": out.as_posix(),
              "node_modules": modules.as_posix()}
    context = run / "context.json"
    context.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    env = dict(os.environ, MATHORCUP_CONTEXT=str(context), PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    sources = {p.name: file_hash(p) for p in sorted(HERE.iterdir()) if p.suffix in {".py", ".mjs", ".json"}}
    git = subprocess.run(["git", "-C", str(HERE.parents[3]), "rev-parse", "HEAD"], capture_output=True, text=True)
    status = subprocess.run(["git", "-C", str(HERE.parents[3]), "status", "--porcelain"], capture_output=True, text=True)
    evidence = {"versions": versions, "input_hashes": input_hashes, "source_sha256": sources,
                "git_head": git.stdout.strip() if git.returncode == 0 else None,
                "git_dirty": bool(status.stdout.strip()) if status.returncode == 0 else None,
                "stages": [], "complete": False}
    evidence_path = run / "run_manifest.json"
    def record():
        evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    def stage(name, command):
        with (run / (name + ".log")).open("w", encoding="utf-8") as log:
            result = subprocess.run(command, cwd=HERE.parents[3], env=env, stdout=log, stderr=subprocess.STDOUT)
        evidence["stages"].append({"name": name, "exit_code": result.returncode})
        record()
        if result.returncode:
            raise RuntimeError(f"{name} failed; inspect {run / (name + '.log')}")
        print(name + ": passed", flush=True)
    record()
    if os.name == "nt":
        command = ("$taskConfig = Get-Content -LiteralPath $env:MATHORCUP_CONTEXT -Raw | ConvertFrom-Json; "
                   "New-Item -ItemType Junction -Path (Join-Path $taskConfig.run 'node_modules') "
                   "-Target $taskConfig.node_modules -ErrorAction Stop | Out-Null")
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", command], env=env, check=True)
    else:
        (run / "node_modules").symlink_to(modules, target_is_directory=True)
    shutil.copyfile(HERE / "build.mjs", run / "build.mjs")
    stage("profile", [sys.executable, "-B", str(HERE / "profile.py")])
    stage("inventory_report", [sys.executable, "-B", str(HERE / "report.py")])
    if args.render:
        stage("preview", [str(node), str(run / "build.mjs"), "preview"])
    stage("build", [str(node), str(run / "build.mjs"), "build"])
    stage("package", [sys.executable, "-B", str(HERE / "package.py")])
    stage("write_log", [sys.executable, "-B", str(HERE / "write_log.py")])
    if args.render:
        stage("final_preview", [str(node), str(run / "build.mjs"), "final"])
    if validate_input(raw) != input_hashes:
        raise RuntimeError("Source hashes changed")
    if {p.name for p in out.iterdir()} != {"clean.csv", "cleaning_log.md", "清洗前后对照表.xlsx"}:
        raise RuntimeError("Expected exactly three deliverables")
    evidence["output_sha256"] = {p.name: file_hash(p) for p in out.iterdir()}
    evidence["complete"] = True
    record()
    print(json.dumps({"complete": True, "output": str(out), "source_fields": 1599,
                      "numeric_changes": 0, "formula_changes": 12}, ensure_ascii=False))

if __name__ == "__main__":
    main()
