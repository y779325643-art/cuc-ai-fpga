# Public PC 2.1 declaration examples

These small, task-independent examples explain the registered PC rules before
any RTL is written. They contain public declarations only: no implementation,
reference algorithm, model response, stimulus or expected output. Passing them
means static admission, not functional correctness or qualified hardware.

Use the existing registered development public-context, target, capability and
design-proposal formats. The target fields are required format metadata; this
tutorial does not execute a compiler, simulator or synthesizer.

| Public context | Positive design | What it demonstrates |
| --- | --- | --- |
| [compute context](public-context-compute.json) | [one compute, two outputs](compute-multioutput.design.json) | All three logical tensor ports belong to one main relation |
| [FIFO context](public-context-fifo.json) | [local FIFO](fifo.design.json) | A local input-to-output, complete-beat, same-domain binding |
| Same FIFO context | [renamed child FIFO](fifo-renamed-child.design.json) | A structural wrapper and child may use different local port, tensor, state and domain-slot names |

Both contexts use [target-profile.json](target-profile.json) and
[capability-profile.json](capability-profile.json), with no public assets.
`design` files are the model-proposal root, without controller-owned bindings.
The controller selects and binds the public source bytes.

## Distinguish three namespaces

In the compute context, `sample` is a local logical port, `Vector` names its
tensor contract, and `sample_data` is a physical RTL ABI wire. Relations use
logical port names. This is valid:

```json
{"kind":"compute","fact":"Relation","inputs":["sample"],"outputs":["result_a","result_b"]}
```

Replacing `inputs` with `["Vector"]` or `["sample_data"]` still fits the JSON
identifier type, but must be rejected as an unknown tensor port. Correct JSON
shape does not establish a valid reference.

## Main relations cover each tensor port once

The valid multi-output relation above accounts for `sample`, `result_a` and
`result_b` together. A computation may consume one input and produce multiple
outputs; a relation is a declaration responsibility, not one arithmetic step.

These two relations are invalid together because they reuse `sample`:

```json
{
  "first":{"kind":"compute","fact":"Relation","inputs":["sample"],"outputs":["result_a"]},
  "second":{"kind":"compute","fact":"Relation","inputs":["sample"],"outputs":["result_b"]}
}
```

Omitting `result_b` from every relation is also invalid. Repeating a port
inside one relation is invalid as well. This rule does not forbid mathematical
input sharing; it requires a consistent declaration of that sharing.

## A tensor FIFO has a local input-to-output binding

In the local FIFO example, `queue` stores one complete `Packet` beat per entry.
The binding is:

```json
{"fact":"Relation","state":"queue","input":"ingress","output":"egress","capacity_unit":"beats"}
```

| Change to the local FIFO example | Required rejection |
| --- | --- |
| Set the binding's `input` to `egress` | `egress` is an output, not a local input |
| Remove `buffer_rules` but retain the tensor FIFO state | Every tensor FIFO still needs a binding |
| Replace the state element type with `{"kind":"uint","width":18}` | Equal bit width does not make it the same complete tensor beat |
| Bind the FIFO state to a different independently supplied clock domain | Storage and both streams must share the same bound domain |

The last counterexample requires a second public clock-domain declaration and
distinct physical clock/reset pins; changing an undeclared name would instead
be an invalid state reference. The tests exercise the two-domain rejection,
without claiming clock-domain crossing support.

This finite binding form does not directly describe an arbitrary internal
compute-result queue inside a module that has no matching input port. Choose
a supported module boundary or a coherent legal declaration; deleting a
binding alone does not discharge its FIFO responsibility. Neither the binding
nor a declared depth proves sufficient capacity or liveness.

The renamed-child example also illustrates that domain-slot spelling is local:
`local_clock` is bound to the parent's `clock_domain`. Names, module count,
FIFO depth and supported read mode are not a prescribed reference architecture.
The corresponding declaration checks leave behavior obligations unevaluated.

The focused test is `agent/tests/test_sr2fpga_pc21_public_rule_examples.py`.
It validates the actual registered formats, then invokes the real public-task
semantic checker for positive examples and each illustrated counterexample.
