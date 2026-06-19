import json

import bcrypt
import pytest

import setup as setup_mod


@pytest.fixture
def auth_file(tmp_path, monkeypatch):
    path = tmp_path / "auth.json"
    monkeypatch.setattr(setup_mod, "AUTH_FILE", str(path))
    for var in ("ODYSSEUS_ADMIN_PASSWORD_RESET", "ODYSSEUS_ADMIN_PASSWORD", "ODYSSEUS_ADMIN_USER"):
        monkeypatch.delenv(var, raising=False)
    return path


def _seed(path, **users):
    path.write_text(json.dumps({"users": users, "allow_signup": False}))


def test_reset_requested_flag(monkeypatch):
    for val, expected in [("true", True), ("1", True), ("on", True),
                          ("false", False), ("", False), ("nope", False)]:
        monkeypatch.setenv("ODYSSEUS_ADMIN_PASSWORD_RESET", val)
        assert setup_mod._admin_reset_requested() is expected


def test_reset_updates_only_target_user(auth_file, monkeypatch):
    old = bcrypt.hashpw(b"old-temp-pass", bcrypt.gensalt()).decode()
    _seed(auth_file,
          admin={"password_hash": old, "is_admin": True},
          alice={"password_hash": "x", "is_admin": False})

    monkeypatch.setenv("ODYSSEUS_ADMIN_PASSWORD_RESET", "true")
    monkeypatch.setenv("ODYSSEUS_ADMIN_PASSWORD", "my-new-password-123")

    assert setup_mod.reset_admin_password() == "reset"

    data = json.loads(auth_file.read_text())
    admin = data["users"]["admin"]
    assert admin["is_admin"] is True
    assert bcrypt.checkpw(b"my-new-password-123", admin["password_hash"].encode())
    assert not bcrypt.checkpw(b"old-temp-pass", admin["password_hash"].encode())
    # Untouched: other users and unrelated settings.
    assert data["users"]["alice"] == {"password_hash": "x", "is_admin": False}
    assert data["allow_signup"] is False


def test_reset_seeds_admin_when_file_absent(auth_file, monkeypatch):
    monkeypatch.setenv("ODYSSEUS_ADMIN_PASSWORD_RESET", "true")
    monkeypatch.setenv("ODYSSEUS_ADMIN_PASSWORD", "brand-new-pass-9")

    assert setup_mod.reset_admin_password() == "reset"
    data = json.loads(auth_file.read_text())
    assert data["users"]["admin"]["is_admin"] is True
    assert bcrypt.checkpw(b"brand-new-pass-9", data["users"]["admin"]["password_hash"].encode())


def test_reset_rejects_short_password(auth_file, monkeypatch):
    monkeypatch.setenv("ODYSSEUS_ADMIN_PASSWORD_RESET", "true")
    monkeypatch.setenv("ODYSSEUS_ADMIN_PASSWORD", "short")
    assert setup_mod.reset_admin_password() == "failed"
    assert not auth_file.exists()


def test_reset_requires_password(auth_file, monkeypatch):
    monkeypatch.setenv("ODYSSEUS_ADMIN_PASSWORD_RESET", "true")
    assert setup_mod.reset_admin_password() == "failed"


def test_reset_targets_custom_admin_user(auth_file, monkeypatch):
    monkeypatch.setenv("ODYSSEUS_ADMIN_PASSWORD_RESET", "true")
    monkeypatch.setenv("ODYSSEUS_ADMIN_PASSWORD", "custom-user-pass")
    monkeypatch.setenv("ODYSSEUS_ADMIN_USER", "justin")

    assert setup_mod.reset_admin_password() == "reset"
    data = json.loads(auth_file.read_text())
    assert data["users"]["justin"]["is_admin"] is True
