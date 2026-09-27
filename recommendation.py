"""
recommendation.py - Rule-based recommendation layer.

Algorithm: forward chaining over a propositional Horn-clause knowledge base
(course Lecture 4, Knowledge-Based Systems).

  1. The fuzzy result is turned into crisp FACTS
     (e.g. level_high, short_sleep, heavy_workload).
  2. Forward chaining repeatedly fires every rule whose premises are all
     known facts and adds its conclusion, until nothing new can be derived.
  3. Conclusions that start with "act_" are recommended actions.
     The order in which rules fired is kept as an inference TRACE so the
     reasoning can be shown step by step in the app.

The advice is general well-being advice for students, NOT medical advice.
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# 1. From fuzzy result to facts
# ---------------------------------------------------------------------------
# A risk factor becomes a fact when its fuzzy membership is >= 0.5,
# i.e. the value is at least as much "risk" as "not risk" (alpha-cut at the
# crossover point of the Ruspini partition).  [DESIGN ASSUMPTION]
FACT_ALPHA_CUT = 0.5

FACT_FROM_RISK = {
    "sleep_hours": "short_sleep",            # mu(sleep is LOW)
    "outstanding_assignments": "heavy_workload",  # mu(assignments is MANY)
    "screen_time_hours": "high_screen_time",  # mu(screen is HIGH)
    "meals_per_day": "irregular_meals",       # mu(meals is LOW)
}


def facts_from_fuzzy(fatigue_level: str, risk_degrees: dict) -> set:
    """Build the initial fact base."""
    facts = {f"level_{fatigue_level.lower()}"}
    for var, fact in FACT_FROM_RISK.items():
        if risk_degrees.get(var, 0.0) >= FACT_ALPHA_CUT:
            facts.add(fact)
    return facts


# ---------------------------------------------------------------------------
# 2. Knowledge base (Horn clauses: premises -> conclusion)  [DESIGN ASSUMPTION]
# ---------------------------------------------------------------------------
KB_RULES = [
    # Intermediate conclusions (show multi-step chaining)
    {"id": "K1", "if": ["level_moderate"], "then": "elevated_fatigue"},
    {"id": "K2", "if": ["level_high"], "then": "elevated_fatigue"},
    {"id": "K3", "if": ["level_high", "short_sleep", "heavy_workload"], "then": "multiple_risk_factors"},
    {"id": "K4", "if": ["level_high", "high_screen_time", "irregular_meals"], "then": "multiple_risk_factors"},

    # Actions
    {"id": "K5", "if": ["level_low"], "then": "act_maintain_routine"},
    {"id": "K6", "if": ["level_moderate"], "then": "act_short_rest"},
    {"id": "K7", "if": ["elevated_fatigue", "high_screen_time"], "then": "act_reduce_non_essential"},
    {"id": "K8", "if": ["elevated_fatigue", "heavy_workload"], "then": "act_prioritize_urgent"},
    {"id": "K9", "if": ["level_high"], "then": "act_recovery_break"},
    {"id": "K10", "if": ["level_high", "heavy_workload"], "then": "act_deadline_extension"},
    {"id": "K11", "if": ["elevated_fatigue", "short_sleep"], "then": "act_protect_sleep"},
    {"id": "K12", "if": ["elevated_fatigue", "irregular_meals"], "then": "act_regular_meals"},
    {"id": "K13", "if": ["multiple_risk_factors"], "then": "act_seek_support"},
]

ACTION_TEXT = {
    "act_maintain_routine": "Maintain your current routine - your reported habits look balanced.",
    "act_short_rest": "Take a short rest between study sessions (e.g. a few minutes away from the screen every hour).",
    "act_reduce_non_essential": "Reduce non-essential activities, especially entertainment screen time, for the next few days.",
    "act_prioritize_urgent": "Prioritize urgent assignments: list them by deadline and work on the closest ones first.",
    "act_recovery_break": "Plan a longer recovery break today (a proper rest block, not only a short pause).",
    "act_deadline_extension": "Consider asking the lecturer for a deadline extension if the workload is not manageable.",
    "act_protect_sleep": "Protect your sleep: aim to get back to a regular sleep schedule.",
    "act_regular_meals": "Try to eat at regular times instead of skipping meals.",
    "act_seek_support": "If this pattern continues for several weeks, talk to someone you trust, your academic advisor, or the campus counseling service.",
}

# Display order of actions (most general first)
ACTION_ORDER = list(ACTION_TEXT.keys())


# ---------------------------------------------------------------------------
# 3. Forward chaining
# ---------------------------------------------------------------------------
@dataclass
class ChainingResult:
    initial_facts: list
    final_facts: list
    trace: list          # [{iteration, rule, premises, derived}]
    actions: list        # [(action_id, text)]


def forward_chain(initial_facts: set, rules: list = KB_RULES) -> ChainingResult:
    """Data-driven inference: fire rules until no new fact is added.

    Each iteration checks every rule against the facts known at the START of
    that iteration, then adds all new conclusions at once. This makes the
    chaining depth visible (e.g. K2 derives elevated_fatigue in iteration 1,
    which then lets K11 fire in iteration 2).
    """
    facts = set(initial_facts)
    trace = []
    iteration = 0
    while True:
        iteration += 1
        new_facts = []
        for rule in rules:
            if rule["then"] in facts or rule["then"] in new_facts:
                continue                                  # already known
            if all(p in facts for p in rule["if"]):       # all premises known
                new_facts.append(rule["then"])
                trace.append({
                    "iteration": iteration,
                    "rule": rule["id"],
                    "premises": " AND ".join(rule["if"]),
                    "derived": rule["then"],
                })
        if not new_facts:                                 # fixed point reached
            break
        facts.update(new_facts)
    actions = [(a, ACTION_TEXT[a]) for a in ACTION_ORDER if a in facts]
    return ChainingResult(
        initial_facts=sorted(initial_facts),
        final_facts=sorted(facts),
        trace=trace,
        actions=actions,
    )


def recommend(fatigue_level: str, risk_degrees: dict) -> ChainingResult:
    """Public entry point used by the app."""
    return forward_chain(facts_from_fuzzy(fatigue_level, risk_degrees))


def main_contributing_factors(risk_degrees: dict, labels: dict | None = None) -> list:
    """Risk factors sorted by membership degree (only those > 0)."""
    names = labels or {
        "sleep_hours": "Short sleep",
        "outstanding_assignments": "Many outstanding assignments",
        "screen_time_hours": "High non-academic screen time",
        "meals_per_day": "Low meal frequency",
    }
    items = [(names[k], v) for k, v in risk_degrees.items() if v > 0]
    return sorted(items, key=lambda kv: kv[1], reverse=True)


if __name__ == "__main__":
    res = recommend("HIGH", {"sleep_hours": 1.0, "outstanding_assignments": 0.0,
                             "screen_time_hours": 1.0, "meals_per_day": 0.5})
    print("Initial facts:", res.initial_facts)
    for step in res.trace:
        print(step)
    for a, t in res.actions:
        print("-", t)
