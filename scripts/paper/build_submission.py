"""Build and verify a local anonymous review package; never upload or submit it.

The main archive contains source and frozen evidence sufficient for `make paper`.
Optional data/checkpoint archives are staged separately because the workshop
has not published supplementary-file limits. Source files are not anonymized
in place. Third-party license and attribution notices are retained.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
IDENTIFIERS = re.compile(rb"abuelsamen|\bluai\b|luaia|/home/jetson3", re.IGNORECASE)
PREFIXES = ("src/", "scripts/", "tests/", "results/", "figures/paper/", "docs/")
PAPER_FILES = {"paper/main.tex", "paper/refs.bib", "paper/corl_2026.sty", "paper/corlabbrvnat.bst"}
EXCLUDED = {
    "scripts/paper/build_submission.py",
    "scripts/paper/check_anonymized.py",
    "docs/workshop_readiness.md",
    "docs/analysis_plans/README.md",
}
CHECKPOINTS = (
    "real50_base_v2",
    "real50_delta_v3_s0",
    "real50_base_v3_s1",
    "real50_delta_v3_s1",
    "real50_base_v3_s2",
    "real50_delta_v3_s2",
    "real50_ghist_v3_s0",
    "real50_ghist_v3_s1",
)


def run(command, log=None):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if log is not None:
        log.write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(
            f"{' '.join(map(str, command))} failed:\n{(result.stdout + result.stderr)[-5000:]}"
        )
    return result.stdout


def anonymous_text(raw):
    text = raw.decode("utf-8")
    replacements = (
        ("https://github.com/luaiabuelsamen/tracking-error-il", "anonymous-review-artifact"),
        ("luai_abuelsamen@berkeley.edu", "anonymous@example.invalid"),
        (r"luai\_abuelsamen@berkeley.edu", "anonymous@example.invalid"),
        ("University of California, Berkeley", "Affiliation withheld for review"),
        ("/home/jetson3/projects/clean_env/venv/bin/python", "python"),
        ("/home/jetson3", "/anonymous"),
    )
    for source, target in replacements:
        text = text.replace(source, target)
    text = re.sub(r"abuelsamen|luai|luaia", "anonymous", text, flags=re.IGNORECASE)
    return text.encode()


def scrub_tar(raw):
    """Sanitize the small tracked helper-source tarball without extracting it."""
    target = io.BytesIO()
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as source:
        with gzip.GzipFile(fileobj=target, mode="wb", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as output:
                for member in sorted(source.getmembers(), key=lambda m: m.name):
                    if not member.isfile():
                        continue
                    path = PurePosixPath(member.name)
                    if path.is_absolute() or ".." in path.parts:
                        raise ValueError(f"unsafe archive path: {member.name}")
                    content = anonymous_text(source.extractfile(member).read())
                    metadata = tarfile.TarInfo(member.name)
                    metadata.size = len(content)
                    metadata.mode = member.mode
                    output.addfile(metadata, io.BytesIO(content))
    return target.getvalue()


def sanitize(name, raw):
    if name.endswith(".tar.gz"):
        return scrub_tar(raw)
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw
    return anonymous_text(raw)


def verify_bytes(name, raw):
    if IDENTIFIERS.search(raw):
        raise ValueError(f"author identifier in review artifact: {name}")
    if name.endswith(".npz"):
        with zipfile.ZipFile(io.BytesIO(raw)) as nested:
            for member in nested.namelist():
                verify_bytes(name + "/" + member, nested.read(member))
    elif name.endswith(".tar.gz"):
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as nested:
            for member in nested.getmembers():
                if member.isfile():
                    verify_bytes(name + "/" + member.name, nested.extractfile(member).read())


def write_archive(path, entries):
    manifest = []
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        for name, raw, executable in sorted(entries, key=lambda entry: entry[0]):
            verify_bytes(name, raw)
            item = zipfile.ZipInfo("tracking-error-review/" + name, (1980, 1, 1, 0, 0, 0))
            item.create_system = 3
            item.external_attr = (0o100755 if executable else 0o100644) << 16
            item.compress_type = (
                zipfile.ZIP_STORED if name.endswith(".mp4") else zipfile.ZIP_DEFLATED
            )
            archive.writestr(item, raw)
            manifest.append(dict(path=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
        item = zipfile.ZipInfo(
            f"tracking-error-review/CONTENTS-{path.stem}.json", (1980, 1, 1, 0, 0, 0)
        )
        item.create_system = 3
        item.external_attr = 0o100644 << 16
        archive.writestr(item, json.dumps(manifest, indent=2) + "\n")
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"archive CRC error: {bad}")
    return dict(
        file=path.name, bytes=path.stat().st_size, sha256=sha256_file(path), files=len(manifest)
    )


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def code_entries():
    tracked = run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]).split(
        "\0"
    )
    for name in sorted(set(tracked) - EXCLUDED - {""}):
        selected = (
            name.startswith(PREFIXES)
            or name in PAPER_FILES
            or name.startswith("paper/generated/")
            or name in {"LICENSE", "pyproject.toml", "requirements-paper.txt"}
        )
        if not selected or name.endswith(".mp4"):
            continue
        path = ROOT / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing or linked artifact source: {name}")
        raw = sanitize(name, path.read_bytes())
        if name == "paper/main.tex":
            raw = b"\\def\\ANON{1}\n" + raw
        yield name, raw, bool(path.stat().st_mode & 0o111)
    yield "README.md", (ROOT / "paper/review_artifact.md").read_bytes(), False
    yield (
        "NOTICE",
        b"Tracking error as an observation for behavior cloning on low-cost arms\nCopyright 2026 Anonymous authors (identity withheld for review).\nThird-party notices are retained with their respective source files.\n",
        False,
    )
    yield (
        "Makefile",
        b"PYTHON ?= python\n.PHONY: paper test\npaper:\n\t$(PYTHON) scripts/paper/build_paper_evidence.py\n\t$(PYTHON) scripts/paper/supplementary_analysis.py\n\tSOURCE_DATE_EPOCH=0 FORCE_SOURCE_DATE=1 latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex\n\t$(PYTHON) scripts/paper/check_paper_numbers.py\ntest:\n\tPYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(PYTHON) -m pytest tests/ -q\n",
        False,
    )


def research_entries(kind):
    if kind == "demonstrations":
        roots = [ROOT / "data/real/pickplace_real_v0" / sub for sub in ("data", "meta", "videos")]
    else:
        roots = [ROOT / "checkpoints" / name for name in CHECKPOINTS]
    for root in roots:
        if not root.is_dir():
            raise ValueError(f"required research artifact missing: {root.relative_to(ROOT)}")
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.name.startswith(".") or "__pycache__" in path.parts:
                continue
            if path.is_symlink():
                raise ValueError(f"linked research artifact: {path}")
            name = path.relative_to(ROOT).as_posix()
            yield name, sanitize(name, path.read_bytes()), False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "dist/workshop")
    parser.add_argument(
        "--research-assets",
        action="store_true",
        help="also stage the local demonstrations and eight checkpoints separately",
    )
    args = parser.parse_args()
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/tracking-error-matplotlib")
    out = args.out.resolve()
    if out == ROOT or ROOT.is_relative_to(out):
        parser.error("output must be a dedicated artifact directory")
    out.mkdir(parents=True, exist_ok=True)
    run(["make", "paper-anon", f"PYTHON={sys.executable}"], out / "build.log")
    anonymous_log = (ROOT / "paper/main_anon.log").read_text()
    if re.search(r"undefined|Overfull|^!", anonymous_log, re.MULTILINE):
        raise ValueError("anonymous LaTeX references/layout need attention")
    run([sys.executable, "scripts/paper/split_submission.py"], out / "split.log")
    outputs = []
    for source, name in (
        ("main_anon_paper.pdf", "paper.pdf"),
        ("main_anon_supplement.pdf", "supplement.pdf"),
    ):
        pdf = ROOT / "paper" / source
        run([sys.executable, "scripts/paper/check_anonymized.py", str(pdf)])
        (out / name).write_bytes(pdf.read_bytes())
        outputs.append(dict(file=name, bytes=pdf.stat().st_size, sha256=sha256_file(pdf)))
    outputs.append(write_archive(out / "review-artifact.zip", code_entries()))
    if args.research_assets:
        for kind in ("demonstrations", "checkpoints"):
            outputs.append(write_archive(out / f"{kind}.zip", research_entries(kind)))
    report = dict(
        outputs=outputs,
        uploaded=False,
        checks=[
            "main text <= 4 pages",
            "paper-number audit",
            "references and layout in both build modes",
            "anonymous PDF text and metadata",
            "artifact identifiers, including nested NPZ and helper tarball contents",
            "ZIP CRC and SHA-256",
        ],
        limitations=[
            "Supplementary upload fields and file limits require author verification.",
            "Media pixels are not anonymized by the text/metadata checks.",
            "Hardware history control remains incomplete; see manuscript disclosures.",
        ],
    )
    (out / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
