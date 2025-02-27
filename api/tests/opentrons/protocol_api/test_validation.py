"""Tests for Protocol API input validation."""
from typing import List, Union

import pytest

from opentrons_shared_data.pipette.dev_types import PipetteNameType
from opentrons.types import Mount, DeckSlotName
from opentrons.hardware_control.modules.types import (
    ModuleModel,
    MagneticModuleModel,
    TemperatureModuleModel,
    ThermocyclerModuleModel,
    HeaterShakerModuleModel,
)
from opentrons.protocol_api import validation as subject


@pytest.mark.parametrize(
    ["input_value", "expected"],
    [
        ("left", Mount.LEFT),
        ("right", Mount.RIGHT),
        ("LeFt", Mount.LEFT),
        (Mount.LEFT, Mount.LEFT),
        (Mount.RIGHT, Mount.RIGHT),
    ],
)
def test_ensure_mount(input_value: Union[str, Mount], expected: Mount) -> None:
    """It should properly map strings and mounts."""
    result = subject.ensure_mount(input_value)
    assert result == expected


def test_ensure_mount_input_invalid() -> None:
    """It should raise if given invalid mount input."""
    with pytest.raises(ValueError, match="must be 'left' or 'right'"):
        subject.ensure_mount("oh no")

    with pytest.raises(TypeError, match="'left', 'right', or an opentrons.types.Mount"):
        subject.ensure_mount(42)  # type: ignore[arg-type]


def test_ensure_pipette_name() -> None:
    """It should properly map strings and PipetteNameType enums."""
    result = subject.ensure_pipette_name("p300_single")
    assert result == PipetteNameType.P300_SINGLE


def test_ensure_pipette_input_invalid() -> None:
    """It should raise a ValueError if given an invalid name."""
    with pytest.raises(ValueError, match="must be given valid pipette name"):
        subject.ensure_pipette_name("oh-no")


@pytest.mark.parametrize(
    ["input_value", "expected"],
    [
        ("1", DeckSlotName.SLOT_1),
        (1, DeckSlotName.SLOT_1),
        (12, DeckSlotName.FIXED_TRASH),
        ("12", DeckSlotName.FIXED_TRASH),
    ],
)
def test_ensure_deck_slot(input_value: Union[str, int], expected: DeckSlotName) -> None:
    """It should map strings and ints to DeckSlotName values."""
    result = subject.ensure_deck_slot(input_value)
    assert result == expected


def test_ensure_deck_slot_invalid() -> None:
    """It should raise a ValueError if given an invalid name."""
    input_values: List[Union[str, int]] = ["0", 0, "13", 13]

    for input_value in input_values:
        with pytest.raises(ValueError, match="not a valid deck slot"):
            subject.ensure_deck_slot(input_value)

    with pytest.raises(TypeError, match="must be a string or integer"):
        subject.ensure_deck_slot(1.23)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("load_name", "expected_model"),
    [
        ("magdeck", MagneticModuleModel.MAGNETIC_V1),
        ("MaGdEcK", MagneticModuleModel.MAGNETIC_V1),
        ("magnetic module", MagneticModuleModel.MAGNETIC_V1),
        ("magneticModuleV1", MagneticModuleModel.MAGNETIC_V1),
        ("magnetic module gen2", MagneticModuleModel.MAGNETIC_V2),
        ("magneticModuleV2", MagneticModuleModel.MAGNETIC_V2),
        ("tempdeck", TemperatureModuleModel.TEMPERATURE_V1),
        ("tEmpDeCk", TemperatureModuleModel.TEMPERATURE_V1),
        ("temperatureModuleV1", TemperatureModuleModel.TEMPERATURE_V1),
        ("temperature module", TemperatureModuleModel.TEMPERATURE_V1),
        ("temperature module gen2", TemperatureModuleModel.TEMPERATURE_V2),
        ("temperatureModuleV2", TemperatureModuleModel.TEMPERATURE_V2),
        ("thermocycler", ThermocyclerModuleModel.THERMOCYCLER_V1),
        ("ThErMoCyClEr", ThermocyclerModuleModel.THERMOCYCLER_V1),
        ("thermocycler module", ThermocyclerModuleModel.THERMOCYCLER_V1),
        ("thermocyclerModuleV1", ThermocyclerModuleModel.THERMOCYCLER_V1),
        ("thermocycler module gen2", ThermocyclerModuleModel.THERMOCYCLER_V2),
        ("thermocyclerModuleV2", ThermocyclerModuleModel.THERMOCYCLER_V2),
        ("heaterShakerModuleV1", HeaterShakerModuleModel.HEATER_SHAKER_V1),
    ],
)
def test_ensure_module_model(load_name: str, expected_model: ModuleModel) -> None:
    """It should map an module load name to a specific model."""
    result = subject.ensure_module_model(load_name)
    assert result == expected_model


def test_ensure_module_model_invalid() -> None:
    """It should reject invalid module load names."""
    with pytest.raises(ValueError, match="not a valid module load name"):
        subject.ensure_module_model("spline reticulator")

    with pytest.raises(TypeError, match="must be a string"):
        subject.ensure_module_model(42)  # type: ignore[arg-type]
