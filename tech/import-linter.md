# import-linter

## What it is

`import-linter` checks the *shape* of a codebase: which modules are allowed to import which others. You write the rules as *contracts* in `pyproject.toml`; the tool builds a graph of all imports and fails if any contract is broken. It is how this repository keeps its layers honest: the domain code never imports the web framework or the model SDK.

## Why this repository uses it

The design is a set of layers: the rules in `domain` and `application` must not depend on frameworks, databases or the model SDK, so they stay testable with fakes. A written, checked contract keeps that true as the code grows. It is what makes the handler and the worker loop testable with an in-memory queue and a scripted model

## Where it appears

| File | What it does with import-linter |
| --- | --- |
| `pyproject.toml` (`[tool.importlinter]`) | the contracts |
| `Makefile` (`lint`) | runs `lint-imports` |

## How it works underneath

Python code imports other code with `import x` or `from x import y`. `import-linter` parses every module in the root package and records an arrow from the importing module to the imported one. It also follows indirect paths: if `a` imports `b` and `b` imports `c`, then `a` depends on `c` through `b`.

A `layers` contract lists layers from top to bottom. A module in a higher layer may import a lower one, never the reverse. A `forbidden` contract lists source modules and modules they must not reach, even indirectly. With `include_external_packages = true` the graph also contains third-party packages, so a contract can forbid `anthropic` or `fastapi`.

The command is `lint-imports`. It prints each contract as KEPT or BROKEN and exits non-zero if any is broken. It caches the graph in `.import_linter_cache`.

## Walkthrough of this repository's use

### The contracts

```toml
[tool.importlinter]
root_package = "inbox_worker"
include_external_packages = true
```

- `[tool.importlinter]`: Settings for `import-linter`, which checks which module may import which.
- `root_package = "inbox_worker"`: The package to analyze: `inbox_worker`.
- `include_external_packages = true`: Let contracts mention third-party packages (such as `anthropic`) as well as this project's own modules.

```toml
[[tool.importlinter.contracts]]
name = "Layers: interfaces -> infrastructure -> application -> domain, never upward"
type = "layers"
layers = [
    "inbox_worker.interfaces",
    "inbox_worker.infrastructure",
    "inbox_worker.application",
    "inbox_worker.domain",
]
```

- `[[tool.importlinter.contracts]]`: One more contract: a rule about imports that the tool must find kept.
- `name = "Layers: interfaces -> infrastructure -> application -> domain, never upward"`: The package name, `Layers: interfaces -> infrastructure -> application -> domain, never upward`. It is the name `pip` shows and the name used in the lock files.
- `type = "layers"`: A `layers` contract: modules listed first may import modules listed later, never the other way.
- `layers = [`: The layers, from the top (may import everything below) to the bottom (imports none of the others).
- `"inbox_worker.interfaces",`: The layer `inbox_worker.interfaces`.
- `"inbox_worker.infrastructure",`: The layer `inbox_worker.infrastructure`.
- `"inbox_worker.application",`: The layer `inbox_worker.application`.
- `"inbox_worker.domain",`: The layer `inbox_worker.domain`.

```toml
[[tool.importlinter.contracts]]
name = "Domain and application import no vendor SDK, web framework or database driver"
type = "forbidden"
source_modules = ["inbox_worker.domain", "inbox_worker.application"]
forbidden_modules = ["anthropic", "fastapi", "uvicorn", "starlette", "psycopg"]
```

- `[[tool.importlinter.contracts]]`: One more contract: a rule about imports that the tool must find kept.
- `name = "Domain and application import no vendor SDK, web framework or database driver"`: The package name, `Domain and application import no vendor SDK, web framework or database driver`. It is the name `pip` shows and the name used in the lock files.
- `type = "forbidden"`: A `forbidden` contract: the source modules must not import the forbidden modules, directly or through other modules.
- `source_modules = ["inbox_worker.domain", "inbox_worker.application"]`: Check these modules (and everything inside them).
- `forbidden_modules = ["anthropic", "fastapi", "uvicorn", "starlette", "psycopg"]`: They must not import any of these third-party packages.

### What a run prints

`lint-imports` prints a short report. With both contracts holding it ends with:

```
Layers: interfaces -> infrastructure -> application -> domain, never upward KEPT
Domain and application import no vendor SDK, web framework or database driver KEPT

Contracts: 2 kept, 0 broken.
```

If someone writes `import fastapi` in a domain module, the second contract turns BROKEN, the report shows the import chain, and `make lint` fails.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
.venv/bin/lint-imports
```

Prints the two contract lines marked KEPT and `Contracts: 2 kept, 0 broken.`

```bash
.venv/bin/lint-imports --version
```

`import-linter 2.15`.

```bash
grep -rn '^import\|^from' src/inbox_worker/domain | grep -v 'from inbox_worker\|__future__\|dataclasses\|typing\|collections\|datetime\|math\|re$\|json\|decimal\|hashlib\|enum\|random\|statistics' | head
```

Lists imports in the domain layer that are not from the standard library or this package; the expected output is empty.

## Mistakes people make

- Writing a contract with the wrong module name, so it checks nothing. The report lists each contract by name; a rule that never fails should be tested by breaking it once on purpose.
- Forgetting indirect imports. `forbidden` contracts catch them; a grep for the package name would not.
- Putting the layer order upside down.
- Leaving `include_external_packages` off while writing a contract about a third-party package.
- Treating the tool as a replacement for review. It enforces direction, not good design.

## Check yourself

1. What is a contract?
   *Answer:* A rule about imports, written in `pyproject.toml`, that the tool checks.
2. What does a `layers` contract allow?
   *Answer:* Higher layers to import lower layers, never the other way.
3. What does a `forbidden` contract catch that `grep` would miss?
   *Answer:* Indirect imports: A imports B and B imports the forbidden package.
4. Which command runs the check?
   *Answer:* `lint-imports` (here via `make lint`).
5. What makes third-party packages visible to a contract?
   *Answer:* `include_external_packages = true`.

## Further reading

- [import-linter documentation (pinned version 2.15)](https://import-linter.readthedocs.io/en/stable/)
- [Contract types](https://import-linter.readthedocs.io/en/stable/contract_types.html)
