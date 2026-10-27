# The MIT license file

## What it is

A *license* is the legal text that says what other people may do with your code. The MIT license is one of the shortest and most permissive: anyone may use, copy, change and sell the code, as long as they keep the copyright line and the license text with it. The software comes with no warranty.

## Why this repository uses it

The reference repositories are meant to be read, copied and reused; the MIT license says so explicitly in four lines.

## Where it appears

| File | What it does with The MIT license file |
| --- | --- |
| `LICENSE` | the license text |
| `pyproject.toml` | `license = { text = "MIT" }` |

## How it works underneath

The file is called `LICENSE` and sits at the top of the repository, where people and tools look for it. It is plain text: the title, a copyright line (year and author), the permission paragraph, and the no-warranty paragraph. `pyproject.toml` repeats the choice in one word (`license = { text = "MIT" }`) so package tools can show it. Nothing executes the license; it only has legal meaning.

## Walkthrough of this repository's use

The file, in full:

```
MIT License

Copyright (c) 2026 Sumit Srivastava

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

The first line is the title. The second is the copyright line: the year and the author. The first paragraph grants the permissions (use, copy, modify, merge, publish, distribute, sublicense, sell) under one condition, that this notice stays with the software. The second paragraph is the disclaimer: the software is provided 'as is', without warranty, and the authors are not liable.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
head -5 LICENSE
```

Prints the title and the copyright line.

```bash
wc -l LICENSE
```

Counts the lines (about 20).

```bash
grep -n license pyproject.toml
```

Shows the one-word summary tools read.

## Mistakes people make

- Publishing code with no license. Without one, the default is that nobody may reuse it.
- Changing the text of the license. Tools recognise it by its exact wording.
- Forgetting the copyright line.
- Assuming the license covers dependencies. Each dependency has its own license.
- Mixing it up with a privacy or terms-of-service text; it only covers use of the code.

## Check yourself

1. What may people do under the MIT license?
   *Answer:* Use, copy, modify, merge, publish, distribute, sublicense and sell the software.
2. What must they keep?
   *Answer:* The copyright notice and the license text.
3. Does MIT give a warranty?
   *Answer:* No. The software is provided as is.
4. Where does the repository state its license for tools?
   *Answer:* In `pyproject.toml`, `license = { text = "MIT" }`.
5. What is the file called?
   *Answer:* `LICENSE`.

## Further reading

- [The MIT license text](https://opensource.org/license/mit)
- [Choose a license](https://choosealicense.com/licenses/mit/)
