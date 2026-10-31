"""Variation 1: the call loop. Python runs the generator, then the critic, and decides when to stop.

The agents never meet. Each Runner.run has its own context; the code carries the deck and the
feedback between them.
"""

from agents import Agent, Runner

from common import CRITIC_MODEL, GENERATOR, MAX_ROUNDS, MODEL, RUBRIC, SETTINGS, VERDICT_FORMAT, DeckContext, get_article, save_deck

generator = Agent[DeckContext](
    name="Generator",
    instructions=GENERATOR + "\n4. Then reply with one sentence saying the deck is saved.",
    model=MODEL,
    model_settings=SETTINGS,
    tools=[get_article, save_deck],
)

critic = Agent[DeckContext](
    name="Critic",
    instructions=RUBRIC + "\n\n" + VERDICT_FORMAT,
    model=CRITIC_MODEL,
    model_settings=SETTINGS,
)


async def run(ctx: DeckContext, hooks) -> None:
    history = [{"role": "user", "content": ctx.url}]
    for _ in range(MAX_ROUNDS):
        # 1. Generate: the generator's context keeps growing across rounds.
        result = await Runner.run(generator, history, context=ctx, hooks=hooks)
        history = result.to_input_list()

        # 2. Critique: the critic sees only the deck, in a fresh context every round.
        verdict = await Runner.run(critic, ctx.deck, context=ctx, hooks=hooks)
        ctx.rounds += 1
        feedback = verdict.final_output.strip()
        if feedback.upper().startswith("PASS"):
            return  # the code decides when to stop

        # 3. Feedback goes back into the generator's context as a user message.
        history.append({"role": "user", "content": f"A critic reviewed your deck:\n\n{feedback}\n\nRevise it and save it again."})
