"""
Unified DSPy agents and signatures for the Smart WOD workflow.

This file intentionally merges:
- _parse_json_dict() helper function
- UserIntentSignature, WODArchitectSignature, ScalingInjurySignature, PerformanceOptimizerSignature
- UserIntentAgent, WODArchitect, ScalingInjurySpecialist, PerformanceOptimizer

into a single module.
"""

from typing import Any, Dict, List
import json
import sys
import dspy


def _parse_json_dict(raw: str) -> Dict[str, Any] | None:
	"""
	Best-effort helper to parse a JSON string into a dict.
	Returns None if parsing fails or the result is not a dict.
	Prints a short warning when parsing fails.
	"""
	try:
		val = json.loads(raw)
		if isinstance(val, dict):
			return val
		# if parsed but not a dict
		print(
			"[WARN] _parse_json_dict: JSON parsed but is not an object; "
			"expected a dict. Truncating preview: "
			f"{str(val)[:200]!r}",
			file=sys.stderr,
		)
	except Exception as e:
		print(
			"[WARN] _parse_json_dict: failed to parse JSON; "
			f"{type(e).__name__}: {e}. Raw preview: {raw[:200]!r}",
			file=sys.stderr,
		)
	return None


# =========================
# Signatures
# =========================


class UserIntentSignature(dspy.Signature):
	"""Normalize a vague user request into a structured CrossFit-related workout intent."""

	raw_request = dspy.InputField(
		desc=(
			"Free-text user input such as 'I feel tired but want to move', "
			"'I want a heavy lifting day', or 'something light for 15 minutes'."
		),
	)
	intent_json = dspy.OutputField(
		desc=(
			"JSON describing the intent, e.g. "
			'{"type": "Light-duty", "duration": 15, "style": "EMOM"} or '
			'{"type": "Heavy lifting", "duration": 45, "style": "Strength"}'
		),
	)


class WODArchitectSignature(dspy.Signature):
	"""Generate a structured CrossFit workout from a structured intent. Output strict JSON with fields: name, type, movements (list of objects with exercise and a unit like reps, time, or calories)."""

	request = dspy.InputField(
		desc=(
			"Structured intent from the User Intent Agent (dict/JSON string) such as "
			'{"type": "Light-duty", "duration": 15, "style": "EMOM"} or '
			'{"type": "Heavy lifting", "duration": 45, "style": "Strength"}.'
		),
	)
	workout_json = dspy.OutputField(
		desc="JSON with fields: name, type, movements (list of {exercise, reps|time|calories}).",
	)


class ScalingInjurySignature(dspy.Signature):
	"""Annotate a base WOD with scaling and rx_plus options and safe alternatives for injuries."""

	base_wod_json = dspy.InputField(
		desc="JSON from WOD Architect: {name, type, movements}.",
	)
	injury = dspy.InputField(
		desc="Free-text injury description like 'right shoulder pain' (may be empty).",
	)
	annotated_wod_json = dspy.OutputField(
		desc="JSON of same WOD plus for each movement: scaled, rx_plus, injury_alts when needed.",
	)


class PerformanceOptimizerSignature(dspy.Signature):
	"""Provide warm-up, cool-down, and two accessory sessions aligned to user goals."""

	modified_wod_json = dspy.InputField(
		desc="JSON from Scaling & Injury Specialist.",
	)
	goals = dspy.InputField(
		desc="List of user goals like ['improve cardio', 'build leg strength'] (as JSON string).",
	)
	plan_json = dspy.OutputField(
		desc="Output only strict JSON: {warmup, wod, cooldown, accessories: [..]} with actionable details.",
	)


class UserIntentAgent(dspy.Module):
	def __init__(self, debug: bool = False):
		super().__init__()
		self.signature = UserIntentSignature
		self.debug = debug
		self.program = dspy.Predict(UserIntentSignature)

	def forward(self, raw_request: str) -> Dict[str, Any]:
		if self.debug:
			print("=== USER INTENT INPUT REQUEST ===")
			print(raw_request)

		pred = self.program(raw_request=raw_request)
		raw = str(getattr(pred, "intent_json", ""))

		if self.debug:
			print("=== USER INTENT RAW OUTPUT (TEXT) ===")
			print(raw)

		parsed = _parse_json_dict(raw)
		if parsed is not None:
			return parsed

		return {
			"raw_request": raw_request,
			"raw_intent_json": raw,
		}


class WODArchitect(dspy.Module):
	def __init__(self, debug: bool = False):
		super().__init__()
		self.signature = WODArchitectSignature
		self.debug = debug
		self.program = dspy.Predict(WODArchitectSignature)

	def forward(self, request: Any) -> Dict[str, Any]:
		"""
		Accepts the structured intent from the User Intent Agent (dict or JSON string).
		Serializes dicts to JSON so the LM sees a consistent schema.
		"""
		if isinstance(request, dict):
			intent_payload = json.dumps(request)
		else:
			intent_payload = str(request)

		if self.debug:
			print("=== WOD ARCHITECT INPUT REQUEST ===")
			print(intent_payload)

		pred = self.program(request=intent_payload)

		raw = str(getattr(pred, "workout_json", ""))

		if self.debug:
			print("=== WOD ARCHITECT RAW OUTPUT (TEXT) ===")
			print(raw)

		parsed = _parse_json_dict(raw)
		if parsed is not None:
			return parsed

		return {
			"request": request,
			"raw_workout_json": raw,
		}


class ScalingInjurySpecialist(dspy.Module):
	def __init__(self, debug: bool = False):
		super().__init__()
		self.signature = ScalingInjurySignature
		self.debug = debug
		self.program = dspy.ChainOfThought(ScalingInjurySignature)

	def forward(self, base_wod_json: Dict[str, Any], injury: str) -> Dict[str, Any]:
		base_wod_str = json.dumps(base_wod_json)
		injury_text = injury or ""

		if self.debug:
			print("=== SCALER / DSPy INPUTS ===")
			print({"base_wod_json": base_wod_str, "injury": injury_text})

		pred = self.program(base_wod_json=base_wod_str, injury=injury_text)

		raw = str(getattr(pred, "annotated_wod_json", ""))

		if self.debug:
			print("=== SCALER / DSPy RAW OUTPUT ===")
			print(raw)
			print("PRED-injury")
			print(pred.toDict().keys())
			if hasattr(pred, "reasoning"):
				print("--- Reasoning ---")
				print(pred.reasoning)

		parsed = _parse_json_dict(raw)
		if parsed is not None:
			return parsed

		return {
			"base_wod_json": base_wod_json,
			"injury": injury_text,
			"raw_annotated_wod_json": raw,
		}


class PerformanceOptimizer(dspy.Module):
	def __init__(self, debug: bool = False):
		super().__init__()
		self.signature = PerformanceOptimizerSignature
		self.debug = debug
		self.program = dspy.ChainOfThought(PerformanceOptimizerSignature)

	def forward(self, modified_wod_json: Dict[str, Any], goals: str | List[str]) -> Dict[str, Any]:
		modified_wod_str = json.dumps(modified_wod_json)

		if isinstance(goals, list):
			parsed_goals = json.dumps(goals)
		else:
			parsed_goals = str(goals)

		if self.debug:
			print("=== OPTIMIZER / DSPy INPUTS ===")
			print({"modified_wod_json": modified_wod_str, "goals": parsed_goals})

		pred = self.program(modified_wod_json=modified_wod_str, goals=parsed_goals)

		raw_output = str(getattr(pred, "plan_json", ""))

		if self.debug:
			print("=== OPTIMIZER / DSPy RAW OUTPUT ===")
			print(raw_output)
			print("PRED-Optimizer")
			print(pred.toDict().keys())
			if hasattr(pred, "reasoning"):
				print("--- Reasoning ---")
				print(pred.reasoning)

		parsed = _parse_json_dict(raw_output)
		if parsed is not None:
			return parsed

		return {
			"modified_wod_json": modified_wod_json,
			"goals": goals,
			"raw_plan_json": raw_output,
		}



