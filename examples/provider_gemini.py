"""Print Gemini Interactions API kwargs without making a network call."""

import argparse
import json

from reasoning_graph.providers import build_gemini_request

parser = argparse.ArgumentParser()
parser.add_argument("--model", required=True, help="A model ID available to your Gemini project")
args = parser.parse_args()

request = build_gemini_request(
    model=args.model,
    input="Which verified graph paths support this coding decision?",
    thinking_level="medium",
    thinking_summaries="auto",
)
print(json.dumps(request, indent=2))
