from transcritor.updates import is_newer_version, version_key


def test_version_key_accepts_stable_release_tags() -> None:
    assert version_key("v1.2.3") == (1, 2, 3)
    assert version_key("1.2") == (1, 2)
    assert version_key("preview") is None


def test_update_check_compares_versions_without_downgrade() -> None:
    assert is_newer_version("0.1.0", "v0.1.1")
    assert is_newer_version("0.1.0", "v0.2.0")
    assert not is_newer_version("0.1.0", "v0.1.0")
    assert not is_newer_version("0.2.0", "v0.1.9")
