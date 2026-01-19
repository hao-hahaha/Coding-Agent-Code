"""
MuZero Planning demo – Cross‑industry Alpha‑Factory illustration.
Runs a lightweight MuZero agent (MiniMu) on Gymnasium’s CartPole‑v1
(or ``$MUZERO_ENV_ID``) and streams a live Gradio dashboard
on ``$HOST_PORT`` (default 7861).

Core algorithm follows the public pseudocode from Schrittwieser et al. (2020)
but trimmed to <300 LoC for pedagogy.
"""
import os, asyncio, random

try:  # gymnasium optional for offline testing
    import gymnasium as gym
except ModuleNotFoundError:  # pragma: no cover - fallback stub
    from .minimuzero import gym

try:  # OpenAI Agents SDK is optional
    from openai_agents import Agent, Tool, OpenAIAgent
except ModuleNotFoundError:  # pragma: no cover - provide graceful degrade
    class OpenAIAgent:
        def __init__(self, *_, **__):
            pass

        def __call__(self, *_: str) -> str:
            return "LLM commentary unavailable."

    def Tool(*_, **__):  # type: ignore[misc]
        def wrapper(func):
            return func

        return wrapper

import gradio as gr

# ── Minimal MuZero utilities --------------------------------------------------
# (full implementation lives in demo/minimuzero.py, imported here)
from demo.minimuzero import MiniMu, mcts_policy, play_episode

ENV_ID = os.getenv("MUZERO_ENV_ID", "CartPole-v1")  # default environment
EPISODES = int(os.getenv("MUZERO_EPISODES", 3))
PORT = int(os.getenv("HOST_PORT", 7861))

# ── Optional commentary agent -------------------------------------------------
llm = OpenAIAgent(
    model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
    api_key=os.getenv("OPENAI_API_KEY", None),
    base_url=("http://ollama:11434/v1" if not os.getenv("OPENAI_API_KEY") else None)
)

@Tool(name="explain_move", description="explain MuZero's next action")
async def explain_move(state:str):
    prompt=f"You are New‑Yorker‑style columnist. Explain why MuZero picks {state}."
    return llm(prompt)

# ── Gradio UI -----------------------------------------------------------------
def launch_dashboard():
    with gr.Blocks(title="MuZero Planning Demo") as demo:
        vid = gr.Video(label="Live environment")
        log = gr.Markdown()
        def run():
            mu = MiniMu(env_id=ENV_ID)
            txt=""
            frames=[]
            for _ in range(EPISODES):
                ep_frames, ep_reward = play_episode(mu)
                txt += f"**Episode reward:** {ep_reward}<br>"
                frames+=ep_frames
            return (frames[::2], txt)
        start = gr.Button("▶ Run MuZero")
        start.click(run, outputs=[vid, log])
    demo.launch(server_name="0.0.0.0", server_port=PORT)

if __name__ == "__main__":
    launch_dashboard()
