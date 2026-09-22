import json

class MathematicalScoringEngine:
    """
    Transparent, evidence-weighted scoring engine with feature attribution.
    Eliminates arbitrary static scores.
    """
    
    DAG_PREREQUISITES = {
        "Machine Learning": ["Python"],
        "Deep Learning": ["Machine Learning", "Python"],
        "PyTorch": ["Deep Learning", "Python"],
        "MLOps": ["Docker", "Machine Learning"],
        "FastAPI": ["Python"]
    }

    def __init__(self, benchmark_path="backend/data/role_benchmarks.json"):
        with open(benchmark_path, "r", encoding="utf-8") as f:
            self.role_benchmarks = json.load(f)

    
    
    def simulate_what_if(self, current_skills: dict, target_role: str, new_skills: list):
        simulated_claims = dict(current_skills)
        for s in new_skills:
            simulated_claims[s] = max(simulated_claims.get(s, 0.0), 0.85)

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

    def calculate_readiness(self, candidate_claims: dict, target_role: str = 'AI_Engineer', code_evidence: dict = None):
        if not code_evidence:
            # Check if fastapi/fastapi sample or claims provide evidence
            code_evidence = {'verified_skills': [s for s, v in candidate_claims.items() if v >= 0.7 and s in ['Python', 'FastAPI']], 'evidence_confidence': 0.65}
        
        eval_res = self.calculate_grounded_score(candidate_claims, code_evidence, target_role)
        return {
            'readiness_score': eval_res['readiness_score'],
            'target_role': target_role,
            'evidence_confidence': eval_res['evidence_confidence'],
            'explainability_attributions': eval_res['explainability_attributions'],
            'confidence_vector': eval_res['confidence_vector']
        }

    def calculate_grounded_score(self, candidate_claims: dict, code_evidence: dict, target_role: str):
        role_weights = self.role_benchmarks.get(target_role, self.role_benchmarks["AI_Engineer"])
        
        verified_skills_from_code = set(code_evidence.get("verified_skills", []))
        confidence_map = {}
        attributions = []

        total_role_weight = sum(role_weights.values())
        weighted_score_sum = 0.0

        for skill, target_weight in role_weights.items():
            claim_val = candidate_claims.get(skill, 0.0)
            code_val = 1.0 if skill in verified_skills_from_code else 0.0

            # Check DAG prerequisite grounding
            prereqs = self.DAG_PREREQUISITES.get(skill, [])
            if prereqs:
                prereqs_met = sum([1 for p in prereqs if (candidate_claims.get(p, 0.0) >= 0.5 or p in verified_skills_from_code)])
                dag_grounding = prereqs_met / len(prereqs)
            else:
                dag_grounding = 1.0

            # Mathematical Confidence Equation
            # 25% Resume Claim + 50% GitHub Ground Truth + 25% DAG Prerequisite Grounding
            if code_val > 0:
                skill_conf = (0.25 * claim_val) + (0.50 * code_val) + (0.25 * dag_grounding)
            else:
                # Agar code evidence nahi hai toh max claim value 0.45 tak downweight ho jayegi
                skill_conf = (0.35 * claim_val) * (0.5 + 0.5 * dag_grounding)

            skill_conf = min(1.0, max(0.0, skill_conf))
            confidence_map[skill] = round(skill_conf, 3)

            # Attribution contribution
            contribution = (skill_conf * target_weight) / total_role_weight
            weighted_score_sum += contribution

            # Generate Explainability Log
            if code_val > 0:
                attributions.append({
                    "skill": skill,
                    "impact": f"+{round(contribution * 100, 1)}%",
                    "reason": f"Deterministic code evidence verified in repository."
                })
            elif claim_val > 0.6 and dag_grounding < 1.0:
                attributions.append({
                    "skill": skill,
                    "impact": f"-{round((target_weight / total_role_weight) * 15, 1)}%",
                    "reason": f"Prerequisite deficit: Lacks verified foundation in {', '.join(prereqs)}."
                })

        final_readiness = round(weighted_score_sum * 100, 1)

        return {
            "target_role": target_role,
            "readiness_score": final_readiness,
            "confidence_vector": confidence_map,
            "explainability_attributions": attributions[:4],
            "evidence_confidence": code_evidence.get("evidence_confidence", 0.0)
        }

if __name__ == "__main__":
    engine = MathematicalScoringEngine()
    sample_claims = {"Python": 1.0, "Machine Learning": 0.8, "PyTorch": 0.9, "MLOps": 0.7}
    sample_evidence = {"verified_skills": ["Python", "FastAPI"], "evidence_confidence": 0.70}
    res = engine.calculate_grounded_score(sample_claims, sample_evidence, "AI_Engineer")
    print(json.dumps(res, indent=2))

ScoringEngine = MathematicalScoringEngine
