#!/bin/bash
# Regenerate the paper PDF from markdown via pandoc + xelatex.
# Usage: ./make_pdf.sh
set -e
export PATH="/Library/TeX/texbin:$PATH"
PANDOC="$HOME/bin/pandoc-3.1.11-x86_64/bin/pandoc"
MD="QEC_Paper_Exact_Scaling_Geometric_CSS_RM_EN_260807.md"
cat > /tmp/qec_header.tex <<'TEX'
\usepackage{newunicodechar}
\newunicodechar{θ}{\(\theta\)}
\newunicodechar{∎}{\(\blacksquare\)}
\newunicodechar{✓}{\(\checkmark\)}
TEX
"$PANDOC" "$MD" -o "${MD%.md}.pdf" \
  --pdf-engine=xelatex \
  --lua-filter=refs_hanging.lua \
  -H /tmp/qec_header.tex \
  -V geometry:margin=2.5cm \
  -V linkcolor=blue
echo "PDF regenerated: ${MD%.md}.pdf ($(du -h ${MD%.md}.pdf | cut -f1))"
