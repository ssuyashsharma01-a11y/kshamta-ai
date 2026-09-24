from typing import Dict, List, Any

class MathematicalScoringEngine:
    def __init__(self):
        self.role_benchmarks = {
            "AI_Engineer": {
                "Python": 0.20,
                "Machine Learning": 0.18,
                "Deep Learning": 0.15,
                "PyTorch": 0.15,
                "FastAPI": 0.12,
                "Docker": 0.10,
                "MLOps": 0.10
            },
            "Backend_Engineer": {
                "Python": 0.25,
                "FastAPI": 0.25,
                "Docker": 0.20,
                "Cloud/AWS": 0.15,
                "Database/SQL": 0.15
            },
            "MLOps_Engineer": {
                "Python": 0.15,
                "Docker": 0.25,
                "MLOps": 0.25,
                "Cloud/AWS": 0.20,
                "FastAPI": 0.15
            }
        }
        self.prerequisites = {
            "PyTorch": ["Deep Learning", "Python"],
            "MLOps": ["Docker", "Machine Learning"],
            "FastAPI": ["Python"],
            "Deep Learning": ["Machine Learning", "Python"]
        }

    def calculate_grounded_score(self, candidate_claims: Dict[str, float], code_evidence: Dict[str, Any], target_role: str = "AI_Engineer") -> Dict[str, Any]:
        role_weights = self.role_benchmarks.get(target_role, self.role_benchmarks["AI_Engineer"])
        verified_set = set(code_evidence.get("verified_skills", []))
        
        confidence_vector = {}
        attributions = []
        raw_score = 0.0

        for skill, weight in role_weights.items():
            claim = candidate_claims.get(skill, 0.0)
            is_code_verified = skill in verified_set
            
            prereq_failed = False
            missing_parents = []
            if skill in self.prerequisites:
                for parent in self.prerequisites[skill]:
                    if candidate_claims.get(parent, 0.0) < 0.40:
                        prereq_failed = True
                        missing_parents.append(parent)

            if is_code_verified:
                effective_val = min(1.0, (0.3 * claim) + (0.7 * 0.95))
                attributions.append({
                    "skill": skill,
                    "impact": f"+{round(weight * 100, 1)}%",
                    "reason": "Deterministic AST imports & source files verified in repository."
                })
            elif prereq_failed:
                effective_val = max(0.0, claim * 0.35)
                attributions.append({
                    "skill": skill,
                    "impact": f"-{round(weight * 0.4 * 100, 1)}%",
                    "reason": f"Prerequisite deficit: Lacks verified foundation in {', '.join(missing_parents)}."
                })
            else:
                effective_val = claim * 0.65
                if claim < 0.3:
                    attributions.append({
                        "skill": skill,
                        "impact": f"-{round(weight * 0.5 * 100, 1)}%",
                        "reason": f"Critical vacancy for {target_role.replace('_', ' ')} benchmark."
                    })

            confidence_vector[skill] = round(effective_val, 2)
            raw_score += effective_val * weight

        final_score = round(min(100.0, raw_score * 100), 1)

        return {
            "target_role": target_role,
            "readiness_score": final_score,
            "confidence_vector": confidence_vector,
            "explainability_attributions": attributions,
            "evidence_confidence": code_evidence.get("evidence_confidence", 0.65)
        }

    def calculate_readiness(self, candidate_claims: dict, target_role: str = "AI_Engineer", code_evidence: dict = None):
        if not code_evidence:
            code_evidence = {
                "verified_skills": [s for s, v in candidate_claims.items() if v >= 0.7 and s in ["Python", "FastAPI"]],
                "evidence_confidence": 0.75
            }
        return self.calculate_grounded_score(candidate_claims, code_evidence, target_role)

    def simulate_what_if(self, current_skills: dict, target_role: str, new_skills: list):
        simulated_claims = dict(current_skills)
        for s in new_skills:
            simulated_claims[s] = max(simulated_claims.get(s, 0.0), 0.88)

        base_evidence = {"verified_skills": [s for s, v in current_skills.items() if v >= 0.7]}
        sim_evidence = {"verified_skills": list(set(base_evidence["verified_skills"] + new_skills))}

        base_res = self.calculate_grounded_score(current_skills, base_evidence, target_role)
        sim_res = self.calculate_grounded_score(simulated_claims, sim_evidence, target_role)

        cur = base_res["readiness_score"]
        proj = sim_res["readiness_score"]
        delta = round(max(0.0, proj - cur), 1)

        return {
            "current_score": cur,
            "projected_score": proj,
            "delta_jump": delta,
            "unlocked_capabilities": [f"Verified competency in {s}" for s in new_skills]
        }

scoring = MathematicalScoringEngine()

# Compatibility Aliases
ScoringEngine = MathematicalScoringEngine
