# Reference Material

`references/` contains source material used to understand the domain and frame
the research. It is not a runtime-contract, current-status, or experiment-result
namespace.

## Literature Readers

- [HORIZON / arXiv:2606.28279v1 reader packet](paper-readers/2606.28279v1/paper.md)
  contains the source-grounded reader, extraction/translation notes, provenance
  map, figures/tables, and a dated SR2FPGA positioning memo. The memo informs
  the research argument, but the current experiment protocol is the
  [Paper-1 research plan v2.2](../docs/specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md).
  Its section 13.1 fixes the comparison granularity against HORIZON, CPPL, and
  HINT: those works already cover project packs, JSON circuit IR, and
  pre-RTL intent checking, so none of those capabilities is claimed here as
  novelty on its own. A conceptual comparison is not an executable baseline.

## Hardware References

- [`AC820开发板/`](AC820开发板/) contains board manuals, schematics,
  tutorials, and the pin/resource table. These are vendor/reference inputs, not
  evidence that a design passed L5 board validation.

## Background Material

- [`AI_Hardware_Design_Evolution.md`](AI_Hardware_Design_Evolution.md) and its
  supporting images under `assets/` provide background notes.
- [`AI 写 RTL，最先淘汰的不是工程师，而是“拍脑袋写代码”.pdf`](AI%20写%20RTL，最先淘汰的不是工程师，而是“拍脑袋写代码”.pdf)
  is retained as background reading, not as a scientific evidence source.

For current engineering facts, use [`docs/current-status.md`](../docs/current-status.md).
For documentation authority and navigation, use [`docs/README.md`](../docs/README.md).
