# SPDX-License-Identifier: Apache-2.0
"""Agent producing small code samples from market data.

The ``CodeGenAgent`` consumes analysis messages and replies with a candidate
code snippet. When available, an OpenAI agent context or local model is used
to generate the snippet; otherwise a stub is returned via :meth:`handle`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time


from .base_agent import BaseAgent
from ..utils import messaging
from ..utils.logging import Ledger
from ..utils.retry import with_retry


class CodeGenAgent(BaseAgent):
    """Generate code snippets from market analysis."""

    def __init__(self, bus: messaging.A2ABus, ledger: "Ledger") -> None:
        super().__init__("codegen", bus, ledger)

    async def run_cycle(self) -> None:
        """No-op background loop."""
        return None

    async def handle(self, env: messaging.Envelope) -> None:
        """Translate market insight into executable code."""
        analysis = env.payload.get("analysis", "")
        code = "print('alpha')"
        if self.oai_ctx and not self.bus.settings.offline:
            try:  # pragma: no cover
                code = await with_retry(self.oai_ctx.run)(prompt=str(analysis))
            except Exception:
                pass
        self.execute_in_sandbox(code)
        await self.emit("safety", {"code": code})

    def execute_in_sandbox(self, code: str) -> tuple[str, str]:
        """Run ``code`` inside a subprocess with resource limits."""

        def _apply_limits() -> None:  # pragma: no cover - platform dependent
            try:
                import resource

                resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
                mem = 128 * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
            except Exception:
                pass

        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
            fh.write(code)
            code_path = fh.name

        helper = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False)
        helper.write(
            "import json,sys,contextlib,io,textwrap,resource\n"
            "code=open(sys.argv[1]).read()\n"
            "try:\n"
            "    resource.setrlimit(resource.RLIMIT_CPU,(2,2))\n"
            "    resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))\n"
            "except Exception:\n"
            "    pass\n"
            "wrapped='def snippet():\\n'+textwrap.indent(code,'    ')\n"
            "env={'__builtins__':{'print':print,'range':range,'len':len}}\n"
            "loc={}\n"
            "out,err=io.StringIO(),io.StringIO()\n"
            "with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):\n"
            "    try:\n"
            "        exec(compile(wrapped,'<agent>','exec'),env,loc)\n"
            "        loc['snippet']()\n"
            "    except Exception as e:\n"
            "        err.write(type(e).__name__)\n"
            "print(json.dumps({'stdout':out.getvalue(),'stderr':err.getvalue()}))\n"
        )
        helper.flush()
        helper_path = helper.name
        helper.close()

        try:
            proc = subprocess.run(
                [sys.executable, helper_path, code_path],
                text=True,
                capture_output=True,
                timeout=3,
                preexec_fn=_apply_limits if os.name == "posix" else None,
            )
            try:
                data = json.loads(proc.stdout or "{}")
                out = data.get("stdout", "")
                err = data.get("stderr", "")
            except json.JSONDecodeError:
                out, err = proc.stdout, proc.stderr
        except Exception as exc:  # pragma: no cover - runtime errors
            out, err = "", str(exc)
        finally:
            os.unlink(code_path)
            os.unlink(helper_path)

        env = messaging.Envelope(self.name, "exec", {"stdout": out, "stderr": err}, time.time())
        self.ledger.log(env)
        return out, err
