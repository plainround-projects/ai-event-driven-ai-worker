# pip-audit

## What it is

`pip-audit` checks installed or pinned Python packages against databases of known security vulnerabilities. If one of the exact versions you use has a published security problem, it tells you and says which version fixes it.

## Why this repository uses it

A pinned dependency can still be a vulnerable one. `make audit` checks every pinned version against the public advisory database and fails on a finding; it already caught a real set of Pillow vulnerabilities in one of these repositories, which is why the lock now pins the fixed release.

## Where it appears

| File | What it does with pip-audit |
| --- | --- |
| `Makefile` (`audit`) | the command |
| `.github/workflows/ci.yml` | runs `make audit` |

## How it works underneath

You give it the lock file (`-r requirements-dev.lock`). It reads every `name==version` line and sends those to a vulnerability service (by default the Python Packaging Advisory Database, queried through PyPI). The service answers with advisory identifiers (CVE, GHSA or PYSEC numbers), a description, and the fixed versions. `pip-audit` prints a table and exits non-zero if anything was found.

`--no-deps` tells it not to resolve dependencies itself (the lock already lists everything) and `--disable-pip` stops it from calling `pip` at all, so it only reads the file. It needs network access, which is why it is a separate target (`make audit`) and not part of the offline `make check`.

## Walkthrough of this repository's use

```make
audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock
```

- `audit: $(STAMP) ## check the locked dependencies for known vulnerabilities`: A target that checks the pinned packages.
- `$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock`: Look up every pinned package and version in a database of known security problems. `--no-deps` and `--disable-pip` stop it from resolving or installing anything: it only reads the lock file.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
.venv/bin/pip-audit --version
```

`pip-audit 2.10.1`.

```bash
make audit
```

Needs the network. Ends with `No known vulnerabilities found` when the lock is clean.

```bash
.venv/bin/pip-audit --no-deps --disable-pip -r requirements.lock
```

The same check on the smaller runtime lock.

## Mistakes people make

- Ignoring a finding because the app 'does not use' the affected feature. Decide that deliberately and write it down.
- Running it only once. New advisories appear over time; the CI workflow runs it on every change.
- Auditing the wrong file. The runtime lock is smaller; the development lock includes the test tools too.
- Treating 'no known vulnerabilities' as 'secure'. It only covers published advisories.
- Pinning an old version to keep the build green. The fix is to move to the fixed version and re-run the tests.

## Check yourself

1. What does pip-audit compare?
   *Answer:* Each pinned package version against a database of known vulnerabilities.
2. What do `--no-deps --disable-pip` do?
   *Answer:* They make it read the lock file only, without resolving or installing anything.
3. Why is `make audit` not part of `make check`?
   *Answer:* It needs the network, and `make check` must work offline.
4. What is a CVE?
   *Answer:* A public identifier for a known security problem.
5. What should you do when it reports a fixed version?
   *Answer:* Update the dependency range, regenerate the lock with `make lock`, and re-run the tests.

## Further reading

- [pip-audit on GitHub (pinned version 2.10.1)](https://github.com/pypa/pip-audit)
- [Python Packaging Advisory Database](https://github.com/pypa/advisory-database)
