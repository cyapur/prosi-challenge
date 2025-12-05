# Setup and project run
1) Python 3.12+ recommended.
2) Install dependencies with `pip install -r requirements.txt` (exported from poetry including transitive dependencies)
3) Create a .env file and set your `OPENAI_API_KEY`
4) Run `python main.py`

To change the inputs (request, goals and/or injury), edit `main.py` and modify
`USER_REQUEST` and `USER_CONTEXT`, these variables stand in for user-provided
inputs. You can also toggle `DEFAULT_DEBUG` to `True` if you want to see more
details about the flow (inputs, outputs, and reasoning of each agent).


# Design Choices
- **JSON as the interface between agents**: All agents communicate via JSON rather than free-form text. CrossFit-style workouts are naturally structured (name, type, movements, reps/time, etc.), so using JSON makes the data flow explicit and machine-checkable. This also makes each agent easier to test in isolation: I can feed in a JSON object and assert the shape of the JSON that comes out.
- **Best-effort JSON parsing instead of a full schema layer**: For this 4-hour prototype I skipped Pydantic contracts and used lightweight JSON parsing with safe fallbacks. In a real product I’d promote this into a proper data contract (e.g. Pydantic models + stricter validation), but here the goal was to show the agentic structure and DSPy usage rather than spend most of the time on schema validation.  Also, in theory I could wrap the agents with `dspy.Refine` and a reward function that checks for valid JSON, but that implies multiple high-temperature rollouts and extra complexity. For this task, a single low-temperature call plus a small `_parse_json_dict` helper is a simpler and more predictable way to keep the outputs usable without spending most of the time on constraint infrastructure.
- **dspy.Predict for simple, single-step generations**: I use `dspy.Predict` for the `UserIntentAgent` and the `WODArchitect`. Both are essentially “one-shot mappings”. They don’t need multi-step reasoning, just a clear signature and deterministic-ish output, so Predict(Signature) is the simplest and clearest primitive.
- **dspy.ChainOfThought where reasoning and tradeoffs matter**: I use `dspy.ChainOfThought` for the `ScalingInjurySpecialist` and the `PerformanceOptimizer`. These agents have to reason about tradeoffs (how to scale movements, how to respect injuries, how to align warm-up/cool-down/accessories with goals). Letting the model produce a rationale before the final JSON output tends to yield more consistent and domain-sensible decisions, while I still enforce structure on the Python side.
- **dspy.Prediction only at the top level**: The final `SmartWODWorkflow` returns a `dspy.Prediction` with four fields: `intent`, `base_wod`, `annotated_wod`, and `plan`. Between agents I just pass plain Python dicts (parsed JSON), which keeps each module simple and focused. Wrapping the final plan into a `dspy.Prediction` class makes it easy to inspect or log intermediate artifacts for future implementations.
- **Low temperature to reduce JSON errors**: I use `temperature=0.0` for the `dspy.LM()` configuration. In practice, when I increased the temperature, JSON parsing failures became significantly more frequent, so keeping it at zero helped the agents stick to the expected output format.

# Example of final output
Input used for this final output:
```python
USER_REQUEST: str = "I want to train my endurance and improve my running"
USER_CONTEXT: dict = {
	"injury": "back pain",
	"goals": ["improve endurance"],
}
```

Final output:
```json
{
  "warmup": {
    "duration": "10 minutes",
    "exercises": [
      {
        "exercise": "Dynamic Stretching",
        "time": "5 minutes"
      },
      {
        "exercise": "Light Jog",
        "time": "5 minutes"
      }
    ]
  },
  "wod": {
    "name": "30-Minute Endurance Run",
    "type": "Endurance",
    "movements": [
      {
        "exercise": "Running",
        "time": "30 minutes",
        "scaled": {
          "exercise": "Walking",
          "time": "20 minutes"
        },
        "rx_plus": {
          "exercise": "Running",
          "time": "30 minutes",
          "intensity": "increased pace"
        },
        "injury_alts": {
          "exercise": "Cycling",
          "time": "30 minutes"
        }
      }
    ]
  },
  "cooldown": {
    "duration": "5 minutes",
    "exercises": [
      {
        "exercise": "Walking",
        "time": "3 minutes"
      },
      {
        "exercise": "Static Stretching",
        "time": "2 minutes"
      }
    ]
  },
  "accessories": [
    {
      "name": "Interval Cycling",
      "duration": "20 minutes",
      "details": "Alternate between 1 minute of high intensity and 2 minutes of low intensity."
    },
    {
      "name": "Bodyweight Circuit",
      "duration": "15 minutes",
      "exercises": [
        {
          "exercise": "Burpees",
          "reps": 10
        },
        {
          "exercise": "Jump Squats",
          "reps": 10
        },
        {
          "exercise": "Mountain Climbers",
          "time": "30 seconds"
        }
      ]
    }
  ]
}
```


# Additional comments

## Overall workflow: What's the project workflow?
- At runtime, `main.py` loads environment variables and configures DSPy with an OpenAI chat model, then instantiates `SmartWODWorkflow` from `workflow.py` with a simple `request` string and a `context` dict containing the user’s injury and goals. `SmartWODWorkflow` (a `dspy.Module`) calls, in order, four agents defined in `functions.py`: the User Intent Agent normalizes the raw request into a structured intent, the WOD Architect generates a base WOD, the Scaling & Injury Specialist annotates each movement with scaling/Rx+/injury‑safe options, and the Performance Optimizer adds warm‑up, cool‑down, and accessory sessions. Those intermediate results are wrapped in a `dspy.Prediction`, and `main.py` extracts the final `plan` dict and pretty‑prints it as JSON.


## Project Structure
- `functions.py`: `dspy.Signature`s and all four agents (User Intent Agent, WOD Architect, Scaling & Injury Specialist, Performance Optimizer)
- `workflow.py`: `SmartWODWorkflow` (`dspy.Module`) composing the agents into a single pipeline and returning a `dspy.Prediction` (`intent`, `base_wod`, `annotated_wod`, `plan`)
- `main.py`: simple entrypoint that configures DSPy, sets a default request/context, invokes the workflow, and prints the final JSON `plan`
- `requirements.txt`


## Future improvements discussion

### Strength skill ladder
- Defininng a strength skill ladder for each movement pattern, where move down when the athlete can’t perform the Rx, and move up for Rx+, and feeding this into the `ScalingInjurySpecialist` would significantly reduce the potential errors and increase the accuracy of the agent answers when assessing what exercise to provide as scaling/Rx+. For example:
> Ladder: Ring row -> Jumping pull-up -> Kipping pull-up -> Strict pull-up -> Butterfly pull-up -> C2B -> Bar muscle-up -> Ring muscle-up
>Given an Rx movement in the WOD (e.g. Strict Pull-up), the system could:
>- Move **down** the ladder (e.g. Kipping pull-up) if scalling is needed.
>- Move **up** the ladder (e.g. Butterfly pull-up) if an Rx+ option is needed


### Injury branch
Right now, the prototype only handles injuries in a coarse way. A more complete version would:
- Map **injury descriptions** to body regions (e.g. “shoulder pain” → `upper`, “knee pain” → `lower`).
- Map **each exercise** to the body regions it involves, e.g.:
  - Thruster -> `{upper, lower, arms, shoulders, legs, back}`
  - Back Squat -> `{lower, legs, back}`
- Define **injury-safe substitution pools** per region. For example, for an upper-body injury you might replace Thrusters with Front Squats or Back Squats (keep leg/trunk stimulus, avoid overhead pressing).

At runtime, if a movement’s `body_parts` intersect an injured region, the system would either:
- Move **down the skill ladder** for that pattern (if a safer movement exists), or
- Swap to an **alternative movement** from the appropriate substitution pool (e.g. Thruster -> Front Squat) when the entire pattern ladder is contraindicated.

Whether this extra complexity is worth it is a product decision: many physicians will recommend full rest for acute injuries, but in my experience most CrossFit members train without significant injuries, and if they have minor issues, they usually will not even scale until they have an acute injury and a physician sends them to full rest.

## Technical (future) improvements:
- **Stronger data contracts**: Add a WOD `pydantic` dataclass for robust JSON parsing and schema validation between agents.
- **Retry on contract violations**: Add lightweight retry logic so that if an agent’s response doesn’t match the expected JSON/output contract, the system can automatically re‑prompt the model with a clarification and try again before falling back to best‑effort parsing.
- **Evaluation harness**: Design an evaluation setup using a small “golden dataset" (e.g., ~100 example requests + contexts with final soft WOD expected) to periodically assess the agents’ behavior and track regressions/improvements over time.
- **Modularity & observability**: As the codebase grows, split agents, signatures, and workflows into separate modules, and add structured logging / per‑agent traces for inputs, outputs, and model rationales.

