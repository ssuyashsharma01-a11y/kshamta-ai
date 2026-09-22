from backend.graph_engine import SkillGraph
from backend.scoring import ScoringEngine

graph = SkillGraph()
scoring = ScoringEngine()

# Test candidate: Claims FastAPI, but Python is missing/deficit
candidate = {"FastAPI": 0.8, "Machine Learning": 0.75}
validated = graph.validate_prerequisites(candidate)
print("\n--- 1. Validated Skills with Prerequisite Penalties ---")
print(validated)

result = scoring.calculate_readiness(validated, "AI_Engineer")
print("\n--- 2. Base Readiness Score ---")
print(f"Readiness Score: {result['readiness_score']}%")

sim = scoring.simulate_what_if(validated, "AI_Engineer", ["Docker", "MLOps"])
print("\n--- 3. What-If Simulator (+Docker, +MLOps) ---")
print(sim)
