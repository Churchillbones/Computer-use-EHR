"""
Session Review Tool

Load and analyze saved sessions to identify:
- What worked well
- What failed and why
- User corrections (learning opportunities)
- Suggested prompt improvements

Usage:
    python -m src.review_session                    # Review latest session
    python -m src.review_session sessions/session_20251126_123456.json  # Review specific session
    python -m src.review_session --all              # Summary of all sessions
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

SESSIONS_DIR = Path(__file__).parent.parent / "sessions"


def load_session(session_file: Path) -> dict:
    """Load a session from JSON file."""
    with open(session_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_latest_session() -> Path | None:
    """Get the most recent session file."""
    if not SESSIONS_DIR.exists():
        return None
    
    sessions = list(SESSIONS_DIR.glob("session_*.json"))
    if not sessions:
        return None
    
    return max(sessions, key=lambda p: p.stat().st_mtime)


def analyze_session(session: dict) -> dict:
    """Analyze a session for learning insights."""
    analysis = {
        "session_id": session.get("session_id"),
        "duration": None,
        "total_interactions": session["summary"]["total_interactions"],
        "success_rate": 0,
        "corrections": [],
        "failures": [],
        "successful_patterns": [],
        "coordinate_corrections": [],
        "suggested_improvements": []
    }
    
    # Calculate duration
    if session.get("started_at") and session.get("ended_at"):
        start = datetime.fromisoformat(session["started_at"])
        end = datetime.fromisoformat(session["ended_at"])
        analysis["duration"] = str(end - start)
    
    # Calculate success rate
    total = session["summary"]["total_interactions"]
    if total > 0:
        success = session["summary"]["successful_actions"]
        analysis["success_rate"] = round(success / total * 100, 1)
    
    # Analyze interactions
    for interaction in session.get("interactions", []):
        user_input = interaction.get("user_input", "")
        
        # Track corrections
        if interaction.get("user_correction"):
            analysis["corrections"].append({
                "user_asked": user_input,
                "gpt5_proposed": interaction.get("action_proposed"),
                "user_correction": interaction.get("user_correction")
            })
        
        # Track failures
        if interaction.get("action_success") is False:
            analysis["failures"].append({
                "user_asked": user_input,
                "action_attempted": interaction.get("action_executed"),
                "error": interaction.get("error") or interaction.get("result")
            })
        
        # Track successful patterns
        if interaction.get("action_success") is True:
            action = interaction.get("action_executed") or interaction.get("action_proposed")
            if action and action.get("action") not in ["describe", "wait"]:
                analysis["successful_patterns"].append({
                    "user_asked": user_input,
                    "action": action
                })
        
        # Track coordinate adjustments (user skipped or corrected)
        if interaction.get("user_skipped") or interaction.get("user_correction"):
            proposed = interaction.get("action_proposed", {})
            if proposed.get("x") and proposed.get("y"):
                analysis["coordinate_corrections"].append({
                    "element": user_input,
                    "proposed_coords": (proposed.get("x"), proposed.get("y")),
                    "correction_note": interaction.get("user_correction")
                })
    
    # Generate improvement suggestions
    if analysis["corrections"]:
        analysis["suggested_improvements"].append(
            f"Found {len(analysis['corrections'])} user corrections - review for prompt updates"
        )
    
    if analysis["coordinate_corrections"]:
        analysis["suggested_improvements"].append(
            "Coordinate accuracy issues detected - consider updating UI location hints in system prompt"
        )
    
    if analysis["success_rate"] < 70:
        analysis["suggested_improvements"].append(
            "Low success rate - review failures for common patterns"
        )
    
    return analysis


def print_session_review(session: dict, analysis: dict):
    """Print a formatted session review."""
    print("\n" + "="*70)
    print(f"📊 Session Review: {session.get('session_id')}")
    print("="*70)
    
    print(f"\n📅 Started: {session.get('started_at')}")
    print(f"⏱️  Duration: {analysis.get('duration', 'Unknown')}")
    print(f"📈 Success Rate: {analysis['success_rate']}%")
    print(f"🔢 Total Interactions: {analysis['total_interactions']}")
    print(f"✅ Successful: {session['summary']['successful_actions']}")
    print(f"❌ Failed: {session['summary']['failed_actions']}")
    print(f"📝 User Corrections: {session['summary']['user_corrections']}")
    
    if analysis["corrections"]:
        print("\n" + "-"*70)
        print("📝 USER CORRECTIONS (Learning Opportunities)")
        print("-"*70)
        for i, corr in enumerate(analysis["corrections"], 1):
            print(f"\n  {i}. User asked: \"{corr['user_asked']}\"")
            if corr.get("gpt5_proposed"):
                proposed = corr["gpt5_proposed"]
                print(f"     GPT-5 proposed: {proposed.get('action')} at ({proposed.get('x')}, {proposed.get('y')})")
            print(f"     User said: \"{corr['user_correction']}\"")
    
    if analysis["failures"]:
        print("\n" + "-"*70)
        print("❌ FAILURES")
        print("-"*70)
        for i, fail in enumerate(analysis["failures"], 1):
            print(f"\n  {i}. User asked: \"{fail['user_asked']}\"")
            print(f"     Error: {fail['error']}")
    
    if analysis["successful_patterns"]:
        print("\n" + "-"*70)
        print("✅ SUCCESSFUL PATTERNS")
        print("-"*70)
        for i, pattern in enumerate(analysis["successful_patterns"][:10], 1):  # Show first 10
            action = pattern["action"]
            coords = f"({action.get('x')}, {action.get('y')})" if action.get('x') else ""
            print(f"  {i}. \"{pattern['user_asked']}\" → {action.get('action')} {coords}")
    
    if analysis["suggested_improvements"]:
        print("\n" + "-"*70)
        print("💡 SUGGESTED IMPROVEMENTS")
        print("-"*70)
        for suggestion in analysis["suggested_improvements"]:
            print(f"  • {suggestion}")
    
    print("\n" + "="*70)


def export_learnings(analysis: dict, output_file: Path):
    """Export learnings to JSON for LLM consumption."""
    learnings = {
        "session_id": analysis["session_id"],
        "exported_at": datetime.now().isoformat(),
        "success_rate": analysis["success_rate"],
        "coordinate_mappings": [],
        "user_corrections": analysis["corrections"],
        "successful_patterns": analysis["successful_patterns"],
        "prompt_update_suggestions": []
    }
    
    # Extract coordinate mappings from successful patterns
    for pattern in analysis["successful_patterns"]:
        action = pattern["action"]
        if action.get("x") and action.get("y"):
            learnings["coordinate_mappings"].append({
                "element_description": pattern["user_asked"],
                "coordinates": {"x": action["x"], "y": action["y"]},
                "action_type": action.get("action")
            })
    
    # Generate prompt update suggestions
    if analysis["coordinate_corrections"]:
        for corr in analysis["coordinate_corrections"]:
            learnings["prompt_update_suggestions"].append({
                "type": "coordinate_hint",
                "element": corr["element"],
                "proposed_wrong": corr["proposed_coords"],
                "user_note": corr.get("correction_note")
            })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(learnings, f, indent=2, ensure_ascii=False)
    
    print(f"\n📤 Learnings exported to: {output_file}")


def summarize_all_sessions():
    """Summarize all sessions."""
    if not SESSIONS_DIR.exists():
        print("No sessions directory found.")
        return
    
    sessions = list(SESSIONS_DIR.glob("session_*.json"))
    if not sessions:
        print("No sessions found.")
        return
    
    print("\n" + "="*70)
    print(f"📊 All Sessions Summary ({len(sessions)} sessions)")
    print("="*70)
    
    total_interactions = 0
    total_successes = 0
    total_corrections = 0
    
    for session_file in sorted(sessions):
        session = load_session(session_file)
        summary = session.get("summary", {})
        
        interactions = summary.get("total_interactions", 0)
        successes = summary.get("successful_actions", 0)
        corrections = summary.get("user_corrections", 0)
        
        total_interactions += interactions
        total_successes += successes
        total_corrections += corrections
        
        success_rate = round(successes / interactions * 100, 1) if interactions > 0 else 0
        
        print(f"\n📁 {session_file.name}")
        print(f"   Interactions: {interactions}, Success: {success_rate}%, Corrections: {corrections}")
    
    print("\n" + "-"*70)
    overall_rate = round(total_successes / total_interactions * 100, 1) if total_interactions > 0 else 0
    print(f"📈 Overall: {total_interactions} interactions, {overall_rate}% success, {total_corrections} corrections")
    print("="*70)


def main():
    parser = argparse.ArgumentParser(description="Review and analyze saved sessions")
    parser.add_argument("session_file", nargs="?", help="Path to session JSON file")
    parser.add_argument("--all", action="store_true", help="Summarize all sessions")
    parser.add_argument("--export", action="store_true", help="Export learnings to JSON")
    args = parser.parse_args()
    
    if args.all:
        summarize_all_sessions()
        return
    
    # Determine which session to review
    if args.session_file:
        session_file = Path(args.session_file)
    else:
        session_file = get_latest_session()
        if not session_file:
            print("No sessions found. Run interactive_cprs.py first to create a session.")
            return
    
    if not session_file.exists():
        print(f"Session file not found: {session_file}")
        return
    
    # Load and analyze
    session = load_session(session_file)
    analysis = analyze_session(session)
    
    # Print review
    print_session_review(session, analysis)
    
    # Export if requested
    if args.export:
        learnings_file = SESSIONS_DIR / f"learnings_{session['session_id']}.json"
        export_learnings(analysis, learnings_file)


if __name__ == "__main__":
    main()
