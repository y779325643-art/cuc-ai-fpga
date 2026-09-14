# M3 IEEE/ACM Figure Style QA

Date: 2026-09-01

Status: style revision QA passed; user final approval pending

## Applied style contract

- Exact double-column width: 182 mm.
- Figure titles and explanatory subtitles removed from the image; captions remain
  outside the graphic.
- Arial/Helvetica-compatible sans-serif stack with editable SVG text and embedded
  TrueType PDF text.
- Flat, compact engineering block-diagram layout with uniform border weights.
- Restrained blue/grey palette; public and hidden zones remain directly labelled.
- Solid borders identify development implementation; dashed orange borders identify
  incomplete official authority, so meaning does not depend on colour alone.
- Vector SVG/PDF plus 300 dpi PNG and 600 dpi TIFF.
- ACM-style accessibility descriptions added for all three figures.

## Official guidance used

- IEEE Author Center: vector graphics preferred; one/two-column widths; >300 dpi
  colour/grayscale and >600 dpi line art.
- IEEE Author Center: combine colour with line style/shape and preserve greyscale
  interpretability.
- IEEE file guidance: PDF/PNG/TIFF accepted; consistent embedded fonts.
- ACM publication guidance: prefer vector graphics, place captions after figures,
  use exact intended size and provide meaningful figure descriptions/alt text.

## QA result

| Check | Result |
|---|---|
| Static Python preflight | 14 pass, 0 warn, 0 fail |
| Final width | 182 mm |
| Visual QA | pass after three revision cycles |
| Text overlap/clipping | none detected |
| SVG editable text | present |
| Colour-only encoding | none; labels and line styles carry meaning |
| Unsupported results | none |
| Official/development boundary | retained |

This record does not mark the figures final or insert them into the manuscript.
