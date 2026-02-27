import importlib.util
from pathlib import Path

import pytest
import pytest_asyncio
from monocle_test_tools import TraceAssertion


MODULE_PATH = Path(__file__).parent.parent / "ms-travel-agent.py"
SPEC = importlib.util.spec_from_file_location("ms_travel_agent_module", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
	raise RuntimeError(f"Unable to load module from path: {MODULE_PATH}")

ms_travel_agent = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ms_travel_agent)

setup_agents = ms_travel_agent.setup_agents

supervisor = None


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_supervisor():
	global supervisor
	try:
		supervisor = await setup_agents()
	except Exception as exc:
		pytest.skip(f"Skipping tests: unable to initialize OpenAI assistant client ({exc})")


async def _run_prompt_or_skip(prompt: str):
	thread = supervisor.get_new_thread()
	try:
		await supervisor.run(prompt, thread=thread)
	except Exception as exc:
		message = str(exc)
		if "Resource not found" in message or "Error code: 404" in message:
			pytest.skip("Skipping tests: OpenAI endpoint/model is not reachable or invalid (404).")
		raise


@pytest.mark.asyncio
async def test_tool_and_agent_invocation(monocle_trace_asserter: TraceAssertion):
	await _run_prompt_or_skip("Book a flight from San Jose to Seattle for 22 Nov 2026")

	monocle_trace_asserter.called_tool("book_flight", "Flight Agent")
	monocle_trace_asserter.called_agent("Flight Agent")


if __name__ == "__main__":
	pytest.main([__file__])
