# SPDX-License-Identifier: Apache-2.0
# llm_client.py
import os, openai

# Load config from env or default
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-0613")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"


def call_local_model(prompt_messages: list[dict[str, str]]) -> str:
    """Return a response from a local model (placeholder implementation)."""
    return ""


def build_prompt(error_log: str, code_dir: str) -> list[dict[str, str]]:
    """Construct the prompt for the LLM based on the error log (and optional code context)."""
    # We include a system prompt to instruct the assistant to only output a diff.
    system_msg = (
        "You are an AI developer assistant. A software test has failed, and your task is to suggest a fix. "
        "You will be given an error log and possibly some code snippets. "
        "Provide a unified diff patch that fixes the issue, and nothing else. "
        "The diff should be in unified format (starting with filenames '+++')."
    )
    user_msg = "The following test failed with this error:\n```\n" + error_log + "\n```\n"
    user_msg += "Please propose a fix as a patch (unified diff) that would resolve this error."
    # Optionally, we could attach relevant code context (like the file and line indicated in error_log).
    # For example, if error_log mentions a file and line, we can read a few lines around that and include in prompt.
    code_context = extract_code_context(error_log, code_dir)
    if code_context:
        user_msg += "\n\nRelevant Code Context:\n```python\n" + code_context + "\n```"
    return [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]


def extract_code_context(error_log: str, code_dir: str) -> str:
    """Optional: find file path and line number in error_log and retrieve surrounding code."""
    # Simplistic implementation: search for patterns like 'File "path/to/file.py", line X'
    import re

    m = re.search(r"File \"(.+\.py)\", line (\d+)", error_log)
    if m:
        file_path = os.path.join(code_dir, m.group(1))
        line_no = int(m.group(2))
        if os.path.exists(file_path):
            lines = open(file_path).read().splitlines()
            start = max(0, line_no - 5)
            end = min(len(lines), line_no + 5)
            snippet = "\n".join(lines[start:end])
            return f"...\n{snippet}\n..."
    return ""


def request_patch(prompt_messages: list[dict[str, str]]) -> str:
    """Call the LLM (OpenAI or local) to get a patch suggestion."""
    if USE_LOCAL_LLM:
        return call_local_model(prompt_messages)
    if not OPENAI_API_KEY:
        raise RuntimeError("No OpenAI API key provided and not using local model.")
    openai.api_key = OPENAI_API_KEY
    # Use function calling to ensure output is a diff via a "function"
    functions = [
        {
            "name": "propose_patch",
            "description": "Return a unified diff patch as a fix.",
            "parameters": {
                "type": "object",
                "properties": {"diff": {"type": "string", "description": "Unified diff patch."}},
                "required": ["diff"],
            },
        }
    ]
    try:
        response = openai.ChatCompletion.create(  # type: ignore[attr-defined]
            model=OPENAI_MODEL,
            messages=prompt_messages,
            functions=functions,
            function_call={"name": "propose_patch"},  # force it to respond via the function
        )
    except Exception as e:
        raise
    # If the model decided to call the function:
    choices = response.get("choices", [])
    if choices and choices[0].get("finish_reason") == "function_call":
        # The model is requesting to call a function (e.g., could integrate tools if needed)
        func_call = choices[0]["message"]["function_call"]
        if func_call["name"] == "propose_patch":
            # This means model returned a function call with diff content
            diff_content = func_call["arguments"].get("diff")
            if diff_content:
                return str(diff_content)
    # Otherwise, the model might have directly given an answer
    text = str(choices[0]["message"].get("content", ""))
    return text or ""
