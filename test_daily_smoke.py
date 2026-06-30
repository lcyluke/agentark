"""Quick smoke test for daily_report module"""
import sys
sys.path.insert(0, '/Users/Mac/Desktop/2026AIAPP/Apex')
from agentark.orchestration.daily_report import generate_report, generate_json_report

# Test dataclass
r = generate_report()
print(f"Projects: {len(r.projects)}")
for p in r.projects:
    print(f"  {p.emoji} {p.name}: {p.tasks_done}/{p.tasks_total} tasks, {p.today_tokens} tokens, ${p.today_cost:.4f}, {p.bugs_open} bugs, git={p.git_commits_today}")

# Test JSON
j = generate_json_report()
print(f"\nJSON: {len(j['projects'])} projects, summary={j['summary']['status']}")
print("OK - all tests pass")
