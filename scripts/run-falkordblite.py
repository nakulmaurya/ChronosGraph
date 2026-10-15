"""Run owned, ephemeral native FalkorDB on localhost. No system-library changes.

Requires falkordblite==0.10.0 and a compatible platform. Optional loader/library
paths support workspace-only compatibility libraries; they are not downloaded.
The temporary DB exists only for this process lifetime. Never use for real data.
"""
import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile


def main():
    spec = importlib.util.find_spec("redislite")
    if spec is None or spec.origin is None:
        raise SystemExit("Install falkordblite==0.10.0 in this Python environment first")
    binaries = Path(spec.origin).parent / "bin"
    port = int(os.environ.get("FALKORDB_PORT", "6379"))
    if not 1024 <= port <= 65535:
        raise SystemExit("FALKORDB_PORT must be 1024..65535")
    command = [str(binaries / "redis-server")]
    loader = os.environ.get("FALKORDB_NATIVE_LOADER")
    library_path = os.environ.get("FALKORDB_NATIVE_LIBRARY_PATH")
    if loader:
        if not library_path or not Path(loader).is_file():
            raise SystemExit("A valid explicit loader and library path are required")
        command = [loader, "--library-path", library_path] + command
    with tempfile.TemporaryDirectory(prefix="chronosgraph-native-") as data:
        command += ["--bind", "127.0.0.1", "--protected-mode", "yes", "--port", str(port),
                    "--loadmodule", str(binaries / "falkordb.so"), "--dir", data, "--save", ""]
        process = subprocess.Popen(command)
        def stop(signum, frame):
            if process.poll() is None:
                process.terminate()
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        try:
            code = process.wait()
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=15)
        if code:
            print("Native startup failed. Check platform/glibc compatibility; no host libraries were changed.", file=sys.stderr)
        return code


if __name__ == "__main__":
    sys.exit(main())
