import json
import streamlit as st

# ---------- Default rules (EXACTLY as given in the lab) ----------
DEFAULT_RULES_JSON = """[
  {
    "name": "Top merit candidate",
    "priority": 100,
    "conditions": [
      ["cga", ">=", 3.7],
      ["co_curricular_score", ">=", 80],
      ["family_income", "<=", 8000],
      ["disciplinary_actions", "==", 0]
    ],
    "action": {
      "decision": "AWARD_FULL",
      "reason": "Excellent academic & co-curricular performance, with acceptable need"
    }
  },
  {
    "name": "Good candidate - partial scholarship",
    "priority": 80,
    "conditions": [
      ["cga", ">=", 3.3],
      ["co_curricular_score", ">=", 60],
      ["family_income", "<=", 12000],
      ["disciplinary_actions", "<=", 1]
    ],
    "action": {
      "decision": "AWARD_PARTIAL",
      "reason": "Good academic & involvement record with moderate need"
    }
  },
  {
    "name": "Need-based review",
    "priority": 70,
    "conditions": [
      ["cga", ">=", 2.5],
      ["family_income", "<=", 4000]
    ],
    "action": {
      "decision": "REVIEW",
      "reason": "High need but borderline academic score"
    }
  },
  {
    "name": "Low CGPA - not eligible",
    "priority": 95,
    "conditions": [
      ["cga", "<=", 2.5]
    ],
    "action": {
      "decision": "REJECT",
      "reason": "CGPA below minimum scholarship requirement"
    }
  },
  {
    "name": "Serious disciplinary record",
    "priority": 90,
    "conditions": [
      ["disciplinary_actions", ">=", 2]
    ],
    "action": {
      "decision": "REJECT",
      "reason": "Too many disciplinary records"
    }
  }
]"""


# ---------- Comparison operators ----------
def compare(left, op, right):
    if op == ">=": return left >= right
    if op == "<=": return left <= right
    if op == ">":  return left > right
    if op == "<":  return left < right
    if op == "==": return left == right
    if op == "!=": return left != right
    raise ValueError(f"Unsupported operator: {op}")


def evaluate_rules(rules, facts):
    """Return (decision, reason, rule_name) for the highest-priority matching rule."""
    matches = []
    for rule in rules:
        try:
            ok = all(compare(facts[field], op, value)
                     for field, op, value in rule["conditions"])
        except KeyError as e:
            st.warning(f"Rule '{rule.get('name')}' references unknown field: {e}")
            ok = False
        if ok:
            matches.append(rule)

    if not matches:
        return "NO_MATCH", "No rule matched the applicant's facts.", None

    best = max(matches, key=lambda r: r.get("priority", 0))
    return (best["action"]["decision"],
            best["action"]["reason"],
            best["name"])


# ---------- UI ----------
st.set_page_config(page_title="Scholarship Advisory System", page_icon="🎓")
st.title("🎓 Scholarship Advisory Rule-Based System")
st.caption("BSD3513 Lab 3 — Knowledge Representation System")

# Sidebar: applicant facts
st.sidebar.header("Applicant Facts")
cga = st.sidebar.number_input("CGPA", 0.0, 4.0, 3.5, 0.01)
income = st.sidebar.number_input("Monthly Family Income (RM)", 0, 50000, 7000, 100)
co_curricular = st.sidebar.slider("Co-curricular score", 0, 100, 70)
service_hours = st.sidebar.number_input("Community service hours", 0, 500, 20)
semester = st.sidebar.number_input("Current semester", 1, 12, 4)
disciplinary = st.sidebar.number_input("Disciplinary actions", 0, 10, 0)

facts = {
    "cga": cga,                        # NOTE: paper uses "cga", not "cgpa"
    "cgpa": cga,                       # alias for convenience
    "family_income": income,
    "co_curricular_score": co_curricular,
    "community_service_hours": service_hours,
    "semester": semester,
    "disciplinary_actions": disciplinary,
}

# Rules editor
st.subheader("Rules (JSON editor)")
rules_text = st.text_area("Edit rules below:", DEFAULT_RULES_JSON, height=400)

rules = []
parse_error = None
try:
    rules = json.loads(rules_text)
    if not isinstance(rules, list):
        raise ValueError("Top-level JSON must be a list of rule objects.")
except json.JSONDecodeError as e:
    parse_error = f"JSON parse error: {e}"
except ValueError as e:
    parse_error = str(e)

# Evaluate
st.subheader("Decision")
if parse_error:
    st.error(parse_error)
else:
    decision, reason, rule_name = evaluate_rules(rules, facts)

    color = {"AWARD_FULL": "green",
             "AWARD_PARTIAL": "blue",
             "REVIEW": "orange",
             "REJECT": "red",
             "NO_MATCH": "gray"}.get(decision, "gray")

    st.markdown(f"### Decision: :{color}[**{decision}**]")
    if rule_name:
        st.write(f"**Matched rule:** {rule_name}")
    st.write(f"**Reason:** {reason}")

    with st.expander("Applicant facts used"):
        st.json(facts)

    with st.expander("All matching rules"):
        ms = [r["name"] for r in rules
              if all(compare(facts.get(f), o, v) for f, o, v in r["conditions"])]
        st.write(ms if ms else "No matching rules")