from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_retirement_launcher_is_syntax_valid_and_fail_closed() -> None:
    path = ROOT / "scripts/launch_superseded_archive_retirement.sh"
    source = path.read_text(encoding="utf-8")

    subprocess.run(["bash", "-n", str(path)], check=True)
    assert "execute mode requires a completed dry-run directory" in source
    assert "another retirement operation is active" in source
    assert ".active_run_paths_included==false" in source
    assert ".model_or_dataset_paths_included==false" in source
    assert 'EXECUTE_ARG=" --execute"' in source
    assert "validated_not_executed" in source
    assert "all_file_hashes_match" in source
