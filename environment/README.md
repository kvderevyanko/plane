# CadQuery environment

`environment.yml` is the reproducible specification for CadQuery and the
libraries actually used by this project. The project-local prefix is
`.tools/conda/lr1600-cad` and is intentionally ignored by Git.

Create it without touching system Python:

```bash
CONDA_PKGS_DIRS="$PWD/.tools/conda/pkgs" \
  /home/kirill/miniforge3/bin/mamba env create --prefix "$PWD/.tools/conda/lr1600-cad" \
  --file environment/environment.yml
```

The convenience scripts select this prefix. No `conda init` is required.
