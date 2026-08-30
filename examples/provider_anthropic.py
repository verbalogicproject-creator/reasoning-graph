"""Print Anthropic Messages API kwargs without making a network call."""

import argparse
import json

from reasoning_graph.providers import build_anthropic_request

parser = argparse.ArgumentParser()
parser.add_argument("--model", required=True, help="A model ID available to your Anthropic account")
args = parser.parse_args()

request = build_anthropic_request(
    model=args.model,
    messages=[{"role": "user", "content": "Which verified graph paths support this coding decision?"}],
    thinking_mode="adaptive",
    effort="medium",
)
print(json.dumps(request, indent=2))
