# Uncomment to enable logging during tests
from __future__ import annotations
import asyncio
import inspect
import io
import json
import os
import pathlib
import zipfile
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    Generator,
    NamedTuple,
    TextIO,
    Union,
    cast,
)
from typing_extensions import TypedDict

import pytest
from decoy import Decoy

try:
    import aionotify  # type: ignore[import]
except (OSError, ModuleNotFoundError):
    aionotify = None

from opentrons_shared_data.protocol.dev_types import JsonProtocol
from opentrons_shared_data.labware.dev_types import LabwareDefinition
from opentrons_shared_data.module.dev_types import ModuleDefinitionV3
from opentrons_shared_data.deck.dev_types import RobotModel, DeckDefinitionV3
from opentrons_shared_data.deck import (
    load as load_deck,
    DEFAULT_DECK_DEFINITION_VERSION,
)

from opentrons import config
from opentrons import hardware_control as hc
from opentrons.drivers.rpi_drivers.gpio_simulator import SimulatingGPIOCharDev
from opentrons.hardware_control import (
    API,
    HardwareControlAPI,
    ThreadManager,
    ThreadManagedHardware,
)
from opentrons.protocol_api import (
    MAX_SUPPORTED_VERSION,
    ProtocolContext,
    Labware,
    create_protocol_context,
)
from opentrons.protocol_api.core.protocol_api.labware import LabwareImplementation

from opentrons.types import Location, Point


if TYPE_CHECKING:
    from opentrons.drivers.smoothie_drivers import SmoothieDriver as SmoothieDriverType


class Protocol(NamedTuple):
    text: str
    filename: str
    filelike: TextIO


class Bundle(TypedDict):
    source_dir: pathlib.Path
    filename: str
    contents: str
    filelike: io.BytesIO
    binary_zipfile: bytes
    metadata: Dict[str, str]
    bundled_data: Dict[str, str]
    bundled_labware: Dict[str, LabwareDefinition]
    bundled_python: Dict[str, Any]


@pytest.fixture()
def ot_config_tempdir(tmp_path: pathlib.Path) -> Generator[pathlib.Path, None, None]:
    os.environ["OT_API_CONFIG_DIR"] = str(tmp_path)
    config.reload()

    yield tmp_path

    del os.environ["OT_API_CONFIG_DIR"]
    config.reload()


@pytest.fixture()
def is_robot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "IS_ROBOT", True)


@pytest.fixture
def mock_feature_flags(decoy: Decoy, monkeypatch: pytest.MonkeyPatch) -> None:
    for name, func in inspect.getmembers(config.feature_flags, inspect.isfunction):
        mock_get_ff = decoy.mock(func=func)
        decoy.when(mock_get_ff()).then_return(False)
        monkeypatch.setattr(config.feature_flags, name, mock_get_ff)


@pytest.fixture
async def enable_ot3_hardware_controller(
    request: pytest.FixtureRequest,
    decoy: Decoy,
    mock_feature_flags: None,
) -> None:
    # this is from the command line parameters added in root conftest
    if request.config.getoption("--ot2-only"):
        pytest.skip("testing only ot2")

    decoy.when(config.feature_flags.enable_ot3_hardware_controller()).then_return(True)


@pytest.fixture()
def protocol_file() -> str:
    return "testosaur_v2.py"


@pytest.fixture()
def protocol(protocol_file: str) -> Generator[Protocol, None, None]:
    root = protocol_file
    filename = os.path.join(os.path.dirname(__file__), "data", root)

    file = open(filename)
    text = "".join(list(file))
    file.seek(0)

    yield Protocol(text=text, filename=filename, filelike=file)

    file.close()


@pytest.fixture()
def virtual_smoothie_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # TODO (ben 20180426): move this to the .env file
    monkeypatch.setenv("ENABLE_VIRTUAL_SMOOTHIE", "true")


@pytest.fixture(params=["ot2", "ot3"])
async def machine_variant_ffs(
    request: pytest.FixtureRequest,
    decoy: Decoy,
    mock_feature_flags: None,
) -> None:
    device_param = request.param  # type: ignore[attr-defined]

    if request.node.get_closest_marker("ot3_only") and device_param == "ot2":
        pytest.skip()
    if request.node.get_closest_marker("ot2_only") and device_param == "ot3":
        pytest.skip()

    decoy.when(config.feature_flags.enable_ot3_hardware_controller()).then_return(
        device_param == "ot3"
    )


async def _build_ot2_hw() -> AsyncGenerator[ThreadManagedHardware, None]:
    hw_sim = ThreadManager(API.build_hardware_simulator)
    old_config = config.robot_configs.load()
    try:
        yield hw_sim
    finally:
        config.robot_configs.clear()
        for m in hw_sim.attached_modules:
            await m.cleanup()
        hw_sim.set_config(old_config)
        hw_sim.clean_up()


@pytest.fixture()
async def ot2_hardware(
    virtual_smoothie_env: None,
) -> AsyncGenerator[ThreadManagedHardware, None]:
    async for hw in _build_ot2_hw():
        yield hw


async def _build_ot3_hw() -> AsyncGenerator[ThreadManagedHardware, None]:
    from opentrons.hardware_control.ot3api import OT3API

    hw_sim = ThreadManager(OT3API.build_hardware_simulator)
    old_config = config.robot_configs.load()
    try:
        yield hw_sim
    finally:
        config.robot_configs.clear()
        for m in hw_sim.attached_modules:
            await m.cleanup()
        hw_sim.set_config(old_config)
        hw_sim.clean_up()


@pytest.fixture()
async def ot3_hardware(
    request: pytest.FixtureRequest,
    enable_ot3_hardware_controller: None,
) -> AsyncGenerator[ThreadManagedHardware, None]:
    # this is from the command line parameters added in root conftest
    if request.config.getoption("--ot2-only"):
        pytest.skip("testing only ot2")
    async for hw in _build_ot3_hw():
        yield hw


@pytest.fixture(params=["OT-2 Standard", "OT-3 Standard"])
async def robot_model(
    request: pytest.FixtureRequest,
    decoy: Decoy,
    mock_feature_flags: None,
    virtual_smoothie_env: None,
) -> AsyncGenerator[RobotModel, None]:
    which_machine = cast(RobotModel, request.param)  # type: ignore[attr-defined]
    if request.node.get_closest_marker("ot2_only") and which_machine == "OT-3 Standard":
        pytest.skip("test requests only ot-2")
    if request.node.get_closest_marker("ot3_only") and which_machine == "OT-2 Standard":
        pytest.skip("test requests only ot-3")
    if which_machine == "OT-3 Standard" and request.config.getoption("--ot2-only"):
        pytest.skip("testing only ot2")

    decoy.when(config.feature_flags.enable_ot3_hardware_controller()).then_return(
        which_machine == "OT-3 Standard"
    )

    yield which_machine


@pytest.fixture
def deck_definition(robot_model: RobotModel) -> DeckDefinitionV3:
    if robot_model == "OT-3 Standard":
        return load_deck("ot3_standard", DEFAULT_DECK_DEFINITION_VERSION)
    else:
        return load_deck("ot2_standard", DEFAULT_DECK_DEFINITION_VERSION)


@pytest.fixture()
async def hardware(
    request: pytest.FixtureRequest,
    decoy: Decoy,
    mock_feature_flags: None,
    virtual_smoothie_env: None,
    robot_model: RobotModel,
) -> AsyncGenerator[ThreadManagedHardware, None]:
    hw_builder = {"OT-2 Standard": _build_ot2_hw, "OT-3 Standard": _build_ot3_hw}[
        robot_model
    ]

    async for hw in hw_builder():
        decoy.when(config.feature_flags.enable_ot3_hardware_controller()).then_return(
            robot_model == "OT-3 Standard"
        )

        yield hw


@pytest.fixture()
def ctx(hardware: ThreadManagedHardware) -> Generator[ProtocolContext, None, None]:
    c = create_protocol_context(
        api_version=MAX_SUPPORTED_VERSION, hardware_api=hardware
    )
    yield c
    # Manually clean up all the modules.
    for m in c.loaded_modules.items():
        m[1]._module.cleanup()


@pytest.fixture()
async def smoothie(
    virtual_smoothie_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[SmoothieDriverType, None]:
    from opentrons.drivers.smoothie_drivers import SmoothieDriver
    from opentrons.config import robot_configs

    driver = SmoothieDriver(
        robot_configs.load_ot2(), SimulatingGPIOCharDev("simulated")
    )
    await driver.connect()
    yield driver
    try:
        await driver.disconnect()
    except AttributeError:
        # if the test disconnected
        pass


@pytest.fixture
def hardware_controller_lockfile(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> pathlib.Path:
    lockfile_dir = tmp_path / "hardware_controller_lockfile"
    lockfile_dir.mkdir()
    lockfile = lockfile_dir / "hardware.lock"

    monkeypatch.setitem(config.CONFIG, "hardware_controller_lockfile", lockfile)

    return lockfile_dir


@pytest.mark.skipif(
    not hc.Controller,
    reason="hardware controller not available (probably windows)",
)
@pytest.fixture()
def cntrlr_mock_connect(monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_connect(obj: object, port: Any = None) -> None:
        return

    monkeypatch.setattr(hc.Controller, "connect", mock_connect)
    monkeypatch.setattr(hc.Controller, "fw_version", "virtual")


@pytest.fixture()
async def hardware_api(is_robot: None) -> HardwareControlAPI:
    hw_api = await API.build_hardware_simulator(loop=asyncio.get_running_loop())
    return hw_api


@pytest.fixture()
def get_labware_fixture() -> Callable[[str], LabwareDefinition]:
    def _get_labware_fixture(fixture_name: str) -> LabwareDefinition:
        with open(
            (
                pathlib.Path(__file__).parent
                / ".."
                / ".."
                / ".."
                / "shared-data"
                / "labware"
                / "fixtures"
                / "2"
                / f"{fixture_name}.json"
            ),
            "rb",
        ) as f:
            return cast(LabwareDefinition, json.loads(f.read().decode("utf-8")))

    return _get_labware_fixture


@pytest.fixture()
def get_json_protocol_fixture() -> Callable[[str, str, bool], Union[str, JsonProtocol]]:
    def _get_json_protocol_fixture(
        fixture_version: str,
        fixture_name: str,
        decode: bool = True,
    ) -> Union[str, JsonProtocol]:
        with open(
            pathlib.Path(__file__).parent
            / ".."
            / ".."
            / ".."
            / "shared-data"
            / "protocol"
            / "fixtures"
            / fixture_version
            / f"{fixture_name}.json",
            "rb",
        ) as f:
            contents = f.read().decode("utf-8")
            if decode:
                return cast(JsonProtocol, json.loads(contents))
            else:
                return contents

    return _get_json_protocol_fixture


@pytest.fixture
def get_bundle_fixture() -> Callable[[str], Bundle]:
    def get_std_labware(loadName: str, version: int = 1) -> LabwareDefinition:
        with open(
            pathlib.Path(__file__).parent
            / ".."
            / ".."
            / ".."
            / "shared-data"
            / "labware"
            / "definitions"
            / "2"
            / loadName
            / f"{version}.json",
            "rb",
        ) as f:
            labware_def = cast(LabwareDefinition, json.loads(f.read().decode("utf-8")))
        return labware_def

    def _get_bundle_protocol_fixture(fixture_name: str) -> Bundle:
        """
        It's ugly to store bundles as .zip's, so we'll build the .zip
        from fixtures and return it as `bytes`.
        We also need to hard-code fixture data here (bundled_labware,
        bundled_python, bundled_data, metadata) for the tests to use in
        their assertions.
        """
        fixture_dir = (
            pathlib.Path(__file__).parent
            / "protocols"
            / "fixtures"
            / "bundled_protocols"
            / fixture_name
        )

        result: Bundle = {  # type: ignore[typeddict-item]
            "filename": f"{fixture_name}.zip",
            "source_dir": fixture_dir,
        }

        fixed_trash_def = get_std_labware("opentrons_1_trash_1100ml_fixed")

        empty_protocol = "def run(context):\n    pass"

        if fixture_name == "simple_bundle":
            with open(fixture_dir / "protocol.py", "r") as f:
                result["contents"] = f.read()
            with open(fixture_dir / "data.txt", "rb") as f:  # type: ignore[assignment]
                result["bundled_data"] = {"data.txt": f.read()}
            with open(fixture_dir / "custom_labware.json", "r") as f:
                custom_labware = json.load(f)

            tiprack_def = get_std_labware("opentrons_96_tiprack_10ul")
            result["bundled_labware"] = {
                "opentrons/opentrons_1_trash_1100ml_fixed/1": fixed_trash_def,
                "custom_beta/custom_labware/1": custom_labware,
                "opentrons/opentrons_96_tiprack_10ul/1": tiprack_def,
            }
            result["bundled_python"] = {}

            # NOTE: this is copy-pasted from the .py fixture file
            result["metadata"] = {"author": "MISTER FIXTURE", "apiLevel": "2.0"}

            # make binary zipfile
            binary_zipfile = io.BytesIO()
            with zipfile.ZipFile(binary_zipfile, "w") as z:
                z.writestr("labware/custom_labware.json", json.dumps(custom_labware))
                z.writestr("labware/tiprack.json", json.dumps(tiprack_def))
                z.writestr("labware/fixed_trash.json", json.dumps(fixed_trash_def))
                z.writestr("protocol.ot2.py", result["contents"])
                z.writestr("data/data.txt", result["bundled_data"]["data.txt"])
            binary_zipfile.seek(0)
            result["binary_zipfile"] = binary_zipfile.read()
            binary_zipfile.seek(0)
            result["filelike"] = binary_zipfile

        elif fixture_name == "no_root_files_bundle":
            binary_zipfile = io.BytesIO()
            with zipfile.ZipFile(binary_zipfile, "w") as z:
                z.writestr("inner_dir/protocol.ot2.py", empty_protocol)
            binary_zipfile.seek(0)
            result["binary_zipfile"] = binary_zipfile.read()
            binary_zipfile.seek(0)
            result["filelike"] = binary_zipfile
        elif fixture_name == "no_entrypoint_protocol_bundle":
            binary_zipfile = io.BytesIO()
            with zipfile.ZipFile(binary_zipfile, "w") as z:
                z.writestr("rando_pyfile_name.py", empty_protocol)
            binary_zipfile.seek(0)
            result["binary_zipfile"] = binary_zipfile.read()
            binary_zipfile.seek(0)
            result["filelike"] = binary_zipfile
        elif fixture_name == "conflicting_labware_bundle":
            binary_zipfile = io.BytesIO()
            with zipfile.ZipFile(binary_zipfile, "w") as z:
                plate_def = get_std_labware("biorad_96_wellplate_200ul_pcr")
                z.writestr("protocol.ot2.py", empty_protocol)
                z.writestr("labware/fixed_trash.json", json.dumps(fixed_trash_def))
                z.writestr("labware/plate.json", json.dumps(plate_def))
                z.writestr("labware/same_plate.json", json.dumps(plate_def))
            binary_zipfile.seek(0)
            result["binary_zipfile"] = binary_zipfile.read()
            binary_zipfile.seek(0)
            result["filelike"] = binary_zipfile
        elif fixture_name == "missing_labware_bundle":
            # parsing should fail b/c this bundle lacks labware defs.
            with open(fixture_dir / "protocol.py", "r") as f:
                protocol_contents = f.read()
            binary_zipfile = io.BytesIO()
            with zipfile.ZipFile(binary_zipfile, "w") as z:
                z.writestr("protocol.ot2.py", protocol_contents)
            binary_zipfile.seek(0)
            result["binary_zipfile"] = binary_zipfile.read()
            binary_zipfile.seek(0)
            result["filelike"] = binary_zipfile
        else:
            raise ValueError(
                f"get_bundle_fixture has no case to handle " f'fixture "{fixture_name}"'
            )
        return result

    return _get_bundle_protocol_fixture


@pytest.fixture()
def minimal_labware_def() -> LabwareDefinition:
    return {
        "metadata": {
            "displayName": "minimal labware",
            "displayCategory": "other",
            "displayVolumeUnits": "mL",
        },
        "cornerOffsetFromSlot": {"x": 10, "y": 10, "z": 5},
        "parameters": {
            "isTiprack": False,
            "loadName": "minimal_labware_def",
            "isMagneticModuleCompatible": True,
            "format": "irregular",
        },
        "ordering": [["A1"], ["A2"]],
        "wells": {
            "A1": {
                "depth": 40,
                "totalLiquidVolume": 100,
                "diameter": 30,
                "x": 0,
                "y": 0,
                "z": 0,
                "shape": "circular",
            },
            "A2": {
                "depth": 40,
                "totalLiquidVolume": 100,
                "diameter": 30,
                "x": 10,
                "y": 0,
                "z": 0,
                "shape": "circular",
            },
        },
        "dimensions": {"xDimension": 1.0, "yDimension": 2.0, "zDimension": 3.0},
        "groups": [],
        "brand": {"brand": "opentrons"},
        "version": 1,
        "schemaVersion": 2,
        "namespace": "opentronstest",
    }


@pytest.fixture()
def minimal_labware_def2() -> LabwareDefinition:
    return {
        "metadata": {
            "displayName": "other test labware",
            "displayCategory": "other",
            "displayVolumeUnits": "mL",
        },
        "cornerOffsetFromSlot": {"x": 10, "y": 10, "z": 5},
        "parameters": {
            "isTiprack": False,
            "loadName": "minimal_labware_def",
            "isMagneticModuleCompatible": True,
            "format": "irregular",
        },
        "ordering": [["A1", "B1", "C1"], ["A2", "B2", "C2"]],
        "wells": {
            "A1": {
                "depth": 40,
                "totalLiquidVolume": 100,
                "diameter": 30,
                "x": 0,
                "y": 18,
                "z": 0,
                "shape": "circular",
            },
            "B1": {
                "depth": 40,
                "totalLiquidVolume": 100,
                "diameter": 30,
                "x": 0,
                "y": 9,
                "z": 0,
                "shape": "circular",
            },
            "C1": {
                "depth": 40,
                "totalLiquidVolume": 100,
                "diameter": 30,
                "x": 0,
                "y": 0,
                "z": 0,
                "shape": "circular",
            },
            "A2": {
                "depth": 40,
                "totalLiquidVolume": 100,
                "diameter": 30,
                "x": 9,
                "y": 18,
                "z": 0,
                "shape": "circular",
            },
            "B2": {
                "depth": 40,
                "totalLiquidVolume": 100,
                "diameter": 30,
                "x": 9,
                "y": 9,
                "z": 0,
                "shape": "circular",
            },
            "C2": {
                "depth": 40,
                "totalLiquidVolume": 100,
                "diameter": 30,
                "x": 9,
                "y": 0,
                "z": 0,
                "shape": "circular",
            },
        },
        "groups": [],
        "dimensions": {"xDimension": 1.0, "yDimension": 2.0, "zDimension": 3.0},
        "schemaVersion": 2,
        "version": 1,
        "namespace": "dummy_namespace",
        "brand": {"brand": "opentrons"},
    }


@pytest.fixture()
def min_lw_impl(minimal_labware_def: LabwareDefinition) -> LabwareImplementation:
    return LabwareImplementation(
        definition=minimal_labware_def, parent=Location(Point(0, 0, 0), "deck")
    )


@pytest.fixture()
def min_lw2_impl(minimal_labware_def2: LabwareDefinition) -> LabwareImplementation:
    return LabwareImplementation(
        definition=minimal_labware_def2, parent=Location(Point(0, 0, 0), "deck")
    )


@pytest.fixture()
def min_lw(min_lw_impl: LabwareImplementation) -> Labware:
    return Labware(implementation=min_lw_impl)


@pytest.fixture()
def min_lw2(min_lw2_impl: LabwareImplementation) -> Labware:
    return Labware(implementation=min_lw2_impl)


@pytest.fixture()
def minimal_module_def() -> ModuleDefinitionV3:
    return {
        "$otSharedSchema": "module/schemas/3",
        "moduleType": "temperatureModuleType",
        "model": "temperatureModuleV1",
        "labwareOffset": {"x": -0.15, "y": -0.15, "z": 80.09},
        "dimensions": {
            "bareOverallHeight": 84,
            "overLabwareHeight": 0,
            "xDimension": 123,
            "yDimension": 321,
        },
        "calibrationPoint": {"x": 12.0, "y": 8.75, "z": 0.0},
        "config": {},
        "displayName": "Sample Module",
        "quirks": [],
        "slotTransforms": {},
        "compatibleWith": ["temperatureModuleV2"],
        "cornerOffsetFromSlot": {"x": 0.1, "y": 0.1, "z": 0.0},
        "twoDimensionalRendering": {},
    }
