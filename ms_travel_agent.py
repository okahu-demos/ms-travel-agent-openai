import asyncio
import logging
import os
import random
from typing import Annotated

from agent_framework import ChatAgent
from agent_framework.openai import OpenAIAssistantsClient
from dotenv import load_dotenv
load_dotenv()
from monocle_apptrace import setup_monocle_telemetry

# Enable Monocle Tracing
setup_monocle_telemetry(
	workflow_name="okahu_demos_ms_openai_travel_agent",
	monocle_exporters_list="file",
)

logger = logging.getLogger(__name__)


def book_flight(
	from_airport: Annotated[str, "The departure airport code (e.g., JFK, LAX)"],
	to_airport: Annotated[str, "The destination airport code (e.g., SFO, ORD)"],
	travel_date: Annotated[str, "Travel date in YYYY-MM-DD format"],
) -> str:
	"""Book a flight from one airport to another"""
	confirmation = f"FL{random.randint(100000, 999999)}"
	cost = random.randint(300, 900)
	return (
		f"FLIGHT BOOKING CONFIRMED #{confirmation}: {from_airport} to {to_airport} "
		f"on {travel_date} - ${cost}"
	)


def create_assistants_client() -> OpenAIAssistantsClient:
	model_id = (
		os.getenv("OPENAI_CHAT_MODEL_ID")
		or "gpt-4o-mini"
	)
	api_key = os.getenv("OPENAI_API_KEY")

	if not api_key:
		raise RuntimeError("OpenAI API key is missing. Set OPENAI_API_KEY.")

	return OpenAIAssistantsClient(
		api_key=api_key,
		model_id=model_id,
	)


async def setup_agents() -> ChatAgent:
	client = create_assistants_client()
	return client.as_agent(
		name="Flight Agent",
		instructions=(
			"You are a Flight Booking Assistant. "
			"Help users book flights between airports. "
			"If key details are missing, ask follow-up questions before booking."
		),
		tools=[book_flight],
	)


async def run_agent(request: str, service_thread_id: str | None = None):
	try:
		travel_agent = await setup_agents()
	except Exception as exc:
		logger.error("Failed to initialize agent. Check OpenAI settings in .env", exc_info=True)
		raise RuntimeError("Failed to initialize OpenAI assistant client.") from exc

	thread = travel_agent.get_new_thread(service_thread_id=service_thread_id)
	response = await travel_agent.run(request, thread=thread)
	return response.text, thread.service_thread_id

#sample convo
#Book a flight from BOM to JFK on 2026-12-15
#Also add a return flight on 2026-12-21
#What did we plan so far?

async def interactive_chat():
	print("\nFlight Agent is ready.")
	print("Type your request and press Enter.")
	print("Type 'exit' or 'quit' to end.\n")

	service_thread_id: str | None = None

	while True:
		user_input = input("[User]: ").strip()
		if not user_input:
			continue
		if user_input.lower() in {"exit", "quit"}:
			print("\nSession ended.")
			break

		response_text, service_thread_id = await run_agent(
			user_input,
			service_thread_id=service_thread_id,
		)
		print(f"[Agent]: {response_text}")
		if service_thread_id:
			print(f"📋 Thread ID: {service_thread_id}\n")


if __name__ == "__main__":
	logging.basicConfig(level=logging.WARN)
	asyncio.run(interactive_chat())
