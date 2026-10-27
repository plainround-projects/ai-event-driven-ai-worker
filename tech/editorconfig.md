# EditorConfig

## What it is

EditorConfig is a tiny file format, `.editorconfig`, that tells every code editor the same basic habits for a project: which character set, how to indent, how to end lines. Most editors read it with no extra setup or with a small plugin.

## Why this repository uses it

Every editor that opens a file here will use the same indentation, line endings and encoding, so diffs stay clean and the Makefile keeps its tabs.

## Where it appears

| File | What it does with EditorConfig |
| --- | --- |
| `.editorconfig` | the whole file |

## How it works underneath

The file is made of sections whose headers are file-name patterns in square brackets (`[*]` for all files, `[*.md]` for Markdown, `[Makefile]` for that one file). Under each header are `key = value` lines. When an editor opens a file it reads `.editorconfig` in the file's folder and the folders above it (until a file that says `root = true`), and applies every section whose pattern matches. Later sections override earlier ones.

EditorConfig only configures editors; it does not run during the build. The formatter (`ruff format`) enforces layout for Python, so the two agree: four spaces, 120 columns.

## Walkthrough of this repository's use

```ini
root = true
```

- `root = true`: This is the top-level settings file: editors stop looking for more `.editorconfig` files in parent folders.

```ini
[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 4
```

- `[*]`: A section header. `*` means every file.
- `charset = utf-8`: Save files as UTF-8, the standard text encoding that can hold every language's letters.
- `end_of_line = lf`: End each line with a single line-feed character (the Unix and macOS way), not carriage-return plus line-feed.
- `insert_final_newline = true`: Every file ends with a newline.
- `trim_trailing_whitespace = true`: Remove spaces at the end of lines when saving.
- `indent_style = space`: Indent with spaces.
- `indent_size = 4`: One indent level is four spaces.

```ini
[*.{yml,yaml,json,toml}]
indent_size = 2
```

- `[*.{yml,yaml,json,toml}]`: A section for files ending in `.yml`, `.yaml`, `.json` or `.toml`.
- `indent_size = 2`: In those files, one indent level is two spaces.

```ini
[Makefile]
indent_style = tab
```

- `[Makefile]`: A section for the file named `Makefile`.
- `indent_style = tab`: Makefiles require a tab character at the start of command lines, so use tabs there.

```ini
[*.md]
trim_trailing_whitespace = false
```

- `[*.md]`: A section for Markdown files.
- `trim_trailing_whitespace = false`: In Markdown, two spaces at the end of a line mean a line break, so do not trim them.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
cat .editorconfig
```

Prints the 13-line file.

```bash
grep -c $'\r' Makefile || true
```

Counts carriage-return characters in the Makefile; expect `0` because lines end with a line feed only.

```bash
file Makefile
```

Reports ASCII text (no Windows line endings).

## Mistakes people make

- Using spaces in a Makefile. Make requires tabs on recipe lines, so the file sets `indent_style = tab` for it.
- Trimming trailing whitespace in Markdown, where two trailing spaces mean a line break.
- Forgetting `root = true`, so a stray file in a parent folder changes the rules.
- Expecting it to fix files by itself; it only tells the editor how to behave when you save.
- Different line endings on different machines. The file fixes `lf`.

## Check yourself

1. What does `[*.md]` mean?
   *Answer:* A section that applies to all files ending in `.md`.
2. What does `root = true` do?
   *Answer:* Stops the editor from looking for more `.editorconfig` files in parent folders.
3. Why does the Makefile section use tabs?
   *Answer:* Make requires a tab at the start of recipe lines.
4. Does EditorConfig run during `make lint`?
   *Answer:* No. It only affects editors.
5. What does `end_of_line = lf` do?
   *Answer:* Lines end with a single line-feed character.

## Further reading

- [EditorConfig specification](https://spec.editorconfig.org/)
- [EditorConfig website](https://editorconfig.org/)
