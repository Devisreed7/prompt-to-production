"""
UC-0A — Complaint Classifier
Chennai Municipal Corporation — Civic Grievance Classifier
AI Code Sarathi | Nasscom Prompt-to-Production Workshop

Usage:
    python classifier.py

Input:  data/city-test-files/test_chennai.csv
Output: uc-0a/results_chennai.csv
"""

import csv
import os
import sys

# ─────────────────────────────────────────────
# DEPARTMENT KEYWORD MAP
# ─────────────────────────────────────────────
DEPARTMENT_KEYWORDS = {
    "roads": [
        "pothole", "road", "footpath", "pavement", "traffic",
        "signal", "divider", "tar", "crater", "broken road",
        "speed breaker", "median", "street repair"
    ],
    "water": [
        "water", "pipe", "leak", "supply", "tap", "borewell",
        "no water", "water shortage", "pipeline", "burst pipe",
        "drinking water", "metro water"
    ],
    "sanitation": [
        "garbage", "waste", "trash", "drain", "sewage",
        "stink", "smell", "overflow", "drainage", "clog",
        "dustbin", "litter", "solid waste", "open defecation",
        "dirty", "filth", "blocked drain"
    ],
    "electricity": [
        "light", "electricity", "power", "current", "electric",
        "shock", "wire", "eb ", "street light", "power cut",
        "no power", "blackout", "transformer", "voltage",
        "short circuit", "live wire"
    ],
    "health": [
        "mosquito", "dengue", "malaria", "stagnant", "disease",
        "rats", "pest", "rodent", "vector", "fever", "epidemic",
        "contaminated", "health hazard", "cockroach"
    ],
    "parks": [
        "park", "tree", "garden", "playground", "bench",
        "public space", "fallen tree", "greenery", "shrubs",
        "walking track", "recreation"
    ],
    "encroachment": [
        "encroach", "illegal", "construct", "block", "occupy",
        "hawker", "vendor", "unauthorised", "squatter",
        "footpath blocked", "parking"
    ],
    "noise": [
        "noise", "sound", "loudspeaker", "music", "party",
        "loud", "horn", "disturbance", "late night sound"
    ],
}

# ─────────────────────────────────────────────
# ESCALATION TRIGGER KEYWORDS
# ─────────────────────────────────────────────
ESCALATION_KEYWORDS = [
    "injury", "injured", "hurt", "accident", "bleeding", "blood",
    "child", "children", "minor", "school", "kid", "baby",
    "hospital", "clinic", "medical", "emergency",
    "flood", "waterlog", "waterlogging", "sewage overflow",
    "fire", "explosion", "electric shock", "electrocution",
    "death", "died", "dead", "fatality", "killed", "serious"
]

# ─────────────────────────────────────────────
# CLASSIFICATION LOGIC
# ─────────────────────────────────────────────

def detect_escalation(text: str) -> bool:
    """Return True if any escalation trigger keyword is found."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in ESCALATION_KEYWORDS)


def classify_department(text: str) -> tuple[str, str]:
    """
    Match complaint text to a department.
    Returns (department_code, matched_keyword).
    """
    text_lower = text.lower()
    for dept, keywords in DEPARTMENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return dept, kw
    return "other", ""


def assign_severity(text: str, escalate: bool) -> str:
    """
    Assign severity based on escalation status and scope indicators.
    """
    text_lower = text.lower()

    if escalate:
        return "high"

    # Medium severity indicators
    medium_keywords = [
        "many", "several", "residents", "area", "whole", "entire",
        "days", "weeks", "months", "long time", "repeatedly",
        "damage", "broken", "collapsed", "overflow", "blocked"
    ]
    if any(kw in text_lower for kw in medium_keywords):
        return "medium"

    return "low"


def generate_reason(text: str, dept: str, severity: str,
                    escalate: bool, matched_kw: str) -> str:
    """Generate a one-sentence reason for the classification."""
    esc_note = " Escalated due to safety/injury risk." if escalate else ""
    kw_note = f" Keyword matched: '{matched_kw}'." if matched_kw else ""
    return (
        f"Complaint classified as '{dept}' with '{severity}' severity.{kw_note}{esc_note}"
    )


def classify_complaint(complaint_id: str, complaint_text: str) -> dict:
    """Full classification pipeline for a single complaint."""
    text = complaint_text.strip()
    escalate = detect_escalation(text)
    dept, matched_kw = classify_department(text)
    severity = assign_severity(text, escalate)
    reason = generate_reason(text, dept, severity, escalate, matched_kw)

    return {
        "complaint_id": complaint_id,
        "department": dept,
        "severity": severity,
        "escalate": str(escalate).lower(),
        "reason": reason,
    }


# ─────────────────────────────────────────────
# FILE I/O
# ─────────────────────────────────────────────

def find_input_file() -> str:
    """Locate the input CSV file."""
    candidates = [
        "data/city-test-files/test_chennai.csv",
        "../data/city-test-files/test_chennai.csv",
        "test_chennai.csv",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(
        "Could not find test_chennai.csv. "
        "Please ensure it exists at data/city-test-files/test_chennai.csv"
    )


def read_complaints(filepath: str) -> list[dict]:
    """Read complaints from CSV. Auto-detects id and text columns."""
    complaints = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = [h.lower().strip() for h in reader.fieldnames or []]

        # Detect column names flexibly
        id_col = next(
            (h for h in reader.fieldnames
             if h.lower().strip() in ["complaint_id", "id", "sr_no", "no", "complaint id"]),
            reader.fieldnames[0] if reader.fieldnames else None
        )
        text_col = next(
            (h for h in reader.fieldnames
             if h.lower().strip() in ["complaint", "complaint_text", "text",
                                       "description", "grievance", "details"]),
            reader.fieldnames[1] if reader.fieldnames and len(reader.fieldnames) > 1 else None
        )

        if not id_col or not text_col:
            raise ValueError(
                f"Cannot detect required columns. Found: {reader.fieldnames}"
            )

        print(f"  → ID column   : '{id_col}'")
        print(f"  → Text column : '{text_col}'")

        # Re-read from start
        f.seek(0)
        reader = csv.DictReader(f)
        for row in reader:
            complaints.append({
                "id": row[id_col].strip(),
                "text": row[text_col].strip(),
            })
    return complaints


def write_results(results: list[dict], output_path: str):
    """Write classification results to CSV."""
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    fieldnames = ["complaint_id", "department", "severity", "escalate", "reason"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────

ALLOWED_DEPARTMENTS = {
    "roads", "water", "sanitation", "electricity",
    "health", "parks", "encroachment", "noise", "other"
}
ALLOWED_SEVERITIES = {"low", "medium", "high"}
ALLOWED_ESCALATE = {"true", "false"}


def validate_results(results: list[dict]) -> bool:
    """Validate output quality. Returns True if all checks pass."""
    errors = []
    for i, row in enumerate(results, 1):
        if not row["complaint_id"]:
            errors.append(f"Row {i}: missing complaint_id")
        if row["department"] not in ALLOWED_DEPARTMENTS:
            errors.append(f"Row {i}: invalid department '{row['department']}'")
        if row["severity"] not in ALLOWED_SEVERITIES:
            errors.append(f"Row {i}: invalid severity '{row['severity']}'")
        if row["escalate"] not in ALLOWED_ESCALATE:
            errors.append(f"Row {i}: invalid escalate value '{row['escalate']}'")
        if not row["reason"].strip():
            errors.append(f"Row {i}: empty reason")

    if errors:
        print("\n⚠️  VALIDATION ERRORS:")
        for e in errors:
            print(f"   {e}")
        return False
    return True


# ─────────────────────────────────────────────
# SUMMARY REPORT
# ─────────────────────────────────────────────

def print_summary(results: list[dict]):
    """Print a quick summary of classification results."""
    total = len(results)
    escalated = sum(1 for r in results if r["escalate"] == "true")

    dept_counts = {}
    sev_counts = {"low": 0, "medium": 0, "high": 0}
    for r in results:
        dept_counts[r["department"]] = dept_counts.get(r["department"], 0) + 1
        sev_counts[r["severity"]] = sev_counts.get(r["severity"], 0) + 1

    print("\n" + "=" * 50)
    print("  CLASSIFICATION SUMMARY — Chennai")
    print("=" * 50)
    print(f"  Total complaints processed : {total}")
    print(f"  Escalated (urgent)         : {escalated}")
    print()
    print("  By Department:")
    for dept, count in sorted(dept_counts.items(), key=lambda x: -x[1]):
        print(f"    {dept:<20} {count:>4}")
    print()
    print("  By Severity:")
    for sev in ["high", "medium", "low"]:
        print(f"    {sev:<20} {sev_counts[sev]:>4}")
    print("=" * 50)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print("\n🚀 UC-0A Complaint Classifier — Chennai")
    print("-" * 50)

    # 1. Locate input
    try:
        input_path = find_input_file()
        print(f"✅ Input file  : {input_path}")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)

    # 2. Read complaints
    try:
        complaints = read_complaints(input_path)
        print(f"✅ Complaints loaded : {len(complaints)}")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        sys.exit(1)

    # 3. Classify
    print("\n⏳ Classifying complaints...")
    results = []
    for c in complaints:
        result = classify_complaint(c["id"], c["text"])
        results.append(result)

    # 4. Validate
    print("\n🔍 Validating output...")
    valid = validate_results(results)
    if valid:
        print("✅ All validation checks passed.")
    else:
        print("⚠️  Fix the above errors before submitting.")

    # 5. Write output
    output_path = "uc-0a/results_chennai.csv"
    write_results(results, output_path)
    print(f"\n✅ Results written : {output_path}")

    # 6. Summary
    print_summary(results)
    print("\n✅ Done! Commit results_chennai.csv along with agents.md, skills.md, and classifier.py\n")


if __name__ == "__main__":
    main()
