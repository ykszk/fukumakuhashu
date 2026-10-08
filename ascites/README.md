Standalone nnU-Net v1 environment for ascites segmentation (Task505_TCGA-OV).

No TensorFlow dependency — verified the inference stack (`nnunet`, `batchgenerators`, `acvl-utils`) never imports it.

## Setup

`nnunet==1.7.0`'s PyPI release declares a dependency on the deprecated `sklearn`
placeholder package, which modern pip/setuptools refuse to build by default.
Set this env var before syncing:

```bash
SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL=True uv sync
```

(`matplotlib` — missing from `nnunet`'s own declared dependencies despite being
imported directly by `nnUNetTrainer.py` — is already listed explicitly in
`pyproject.toml`, so no extra step needed for that one.)

Verified: this plain-PyPI setup produces byte-identical output to
`StanfordMIMI/nnUNet_cust` (the fork Comp2Comp depends on) for the same input —
the fork isn't functionally required, it just bundles fixes for the two issues
above.
