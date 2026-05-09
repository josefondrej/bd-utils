# bd-utils

`bd-utils` provides a `dbutils`-like interface that works in both Databricks and local environments.

## Goals

- Use native Databricks `dbutils` when running on Databricks.
- Use a predictable local implementation for tests and local scripts.
- Keep unsupported APIs explicit with actionable errors.

## API compatibility target

`bdutils` mirrors the Databricks module layout:

- `credentials`, `data`, `fs`, `jobs.taskValues`, `library`, `meta`, `notebook`, `preview`, `secrets`, `widgets`, `api`

Locally, commonly used commands are implemented (`widgets`, `secrets`, `fs`, `jobs.taskValues`, `notebook.exit`); unsupported commands are present and raise `NotImplementedError`.

## Quick start

```python
import bdutils
value = bdutils.widgets.get("country")
```

Alternative (useful in tests when you need explicit config):

```python
from bdutils import get_dbutils
dbutils = get_dbutils(force_adapter="local")
print(dbutils.fs.help("ls"))
```

## Run tests

```bash
make test
```

This runs:

`PYTHONPATH=src python -m pytest -q tests`

### Local widget lookup order

1. Values set with `widgets.text(...)` in-process
2. Environment variable `DBX_WIDGET_<NAME_UPPER_SNAKE>`

### Local secret mapping

`dbutils.secrets.get(scope, key)` maps to environment variable:

`DBX_SECRET__<SCOPE>__<KEY>`

## Notes

- `dbfs:/...` paths are mapped to `~/.bd-utils/dbfs/...` by default.
- Unsupported methods raise `NotImplementedError`.
