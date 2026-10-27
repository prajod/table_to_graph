# Contributing

Thank you for contributing to `table-to-graph`.

## Development setup

Python 3.10 through 3.13 and Poetry 2.4 are supported.

Windows Command Prompt:

```cmd
git clone https://github.com/prajod/table_to_graph.git
cd table_to_graph
poetry install --with dev
poetry run check_code_quality
```

Ubuntu or another POSIX environment:

```bash
git clone https://github.com/prajod/table_to_graph.git
cd table_to_graph
poetry install --with dev
poetry run check_code_quality
```

Install optional vision dependencies with `poetry install --with dev --extras vision`.

## Pull requests

1. Open an issue before making a large behavioral or architectural change.
2. Add or update tests for every behavior change.
3. Keep public APIs typed and preserve table/cell provenance.
4. Run `poetry run check_code_quality` before submitting.
5. Update documentation and `CHANGELOG.md` for user-visible changes.

Benchmark changes must state the corpus, metric definition, context budget, environment, and
whether extraction/indexing time is included. Do not label target-token containment as precision.

By participating, you agree to follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
