from typing import Any, Dict, List
import json
import dspy

from functions import (
	UserIntentAgent,
	WODArchitect,
	ScalingInjurySpecialist,
	PerformanceOptimizer,
)


class SmartWODWorkflow(dspy.Module):
	def __init__(self, debug: bool = False):
		super().__init__()
		self.debug = debug
		self.intent = UserIntentAgent(debug=debug)
		self.architect = WODArchitect(debug=debug)
		self.scaler = ScalingInjurySpecialist(debug=debug)
		self.optimizer = PerformanceOptimizer(debug=debug)

	def forward(self, request: str, context: Dict[str, Any]) -> dspy.Prediction:
		injury = context.get("injury", "") if isinstance(context, dict) else ""
		goals: List[str] = context.get("goals", []) if isinstance(context, dict) else []

		# 1) Normalize the raw request into a structured intent
		user_intent = self.intent(raw_request=request)

		# 2) Generate the base WOD
		base_wod = self.architect(request=user_intent)

		# 3) Apply scaling and injury logic
		annotated = self.scaler(base_wod_json=base_wod, injury=injury)

		# 4) Optimize performance (warm-up, cool-down, +2 accessories)
		plan = self.optimizer(modified_wod_json=annotated, goals=goals)

		return dspy.Prediction(
			intent=user_intent,
			base_wod=base_wod,
			annotated_wod=annotated,
			plan=plan,
		)
