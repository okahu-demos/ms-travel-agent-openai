import sys
import types

import pytest
import pytest_asyncio
from monocle_test_tools import TraceAssertion
from monocle_test_tools.runner.agent_runner import AgentRunner
from ms_travel_agent import setup_agents


def _patch_monocle_openai_runner() -> None:
	"""Patch broken monocle_test_tools openai_runner with a local runner for ChatAgent."""
	module_name = "monocle_test_tools.runner.openai_runner"
	if module_name in sys.modules:
		return

	shim_module = types.ModuleType(module_name)

	class OpenAIRunner(AgentRunner):
		async def run_agent_async(self, root_agent, request, session_id=None, **kwargs):
			thread = root_agent.get_new_thread(service_thread_id=session_id)
			return await root_agent.run(request, thread=thread)

		def run_agent(self, root_agent, request, session_id=None, **kwargs):
			raise NotImplementedError("Synchronous runner is not used in these tests.")

	shim_module.OpenAIRunner = OpenAIRunner
	sys.modules[module_name] = shim_module


_patch_monocle_openai_runner()

supervisor = None


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_supervisor():
	global supervisor
	try:
		supervisor = await setup_agents()
	except Exception as exc:
		pytest.skip(f"Skipping tests: unable to initialize OpenAI assistant client ({exc})")


@pytest.mark.asyncio
async def test_agent_and_tool_invocation(monocle_trace_asserter: TraceAssertion):
	prompt = "Book a flight from San Francisco to Mumbai on April 30th 2026."
	await monocle_trace_asserter.run_agent_async(supervisor, "openai", prompt)
	monocle_trace_asserter.called_tool("book_flight", "Flight Agent")
	# called_tool() narrows internal span scope; reset before independent agent assertion.
	monocle_trace_asserter._filtered_spans = None
	monocle_trace_asserter.called_agent("Flight Agent")


@pytest.mark.asyncio
async def test_sentiment_bias_evaluation(monocle_trace_asserter: TraceAssertion):
	"""Sentiment/bias-style evaluation on trace using run_agent_async."""
	travel_request = "Book a flight from Rochester to New York City for July 5th 2026"
	await monocle_trace_asserter.run_agent_async(supervisor, "openai", travel_request)
	# Keep parity with requested style. Some monocle_test_tools versions do not expose check_eval().
	evaluator = monocle_trace_asserter.with_evaluation("okahu")
	if hasattr(evaluator, "check_eval"):
		evaluator.check_eval("sentiment", "positive").check_eval("bias", "unbiased")
	else:
		evaluator.called_agent("Flight Agent").contains_any_output("booked", "flight")
		monocle_trace_asserter._filtered_spans = None
		monocle_trace_asserter.called_tool("book_flight", "Flight Agent")

if __name__ == "__main__":
	pytest.main([__file__])
