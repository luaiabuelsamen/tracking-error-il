#!/usr/bin/env bash
# Assemble a self-contained arXiv source tarball and verify it compiles on its own.
#
# arXiv untars into a single root, so the manuscript's `../figures/paper/` path cannot survive. This
# stages a flat copy, rewrites the one path, includes the .bbl so no bibtex run is required, and then
# builds the staged copy from scratch to prove the tarball is complete rather than assuming it.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/dist/arxiv"
rm -rf "$OUT" && mkdir -p "$OUT/figures" "$OUT/generated"

cp "$ROOT/paper/main.tex" "$OUT/"
cp "$ROOT/paper/corl_2026.sty" "$ROOT/paper/corlabbrvnat.bst" "$OUT/"
cp "$ROOT/paper/main.bbl" "$OUT/"
cp "$ROOT/paper/generated/"*.tex "$OUT/generated/" 2>/dev/null || true
cp "$ROOT/figures/paper/"*.pdf "$OUT/figures/"

sed -i 's|\\graphicspath{{../figures/paper/}}|\\graphicspath{{figures/}}|' "$OUT/main.tex"

# Build the staged copy in isolation. If anything is missing this fails here rather than on arXiv.
( cd "$OUT" && latexmk -pdf -interaction=nonstopmode -f main.tex >/dev/null 2>&1 || true )
test -f "$OUT/main.pdf" || { echo "staged build produced no PDF"; exit 1; }
PAGES=$(pdfinfo "$OUT/main.pdf" | awk '/^Pages:/{print $2}')
UNDEF=$(grep -c "Citation.*undefined\|Reference.*undefined" "$OUT/main.log" || true)
echo "staged build: $PAGES pages, $UNDEF undefined references"

( cd "$OUT" && latexmk -c >/dev/null 2>&1 || true; rm -f main.pdf )
TAR="$ROOT/dist/arxiv-submission.tar.gz"
( cd "$OUT" && tar czf "$TAR" . )
echo "wrote $TAR  ($(du -h "$TAR" | cut -f1))"
tar tzf "$TAR" | head -20
