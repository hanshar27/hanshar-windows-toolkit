import subprocess
from typing import List


def run_command(args: List[str], timeout: int = 30, shell: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        shell=shell,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
