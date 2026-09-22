import networkx as nx

class SkillGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_skill_dag()

    def _build_skill_dag(self):
        # Directed Dependencies: Prerequisite -> Advanced Skill
        self.graph.add_edge("Python", "FastAPI")
        self.graph.add_edge("Python", "Machine Learning")
        self.graph.add_edge("Machine Learning", "Deep Learning")
        self.graph.add_edge("Deep Learning", "PyTorch")
        self.graph.add_edge("Machine Learning", "MLOps")
        self.graph.add_edge("Docker", "MLOps")
        self.graph.add_edge("Docker", "Cloud/AWS")

    def validate_prerequisites(self, detected_skills: dict):
        validated_report = {}

        for skill, score in detected_skills.items():
            # Agar candidate ne actively claim hi nahi kiya (score < 0.35), to penalty mat do
            if score < 0.35:
                validated_report[skill] = {"confidence": score, "status": "baseline"}
                continue

            prereqs = list(self.graph.predecessors(skill)) if self.graph.has_node(skill) else []
            penalized = False
            missing_cause = None

            for p in prereqs:
                parent_score = detected_skills.get(p, 0.0)
                # Agar parent prerequisite missing ya negligible hai
                if parent_score < 0.35:
                    penalized = True
                    missing_cause = p
                    break

            if penalized:
                discounted = round(score * 0.5, 2)
                validated_report[skill] = {
                    "confidence": discounted,
                    "status": "penalized",
                    "missing_prereq": missing_cause,
                    "raw_score": score
                }
            else:
                validated_report[skill] = {
                    "confidence": score,
                    "status": "validated"
                }

        return validated_report
