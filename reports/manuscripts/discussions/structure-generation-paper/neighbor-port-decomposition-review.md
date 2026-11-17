# Port-level decomposition: additional primary-source check

21 October 2026. [QiMeng-VPID, IJCAI 2026, pp. 410–418](https://www.ijcai.org/proceedings/2026/0047.pdf), DOI 10.24963/ijcai.2026/47. Read the official nine-page paper, especially §§3–4.3 and §5.3; no framework execution.

The method already makes decomposition verification-grounded. Section 4.1 derives verified and remaining output-port sets from generated candidates, aligns fan-in cones with AST statements, and extracts self-contained fragments. Section 4.2 retains verified behavior in a growing skeleton; compilation and waveform gates constrain generation and merging. The waveform gate compares previously verified outputs under common random stimuli and reset perturbations. Section 4.3 turns failure traces into port-specific guidance. Its reported pass@1 includes iterative generation; it is not this project's uncorrected first output.

Thus “port boundaries plus verification-guided decomposition” is existing work. The inspected procedure does not describe selecting new arithmetic interfaces at saturation points before RTL exists, or optimizing complete-domain proof cost. That observation establishes a comparison question, not novelty. A bounded web search did not locate an author implementation; the connector rejected the attempted global GitHub-search endpoint. No author-code inspection is claimed.

Any proposed pre-generation decomposition must beat ordinary semantic-AST outlining and compositional verification on identical inputs. Fewer interface bits alone do not demonstrate easier proofs. No model experiment or study metric was changed here.
