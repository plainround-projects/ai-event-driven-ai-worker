# YAML

## What it is

YAML is a text format for configuration, written as indented `key: value` lines and `- item` lists. This repository uses it for the CI workflow files (and for the Compose file where one exists).

## Why this repository uses it

GitHub Actions and Docker Compose are configured in YAML. The files here are short and explained line by line in the notes for those tools; this note is about the format itself.

## Where it appears

| File | What it does with YAML |
| --- | --- |
| `.github/workflows/ci.yml` | YAML |
| `docker-compose.yml` | YAML |

## How it works underneath

A YAML file describes the same things JSON does: *maps* (keys with values), *lists*, strings, numbers and booleans. Structure comes from indentation with spaces (never tabs). `key: value` is a map entry. A line starting with `- ` is an item of a list. `[a, b]` and `{x: 1}` are compact list and map forms. A `#` starts a comment. Strings usually need no quotes, but quotes protect text that could be misread, such as `"3.13"` (otherwise it is the number 3.13, which loses the trailing zero for `3.10`).

Compose files add *anchors*: `&name` labels a block and `*name` reuses it. A program reads the file into data structures and uses them; nothing in YAML itself runs.

## Walkthrough of this repository's use

YAML has no code of its own, so the line-by-line explanations live in the notes for the tools that read each file:

- `.github/workflows/ci.yml`: see `github-actions.md`
- `docker-compose.yml`: see `docker-compose.md`

The YAML features these files use:

- **Maps** (`runs-on: ubuntu-latest`): a key, a colon, a space, a value.
- **Nested maps** by indentation: `jobs:` then a job name indented two spaces, then its keys indented two more.
- **Lists** with `- `: the `steps:` of a job.
- **Flow lists** in square brackets (`on: [push, pull_request]`), the same data on one line.
- **Quoted strings** (`"3.13"`) so the version stays text.
- **Comments** with `#`.
- **Anchors and aliases** in the Compose file: `&app_env` labels a block, `*app_env` reuses it.
- **Interpolation** in the Compose file: `${NAME:-default}` is not YAML but Compose syntax inside a YAML string.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
python3 -c "print(open('.github/workflows/ci.yml').read()[:200])"
```

Prints the top of the workflow file.

```bash
grep -c '^ *- ' .github/workflows/ci.yml
```

Counts list items (steps) in the workflow.

```bash
grep -n '^[a-z]' .github/workflows/ci.yml
```

Shows the top-level keys: `name`, `on`, `jobs`.

## Mistakes people make

- Tab characters or inconsistent indentation. YAML allows only spaces and the depth carries the meaning.
- Unquoted values that look like something else: `3.10` becomes `3.1`, `yes` may become a boolean in some parsers, `no` too.
- Forgetting the space after the colon (`key:value` is a single string).
- Copy-pasting a list item at the wrong indent so it attaches to the wrong key.
- Putting secrets in the file. Workflows here use none.

## Check yourself

1. What gives YAML its structure?
   *Answer:* Indentation with spaces.
2. How do you write a list?
   *Answer:* One line per item, each starting with `- `.
3. Why is the Python version quoted as `"3.13"`?
   *Answer:* So it stays text and cannot be read as a number.
4. What does `#` do?
   *Answer:* Starts a comment.
5. What does `*name` do in Compose?
   *Answer:* Reuses the block labeled `&name` (an alias of an anchor).

## Further reading

- [YAML 1.2.2 specification](https://yaml.org/spec/1.2.2/)
- [Learn YAML in Y minutes](https://learnxinyminutes.com/docs/yaml/)
