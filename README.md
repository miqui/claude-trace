# claude-trace

OpenTelemetry traces from the Claude API SDK (`anthropic`) and the Claude Agent SDK (`claude-agent-sdk`), sent to a local Jaeger.

## Run

```bash
docker compose up -d          # Jaeger UI at http://localhost:16686
uv sync
export ANTHROPIC_API_KEY=...  # or `ant auth login`

uv run python api_example.py        # Claude API: tool runner + custom tool
uv run python agent_sdk_example.py  # Agent SDK: Claude Code agent loop
```

In Jaeger, pick the service `claude-api-example` or `claude-agent-example` and open the most recent trace.

## What you get

**`api_example.py`** — the Anthropic SDK emits spans in-process through the tracer provider registered in `tracing.py`:

```
answer_question                          (your span)
  anthropic.messages.tool_runner
    anthropic.messages.create            CLIENT, model/tokens/latency
    anthropic.custom_tool_use get_weather
      weather_lookup                     (your span inside the tool)
    anthropic.messages.create
```

`content_mode: "content"` puts prompts and responses on the spans. Remove it to export metadata only (IDs, timing, token counts).

**`agent_sdk_example.py`** — the Agent SDK runs the Claude Code CLI, which exports its own spans (service `claude-agent-cli`) when the `OTEL_*` / `CLAUDE_CODE_*` env vars are set. The SDK passes `TRACEPARENT` to the CLI, so its spans nest under `run_agent`:

```
run_agent                                (your span)
  claude_code.interaction
    claude_code.llm_request
    claude_code.tool  (Glob, Read, ...)
```

## Pointing at another backend

Set `OTEL_EXPORTER_OTLP_ENDPOINT` (base URL, without `/v1/traces`). Both examples read it. For auth headers, add `headers=` to `OTLPSpanExporter` in `tracing.py` and set `OTEL_EXPORTER_OTLP_HEADERS` in `OTEL_ENV`.

## Optional: server-side API tracing

An org admin can also have the Claude API export its own spans (`anthropic.model_request`, server tools) to an HTTPS OTLP endpoint (Console → Settings → OpenTelemetry). The SDK already sends `traceparent`, so those spans nest under the SDK's `anthropic.messages.create`. Local Jaeger on `localhost` can't receive them. That needs a public HTTPS endpoint on port 443.
