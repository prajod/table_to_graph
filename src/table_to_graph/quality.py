"""Repository quality-check command used by contributors and CI."""

import os
import shutil

# Developer-only runner; subprocess executes only the fixed command list in main().
import subprocess  # nosec B404
import sys


def run_command(command: list[str], step_name: str) -> None:
    """Run one required quality command and stop on failure."""
    print("\n" + "=" * 60)
    print(f"[RUN] {step_name}...")
    print("=" * 60)

    cmd_path = shutil.which(command[0])
    if not cmd_path:
        print(f"\n[FAIL] {step_name}: required command '{command[0]}' was not found.")
        raise SystemExit(1)

    if os.name == "nt" and not cmd_path.lower().endswith((".exe", ".cmd", ".bat")):
        command = [sys.executable, cmd_path, *command[1:]]
    else:
        command[0] = cmd_path

    # The command comes from main()'s fixed list; shell=False prevents shell interpretation.
    result = subprocess.run(command, check=False)  # nosec B603
    if result.returncode != 0:
        print(f"\n[FAIL] {step_name}. Aborting further checks.")
        raise SystemExit(result.returncode)

    print(f"[PASS] {step_name}")


def main() -> None:
    """Run formatting, linting, typing, security, and test gates."""
    print("Starting comprehensive code quality and security checks...")

    commands = [
        (["ruff", "format", "--check", "src", "tests", "benchmarks", "scripts"], "Ruff Formatting"),
        (["ruff", "check", "src", "tests", "benchmarks", "scripts"], "Ruff Linting"),
        (["mypy", "src", "tests"], "MyPy Static Type Checking"),
        (["bandit", "-r", "src/table_to_graph"], "Bandit Security Scanning"),
        (
            [
                "pytest",
                "--cov=table_to_graph",
                "--cov-report=term-missing",
                "--cov-fail-under=90",
                "tests",
            ],
            "Pytest Test Suite",
        ),
    ]

    for command, name in commands:
        run_command(command, name)

    print("\n" + "=" * 60)
    print("[PASS] All code quality, security, and test checks completed successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()
