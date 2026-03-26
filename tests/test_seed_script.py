import os
import runpy
import sqlite3
import subprocess
import sys
from pathlib import Path


def test_seed_script_imports_cleanly_without_running_main():
    seed_script = Path(__file__).resolve().parent.parent / "scripts" / "seed.py"

    runpy.run_path(str(seed_script), run_name="seed_script_for_test")


def test_seed_script_runs_from_cli_and_populates_database(tmp_path):
    project_root = Path(__file__).resolve().parent.parent
    db_path = tmp_path / "seed_test.db"
    seed_script = project_root / "scripts" / "seed.py"
    seed_module = runpy.run_path(str(seed_script), run_name="seed_script_metadata")
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{db_path}",
        "SEED_SIGHTING_COUNT": "10",
    }

    result = subprocess.run(
        [sys.executable, "scripts/seed.py"],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "=== Seeding Complete ===" in result.stdout

    with sqlite3.connect(db_path) as connection:
        pokemon_count = connection.execute("SELECT COUNT(*) FROM pokemon").fetchone()[0]
        ranger_count = connection.execute("SELECT COUNT(*) FROM rangers").fetchone()[0]
        sighting_count = connection.execute(
            "SELECT COUNT(*) FROM sightings"
        ).fetchone()[0]

    assert pokemon_count == 493
    assert ranger_count == len(seed_module["RANGER_DATA"])
    assert sighting_count == 10
