"""
UAT: Origin Agent — 始祖Agent 测试
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "apex"))

TEST_HOME = Path(tempfile.mkdtemp(prefix="apex_origin_uat_"))
os.environ["AGENTARK_HOME"] = str(TEST_HOME)


class TestOriginInit:
    def test_init_creates_profile(self):
        from agentark.orchestration.origin import OriginAgent, ORIGIN_PROFILE_NAME
        origin = OriginAgent()
        from agentark.core.profile import ProfileManager
        pm = ProfileManager()
        p = pm.load(ORIGIN_PROFILE_NAME)
        assert p is not None
        assert p.soul.role.startswith("Origin Agent")
        assert len(p.skills) >= 8

    def test_init_idempotent(self):
        from agentark.orchestration.origin import OriginAgent
        # First call should create
        r1 = OriginAgent()._ensure_origin_profile()
        # Second call should detect it exists and upgrade
        r2 = OriginAgent()._ensure_origin_profile()
        # Both should succeed (created first time, upgraded second)
        assert r1["status"] in ("created", "upgraded")
        assert r2["status"] == "upgraded"


class TestReplicate:
    def test_replicate_merge(self):
        import tempfile
        tmp = Path(tempfile.mkdtemp(prefix="apex_repl_test_"))
        os.environ["AGENTARK_HOME"] = str(tmp)
        try:
            from agentark.orchestration.origin import OriginAgent, PM_SKILLS
            from agentark.core.profile import ProfileManager, Profile, SoulConfig

            pm = ProfileManager()
            pm.save(Profile(name="test_pm_x", soul=SoulConfig(role="Test PM")))
            result = OriginAgent().replicate_to("test_pm_x", strategy="pm")
            assert result["ok"] is True
            p = pm.load("test_pm_x")
            added = [s for s in PM_SKILLS if s in p.skills]
            assert len(added) > 0, f"No PM skills found in {p.skills}"
        finally:
            os.environ["AGENTARK_HOME"] = str(TEST_HOME)

    def test_replicate_all(self):
        from agentark.core.profile import ProfileManager, Profile, SoulConfig
        from agentark.orchestration.origin import OriginAgent

        pm = ProfileManager()
        for name in ["proj_backend", "proj_frontend"]:
            pm.save(Profile(name=name, soul=SoulConfig(role="Dev")))
        result = OriginAgent().replicate_to_all()
        assert result["replicated"] >= 2


class TestPortfolio:
    def test_create_portfolio(self):
        from agentark.orchestration.origin import OriginAgent
        result = OriginAgent().create_portfolio(
            name="羽球宝AI", strategic_goal="L7评估准确率>90%",
            expected_outcome="500+日活", pm_agent="羽球宝AI_pm"
        )
        assert result["ok"] is True
        assert result["pm_agent_deployed"] is True

    def test_list_portfolios(self):
        from agentark.orchestration.origin import OriginAgent
        portfolios = OriginAgent().list_portfolios()
        assert len(portfolios) >= 1
        assert "羽球宝AI" in [p["name"] for p in portfolios]

    def test_portfolio_overview(self):
        from agentark.orchestration.origin import OriginAgent
        overview = OriginAgent().portfolio_overview()
        assert "fleets" in overview
        assert overview["fleets"] >= 1


class TestApiEndpoints:
    @pytest.fixture(autouse=True)
    def setup_app(self):
        pytest.importorskip("flask", reason="Flask not installed")
        from agentark.orchestration.origin import OriginAgent
        OriginAgent().create_portfolio(name="test_api_portfolio")

    def test_api_origin_overview(self):
        from agentark.interface.web import create_app
        app = create_app()
        client = app.test_client()
        resp = client.get("/api/origin/overview")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "fleets" in data

    def test_api_origin_replicate(self):
        from agentark.interface.web import create_app
        app = create_app()
        client = app.test_client()
        resp = client.post("/api/origin/replicate",
                          data=json.dumps({"target": "default", "strategy": "merge"}),
                          content_type="application/json")
        assert resp.status_code == 200
