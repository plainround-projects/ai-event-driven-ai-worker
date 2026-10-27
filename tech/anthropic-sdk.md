# The Anthropic Python SDK

## What it is

An *SDK* (software development kit) is a library that wraps a web service so you can call it as ordinary functions. The `anthropic` package wraps the Claude API: you build a client, call `client.messages.create(...)` with the model name and the conversation, and get back an object with the model's reply and the number of tokens used. A *token* is a small piece of text (a few characters) that the model reads and writes; usage and price are counted in tokens.

## Why this repository uses it

Each event runs a model step, the support-email extractor. The real adapter exists so the worker can run over Claude, but every check runs on a fake model with configurable delay, errors and a rate limit, and an authored cassette, because no key was available; the adapter is exercised only by an opt-in live test.

## Where it appears

| File | What it does with The Anthropic Python SDK |
| --- | --- |
| `src/inbox_worker/infrastructure/claude_model.py` | the adapter: `messages.create`, classification of retryable errors |
| `tests/live/test_claude_live.py` | the opt-in test (skipped unless `RUN_LIVE=1` and a key are set) |
| `scripts/smoke.py` | the 20-email smoke run (`--record` uses a key) |

## How it works underneath

`messages.create` sends one HTTPS request to the API and waits for the whole answer. The request names a `model`, a `max_tokens` limit on the reply, an optional `system` text (standing instructions), and a list of `messages` (the conversation, each with a `role` of `user` or `assistant`). The reply has a list of `content` *blocks*; text blocks have `.type == "text"` and `.text`. `stop_reason` says why the model stopped (`end_turn`, `max_tokens`, `tool_use`, or `refusal` when the model declined). `usage.input_tokens` and `usage.output_tokens` say how much was read and written.

*Tools*: the request can describe functions the model may ask for. The model answers with a `tool_use` block (a name and arguments); the program runs the function itself and sends the result back as a `tool_result` block. The model never runs anything.

*Streaming*: `client.messages.stream(...)` returns the answer in pieces as the model writes them; `text_stream` yields the text pieces and `get_final_message()` gives the complete message. When a program stops reading and leaves the `with` block, the connection closes.

The client reads its key from the argument or from the `ANTHROPIC_API_KEY` environment variable. It retries some failures itself (`max_retries`) and raises typed errors: `RateLimitError` (HTTP 429), `APITimeoutError`, `APIConnectionError`, and `APIStatusError` for other bad statuses; all derive from `APIError`.

In this repository the SDK is used **only** in one adapter file, behind a port (an interface the rest of the code depends on). Every test uses a fake or a recording, so no key is needed to run anything. The adapter is exercised only by an opt-in live test.

## Walkthrough of this repository's use

The only file in the repository that imports the SDK is `src/inbox_worker/infrastructure/claude_model.py`. Here is its adapter class:

From `src/inbox_worker/infrastructure/claude_model.py`:

```python
class ClaudeModel:
    """One Messages API call per request. Rate limits, server errors, timeouts and dropped connections are retryable."""
```

- `class ClaudeModel:`: The adapter class: the only place in the repository that imports the SDK.
- `"""One Messages API call per request. Rate limits, server errors, timeouts and dropped connections are retryable."""`: The docstring.

```python
    def __init__(
        self, model_id: str, api_key: str | None, *, timeout_seconds: float = 30.0, client: Any = None
    ) -> None:
        if client is None:
            if not api_key:
                raise ConfigurationError("ANTHROPIC_API_KEY must be set to use the Claude adapter")
            client = anthropic.Anthropic(api_key=api_key, timeout=timeout_seconds, max_retries=0)
        self._client = client
        self._model_id = model_id
```

- `def __init__(`: The constructor; the parameters follow.
- `self, model_id: str, api_key: str | None, *, timeout_seconds: float = 30.0, client: Any = None`: Takes the model name, the key (or nothing), a timeout (default 30.0 seconds), and optionally a ready-made `client`. Tests pass a fake `client`, so no key is needed.
- `) -> None:`: Closes the parameter list; the constructor returns nothing.
- `if client is None:`: Only build a real client when none was given.
- `if not api_key:`: No key and no client: the adapter cannot work.
- `raise ConfigurationError("ANTHROPIC_API_KEY must be set to use the Claude adapter")`: Fails at start with a clear message instead of failing later inside a request.
- `client = anthropic.Anthropic(api_key=api_key, timeout=timeout_seconds, max_retries=0)`: Creates the real client. `timeout` limits how long to wait for the API; `max_retries=0` is how many times the SDK itself retries transient failures (0 means the application does its own retrying).
- `self._client = client`: Keeps the client.
- `self._model_id = model_id`: Keeps the model name(s).

```python
    def complete(self, system: str, user: str, prompt_version: str) -> ModelReply:
        """Send the prompt as the system text and the email as the user message."""
        try:
            message = self._client.messages.create(
                model=self._model_id, max_tokens=300, system=system, messages=[{"role": "user", "content": user}]
            )
        except (anthropic.RateLimitError, anthropic.APITimeoutError, anthropic.APIConnectionError) as error:
            raise RetryableModelError(f"{type(error).__name__}: {error}") from error
        except anthropic.APIStatusError as error:
            if error.status_code >= 500:
                raise RetryableModelError(f"{type(error).__name__}: {error}") from error
            raise ModelCallError(f"{type(error).__name__}: {error}") from error
        if message.stop_reason == "refusal":
            raise ModelCallError("the model declined the request (stop_reason=refusal)")
        text = "".join(block.text for block in message.content if block.type == "text")
        return ModelReply(text, message.model, message.usage.input_tokens, message.usage.output_tokens)
```

- `def complete(self, system: str, user: str, prompt_version: str) -> ModelReply:`: Another line of the function (a statement or a continuation of the one above).
- `"""Send the prompt as the system text and the email as the user message."""`: The docstring.
- `try:`: Guards the network call.
- `message = self._client.messages.create(`: The call itself: one HTTPS request; the program waits for the whole answer.
- `model=self._model_id, max_tokens=300, system=system, messages=[{"role": "user", "content": user}]`: Another line of the function (a statement or a continuation of the one above).
- `except (anthropic.RateLimitError, anthropic.APITimeoutError, anthropic.APIConnectionError) as error:`: Catches these SDK errors: anthropic.RateLimitError, anthropic.APITimeoutError, anthropic.APIConnectionError.
- `raise RetryableModelError(f"{type(error).__name__}: {error}") from error`: Re-raises it as the repository's own error `RetryableModelError`, so the rest of the code never sees SDK classes. `from error` keeps the original as its cause.
- `except anthropic.APIStatusError as error:`: Any other bad HTTP status from the API.
- `if error.status_code >= 500:`: A server-side failure is retryable; other statuses are not.
- `raise RetryableModelError(f"{type(error).__name__}: {error}") from error`: Re-raises it as the repository's own error `RetryableModelError`, so the rest of the code never sees SDK classes. `from error` keeps the original as its cause.
- `raise ModelCallError(f"{type(error).__name__}: {error}") from error`: Re-raises it as the repository's own error `ModelCallError`, so the rest of the code never sees SDK classes. `from error` keeps the original as its cause.
- `if message.stop_reason == "refusal":`: The model declined to answer.
- `raise ModelCallError("the model declined the request (stop_reason=refusal)")`: A refusal is a failure of this call, not a reply.
- `text = "".join(block.text for block in message.content if block.type == "text")`: The reply is a list of blocks; this keeps the text blocks and joins them into one string.
- `return ModelReply(text, message.model, message.usage.input_tokens, message.usage.output_tokens)`: Returns the reply text, the model's name, and the number of tokens read and written.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
.venv/bin/python -c "import anthropic; print(anthropic.__version__)"
```

Prints `2.3.0`, the pinned version.

```bash
grep -rn 'import anthropic' src | wc -l
```

Counts the files that import the SDK; expect exactly 1 (the adapter).

```bash
make test
```

Runs every test without a key; the adapter is tested with a fake client.

```bash
RUN_LIVE=1 .venv/bin/pytest tests/live -q
```

Without `ANTHROPIC_API_KEY` set the live test is skipped. With your own key it makes one real call.

## Mistakes people make

- Putting a key in the code or in a committed file. The key comes from the environment, and tests never need it.
- Letting the SDK's retries and the application's retries both run, doubling waits. Where the application retries itself, the client is created with `max_retries=0`.
- Assuming the first content block is text. Blocks can be text, tool use or thinking; the adapter keeps only the `text` ones when it wants text.
- Ignoring `stop_reason`. A `refusal` or `max_tokens` stop is not a normal answer; the adapter treats a refusal as its own error.
- Sending a sampling setting that the chosen model rejects. The adapters send no `temperature`.

## Check yourself

1. What is a token?
   *Answer:* A small piece of text the model reads or writes; usage and cost are counted in tokens.
2. What does `stop_reason == "refusal"` tell you?
   *Answer:* The model declined to answer; it is not a normal reply.
3. Who runs a tool the model asks for?
   *Answer:* The program. The model only asks; the program runs the function and returns the result.
4. Why is the SDK imported in only one file?
   *Answer:* So the rest of the code depends on a port and can be tested with fakes without any key or network.
5. Which exception means 'too many requests'?
   *Answer:* `anthropic.RateLimitError` (HTTP 429).

## Further reading

- [Anthropic API documentation](https://docs.anthropic.com/en/api/overview)
- [Messages API](https://docs.anthropic.com/en/api/messages)
- [Python SDK on GitHub (pinned version 2.3.0)](https://github.com/anthropics/anthropic-sdk-python)
