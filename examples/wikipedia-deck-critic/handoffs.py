"""Variation 2: handoffs. The generator and critic hand the conversation back and forth.

A handoff only loops if every turn ends in a tool call. Left alone, the model can answer with
plain text, and plain text ends the run. So both agents get tool_choice="required", which
reset_tool_choice=False keeps on after the first tool call, and the critic gets an explicit
way out: approve_deck, which StopAtTools turns into the end of the run.
"""

from agents import Agent, ModelSettings, RunContextWrapper, Runner, StopAtTools, function_tool, handoff
from pydantic import BaseModel

from common import CRITIC_MODEL, GENERATOR, MAX_ROUNDS, MODEL, RUBRIC, VERTEX, DeckContext, get_article, save_deck

FORCE_TOOLS = ModelSettings(tool_choice="required", extra_args=VERTEX)


class Feedback(BaseModel):
    """What the critic hands back. It becomes the arguments of the transfer_to_generator call."""

    problems: list[str]


@function_tool
def approve_deck(note: str) -> str:
    """Approve the saved deck. This ends the run.

    Args:
        note: One sentence on why the deck passes.
    """
    return note


def critic_instructions(ctx: RunContextWrapper[DeckContext], agent: Agent) -> str:
    """Dynamic instructions: once the critic is out of reviews, it may only approve."""
    if ctx.context.rounds >= MAX_ROUNDS:
        return RUBRIC + "\n\nYou are out of reviews. Call approve_deck."
    return RUBRIC + (
        "\n\nReview the most recently saved deck. If it passes, call approve_deck. Otherwise call "
        "transfer_to_generator with at most 6 problems: the rubric item number, the exact text in "
        "quotes, and a plainer rewrite."
    )


async def count_review(ctx: RunContextWrapper[DeckContext], feedback: Feedback) -> None:
    ctx.context.rounds += 1


critic = Agent[DeckContext](
    name="Critic",
    instructions=critic_instructions,
    model=CRITIC_MODEL,
    model_settings=FORCE_TOOLS,
    reset_tool_choice=False,
    tools=[approve_deck],
    tool_use_behavior=StopAtTools(stop_at_tool_names=["approve_deck"]),
)

generator = Agent[DeckContext](
    name="Generator",
    instructions=GENERATOR + (
        "\n4. Then call transfer_to_critic. If the critic sends problems back, fix them, call "
        "save_deck again, and transfer to the critic again."
    ),
    model=MODEL,
    model_settings=FORCE_TOOLS,
    reset_tool_choice=False,
    tools=[get_article, save_deck],
    handoffs=[critic],
)

# The critic hands back with Feedback. Once it's out of reviews, the handoff disappears
# from its tools, so approve_deck is the only call it can make.
critic.handoffs = [
    handoff(
        agent=generator,
        input_type=Feedback,
        on_handoff=count_review,
        is_enabled=lambda ctx, agent: ctx.context.rounds < MAX_ROUNDS,
    )
]


async def run(ctx: DeckContext, hooks) -> None:
    # One run, one shared conversation. The critic decides when it ends.
    await Runner.run(generator, ctx.url, context=ctx, hooks=hooks, max_turns=40)
