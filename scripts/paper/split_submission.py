"""Split the anonymized PDF into the paper (main text + references) and a supplement.

The workshop limit is four pages excluding references and says nothing about
appendices, so the appendices are uploaded separately. The cut is the first
page whose text starts the appendix heading.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

APPENDIX_MARKER = "Hardware protocol and complete evaluation record"


def page_texts(pdf: Path) -> list[str]:
    out = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    return out.split("\f")[:-1]


def main(pdf: str) -> int:
    src = Path(pdf)
    pages = page_texts(src)
    starts = [i for i, t in enumerate(pages, 1) if APPENDIX_MARKER in t and "Appendix" not in t.split(APPENDIX_MARKER)[0][-40:]]
    if not starts:
        print(f"appendix heading not found in {src}")
        return 1
    cut = starts[0]
    paper = src.with_name(src.stem + "_paper.pdf")
    supp = src.with_name(src.stem + "_supplement.pdf")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdfseparate", str(src), f"{tmp}/p-%d.pdf"], check=True, stderr=subprocess.DEVNULL)
        subprocess.run(["pdfunite", *[f"{tmp}/p-{i}.pdf" for i in range(1, cut)], str(paper)], check=True)
        subprocess.run(["pdfunite", *[f"{tmp}/p-{i}.pdf" for i in range(cut, len(pages) + 1)], str(supp)], check=True)
    print(f"{paper}: pages 1-{cut - 1} (main text ends on page {[i for i, t in enumerate(pages, 1) if 'References' in t][0] - 1})")
    print(f"{supp}: pages {cut}-{len(pages)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "paper/main_anon.pdf"))
