"""Variation 3: the critic as a tool. The generator calls review_deck and decides when it's done.

as_tool runs the critic in its own Runner.run with a fresh context: it sees only the deck the
generator passes in, never the article or the generator's history.
"""

from agents import Agent, Runner

from common import CRITIC_MODEL, GENERATOR, MAX_ROUNDS, MODEL, RUBRIC, SETTINGS, VERDICT_FORMAT, DeckContext, get_article, save_deck

critic = Agent[DeckContext](
    name="Critic",
    instructions=RUBRIC + "\n\n" + VERDICT_FORMAT,
    model=CRITIC_MODEL,
    model_settings=SETTINGS,
)


async def count_review(result) -> str:
    """Runs after each review: count it in the shared context, and return the critic's verdict."""
    result.context_wrapper.context.rounds += 1
    return str(result.final_output)


def make_generator(hooks) -> Agent[DeckContext]:
    # The hooks go to the critic's nested run too, so the page can show the critic's context.
    review_deck = critic.as_tool(
        tool_name="review_deck",
        tool_description="Have a critic review a draft deck for signs of AI writing. Pass the whole deck.",
        custom_output_extractor=count_review,
        hooks=hooks,
        # Out of reviews: the tool disappears, and the generator has to finish.
        is_enabled=lambda ctx, agent: ctx.context.rounds < MAX_ROUNDS,
    )
    return Agent[DeckContext](
        name="Generator",
        instructions=GENERATOR + (
            "\n4. Call review_deck with the whole deck. If the review starts with REVISE, fix the "
            "problems, call save_deck, and review again. When it starts with PASS, or review_deck is "
            "no longer available, reply with one sentence saying the deck is done."
        ),
        model=MODEL,
        model_settings=SETTINGS,
        tools=[get_article, save_deck, review_deck],
    )


async def run(ctx: DeckContext, hooks) -> None:
    # One run. The critic's runs nest inside the generator's tool calls.
    await Runner.run(make_generator(hooks), ctx.url, context=ctx, hooks=hooks, max_turns=30)
