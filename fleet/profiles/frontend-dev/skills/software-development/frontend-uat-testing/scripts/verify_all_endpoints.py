"""
Apex Dashboard — Full API Verification Script
Run with: python3 verify_all_endpoints.py
Assumes Flask server on http://localhost:8080
"""

import json, subprocess, sys

BASE = "http://localhost:8080"
ENDPOINTS = [
    ('/api/status', 'Status', 'object', lambda d: isinstance(d, dict) and d.get('status')),
    ('/api/health', 'Health', 'object', lambda d: d.get('status') == 'ok'),
    ('/api/profiles', 'Profiles', 'array', lambda d: isinstance(d, list) and len(d) > 0),
    ('/api/tasks', 'Tasks', 'array', lambda d: isinstance(d, list) and len(d) > 0),
    ('/api/autonomous', 'Autonomous', 'object', lambda d: isinstance(d, dict) and d.get('knowledge_nodes', 0) >= 0),
    ('/api/knowledge', 'Knowledge', 'object', lambda d: isinstance(d, dict) and d.get('nodes', 0) >= 0),
    ('/api/environment', 'Environment', 'object', lambda d: isinstance(d, dict) and d.get('hostname')),
    ('/api/fleet/profiles/list', 'Hermes Profiles', 'array', lambda d: isinstance(d, list)),
    ('/api/fleet/teams/list', 'Teams', 'object', lambda d: isinstance(d, dict) and isinstance(d.get('teams'), dict)),
    ('/api/ops/agents/workloads', 'Workloads', 'object', lambda d: isinstance(d, dict) and isinstance(d.get('agents'), list)),
    ('/api/ops', 'Ops', 'object', lambda d: isinstance(d, dict)),
    ('/api/live/runtime', 'Live Runtime', 'object', lambda d: isinstance(d, dict) and isinstance(d.get('sessions'), list)),
    ('/api/live/projects', 'Live Projects', 'array', lambda d: isinstance(d, list)),
    ('/api/auth/stats', 'Auth Stats', 'object', lambda d: isinstance(d, dict)),
    ('/api/auth/audit?days=7&limit=5', 'Auth Audit', 'array', lambda d: isinstance(d, list)),
    ('/api/command-center', 'Command Center', 'object', lambda d: isinstance(d, dict)),
]

def curl(ep):
    result = subprocess.run(['curl', '-s', f'{BASE}{ep}'], capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        return None, f"curl failed: {result.stderr[:100]}"
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError:
        return None, f"parse error: {result.stdout[:100]}"

def check_type(data, expected_type):
    if expected_type == 'array':
        return isinstance(data, list)
    return isinstance(data, dict)

passed = 0
failed = 0
issues = []

print(f"{'='*60}")
print(f"Apex Dashboard API Verification")
print(f"Base: {BASE}")
print(f"{'='*60}\n")

for ep, name, exp_type, validator in ENDPOINTS:
    data, error = curl(ep)
    
    if error:
        print(f"❌ {name}: {error}")
        issues.append(f"❌ {name}: {error}")
        failed += 1
        continue
    
    if not check_type(data, exp_type):
        actual = type(data).__name__
        print(f"❌ {name}: expected {exp_type}, got {actual}")
        issues.append(f"❌ {name}: type mismatch ({exp_type} vs {actual})")
        failed += 1
        continue
    
    try:
        ok = validator(data)
        status = '✅' if ok else '⚠️'
        detail = ''
        if isinstance(data, list):
            detail = f'{len(data)} items'
        elif isinstance(data, dict):
            if name == 'Workloads':
                detail = f'{len(data.get("agents",[]))} agents'
            elif name == 'Knowledge':
                detail = f'nodes={data.get("nodes")} edges={data.get("edges")}'
            elif name == 'Teams':
                detail = f'{len(data.get("teams",{}))} teams'
            elif name == 'Live Projects':
                detail = f'{len(data)} projects'
        
        print(f"{status} {name}: {detail}")
        if not ok:
            issues.append(f"⚠️ {name}: validation failed")
        else:
            passed += 1
    except Exception as e:
        print(f"❌ {name}: validator exception: {e}")
        issues.append(f"❌ {name}: validator crashed: {e}")
        failed += 1

print(f"\n{'='*60}")
print(f"Results: {passed} passed, {failed} failed, {len(issues)} issues")
if issues:
    print(f"\nIssues:")
    for i in issues:
        print(f"  {i}")
print(f"{'='*60}")
