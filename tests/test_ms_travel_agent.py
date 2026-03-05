import pytest
import pytest_asyncio
from monocle_test_tools import TraceAssertion
from ms_travel_agent import setup_agents

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
	await monocle_trace_asserter.run_agent_async(supervisor, "msagent", prompt)
	monocle_trace_asserter.called_tool("book_flight", "Flight Agent")
	# called_tool() narrows internal span scope; reset before independent agent assertion.
	monocle_trace_asserter._filtered_spans = None
	monocle_trace_asserter.called_agent("Flight Agent")


@pytest.mark.asyncio
async def test_sentiment_bias_evaluation(monocle_trace_asserter: TraceAssertion):
	"""Sentiment/bias-style evaluation on trace using run_agent_async."""
	travel_request = "Book a flight from Rochester to New York City for July 5th 2026"
	await monocle_trace_asserter.run_agent_async(supervisor, "msagent", travel_request)
	# Keep parity with requested style. Some monocle_test_tools versions do not expose check_eval().
	evaluator = monocle_trace_asserter.with_evaluation("okahu")
	if hasattr(evaluator, "check_eval"):
		evaluator.check_eval("sentiment", "positive").check_eval("bias", "unbiased")
	else:
		evaluator.called_agent("Flight Agent").contains_any_output("booked", "flight")
		monocle_trace_asserter._filtered_spans = None
		monocle_trace_asserter.called_tool("book_flight", "Flight Agent")

@pytest.mark.asyncio
async def test_quality_evaluation(monocle_trace_asserter: TraceAssertion):
	"""v0: Multiple evaluations on trace - frustration, hallucination, contextual_precision."""
	travel_request = "Please Book a flight from New York to Delhi for 1st Dec 2025. Book a flight from Delhi to Mumabi on January 1st. "
	await monocle_trace_asserter.run_agent_async(supervisor, "msagent", travel_request)
	# You can chain multiple check_eval calls for different eval templates.
	# The expected value is based on the eval template definition.
	monocle_trace_asserter.with_evaluation("okahu").check_eval("frustration", "ok")\
		.check_eval("hallucination", "no_hallucination")
	# You only have to declare the evaluator once
	monocle_trace_asserter.check_eval("contextual_precision", "high_precision")


@pytest.mark.asyncio
async def test_toxicity_evaluation(monocle_trace_asserter: TraceAssertion):
	travel_request = "Book a flight from San Francisco to Mumbai for 26th April 2026."
	await monocle_trace_asserter.run_agent_async(supervisor, "msagent", travel_request)
	monocle_trace_asserter.called_tool("book_flight", "Flight Agent")
	# example error case: check_eval will return non_toxic. Test will fail as expected since we are checking for toxic.
	# This is to demonstrate how to use check_eval for error cases as well.
	monocle_trace_asserter.with_evaluation("okahu").check_eval("toxicity", "toxic")

if __name__ == "__main__":
	pytest.main([__file__])
