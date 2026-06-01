"""Apex — Router/Dispatch Mode
Task classification and agent routing with fallback to default generalist.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from ..core.runtime import Agent
from ..core.profile import ProfileManager


# ---------------------------------------------------------------------------
# Default fallback agent configuration
# ---------------------------------------------------------------------------
DEFAULT_FALLBACK_AGENT = "assistant"
DEFAULT_FALLBACK_CATEGORY = "general"

# ---------------------------------------------------------------------------
# Category keyword patterns (ordered by specificity — first match wins)
# ---------------------------------------------------------------------------
CATEGORY_PATTERNS: list[tuple[str, list[str]]] = [
    ("billing", [
        r"\bbill",
        r"\binvoice",
        r"\bpayment",
        r"\bpricing",
        r"\bsubscription",
        r"\bcharge",
        r"\brefund",
        r"\bcost",
        r"\bbudget",
        r"\breceipt",
        r"\btransaction",
        r"\bplan\b",
        r"\bupgrade",
        r"\bdowngrade",
    ]),
    ("tech-support", [
        r"\berror",
        r"\bbug",
        r"\bfix\b",
        r"\bcrash",
        r"\bfail",
        r"\btroubleshoot",
        r"\bdebug",
        r"\bissue\b",
        r"\bproblem\b",
        r"\bnot working",
        r"\bcan't",
        r"\bcannot",
        r"\bunexpected",
        r"\bexception",
        r"\btraceback",
        r"\blog\b",
        r"\brestore",
        r"\brecover",
        r"\bpermission",
        r"\bdenied",
    ]),
    ("sales", [
        r"\bdemo\b",
        r"\btrial\b",
        r"\bquote",
        r"\bprice",
        r"\bdiscount",
        r"\boffer\b",
        r"\bdeal\b",
        r"\bpromotion",
        r"\bcontact sales",
        r"\bbuy\b",
        r"\bpurchase",
        r"\border\b",
        r"\blead\b",
        r"\bprospect",
        r"\bclosing",
        r"\bnegotiat",
        r"\bcommission",
    ]),
    ("compliance", [
        r"\bgdpr",
        r"\bsoc2?\b",
        r"\bhipaa",
        r"\bsecurity",
        r"\baudit",
        r"\bregulat",
        r"\bcomplian",
        r"\bpolicy\b",
        r"\bdata privacy",
        r"\bencrypt",
        r"\bconsent",
        r"\bretention",
        r"\brbac",
        r"\baccess control",
        r"\biso\b",
        r"\bpci\b",
    ]),
    ("architecture", [
        r"\bdesign\b",
        r"\barchitect",
        r"\bworkflow",
        r"\bdiagram",
        r"\bblueprint",
        r"\bscalab",
        r"\breliab",
        r"\bthroughput",
        r"\blatency",
        r"\bmicroservice",
        r"\bapi design",
        r"\bschema",
        r"\bdatabas",
        r"\bsystem design",
        r"\btradeoff",
        r"\bcomponent",
        r"\bmodule",
        r"\bdependency",
        r"\bintegration",
    ]),
    ("devops", [
        r"\bdeploy",
        r"\bci/cd",
        r"\bpipeline",
        r"\bdocker",
        r"\bkubernetes",
        r"\bk8s",
        r"\bterraform",
        r"\bansible",
        r"\bhelm",
        r"\brelease\b",
        r"\brollback",
        r"\bmonitoring",
        r"\balert",
        r"\bmetric",
        r"\blogging",
        r"\bgrafana",
        r"\bprometheus",
        r"\bgithub actions",
        r"\bgitlab ci",
    ]),
    ("content", [
        r"\bwrite\b",
        r"\bdraft",
        r"\bblog\b",
        r"\bpost\b",
        r"\barticle",
        r"\bcopy\b",
        r"\bcontent",
        r"\bseo\b",
        r"\bheadline",
        r"\bslogan",
        r"\bbrand\b",
        r"\bnewsletter",
        r"\bemail campaign",
        r"\bsocial media",
        r"\blanding page",
        r"\bad copy",
        r"\bscript",
        r"\bstoryboard",
    ]),
    ("code-review", [
        r"\breview\b.*\bcode\b",
        r"\bcode\b.*\breview\b",
        r"\bpr\b",
        r"\bpull request",
        r"\bmerge request",
        r"\brefactor",
        r"\blint",
        r"\bstatic analysis",
        r"\bcode quality",
        r"\btech debt",
        r"\bcode smell",
        r"\bcomplexity",
        r"\bcode audit",
    ]),
    ("documentation", [
        r"\bdoc\b",
        r"\bdocumentation",
        r"\bapi doc",
        r"\breadme",
        r"\bwiki\b",
        r"\bmanual\b",
        r"\bguide\b",
        r"\btutorial",
        r"\bfaq\b",
        r"\bchangelog",
        r"\brelease notes",
        r"\bcode comment",
        r"\buser guide",
    ]),
]


# ---------------------------------------------------------------------------
# RouterResult
# ---------------------------------------------------------------------------
@dataclass
class RouterResult:
    """Result of a routed task execution."""
    success: bool = False
    category: str = ""
    agent_used: str = ""
    output: str = ""
    cost: float = 0.0
    error: str = ""


# ---------------------------------------------------------------------------
# TaskClassifier
# ---------------------------------------------------------------------------
class TaskClassifier:
    """Analyze task text and classify into a predefined category.

    Uses keyword pattern matching ordered by specificity. Returns the
    first matching category or the default fallback category if none match.
    """

    def __init__(self) -> None:
        self._patterns: list[tuple[str, re.Pattern]] = [
            (cat, re.compile("|".join(pats), re.IGNORECASE))
            for cat, pats in CATEGORY_PATTERNS
        ]

    def classify(self, task: str) -> str:
        """Classify a task string into a category.

        Args:
            task: The task text to classify.

        Returns:
            A category string (e.g. "billing", "tech-support", "general").
        """
        for category, pattern in self._patterns:
            if pattern.search(task):
                return category
        return DEFAULT_FALLBACK_CATEGORY


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
class Router:
    """Task router — classify, dispatch, and manage agent routing.

    Maintains a routing table mapping categories to agent profile names.
    Tasks are classified via TaskClassifier, then dispatched to the
    appropriate agent. If no route is registered for the matched category,
    the default fallback agent is used.

    Usage::

        router = Router()
        router.register_route("billing", "billing-agent")
        router.register_route("tech-support", "support-agent")

        result = router.route("My invoice is late")
        print(result.output)
    """

    def __init__(
        self,
        profile_manager: Optional[ProfileManager] = None,
        classifier: Optional[TaskClassifier] = None,
        fallback_agent: str = DEFAULT_FALLBACK_AGENT,
        fallback_category: str = DEFAULT_FALLBACK_CATEGORY,
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize the Router.

        Args:
            profile_manager: ProfileManager instance. Creates a default
                one if not provided.
            classifier: TaskClassifier instance. Creates a default one
                if not provided.
            fallback_agent: Profile name for the fallback generalist agent.
            fallback_category: Category label returned when no pattern matches.
            api_key: Optional API key passed to all dispatched agents.
        """
        self._profile_manager = profile_manager or ProfileManager()
        self._classifier = classifier or TaskClassifier()
        self._fallback_agent = fallback_agent
        self._fallback_category = fallback_category
        self._api_key = api_key

        # Routing table: category -> agent profile name
        self._routes: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Route registration
    # ------------------------------------------------------------------
    def register_route(self, category: str, agent_name: str) -> None:
        """Register a route mapping a category to a specific agent profile.

        Args:
            category: Task category (e.g. "billing", "tech-support").
            agent_name: Name of the agent profile to dispatch to.

        Raises:
            ValueError: If the agent profile does not exist.
        """
        # Validate agent profile exists (will raise FileNotFoundError if not)
        self._profile_manager.load(agent_name)
        self._routes[category] = agent_name

    def unregister_route(self, category: str) -> None:
        """Remove a registered route for the given category.

        Args:
            category: The category to remove.
        """
        self._routes.pop(category, None)

    def list_routes(self) -> dict[str, str]:
        """Return a copy of the current routing table."""
        return dict(self._routes)

    # ------------------------------------------------------------------
    # Core routing & dispatch
    # ------------------------------------------------------------------
    def route(self, task: str) -> RouterResult:
        """Classify a task and dispatch it to the appropriate agent.

        Steps:
            1. Classify the task text -> category.
            2. Look up the agent profile name for that category.
            3. Fall back to default generalist if not found.
            4. Instantiate the Agent and execute the task.
            5. Return a RouterResult with the outcome.

        Args:
            task: The task string to route.

        Returns:
            A RouterResult with success, category, agent_used, output, cost.
        """
        # Step 1: classify
        category = self._classifier.classify(task)

        # Step 2: resolve agent profile name
        agent_name = self._routes.get(category)
        if agent_name is None:
            agent_name = self._fallback_agent
            category = self._fallback_category

        # Step 3: load profile and build agent
        try:
            profile = self._profile_manager.load(agent_name)
        except FileNotFoundError as e:
            return RouterResult(
                success=False,
                category=category,
                agent_used=agent_name,
                output="",
                cost=0.0,
                error=str(e),
            )

        agent = Agent(profile, api_key=self._api_key)

        # Step 4: execute
        try:
            output = agent.run(task)
            if agent.profile.auto_improve:
                agent._record_evolution(task, output, True)  # type: ignore[arg-type]
            return RouterResult(
                success=True,
                category=category,
                agent_used=agent_name,
                output=output,
                cost=agent.context.cost,
            )
        except Exception as e:
            return RouterResult(
                success=False,
                category=category,
                agent_used=agent_name,
                output="",
                cost=agent.context.cost,
                error=str(e),
            )

    # ------------------------------------------------------------------
    # Batch dispatch
    # ------------------------------------------------------------------
    def route_batch(self, tasks: list[str]) -> list[RouterResult]:
        """Route a batch of tasks sequentially.

        Args:
            tasks: List of task strings.

        Returns:
            List of RouterResult, one per task.
        """
        return [self.route(task) for task in tasks]

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------
    def classify(self, task: str) -> str:
        """Classify a task without dispatching it.

        Args:
            task: The task text to classify.

        Returns:
            The predicted category string.
        """
        return self._classifier.classify(task)
