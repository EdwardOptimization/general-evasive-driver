# C5-prime manuscript

`main.tex` is the canonical manuscript source. Generated LaTeX files and
`main.pdf` are intentionally ignored.

## Build

The preferred build uses Tectonic or another XeTeX-compatible engine and the
open-source `Noto Serif CJK SC` font for the Chinese abstract:

```bash
tectonic main.tex --keep-logs --keep-intermediates
```

The source retains a pdfTeX/CJK fallback, but release PDFs should be checked
visually because a successful LaTeX exit code does not guarantee that CJK
glyphs were embedded. The verified local build rendered Chinese text, resolved
references, and had no overfull or underfull boxes.

The former `fig4_tworegime` asset is deliberately removed. It visualized an
invalid post-slip comparison that used the wrong normalized pedal semantics and
labeled uniform service braking as ESC.
