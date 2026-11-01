import shutil
from pathlib import Path

import pytest

from psclose.config import Config
from psclose.ledger import assemble, open_ledger

ROOT = Path(__file__).resolve().parents[1]
BASE_DB = ROOT / "data" / "synthetic_ps_recon_scaled.sqlite"
JULY_DB = ROOT / "data" / "july_increment.sqlite"


@pytest.fixture(scope="session")
def config() -> Config:
    return Config.load(ROOT / "psclose.toml")


@pytest.fixture(scope="session")
def policy(config):
    return config.policy


@pytest.fixture
def history_ledger(tmp_path):
    """The June-closed base on its own, for replaying history."""
    conn = assemble(BASE_DB, [], tmp_path / "history.sqlite")
    yield conn
    conn.close()


@pytest.fixture
def july_ledger(tmp_path):
    """Base plus the July increment, before any July close has run."""
    conn = assemble(BASE_DB, [JULY_DB], tmp_path / "july.sqlite")
    yield conn
    conn.close()
