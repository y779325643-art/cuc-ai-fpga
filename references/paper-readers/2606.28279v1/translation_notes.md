# Translation and extraction notes

## Mode

- Source format: selectable-text PDF (`pdf-text`).
- Paper type: methods/system preprint.
- The user asked to learn from the paper and focus on differences with SR2FPGA. The reader therefore covers every substantive section and all figures/tables, with anchored key source passages and Chinese interpretation; it is not a sentence-by-sentence publication translation.
- References are indexed as one bibliography block rather than translated item by item.

## Extraction quality

- All 12 pages have a selectable text layer.
- The paper uses a mostly single-column layout; extracted line-break hyphenation was normalized in the reader.
- Mathematical formulas were manually normalized because PDF extraction split some symbols and subscripts.
- Figure/table crops were visually inspected against rendered pages.
- Table 2 and Table 3 crops exclude their captions; captions are represented as separate bilingual Markdown text.

## Terminology decisions

- `project pack` is retained in English because it is a named HORIZON control-plane object, not a generic FPGA project archive.
- `harness` is retained where it denotes the combined executable task/evaluator environment; `benchmark harness` is not silently equated with a hidden oracle.
- `iteration 0` is never translated as `Pass@1` because the authors explicitly reject that interpretation.
- `repository evolution` and `project generation` are kept distinct. The former describes HORIZON's search substrate; the latter is SR2FPGA's requirement-to-artifact objective.
- `over-solving` is described as evaluator-specific over-adaptation; it overlaps with, but is not identical to, malicious reward hacking.

## Important source caveats

- The reported ChipBench 100% includes one task treated as resolved because the authors attribute the miss to a specification-harness defect.
- Token consumption excludes normalized model pricing, parallelism and infrastructure cost; approximately 91% is cached input.
- CID 014 best coverage is averaged over 60 parsed logs because seven designs lack parsed coverage rows.
- QoR appears in the general reward definition but is not reported in this paper's experiments.
- The paper does not train or update an RL/agent policy.
