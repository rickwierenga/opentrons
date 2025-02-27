from typing import Any, Dict

import pytest
from pytest_lazyfixture import lazy_fixture  # type: ignore[import]
from opentrons.config.advanced_settings import _migrate, _ensure


@pytest.fixture
def migrated_file_version() -> int:
    return 17


@pytest.fixture
def default_file_settings() -> Dict[str, Any]:
    return {
        "shortFixedTrash": None,
        "deckCalibrationDots": None,
        "disableHomeOnBoot": None,
        "useOldAspirationFunctions": None,
        "disableLogAggregation": None,
        "enableDoorSafetySwitch": None,
        "disableFastProtocolUpload": None,
        "enableOT3HardwareController": None,
        "enableProtocolEnginePAPICore": None,
    }


@pytest.fixture
def empty_settings() -> Dict[str, Any]:
    return {}


@pytest.fixture
def version_less() -> Dict[str, Any]:
    return {
        "shortFixedTrash": True,
        "calibrateToBottom": True,
        "deckCalibrationDots": True,
        "disableHomeOnBoot": True,
        "useOldAspirationFunctions": True,
    }


@pytest.fixture
def v1_config() -> Dict[str, Any]:
    return {
        "_version": 1,
        "shortFixedTrash": True,
        "calibrateToBottom": True,
        "deckCalibrationDots": True,
        "disableHomeOnBoot": True,
        "useProtocolApi2": None,
        "useOldAspirationFunctions": True,
    }


@pytest.fixture
def v2_config(v1_config: Dict[str, Any]) -> Dict[str, Any]:
    r = v1_config.copy()
    r.update(
        {
            "_version": 2,
            "disableLogAggregation": True,
        }
    )
    return r


@pytest.fixture
def v3_config(v2_config: Dict[str, Any]) -> Dict[str, Any]:
    r = v2_config.copy()
    r.update({"_version": 3, "enableApi1BackCompat": False})
    return r


@pytest.fixture
def v4_config(v3_config: Dict[str, Any]) -> Dict[str, Any]:
    r = v3_config.copy()
    r.update({"_version": 4, "useV1HttpApi": False})
    return r


@pytest.fixture
def v5_config(v4_config: Dict[str, Any]) -> Dict[str, Any]:
    r = v4_config.copy()
    r.update(
        {
            "_version": 5,
            "enableDoorSafetySwitch": True,
        }
    )
    return r


@pytest.fixture
def v6_config(v5_config: Dict[str, Any]) -> Dict[str, Any]:
    r = v5_config.copy()
    r.update(
        {
            "_version": 6,
            "enableTipLengthCalibration": True,
        }
    )
    return r


@pytest.fixture
def v7_config(v6_config: Dict[str, Any]) -> Dict[str, Any]:
    r = v6_config.copy()
    r.update(
        {
            "_version": 7,
            "enableHttpProtocolSessions": True,
        }
    )
    return r


@pytest.fixture
def v8_config(v7_config: Dict[str, Any]) -> Dict[str, Any]:
    r = v7_config.copy()
    r.update(
        {
            "_version": 8,
            "enableFastProtocolUpload": True,
        }
    )
    return r


@pytest.fixture
def v9_config(v8_config: Dict[str, Any]) -> Dict[str, Any]:
    r = v8_config.copy()
    r.update(
        {
            "_version": 9,
            "enableProtocolEngine": True,
        }
    )
    return r


@pytest.fixture
def v10_config(v9_config: Dict[str, Any]) -> Dict[str, Any]:
    r = v9_config.copy()
    r.pop("useProtocolApi2")
    r.pop("enableApi1BackCompat")
    r.pop("useV1HttpApi")
    r.pop("enableTipLengthCalibration")
    r.pop("enableFastProtocolUpload")
    r.update(
        {
            "_version": 10,
            "disableFastProtocolUpload": True,
        }
    )
    return r


@pytest.fixture
def v11_config(v10_config: Dict[str, Any]) -> Dict[str, Any]:
    r = v10_config.copy()
    r.pop("enableProtocolEngine")
    r.update({"_version": 11})
    return r


@pytest.fixture
def v12_config(v11_config: Dict[str, Any]) -> Dict[str, Any]:
    r = v11_config.copy()
    r.update(
        {
            "_version": 12,
            "enableOT3HardwareController": True,
        }
    )
    return r


@pytest.fixture
def v13_config(v12_config: Dict[str, Any]) -> Dict[str, Any]:
    r = v12_config.copy()
    r.pop("calibrateToBottom")
    r.update({"_version": 13})
    return r


@pytest.fixture
def v14_config(v13_config: Dict[str, Any]) -> Dict[str, Any]:
    r = v13_config.copy()
    r.pop("enableHttpProtocolSessions")
    r.update({"_version": 14})
    return r


@pytest.fixture
def v15_config(v14_config: Dict[str, Any]) -> Dict[str, Any]:
    r = v14_config.copy()
    r.update(
        {
            "_version": 15,
            "enableHeaterShakerPAPI": True,
        }
    )
    return r


@pytest.fixture
def v16_config(v15_config: Dict[str, Any]) -> Dict[str, Any]:
    r = v15_config.copy()
    r.pop("enableHeaterShakerPAPI")
    r.update({"_version": 16})
    return r


@pytest.fixture
def v17_config(v16_config: Dict[str, Any]) -> Dict[str, Any]:
    r = v16_config.copy()
    r.update(
        {
            "_version": 17,
            "enableProtocolEnginePAPICore": True,
        }
    )
    return r


@pytest.fixture(
    scope="session",
    params=[
        lazy_fixture("empty_settings"),
        lazy_fixture("version_less"),
        lazy_fixture("v1_config"),
        lazy_fixture("v2_config"),
        lazy_fixture("v3_config"),
        lazy_fixture("v4_config"),
        lazy_fixture("v5_config"),
        lazy_fixture("v6_config"),
        lazy_fixture("v7_config"),
        lazy_fixture("v8_config"),
        lazy_fixture("v9_config"),
        lazy_fixture("v10_config"),
        lazy_fixture("v11_config"),
        lazy_fixture("v12_config"),
        lazy_fixture("v13_config"),
        lazy_fixture("v14_config"),
        lazy_fixture("v15_config"),
        lazy_fixture("v16_config"),
        lazy_fixture("v17_config"),
    ],
)
def old_settings(request: pytest.FixtureRequest) -> Dict[str, Any]:
    return request.param  # type: ignore[attr-defined, no-any-return]


def test_migrations(
    old_settings: Dict[str, Any],
    migrated_file_version: int,
    default_file_settings: Dict[str, Any],
) -> None:
    settings, version = _migrate(old_settings)

    expected = default_file_settings.copy()
    expected.update(
        {
            k: v
            for k, v in old_settings.items()
            if k != "_version" and k in default_file_settings
        }
    )

    assert version == migrated_file_version
    assert settings == expected


def test_migrates_versionless_old_config(
    migrated_file_version: int,
    default_file_settings: Dict[str, Any],
) -> None:
    settings, version = _migrate(
        {
            "short-fixed-trash": False,
            "calibrate-to-bottom": False,
            "dots-deck-type": True,
            "disable-home-on-boot": False,
        }
    )

    expected = default_file_settings.copy()
    expected.update(
        {
            "shortFixedTrash": None,
            "deckCalibrationDots": True,
            "disableHomeOnBoot": None,
        }
    )

    assert version == migrated_file_version
    assert settings == expected


def test_ignores_invalid_keys(
    migrated_file_version: int,
    default_file_settings: Dict[str, Any],
) -> None:
    settings, version = _migrate(
        {
            "split-labware-def": True,
            "splitLabwareDefinitions": True,
        }
    )

    assert version == migrated_file_version
    assert settings == default_file_settings


def test_ensures_config() -> None:
    assert _ensure(
        {"_version": 3, "shortFixedTrash": False, "disableLogAggregation": True}
    ) == {
        "_version": 3,
        "shortFixedTrash": False,
        "deckCalibrationDots": None,
        "disableHomeOnBoot": None,
        "useOldAspirationFunctions": None,
        "disableLogAggregation": True,
        "enableDoorSafetySwitch": None,
        "disableFastProtocolUpload": None,
        "enableOT3HardwareController": None,
        "enableProtocolEnginePAPICore": None,
    }
