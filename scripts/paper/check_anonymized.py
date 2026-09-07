"""Fail if the double-blind PDF still carries identifying strings."""
import subprocess
import sys

IDENTIFIERS = ("abuelsamen", "berkeley", "luai", "luaia", "github.com/luai")


def main(pdf: str) -> int:
    text = subprocess.run(["pdftotext", pdf, "-"], capture_output=True, text=True, check=True).stdout
    meta = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True, check=True).stdout
    haystack = (text + meta).lower()
    leaks = [w for w in IDENTIFIERS if w in haystack]
    if leaks:
        print(f"anonymization leak in {pdf}: {leaks}")
        return 1
    print(f"anonymized copy OK: {pdf}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "paper/main_anon.pdf"))
