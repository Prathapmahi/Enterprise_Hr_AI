# workflows/engine.py
"""
AI Workflow Orchestration Engine — Feature #2
Executes multi-step enterprise workflows with agent coordination.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional
from loguru import logger


@dataclass
class WorkflowStep:
    name: str
    agent: str
    action: Callable
    timeout: int = 30
    retry_on_fail: bool = True


@dataclass
class WorkflowResult:
    workflow_id: str
    workflow_name: str
    status: str         # running / completed / failed
    steps_total: int
    steps_completed: int
    duration_ms: float
    outputs: dict
    errors: list[str]
    started_at: str
    completed_at: Optional[str]


class WorkflowEngine:
    """
    Sequential workflow executor with step-level logging.
    Each step maps to a specific agent action.
    """

    def __init__(self):
        self._workflow_counter = 0

    def execute(self, workflow_name: str, steps: list[dict], context: dict = None) -> WorkflowResult:
        """
        Execute a workflow synchronously.
        steps: list of {"name": ..., "agent": ..., "fn": callable, "args": dict}
        """
        self._workflow_counter += 1
        wf_id = f"WF-{self._workflow_counter:05d}"
        start_time = datetime.now()
        outputs = {}
        errors = []
        completed = 0

        logger.info(f"[WorkflowEngine] Starting workflow '{workflow_name}' (id={wf_id})")

        for i, step in enumerate(steps):
            step_name = step.get("name", f"Step {i+1}")
            agent = step.get("agent", "orchestrator")
            fn = step.get("fn")
            args = step.get("args", {})

            logger.info(f"[WorkflowEngine] Executing step {i+1}/{len(steps)}: {step_name} (agent={agent})")

            try:
                if fn:
                    result = fn(**args)
                    outputs[step_name] = result
                else:
                    outputs[step_name] = {"status": "simulated", "step": step_name}
                completed += 1
                logger.info(f"[WorkflowEngine] ✅ Step '{step_name}' completed")
            except Exception as e:
                err = f"Step '{step_name}' failed: {e}"
                errors.append(err)
                logger.error(f"[WorkflowEngine] ❌ {err}")
                if not step.get("continue_on_fail", True):
                    break

        end_time = datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        status = "completed" if not errors else ("partial" if completed > 0 else "failed")

        result = WorkflowResult(
            workflow_id=wf_id,
            workflow_name=workflow_name,
            status=status,
            steps_total=len(steps),
            steps_completed=completed,
            duration_ms=round(duration_ms, 2),
            outputs=outputs,
            errors=errors,
            started_at=start_time.isoformat(),
            completed_at=end_time.isoformat(),
        )

        logger.info(
            f"[WorkflowEngine] Workflow '{workflow_name}' {status} — "
            f"{completed}/{len(steps)} steps in {duration_ms:.0f}ms"
        )
        return result


# Singleton
workflow_engine = WorkflowEngine()
