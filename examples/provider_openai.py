"""Print an OpenAI Responses API request without making a network call."""

import argparse
import json

from reasoning_graph.providers import build_openai_request

parser = argparse.ArgumentParser()
parser.add_argument("--model", required=True, help="A model ID available to your OpenAI project")
args = parser.parse_args()

request = build_openai_request(
    model=args.model,
    input="Which verified graph paths support this coding decision?",
    effort="medium",
    summary="auto",
)
print(json.dumps(request, indent=2))
