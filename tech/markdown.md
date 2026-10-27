# Markdown

## What it is

Markdown is a way of writing formatted text in plain files: `#` makes a heading, `*` or `-` a bullet, backticks make `code`, a fenced block of three backticks is a code sample, and pipes make tables. This repository uses it for the README, the architecture notes, the decision records, the changelog, the notes in this folder, and also for the *prompts* the program reads.

## Why this repository uses it

Documentation and prompts are both text that changes over time and needs review. Markdown files in Git give both a history. The prompts are loaded by the program as files, so changing wording is a reviewed change with a changelog line, not an edit hidden in code.

## Where it appears

| File | What it does with Markdown |
| --- | --- |
| `README.md` | what the repository is and how to run and verify it |
| `ARCHITECTURE.md` | components, data flow, decisions |
| `CHANGELOG.md` | what changed per version |
| `docs/adr/*.md` | one decision per file |
| `tech/*.md` | these notes |
| `prompts/CHANGELOG.md` | why each prompt version exists |
| `prompts/extract.v1.md` | a versioned prompt (loaded by the program) |

## How it works underneath

A Markdown file is plain text. A *renderer* (GitHub, an editor preview) converts it to formatted pages. The program that reads the prompt files does not render anything: it treats them as text with a small *header* (lines between two `---` fences that give the version and owner) followed by the prompt body.

Because prompts are files in Git, every change to a prompt is a visible, reviewable change with a history. A new version of the text goes into a new file name (`extract.v2.md`) so that recorded model answers, which are keyed by the prompt version, stop matching and must be re-recorded.

## Walkthrough of this repository's use

The prompts are Markdown files that the program reads at run time.

### `prompts/CHANGELOG.md`

```markdown
# Prompt changelog

Each prompt file is `name.vN.md`. A change to the text is a new file with the next version; the old file stays so a recorded
cassette keyed by the old version still replays. The version is part of every model request key.

## extract.v1 - 2026-10-27

- First version: the four ticket fields and the instruction to reply with one JSON object only.
```

### `prompts/extract.v1.md`

```markdown
---
version: extract.v1
owner: support-platform
---
Extract intent (cancel, refund, order_status or other), order_number (four digits or null), sentiment (positive, neutral or negative) and requested_action (cancel_order, issue_refund, send_tracking or none) from this support email. Reply with one JSON object only.
```

**How the header works.** A prompt file starts with a line containing only `---`, then one `key: value` line per header field, then another `---`; everything after is the prompt text. The program splits the file at the fences, requires the header keys it needs, and uses the rest as the instructions it sends to the model. A file that lacks the first fence, or a required key, is refused with a message that names the problem.

**Versions.** A change to the text is a new file (`name.v2.md`) and a line in `prompts/CHANGELOG.md`. Recorded model answers are keyed by the prompt version, so after a change the old recordings stop matching and the test says to re-record.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
ls prompts
```

Lists the prompt files and the prompt changelog.

```bash
head -8 prompts/CHANGELOG.md
```

Prints the top of a prompt file: the `---` header with version and owner.

```bash
ls docs/adr
```

Lists the decision records.

```bash
grep -c '^## ' README.md
```

Counts the README's second-level headings.

## Mistakes people make

- Treating a prompt as code that can be edited casually. A wording change can change results; it needs a new version and a changelog line.
- Forgetting the blank line before a list or table; many renderers then show plain text.
- Using real file paths and commands that no longer exist in the notes. The notes are rewritten when the code changes.
- Headings out of order, which breaks the table of contents.
- Long lines of code outside a fenced block.

## Check yourself

1. How do you make a code block?
   *Answer:* Put the code between two lines of three backticks.
2. Why are prompts kept as Markdown files?
   *Answer:* So changes are reviewed and versioned like code, and the program can load them without code changes.
3. What is between the two `---` lines at the top of a prompt file?
   *Answer:* The header: version, owner (and in some repositories the schema it expects).
4. Why a new file for a new prompt version?
   *Answer:* So old recordings keyed by the old version stop matching and must be re-recorded.
5. What turns Markdown into formatted pages?
   *Answer:* A renderer, such as GitHub's.

## Further reading

- [CommonMark specification](https://spec.commonmark.org/)
- [GitHub Flavored Markdown](https://github.github.com/gfm/)
