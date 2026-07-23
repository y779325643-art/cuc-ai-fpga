# Deprecated LLM Compatibility Surface

`LLM/` is no longer an implementation project. Canonical ownership is:

- `agent/`: project generation, verification, repair, and trajectories.
- `training/`: dataset preparation, model training, merge, and serving assets.
- `contracts/`: versioned cross-project data contracts.

The Python and shell files retained here are one-cycle compatibility wrappers.
They print an exact canonical replacement and delegate without copying business
logic. New code must not import from or add implementation to `LLM/`.

## Canonical Installation

```powershell
python -m pip install -e "agent[dev]"
python -m pip install -e "training[dev]"
```

Heavy Training backends remain optional:

```powershell
python -m pip install -e "training[train]"
python -m pip install -e "training[serve]"
```

See [Agent documentation](../agent/README.md) and
[Training documentation](../training/README.md) for current commands.

Compatibility removal requires a later explicit approval after active usage
has been reviewed. No removal date is implied by this migration.
