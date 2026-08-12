"""Real tests for SandboxConfig/FilesystemMount -- closes the CI gap where
`pytest packages/fabrica/tests` failed with 'file or directory not found'
because this directory never existed. Also see MCPServerConfig tests in
test_mcp_types.py.
"""

from __future__ import annotations

import pytest

from fabrica.sandbox.config import FilesystemMount, SandboxConfig


def test_filesystem_mount_defaults_to_read_only() -> None:
    mount = FilesystemMount(path="/workspace")
    assert mount.mode == "ro"


def test_filesystem_mount_rejects_invalid_mode() -> None:
    with pytest.raises(ValueError, match="mode must be"):
        FilesystemMount(path="/workspace", mode="invalid")


def test_sandbox_config_defaults_disabled_deny() -> None:
    config = SandboxConfig()
    assert config.enabled is False
    assert config.network == "deny"
    assert config.filesystem == []


def test_sandbox_config_rejects_invalid_network_value() -> None:
    with pytest.raises(ValueError, match="network must be"):
        SandboxConfig(network="invalid")


def test_sandbox_config_from_dict_parses_string_mounts() -> None:
    config = SandboxConfig.from_dict(
        {
            "enabled": True,
            "network": "deny",
            "filesystem": ["/workspace:rw", "/etc/ssl/certs:ro", "/etc/hosts"],
        }
    )

    assert config.enabled is True
    assert config.filesystem[0] == FilesystemMount(path="/workspace", mode="rw")
    assert config.filesystem[1] == FilesystemMount(path="/etc/ssl/certs", mode="ro")
    # No mode suffix defaults to read-only.
    assert config.filesystem[2] == FilesystemMount(path="/etc/hosts", mode="ro")


def test_sandbox_config_from_dict_parses_dict_mounts() -> None:
    config = SandboxConfig.from_dict({"filesystem": [{"path": "/data", "mode": "rw"}]})

    assert config.filesystem == [FilesystemMount(path="/data", mode="rw")]


def test_sandbox_config_from_dict_defaults_when_keys_missing() -> None:
    config = SandboxConfig.from_dict({})

    assert config.enabled is False
    assert config.network == "deny"
    assert config.filesystem == []
