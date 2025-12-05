import os
import sys
from dotenv import load_dotenv
import dspy
from workflow import SmartWODWorkflow


# Define example user inputs here instead of via command-line arguments.
USER_REQUEST: str = "I want to train my endurance and improve my running"
USER_CONTEXT: dict = {
	"injury": "back pain",
	"goals": ["improve endurance"],
}

# Default model and debug mode
DEFAULT_DEBUG: bool = False
DEFAULT_MODEL: str = "gpt-4o-mini"


def main() -> int:
	load_dotenv()
	if not os.getenv("OPENAI_API_KEY"):
		sys.stderr.write("ERROR: OPENAI_API_KEY is not set in environment.\n")
		return 1

	lm = dspy.LM(
		model=f"openai/{DEFAULT_MODEL}", 
		model_type="chat",
		api_key=os.getenv("OPENAI_API_KEY"),
		temperature=0
		)
	dspy.configure(lm=lm)

	workflow = SmartWODWorkflow(debug=DEFAULT_DEBUG)
	result = workflow(request=USER_REQUEST, context=USER_CONTEXT)

	import json
	plan = getattr(result, "plan", result)
	print(json.dumps(plan, indent=2))
	return 0


if __name__ == "__main__":
	sys.exit(main())
