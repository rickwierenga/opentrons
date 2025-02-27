"""Request and response models for /modules endpoints."""
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel
from typing import Generic, Optional, TypeVar, Union
from typing_extensions import Literal

from opentrons.hardware_control.modules import (
    ModuleType,
    TemperatureStatus,
    MagneticStatus,
    HeaterShakerStatus,
    SpeedStatus,
)
from opentrons.drivers.types import (
    ThermocyclerLidStatus,
    HeaterShakerLabwareLatchStatus,
)
from opentrons.protocol_engine import ModuleModel

ModuleT = TypeVar("ModuleT", bound=ModuleType)
ModuleModelT = TypeVar("ModuleModelT", bound=ModuleModel)
ModuleDataT = TypeVar("ModuleDataT", bound=BaseModel)


class UsbPort(BaseModel):
    """The USB port the module is connected to."""

    port: int = Field(
        ...,
        description=(
            "The USB port the module is connected to."
            " If connected via a hub, ``port`` represents a port on the hub."
        ),
    )

    hub: Optional[int] = Field(
        ...,
        description=(
            "If the module is connected via a USB hub,"
            " the USB port the hub is plugged into."
        ),
    )

    path: str = Field(
        ...,
        description="The virtual path of the USB port in the system.",
    )


class GenericModule(GenericModel, Generic[ModuleT, ModuleModelT, ModuleDataT]):
    """Base module response."""

    id: str = Field(
        ...,
        description=(
            "Unique module identifier for use in requests to /modules and /commands."
        ),
    )
    serialNumber: str = Field(..., description="Device serial number.")
    firmwareVersion: str = Field(..., description="Device firmware version.")
    hardwareRevision: str = Field(..., description="Device hardware revision.")
    hasAvailableUpdate: bool = Field(
        ...,
        description="Whether a firmware update is available.",
    )
    moduleType: ModuleT = Field(..., description="General type of the module.")
    moduleModel: ModuleModelT = Field(..., description="Specific model of the module.")
    data: ModuleDataT
    usbPort: UsbPort


class TemperatureModuleData(BaseModel):
    """Live data from an attached Temperature Module."""

    status: TemperatureStatus
    currentTemperature: float = Field(
        ..., description="The module's current temperature, in degrees Celsius."
    )
    targetTemperature: Optional[float] = Field(
        ..., description="The module's target temperature, if set, in degrees Celsius."
    )


class TemperatureModule(
    GenericModule[
        Literal[ModuleType.TEMPERATURE],
        Literal[ModuleModel.TEMPERATURE_MODULE_V1, ModuleModel.TEMPERATURE_MODULE_V2],
        TemperatureModuleData,
    ]
):
    """An attached Temperature Module."""

    moduleType: Literal[ModuleType.TEMPERATURE]
    moduleModel: Literal[
        ModuleModel.TEMPERATURE_MODULE_V1,
        ModuleModel.TEMPERATURE_MODULE_V2,
    ]
    data: TemperatureModuleData


class MagneticModuleData(BaseModel):
    """Live data from an attached Magnetic Module."""

    status: MagneticStatus
    engaged: bool = Field(..., description="Whether the magnets are raised or lowered")
    height: float = Field(
        ...,
        description=(
            "The height of the top of the magnets relative to the labware base,"
            " in millimeters."
        ),
    )


class MagneticModule(
    GenericModule[
        Literal[ModuleType.MAGNETIC],
        Literal[ModuleModel.MAGNETIC_MODULE_V1, ModuleModel.MAGNETIC_MODULE_V2],
        MagneticModuleData,
    ],
):
    """An attached Magnetic Module."""

    moduleType: Literal[ModuleType.MAGNETIC]
    moduleModel: Literal[ModuleModel.MAGNETIC_MODULE_V1, ModuleModel.MAGNETIC_MODULE_V2]
    data: MagneticModuleData


class ThermocyclerModuleData(BaseModel):
    """Live data from an attached Thermocycler Module."""

    status: TemperatureStatus = Field(
        ...,
        description="The current heating status of the thermocycler block.",
    )
    currentTemperature: Optional[float] = Field(
        ...,
        description=(
            "The current temperature of the thermocycler block, if known,"
            " in degrees Celsius."
        ),
    )
    targetTemperature: Optional[float] = Field(
        ...,
        description=(
            "The target temperature of the thermocycler block, if set,"
            " in degrees Celsius."
        ),
    )
    lidStatus: ThermocyclerLidStatus = Field(
        ...,
        description="The current lid status of the thermocycler.",
    )
    lidTemperatureStatus: TemperatureStatus = Field(
        ..., description="The current heating status of the lid."
    )
    lidTemperature: Optional[float] = Field(
        ...,
        description="The current temperature of the lid, if known, in degrees Celsius.",
    )
    lidTargetTemperature: Optional[float] = Field(
        ...,
        description="The target temperature of the lid, if set, in degrees Celsius.",
    )
    holdTime: Optional[float] = Field(
        ...,
        description="The time left in the current hold step, if any, in seconds.",
    )
    rampRate: Optional[float] = Field(
        ...,
        description=(
            "The current ramp rate for the thermocycler block, if set,"
            " in degrees Celsius per second."
        ),
    )
    currentCycleIndex: Optional[int] = Field(
        ...,
        description=(
            "The index of the current cycle within the current sequence,"
            " if a cycle is running."
        ),
    )
    totalCycleCount: Optional[int] = Field(
        ...,
        description=(
            "The total number of cycles within the current sequence,"
            " if a cycle is running."
        ),
    )
    currentStepIndex: Optional[int] = Field(
        ...,
        description=(
            "The index of the current step within the current step,"
            " if a cycle is running."
        ),
    )
    totalStepCount: Optional[int] = Field(
        ...,
        description=(
            "The total number of steps within the current cycle,"
            " if a cycle is running."
        ),
    )


class ThermocyclerModule(
    GenericModule[
        Literal[ModuleType.THERMOCYCLER],
        Literal[ModuleModel.THERMOCYCLER_MODULE_V1, ModuleModel.THERMOCYCLER_MODULE_V2],
        ThermocyclerModuleData,
    ]
):
    """An attached Thermocycler Module."""

    moduleType: Literal[ModuleType.THERMOCYCLER]
    moduleModel: Literal[
        ModuleModel.THERMOCYCLER_MODULE_V1, ModuleModel.THERMOCYCLER_MODULE_V2
    ]
    data: ThermocyclerModuleData


class HeaterShakerModuleData(BaseModel):
    """Live data from a Heater-Shaker module."""

    status: HeaterShakerStatus = Field(
        ...,
        description="Overall status of the module.",
    )
    labwareLatchStatus: HeaterShakerLabwareLatchStatus = Field(
        ...,
        description="Status of the module's labware latch",
    )
    speedStatus: SpeedStatus = Field(
        ...,
        description="Status of the module's shaker.",
    )
    currentSpeed: int = Field(
        ...,
        description="Current speed of the shaker, in rotations-per-minute.",
    )
    targetSpeed: Optional[int] = Field(
        ...,
        description="Target speed of the shaker, if set, in rotations-per-minute.",
    )
    temperatureStatus: TemperatureStatus = Field(
        ...,
        description="Status of the module's heater.",
    )
    currentTemperature: float = Field(
        ...,
        description="Current temperature of the heater, in degrees Celsius.",
    )
    targetTemperature: Optional[float] = Field(
        ...,
        description="Target temperature of the heater, if set, in degrees Celsius.",
    )
    errorDetails: Optional[str] = Field(
        ...,
        description=(
            "Error details, if the module hardware has encountered something"
            " unexpected and unrecoverable."
        ),
    )


class HeaterShakerModule(
    GenericModule[
        Literal[ModuleType.HEATER_SHAKER],
        Literal[ModuleModel.HEATER_SHAKER_MODULE_V1],
        HeaterShakerModuleData,
    ]
):
    """An attached Heater-Shaker Module."""

    moduleType: Literal[ModuleType.HEATER_SHAKER]
    moduleModel: Literal[ModuleModel.HEATER_SHAKER_MODULE_V1]
    data: HeaterShakerModuleData


AttachedModule = Union[
    TemperatureModule,
    MagneticModule,
    ThermocyclerModule,
    HeaterShakerModule,
]


AttachedModuleData = Union[
    TemperatureModuleData,
    MagneticModuleData,
    ThermocyclerModuleData,
    HeaterShakerModuleData,
]
