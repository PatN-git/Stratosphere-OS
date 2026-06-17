# Google Stitch vs StratosphereOS DESIGN.md Schema Conflict

## The Issue
There is a fundamental difference in the `DESIGN.md` schema expected by the Google Stitch engine and the semantic, OKLCH-based schema officially documented in StratosphereOS.

### StratosphereOS Standard (Current `src/memory-templates/DESIGN.md`)
- **Colors**: OKLCH format for perceptual uniformity (`oklch(...)`).
- **Typography**: Fluid semantic roles (`h1`, `body-md`) with numeric properties.
- **Spacing/Radius**: Explicit `px` anchor targets.
- **Workflow (`2b_interface-design`)**: Assumes Stitch acts as an upstream generator. The agent performs a "Token Snap" to translate Stitch's raw output into the project's OKLCH/px format.

### Google Stitch Native Output / Ingestion Format
- **Colors**: Hex codes (`#ffffff`) mapped to Material 3 tokens (e.g., `surface-container-lowest`).
- **Typography**: String-wrapped weights/heights (`fontWeight: '700'`).
- **Spacing/Radius**: `rem` values (except for `full: 9999px`).

## The Dilemma
If `.memory/DESIGN.md` is intended to be directly **ingested** by Stitch without agent translation (as noted in the Versioning Plan: *"the YAML Stitch ingests as the project Design System"*), the current StratOS OKLCH/px format is incompatible. Stitch expects its native Material 3 / Hex / rem schema.

## Proposed Resolution Paths
1. **Align with Stitch**: Update the StratOS `DESIGN.md` template to use Hex, `rem`, and the Stitch schema natively. This ensures frictionless ingestion but overrides StratOS's preference for OKLCH.
2. **Keep StratOS Native**: Maintain the OKLCH/px standard, but acknowledge that any push to Stitch requires an agent or build script to translate the file back into Stitch's native hex/rem format.

## TODO: Clean up dead code in build.py

In `build/build.py` around line 87, there is a lingering piece of code:
```python
version = None if srcfile.name == "DESIGN.md" else VERSION
```

This was originally meant to prevent injecting version metadata into `DESIGN.md` under the legacy Form B architecture to avoid conflicts with the Stitch/Google design schema. 

Because `DESIGN.md` is now safely processed via the unified OKF YAML parser and is copied using `copytree` rather than this specific `copy_md_with_frontmatter` function, this line is actually dead code and does nothing. 

It should be removed in a future cleanup session to keep the build pipeline pristine.
