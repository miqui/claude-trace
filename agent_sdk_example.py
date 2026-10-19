"""Trace a Claude Agent SDK run.

The Agent SDK runs the Claude Code CLI as a subprocess; the CLI exports its own
spans (claude_code.interaction / llm_request / tool) when the OTEL env vars below
are set. Because query() is called inside our `run_agent` span, the SDK injects
TRACEPARENT into the subprocess and the CLI's spans join this trace.
"""

import asyncio

from claude_agent_sdk import ClaudeAgentOptions, query
from opentelemetry import trace

from tracing import OTLP_ENDPOINT, setup_tracing

provider = setup_tracing("claude-agent-example")
tracer = trace.get_tracer("claude-trace")

OTEL_ENV = {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "CLAUDE_CODE_ENHANCED_TELEMETRY_BETA": "1",  # required for traces (beta)
    "OTEL_TRACES_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
    "OTEL_EXPORTER_OTLP_ENDPOINT": OTLP_ENDPOINT,
    "OTEL_TRACES_EXPORT_INTERVAL": "1000",  # flush quickly for short runs
    "OTEL_SERVICE_NAME": "claude-agent-cli",
    # Opt-in content capture; remove if your backend shouldn't store prompts/tool output.
    "OTEL_LOG_USER_PROMPTS": "1",
    "OTEL_LOG_TOOL_DETAILS": "1",
}


async def main() -> None:
    options = ClaudeAgentOptions(env=OTEL_ENV, allowed_tools=["Read", "Glob"])
    with tracer.start_as_current_span("run_agent"):
        async for message in query(
            prompt="List the Python files in this directory and say what each one does.",
            options=options,
        ):
            print(message)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        provider.shutdown()
