# CrossFit WOD Multi-Agent Generator
**Time Limit:** 4 Hours

## 1. Scenario
A new fitness tech company wants to build a "Smart WOD" (Workout of the Day) generator for its app. They need a system that doesn't just create random workouts, but intelligently tailors them to each user's unique needs, including their fitness level, existing injuries, and long-term goals.

## 2. Objective
Your task is to build a prototype for this "Smart WOD" generator. You must create a multi-agent workflow that takes a user's request for a CrossFit-style workout and processes it through a chain of specialized AI agents. The final output should be a complete, safe, and optimized workout plan.

## 3. Core Task
Using a modern AI framework like **DSPy (preferred)**, or an equivalent like LangChain or AutoGen, create a main workflow that orchestrates at least three distinct AI agents.

### User Input
The system should be able to accept a simple user request and a user context object.

* **Example Request:** "I want a 20-minute AMRAP," "Give me a heavy lifting day," or "I want to work on my gymnastics."
* **Example Context:** `{"injury": "right shoulder pain", "goals": ["improve cardio", "build leg strength"]}`

### Agent Requirements
You must design and implement the following agents. In DSPy, each agent's behavior should be defined by a `dspy.Signature`.

#### Agent 1: The 'WOD Architect'
* **Responsibility:** Generates the base workout.
* **Input:** The user's workout request (e.g., "20-minute AMRAP").
* **Output:** A structured workout.
* **Example Output:**
    ```json
    {
      "name": "Rookie's AMRAP",
      "type": "AMRAP 20",
      "movements": [
        {"exercise": "Pull-ups", "reps": 5},
        {"exercise": "Push-ups", "reps": 10},
        {"exercise": "Air Squats", "reps": 15}
      ]
    }
    ```

#### Agent 2: The 'Scaling & Injury Specialist'
* **Responsibility:** Modifies the base WOD for safety and accessibility.
* **Input:** The base WOD from Agent 1 and the user's context (e.g., `{"injury": "right shoulder pain"}`).
* **Tasks:**
    1. **Scaling:** Provide "Scaled" (easier) and "Rx+" (harder) options for each movement.
        * *Example:* For "Pull-ups", Scaled: "Jumping Pull-ups" or "Ring Rows"; Rx+: "Chest-to-Bar Pull-ups".
    2. **Injury Modification:** Check the user's injury against the movements. If a movement is risky (like "Push-ups" with "shoulder pain"), it must provide a safe alternative.
        * *Example:* For "Push-ups", Alt: "Incline Push-ups" or "Dumbbell Bench Press".
* **Output:** The original WOD, annotated with scaling options and injury alternatives.

#### Agent 3: The 'Performance Optimizer'
* **Responsibility:** Provides holistic programming recommendations.
* **Input:** The final, modified WOD from Agent 2 and the user's context (e.g., `{"goals": ["improve cardio"]}`).
* **Tasks:**
    1. Recommend a specific **warm-up** routine for the given movements.
    2. Recommend a specific **cool-down** routine.
    3. Recommend **two "complimentary" accessory workouts** to be done later in the week that support the user's goals.
        * *Example:* If the user's goal is "improve cardio" and the WOD was strength-focused, suggest a running and rowing interval session.
* **Output:** A complete plan including warm-up, the WOD (with scales/alts), cool-down, and future recommendations.

### Final Output
The workflow should produce a single, well-formatted JSON object or markdown text that represents the complete, actionable plan for the user.

## 4. Technical Stack
* **Framework:** **DSPy is preferred.** You should demonstrate the use of `dspy.Signature` to define the agents' inputs/outputs and a `dspy.Module` to define the agentic workflow.
* **Models:** Use any LLM you are comfortable with.

## 5. Deliverables
1. All **Python code** (`.py` files) required to run the project.
2. A `requirements.txt` file listing all dependencies.
3. A `README.md` file that includes:
    * Brief instructions on how to set up and run your project.
    * Your design choices (Why did you structure your agents this way?).
    * An example of the final output from your system.

## 6. Evaluation Criteria
* **Modularity:** Are the agents distinct? Does each agent have a clear, single responsibility (i.e., effective use of `dspy.Signatures`)?
* **Workflow:** Does the data flow logically from one agent to the next? Is the workflow clearly defined in code (i.e., a `dspy.Module`)?
* **Correctness:** Does the final output make sense? Are the scaling options, injury alternatives, and recommendations logical for the domain?
* **Code Quality:** Is the code clean, commented, and runnable?

## Bonus Task (If you have time)
Implement a **"User Intent" agent** that runs first. This agent would take a vague user input (e.g., "I feel tired but want to move") and classify it into a clear, structured request (e.g., `{"type": "Light-duty", "duration": 15, "style": "EMOM"}`) for the 'WOD Architect' to use.