"""ProtocolEngine shared test fixtures."""
import pytest

from opentrons_shared_data import load_shared_data
from opentrons_shared_data.deck import load as load_deck
from opentrons_shared_data.deck.dev_types import DeckDefinitionV3
from opentrons_shared_data.labware import load_definition
from opentrons.protocols.models import LabwareDefinition
from opentrons.protocols.api_support.constants import (
    STANDARD_OT2_DECK,
    SHORT_TRASH_DECK,
)
from opentrons.protocol_engine.types import ModuleDefinition


@pytest.fixture(scope="session")
def standard_deck_def() -> DeckDefinitionV3:
    """Get the OT-2 standard deck definition."""
    return load_deck(STANDARD_OT2_DECK, 3)


@pytest.fixture(scope="session")
def short_trash_deck_def() -> DeckDefinitionV3:
    """Get the OT-2 short-trash deck definition."""
    return load_deck(SHORT_TRASH_DECK, 3)


@pytest.fixture(scope="session")
def fixed_trash_def() -> LabwareDefinition:
    """Get the definition of the OT-2 standard fixed trash."""
    return LabwareDefinition.parse_obj(
        load_definition("opentrons_1_trash_1100ml_fixed", 1)
    )


@pytest.fixture(scope="session")
def short_fixed_trash_def() -> LabwareDefinition:
    """Get the definition of the OT-2 short fixed trash."""
    return LabwareDefinition.parse_obj(
        load_definition("opentrons_1_trash_850ml_fixed", 1)
    )


@pytest.fixture(scope="session")
def well_plate_def() -> LabwareDefinition:
    """Get the definition of a 96 well plate."""
    return LabwareDefinition.parse_obj(
        load_definition("corning_96_wellplate_360ul_flat", 1)
    )


@pytest.fixture(scope="session")
def reservoir_def() -> LabwareDefinition:
    """Get the definition of single-row reservoir."""
    return LabwareDefinition.parse_obj(load_definition("nest_12_reservoir_15ml", 1))


@pytest.fixture(scope="session")
def tip_rack_def() -> LabwareDefinition:
    """Get the definition of Opentrons 300 uL tip rack."""
    return LabwareDefinition.parse_obj(load_definition("opentrons_96_tiprack_300ul", 1))


@pytest.fixture
def falcon_tuberack_def() -> LabwareDefinition:
    """Get the definition of the 6-well Falcon tuberack."""
    return LabwareDefinition.parse_obj(
        load_definition("opentrons_6_tuberack_falcon_50ml_conical", 1)
    )


@pytest.fixture(scope="session")
def tempdeck_v1_def() -> ModuleDefinition:
    """Get the definition of a V1 tempdeck."""
    definition = load_shared_data("module/definitions/3/temperatureModuleV1.json")
    return ModuleDefinition.parse_raw(definition)


@pytest.fixture(scope="session")
def tempdeck_v2_def() -> ModuleDefinition:
    """Get the definition of a V2 tempdeck."""
    definition = load_shared_data("module/definitions/3/temperatureModuleV2.json")
    return ModuleDefinition.parse_raw(definition)


@pytest.fixture(scope="session")
def magdeck_v1_def() -> ModuleDefinition:
    """Get the definition of a V1 magdeck."""
    definition = load_shared_data("module/definitions/3/magneticModuleV1.json")
    return ModuleDefinition.parse_raw(definition)


@pytest.fixture(scope="session")
def magdeck_v2_def() -> ModuleDefinition:
    """Get the definition of a V2 magdeck."""
    definition = load_shared_data("module/definitions/3/magneticModuleV2.json")
    return ModuleDefinition.parse_raw(definition)


@pytest.fixture(scope="session")
def thermocycler_v1_def() -> ModuleDefinition:
    """Get the definition of a V2 thermocycler."""
    definition = load_shared_data("module/definitions/3/thermocyclerModuleV1.json")
    return ModuleDefinition.parse_raw(definition)


@pytest.fixture(scope="session")
def thermocycler_v2_def() -> ModuleDefinition:
    """Get the definition of a V2 thermocycler."""
    definition = load_shared_data("module/definitions/3/thermocyclerModuleV2.json")
    return ModuleDefinition.parse_raw(definition)


@pytest.fixture(scope="session")
def heater_shaker_v1_def() -> ModuleDefinition:
    """Get the definition of a V1 heater-shaker."""
    definition = load_shared_data("module/definitions/3/heaterShakerModuleV1.json")
    return ModuleDefinition.parse_raw(definition)
