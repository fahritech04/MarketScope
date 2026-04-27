from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def scrape_with_scrapy_batch(
    urls: list[str],
    timeout_seconds: int = 20,
    delay_seconds: float = 1.5,
    concurrent_requests: int = 8,
    obey_robots_txt: bool = True,
    allow_insecure_ssl: bool = False,
) -> list[dict[str, Any]]:
    if not urls:
        return []

    api_workdir = Path(__file__).resolve().parents[2]

    with tempfile.TemporaryDirectory(prefix="marketscope_scrapy_") as tmpdir:
        input_path = Path(tmpdir) / "input.json"
        output_path = Path(tmpdir) / "output.json"
        input_path.write_text(json.dumps({"urls": urls}, ensure_ascii=False), encoding="utf-8")

        command = [
            sys.executable,
            "-m",
            "app.workers.scrapy_cli",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--timeout",
            str(timeout_seconds),
            "--delay",
            str(delay_seconds),
            "--concurrency",
            str(concurrent_requests),
            "--obey-robots",
            "1" if obey_robots_txt else "0",
            "--allow-insecure-ssl",
            "1" if allow_insecure_ssl else "0",
        ]

        result = subprocess.run(
            command,
            cwd=str(api_workdir),
            capture_output=True,
            text=True,
            timeout=max(120, timeout_seconds * max(3, len(urls))),
            check=False,
        )
        if result.returncode != 0 or not output_path.exists():
            return []

        payload = json.loads(output_path.read_text(encoding="utf-8"))
        return payload.get("results", [])

