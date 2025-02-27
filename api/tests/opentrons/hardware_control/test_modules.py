import asyncio
import pytest

from pathlib import Path
from unittest import mock

from opentrons.hardware_control import ExecutionManager
from opentrons.hardware_control.modules import ModuleAtPort
from opentrons.hardware_control.modules.types import (
    BundledFirmware,
    ModuleModel,
    MagneticModuleModel,
    TemperatureModuleModel,
    HeaterShakerModuleModel,
    ThermocyclerModuleModel,
    ModuleType,
)
from opentrons.hardware_control.modules import (
    TempDeck,
    MagDeck,
    Thermocycler,
    HeaterShaker,
    AbstractModule,
)
from opentrons.drivers.rpi_drivers.types import USBPort


async def test_get_modules_simulating():
    import opentrons.hardware_control as hardware_control

    mods = ["tempdeck", "magdeck", "thermocycler", "heatershaker"]
    api = await hardware_control.API.build_hardware_simulator(attached_modules=mods)
    await asyncio.sleep(0.05)
    from_api = api.attached_modules
    assert sorted([mod.name() for mod in from_api]) == sorted(mods)
    for m in api.attached_modules:
        await m.cleanup()


async def test_module_caching():
    import opentrons.hardware_control as hardware_control

    mod_names = ["tempdeck"]
    api = await hardware_control.API.build_hardware_simulator(
        attached_modules=mod_names
    )
    await asyncio.sleep(0.05)

    # Check that we can add and remove modules and the caching keeps up
    found_mods = api.attached_modules
    assert found_mods[0].name() == "tempdeck"
    await api._backend.module_controls.register_modules(
        new_mods_at_ports=[
            ModuleAtPort(port="/dev/ot_module_sim_magdeck1", name="magdeck")
        ]
    )
    with_magdeck = api.attached_modules.copy()
    assert len(with_magdeck) == 2
    assert with_magdeck[0] is found_mods[0]
    await api._backend.module_controls.register_modules(
        removed_mods_at_ports=[
            ModuleAtPort(port="/dev/ot_module_sim_tempdeck0", name="tempdeck")
        ]
    )
    only_magdeck = api.attached_modules.copy()
    assert only_magdeck[0] is with_magdeck[1]

    # Check that two modules of the same kind on different ports are
    # distinct
    await api._backend.module_controls.register_modules(
        new_mods_at_ports=[
            ModuleAtPort(port="/dev/ot_module_sim_magdeck2", name="magdeck")
        ]
    )
    two_magdecks = api.attached_modules
    assert len(two_magdecks) == 2
    assert two_magdecks[0] is with_magdeck[1]
    assert two_magdecks[1] is not two_magdecks[0]


@pytest.mark.parametrize(
    argnames=["module_model", "expected_sim_type"],
    argvalues=[
        (MagneticModuleModel.MAGNETIC_V1, MagDeck),
        (TemperatureModuleModel.TEMPERATURE_V1, TempDeck),
        (ThermocyclerModuleModel.THERMOCYCLER_V1, Thermocycler),
        (HeaterShakerModuleModel.HEATER_SHAKER_V1, HeaterShaker),
    ],
)
async def test_create_simulating_module(
    module_model: ModuleModel,
    expected_sim_type: AbstractModule,
) -> None:
    """It should create simulating module instance for specified module."""
    import opentrons.hardware_control as hardware_control

    api = await hardware_control.API.build_hardware_simulator(attached_modules=[])
    await asyncio.sleep(0.05)

    simulating_module = await api.create_simulating_module(module_model)
    assert isinstance(simulating_module, expected_sim_type)

    await simulating_module.cleanup()


@pytest.fixture
async def mod_tempdeck():
    from opentrons.hardware_control import modules

    loop = asyncio.get_running_loop()

    usb_port = USBPort(
        name="",
        hub=None,
        port_number=0,
        device_path="/dev/ot_module_sim_tempdeck0",
    )

    tempdeck = await modules.build(
        port="/dev/ot_module_sim_tempdeck0",
        usb_port=usb_port,
        type=ModuleType.TEMPERATURE,
        simulating=True,
        loop=loop,
        execution_manager=ExecutionManager(),
        sim_model="temperatureModuleV2",
    )
    yield tempdeck
    await tempdeck.cleanup()


@pytest.fixture
async def mod_magdeck():
    from opentrons.hardware_control import modules

    loop = asyncio.get_running_loop()

    usb_port = USBPort(
        name="",
        hub=None,
        port_number=0,
        device_path="/dev/ot_module_sim_magdeck0",
    )

    magdeck = await modules.build(
        port="/dev/ot_module_sim_magdeck0",
        usb_port=usb_port,
        type=ModuleType.MAGNETIC,
        simulating=True,
        loop=loop,
        execution_manager=ExecutionManager(),
    )
    yield magdeck
    await magdeck.cleanup()


@pytest.fixture
async def mod_thermocycler():
    from opentrons.hardware_control import modules

    loop = asyncio.get_running_loop()

    usb_port = USBPort(
        name="",
        hub=None,
        port_number=0,
        device_path="/dev/ot_module_sim_thermocycler0",
    )

    thermocycler = await modules.build(
        port="/dev/ot_module_sim_thermocycler0",
        usb_port=usb_port,
        type=ModuleType.THERMOCYCLER,
        simulating=True,
        loop=loop,
        execution_manager=ExecutionManager(),
    )
    yield thermocycler
    await thermocycler.cleanup()


@pytest.fixture
async def mod_thermocycler_gen2():
    from opentrons.hardware_control import modules

    loop = asyncio.get_running_loop()

    usb_port = USBPort(
        name="",
        hub=None,
        port_number=0,
        device_path="/dev/ot_module_sim_thermocycler0",
    )

    thermocycler = await modules.build(
        port="/dev/ot_module_sim_thermocycler0",
        usb_port=usb_port,
        type=ModuleType.THERMOCYCLER,
        simulating=True,
        loop=loop,
        execution_manager=ExecutionManager(),
        sim_model="thermocyclerModuleV2",
    )
    yield thermocycler
    await thermocycler.cleanup()


@pytest.fixture
async def mod_heatershaker():
    from opentrons.hardware_control import modules

    loop = asyncio.get_running_loop()

    usb_port = USBPort(
        name="",
        hub=None,
        port_number=0,
        device_path="/dev/ot_module_sim_heatershaker0",
    )

    heatershaker = await modules.build(
        port="/dev/ot_module_sim_heatershaker0",
        usb_port=usb_port,
        type=ModuleType.HEATER_SHAKER,
        simulating=True,
        loop=loop,
        execution_manager=ExecutionManager(),
    )
    yield heatershaker
    await heatershaker.cleanup()


async def test_module_update_integration(
    monkeypatch,
    mod_tempdeck,
    mod_magdeck,
    mod_thermocycler,
    mod_heatershaker,
    mod_thermocycler_gen2,
):
    from opentrons.hardware_control import modules

    loop = asyncio.get_running_loop()

    def async_return(result):
        f = asyncio.Future()
        f.set_result(result)
        return f

    bootloader_kwargs = {
        "stdout": asyncio.subprocess.PIPE,
        "stderr": asyncio.subprocess.PIPE,
        "loop": loop,
    }

    upload_via_avrdude_mock = mock.Mock(
        return_value=(async_return((True, "avrdude bootloader worked")))
    )
    monkeypatch.setattr(modules.update, "upload_via_avrdude", upload_via_avrdude_mock)

    async def mock_find_avrdude_bootloader_port():
        return "ot_module_avrdude_bootloader1"

    monkeypatch.setattr(
        modules.update, "find_bootloader_port", mock_find_avrdude_bootloader_port
    )

    # test temperature module update with avrdude bootloader
    await modules.update_firmware(mod_tempdeck, "fake_fw_file_path", loop)
    upload_via_avrdude_mock.assert_called_once_with(
        "ot_module_avrdude_bootloader1", "fake_fw_file_path", bootloader_kwargs
    )
    upload_via_avrdude_mock.reset_mock()

    # test magnetic module update with avrdude bootloader
    await modules.update_firmware(mod_magdeck, "fake_fw_file_path", loop)
    upload_via_avrdude_mock.assert_called_once_with(
        "ot_module_avrdude_bootloader1", "fake_fw_file_path", bootloader_kwargs
    )

    # test thermocycler module update with bossa bootloader
    upload_via_bossa_mock = mock.Mock(
        return_value=(async_return((True, "bossa bootloader worked")))
    )
    monkeypatch.setattr(modules.update, "upload_via_bossa", upload_via_bossa_mock)

    async def mock_find_bossa_bootloader_port():
        return "ot_module_bossa_bootloader1"

    monkeypatch.setattr(
        modules.update, "find_bootloader_port", mock_find_bossa_bootloader_port
    )

    await modules.update_firmware(mod_thermocycler, "fake_fw_file_path", loop)
    upload_via_bossa_mock.assert_called_once_with(
        "ot_module_bossa_bootloader1", "fake_fw_file_path", bootloader_kwargs
    )

    # test heater-shaker module update with dfu bootloader
    upload_via_dfu_mock = mock.Mock(
        return_value=(async_return((True, "dfu bootloader worked")))
    )
    monkeypatch.setattr(modules.update, "upload_via_dfu", upload_via_dfu_mock)

    async def mock_find_dfu_device_hs(pid: str, expected_device_count: int):
        if expected_device_count == 2:
            return "df11"
        return "none"

    monkeypatch.setattr(modules.update, "find_dfu_device", mock_find_dfu_device_hs)

    await modules.update_firmware(mod_heatershaker, "fake_fw_file_path", loop)
    upload_via_dfu_mock.assert_called_once_with(
        "df11", "fake_fw_file_path", bootloader_kwargs
    )
    upload_via_dfu_mock.reset_mock()

    async def mock_find_dfu_device_tc2(pid: str, expected_device_count: int):
        if expected_device_count == 3:
            return "df11"
        return "none"

    monkeypatch.setattr(modules.update, "find_dfu_device", mock_find_dfu_device_tc2)

    await modules.update_firmware(mod_thermocycler_gen2, "fake_fw_file_path", loop)
    upload_via_dfu_mock.assert_called_once_with(
        "df11", "fake_fw_file_path", bootloader_kwargs
    )

    mod_thermocycler_gen2


async def test_get_bundled_fw(monkeypatch, tmpdir):
    from opentrons.hardware_control import modules

    dummy_td_file = Path(tmpdir) / "temperature-module@v1.2.3.hex"
    dummy_td_file.write_text("hello")

    dummy_md_file = Path(tmpdir) / "magnetic-module@v3.2.1.hex"
    dummy_md_file.write_text("hello")

    dummy_tc_file = Path(tmpdir) / "thermocycler@v0.1.2.bin"
    dummy_tc_file.write_text("hello")

    dummy_hs_file = Path(tmpdir) / "heater-shaker@v2.10.2.bin"
    dummy_hs_file.write_text("hello")

    dummy_bogus_file = Path(tmpdir) / "thermoshaker@v6.6.6.bin"
    dummy_bogus_file.write_text("hello")

    monkeypatch.setattr(modules.mod_abc, "ROBOT_FIRMWARE_DIR", Path(tmpdir))
    monkeypatch.setattr(modules.mod_abc, "IS_ROBOT", True)

    from opentrons.hardware_control import API

    mods = ["tempdeck", "magdeck", "thermocycler", "heatershaker"]
    api = await API.build_hardware_simulator(attached_modules=mods)
    await asyncio.sleep(0.05)

    assert api.attached_modules[0].bundled_fw == BundledFirmware(
        version="1.2.3", path=dummy_td_file
    )
    assert api.attached_modules[1].bundled_fw == BundledFirmware(
        version="3.2.1", path=dummy_md_file
    )
    assert api.attached_modules[2].bundled_fw == BundledFirmware(
        version="0.1.2", path=dummy_tc_file
    )
    assert api.attached_modules[3].bundled_fw == BundledFirmware(
        version="2.10.2", path=dummy_hs_file
    )
    for m in api.attached_modules:
        await m.cleanup()


async def test_get_thermocycler_bundled_fw(
    mod_thermocycler, mod_thermocycler_gen2, monkeypatch, tmpdir
):
    from opentrons.hardware_control import modules

    dummy_tc_file = Path(tmpdir) / "thermocycler@v0.1.2.bin"
    dummy_tc_file.write_text("hello")
    dummy_tc2_file = Path(tmpdir) / "thermocycler-gen2@v1.9.9.bin"
    dummy_tc2_file.write_text("hello")

    monkeypatch.setattr(modules.mod_abc, "ROBOT_FIRMWARE_DIR", Path(tmpdir))
    monkeypatch.setattr(modules.mod_abc, "IS_ROBOT", True)

    assert mod_thermocycler.get_bundled_fw() == BundledFirmware(
        version="0.1.2", path=dummy_tc_file
    )
    assert mod_thermocycler_gen2.get_bundled_fw() == BundledFirmware(
        version="1.9.9", path=dummy_tc2_file
    )


@pytest.mark.parametrize(
    "revision,model",
    [
        ("mag_deck_v1.1", "magneticModuleV1"),
        ("mag_deck_v20", "magneticModuleV2"),
        ("", "magneticModuleV1"),
        ("asdasdadvasdasd", "magneticModuleV1"),
        (None, "magneticModuleV1"),
    ],
)
def test_magnetic_module_revision_parsing(revision, model):
    assert MagDeck._model_from_revision(revision) == model


@pytest.mark.parametrize(
    "revision,model",
    [
        ("temp_deck_v1.1", "temperatureModuleV1"),
        ("temp_deck_v3.0", "temperatureModuleV1"),
        ("temp_deck_v4.0", "temperatureModuleV1"),
        ("temp_deck_v15", "temperatureModuleV1"),
        ("temp_deck_v20", "temperatureModuleV2"),
        ("", "temperatureModuleV1"),
        ("v", "temperatureModuleV1"),
        (None, "temperatureModuleV1"),
    ],
)
def test_temperature_module_revision_parsing(revision, model):
    assert TempDeck._model_from_revision(revision) == model
