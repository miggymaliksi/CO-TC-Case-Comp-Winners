"""Run only the local Ollama service installed for this checkout or on PATH."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parent


def runtime_env():
    env = os.environ.copy()
    env.update(
        OLLAMA_HOST="127.0.0.1:11434",
        OLLAMA_MODELS=str(ROOT / ".local-ai/models"),
        OLLAMA_NO_CLOUD="1",
        OLLAMA_NUM_PARALLEL="1",
        OLLAMA_MAX_QUEUE="2",
        OLLAMA_CONTEXT_LENGTH="4096",
        OLLAMA_MAX_LOADED_MODELS="1",
    )
    return env


def executable():
    local = ROOT / ".local-ai/runtime/ollama"
    return str(local) if local.is_file() else shutil.which("ollama")


def ready():
    try:
        # Do not route a local-only request through HTTP_PROXY.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open("http://127.0.0.1:11434/api/tags", timeout=1) as r:
            return isinstance(json.load(r).get("models"), list)
    except Exception:
        return False


def start():
    if ready():
        return None
    binary = executable()
    if not binary:
        return None
    (ROOT / ".local-ai").mkdir(exist_ok=True)
    # This log contains only local Ollama operational messages, not application prompts.
    log = (ROOT / ".local-ai/server.log").open("a")
    process = subprocess.Popen(
        [binary, "serve"], env=runtime_env(), stdout=log, stderr=subprocess.STDOUT
    )
    log.close()
    for _ in range(50):
        if ready():
            return process
        if process.poll() is not None:
            return None
        time.sleep(0.2)
    process.terminate()
    return None


def stop(process):
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def setup():
    binary = executable()
    if not binary:
        raise RuntimeError(
            "Install Ollama from https://ollama.com/download first, then rerun this task. No account or API key is needed."
        )
    model = os.environ.get("SAVOR_LOCAL_MODEL", "qwen3:4b")
    config = ROOT / ".env"
    if config.is_file() and "SAVOR_LOCAL_MODEL" not in os.environ:
        for line in config.read_text().splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() == "SAVOR_LOCAL_MODEL":
                model = value.strip().strip('"').strip("'")
    os.environ["SAVOR_LOCAL_MODEL"] = model
    if model not in ("qwen3:1.7b", "qwen3:4b"):
        raise RuntimeError("Only the supported local Qwen3 models are enabled.")
    process = start()
    if not ready():
        raise RuntimeError("The local Ollama service did not start.")
    try:
        print(
            f"Downloading local model {model}. No API account or paid service is used.",
            flush=True,
        )
        subprocess.run([binary, "pull", model], env=runtime_env(), check=True)
    finally:
        stop(process)


if __name__ == "__main__":
    setup()
