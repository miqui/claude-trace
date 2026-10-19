"""Trace Claude API calls made with the Anthropic Python SDK.

Produces, under one `answer_question` span of our own:
  anthropic.messages.tool_runner
    anthropic.messages.create          (request 1 -> asks for get_weather)
    anthropic.custom_tool_use get_weather
    anthropic.messages.create          (request 2 -> final answer)
"""

from anthropic import Anthropic, beta_tool
from opentelemetry import trace

from tracing import setup_tracing

provider = setup_tracing("claude-api-example")
tracer = trace.get_tracer("claude-trace")

# "content" exports prompts and responses on spans; drop it to export metadata only.
client = Anthropic(open_telemetry={"traces": {"content_mode": "content"}})


@beta_tool
def get_weather(location: str) -> str:
    """Get the current weather for a location.

    Args:
        location: City and country, e.g. Paris, France.
    """
    # Spans started here nest under the SDK's `anthropic.custom_tool_use` span.
    with tracer.start_as_current_span("weather_lookup") as span:
        span.set_attribute("weather.location", location)
        return f"18°C and cloudy in {location}"


def main() -> None:
    with tracer.start_as_current_span("answer_question"):
        runner = client.beta.messages.tool_runner(
            model="claude-opus-5-5",
            max_tokens=16000,
            tools=[get_weather],
            messages=[{"role": "user", "content": "What's the weather in Paris?"}],
        )
        final = runner.until_done()

    if final.stop_reason == "refusal":
        print("Refused:", final.stop_details)
    else:
        print("".join(block.text for block in final.content if block.type == "text"))


if __name__ == "__main__":
    try:
        main()
    finally:
        provider.shutdown()  # flush spans before exit
