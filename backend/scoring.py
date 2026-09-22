import json
import os

class ScoringEngine:
    def __init__(self, benchmarks_path: str = None):
        if benchmarks_path is None:
            benchmarks_path = os.path.join(os.path.dirname(__file__), "data", "role_benchmarks.json")
        self.benchmarks_path = benchmarks_path
        self.benchmarks = self._load_benchmarks()

    def _load_benchmarks(self):
        with open(self.benchmarks_path, "r") as f:
            return json.load(f)

    def calculate_readiness(self, validated_skills: dict, target_role: str):
        if target_role not in self.benchmarks:
            target_role = "AI_Engineer"

        role_info = self.benchmarks[target_role]
        requirements = role_info["required_skills"]
        total_weight = sum(requirements.values())

        earned_score = 0.0
        missing_skills = []
        radar_data = []

        for skill, weight in requirements.items():
            candidate_entry = validated_skills.get(skill, 0.0)
            
            # Robust unwrap: supports both raw float and dict validation output
            if isinstance(candidate_entry, dict):
                score = float(candidate_entry.get("confidence", 0.0))
            else:
                score = float(candidate_entry) if candidate_entry is not None else 0.0
            
            earned_score += score * weight
            radar_data.append({
                "skill": skill,
                "candidate_score": round(score * 100, 1),
                "benchmark_score": round(weight * 100, 1)
            })

            if score < 0.6:
                gap = round(weight - score, 2)
                missing_skills.append({
                    "skill": skill,
                    "current": round(score * 100, 1),
                    "required": round(weight * 100, 1),
                    "gap_impact": gap
                })

        missing_skills.sort(key=lambda x: x["gap_impact"], reverse=True)
        readiness_pct = round((earned_score / total_weight) * 100, 1) if total_weight > 0 else 0.0

        return {
            "role": target_role,
            "readiness_score": readiness_pct,
            "radar_data": radar_data,
            "critical_gaps": missing_skills
        }

    def simulate_what_if(self, validated_skills: dict, target_role: str, new_skills: list):
        base_res = self.calculate_readiness(validated_skills, target_role)
        
        simulated_skills = {}
        for k, v in validated_skills.items():
            if isinstance(v, dict):
                simulated_skills[k] = v.get("confidence", 0.0)
            else:
                simulated_skills[k] = v

        for s in new_skills:
            simulated_skills[s] = 0.85

        sim_res = self.calculate_readiness(simulated_skills, target_role)
        delta = round(sim_res["readiness_score"] - base_res["readiness_score"], 1)

        return {
            "current_score": base_res["readiness_score"],
            "projected_score": sim_res["readiness_score"],
            "delta_jump": delta,
            "skills_added": new_skills
        }
