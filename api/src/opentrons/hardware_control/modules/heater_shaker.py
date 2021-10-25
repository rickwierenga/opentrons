import asyncio
import logging
from dataclasses import dataclass
from typing import Optional, Mapping, Callable
from typing_extensions import Final
from opentrons.drivers.rpi_drivers.types import USBPort
from opentrons.hardware_control.execution_manager import ExecutionManager
from opentrons.hardware_control.poller import Reader, WaitableListener, Poller
from opentrons.hardware_control.modules import mod_abc, types, update
from opentrons.drivers.heater_shaker.driver import HeaterShakerDriver
from opentrons.drivers.heater_shaker.abstract import AbstractHeaterShakerDriver
from opentrons.drivers.heater_shaker.simulator import SimulatingDriver
from opentrons.drivers.types import Temperature, RPM, HeaterShakerPlateLockStatus

log = logging.getLogger(__name__)

POLL_PERIOD = 1


class HeaterShaker(mod_abc.AbstractModule):
    @classmethod
    async def build(
        cls,
        port: str,
        usb_port: USBPort,
        execution_manager: ExecutionManager,
        simulating: bool = False,
        loop: asyncio.AbstractEventLoop = None,
        sim_model: str = None,
        **kwargs,
    ):
        """
        Build a HeaterShaker

        Args:
            port: The port to connect to
            usb_port: USB Port
            execution_manager: Execution manager.
            simulating: whether to build a simulating driver
            loop: Loop
            sim_model: The model name used by simulator
            polling_period: the polling period in seconds
            kwargs: further kwargs are in starargs because of inheritance rules.
            possible values include polling_period: float, a time in seconds to poll

        Returns:
            HeaterShaker instance
        """
        driver: AbstractHeaterShakerDriver
        if not simulating:
            driver = await HeaterShakerDriver.create(port=port, loop=loop)
        else:
            driver = SimulatingDriver()
        mod = cls(
            port=port,
            usb_port=usb_port,
            execution_manager=execution_manager,
            driver=driver,
            device_info=await driver.get_device_info(),
            loop=loop,
            polling_period=kwargs.get("polling_period"),
        )
        return mod

    def __init__(
        self,
        port: str,
        usb_port: USBPort,
        execution_manager: ExecutionManager,
        driver: AbstractHeaterShakerDriver,
        device_info: Mapping[str, str],
        loop: asyncio.AbstractEventLoop = None,
        polling_period: float = None,
    ):
        super().__init__(
            port=port, usb_port=usb_port, loop=loop, execution_manager=execution_manager
        )
        poll_time_s = polling_period or POLL_PERIOD
        self._device_info = device_info
        self._driver = driver
        self._listener = HeaterShakerListener(loop=loop)
        self._poller = Poller(
            reader=PollerReader(driver=self._driver),
            interval_seconds=poll_time_s,
            listener=self._listener,
            loop=loop,
        )

    async def cleanup(self) -> None:
        """Stop the poller task"""
        await self._poller.stop_and_wait()

    @classmethod
    def name(cls) -> str:
        """Used for picking up serial port symlinks"""
        return "heatershaker"

    @staticmethod
    def _model_from_revision(revision: Optional[str]) -> str:
        """Defines the revision -> model mapping"""
        return "heaterShakerV1"

    @staticmethod
    def _get_temperature_status(temperature: Temperature) -> types.TemperatureStatus:
        """
        Determine the status from the temperature.

        Args:
            temperature: A Temperature instance

        Returns:
            The status
        """
        DELTA: Final = 0.7
        status = types.TemperatureStatus.IDLE
        if temperature.target is not None:
            diff = temperature.target - temperature.current
            if abs(diff) < DELTA:  # To avoid status fluctuation near target
                status = types.TemperatureStatus.HOLDING
            elif diff < 0:
                status = types.TemperatureStatus.COOLING
            else:
                status = types.TemperatureStatus.HEATING
        return status

    @staticmethod
    def _get_speed_status(speed: RPM) -> types.SpeedStatus:
        """
        Determine the status from the speed.

        Args:
            speed: An RPM instance

        Returns:
            The status
        """
        DELTA: Final = 100
        status = types.SpeedStatus.IDLE
        if speed.target is not None:
            diff = speed.target - speed.current
            if abs(diff) < DELTA:  # To avoid status fluctuation near target
                status = types.SpeedStatus.HOLDING
            elif diff < 0:
                status = types.SpeedStatus.DECELERATING
            else:
                status = types.SpeedStatus.ACCELERATING
        return status

    def model(self) -> str:
        return self._model_from_revision(self._device_info.get("model"))

    @classmethod
    def bootloader(cls) -> types.UploadFunction:
        return update.upload_via_dfu

    async def wait_next_poll(self) -> None:
        """Wait for the next poll to complete."""
        await self._listener.wait_next_poll()

    @property
    def device_info(self) -> Mapping[str, str]:
        return self._device_info

    @property
    def live_data(self) -> types.LiveData:
        return {
            "temperatureStatus": self.temperature_status,
            "speedStatus": self.speed_status,
            "status": self.status,
            "data": {
                "currentTemp": self.temperature,
                "targetTemp": self.target_temperature,
                "currentSpeed": self.speed,
                "targetSpeed": self.target_speed,
            },
        }

    @property
    def temperature(self) -> float:
        return self._listener.state.temperature.current

    @property
    def target_temperature(self) -> Optional[float]:
        return self._listener.state.temperature.target

    @property
    def speed(self) -> int:
        return self._listener.state.rpm.current

    @property
    def target_speed(self) -> Optional[int]:
        return self._listener.state.rpm.target

    @property
    def temperature_status(self) -> str:
        return self._get_temperature_status(self._listener.state.temperature).value

    @property
    def speed_status(self) -> str:
        return self._get_speed_status(self._listener.state.rpm).value

    @property
    def status(self) -> str:
        return f"temperature {self.temperature_status}, speed {self.speed_status}"

    @property
    def is_simulated(self) -> bool:
        return isinstance(self._driver, SimulatingDriver)

    async def set_temperature(self, celsius: float) -> None:
        """
        Set temperature in degree Celsius

        Range: Room temperature to 90 degree Celsius
               Any temperature above the value will be clipped to
               the nearest limit. This is a resistive heater, not
               a Peltier TEC, so a temperature that is too low
               may be unattainable but we do not limit input on the
               low side in case the user has this in a freezer.

        This function will not complete until the heater/shaker is at
        the requested temperature or an error occurs. To start heating
        but not wait until heating is complete, see start_set_temperature.
        """
        await self.wait_for_is_running()
        await self._driver.set_temperature(temperature=celsius)
        await self.wait_next_poll()

        async def _wait():
            # Wait until we reach the target temperature.
            while self.temperature_status != types.TemperatureStatus.HOLDING:
                await self.wait_next_poll()

        task = self._loop.create_task(_wait())
        await self.make_cancellable(task)
        await task

    async def start_set_temperature(self, celsius: float) -> None:
        """
        Set temperature in degree Celsius

        Range: Room temperature to 90 degree Celsius
               Any temperature above the value will be clipped to
               the nearest limit. This is a resistive heater, not
               a Peltier TEC, so a temperature that is too low
               may be unattainable but we do not limit input on the
               low side in case the user has this in a freezer.

        This function will complete as soon as heating begins, and
        will not wait until the temperature is achieved. To then wait
        until heating is complete, use await_temperature. To start
        heating and wait until heating is complete in one call, use
        set_temperature.

        """
        await self.wait_for_is_running()
        await self._driver.set_temperature(celsius)

    async def await_temperature(self, awaiting_temperature: float) -> None:
        """
        Await temperature in degree Celsius
        Polls temperature module's temperature until
        the specified temperature is reached
        """
        if self.is_simulated:
            return

        await self.wait_for_is_running()
        await self.wait_next_poll()

        async def _await_temperature():
            if self.temperature_status == types.TemperatureStatus.HEATING:
                while self.temperature < awaiting_temperature:
                    await self.wait_next_poll()
            elif self.status == types.TemperatureStatus.COOLING:
                while self.temperature > awaiting_temperature:
                    await self.wait_next_poll()

        t = self._loop.create_task(_await_temperature())
        await self.make_cancellable(t)
        await t

    async def set_speed(self, rpm: int) -> None:
        """
        Set shake speed in RPM

        Range: 0-3000 RPM
               Any speed above or below these values will cause an error.

        This function will not complete until the heater/shaker is at
        the speed or an error occurs. To start spinning but not wait
        until the final speed is reached, see start_set_speed.
        """
        await self.wait_for_is_running()
        await self._driver.set_rpm(rpm)
        await self.wait_next_poll()

        async def _wait():
            # Wait until we reach the target speed.
            while self.speed_status != types.SpeedStatus.HOLDING:
                await self.wait_next_poll()

        task = self._loop.create_task(_wait())
        await self.make_cancellable(task)
        await task

    async def start_set_speed(self, rpm: int) -> None:
        """
        Set shake speed in RPM

         Range: 0-3000 RPM
                Any speed above or below these values will cause an
                error

         This function will complete after the heater/shaker begins
         to accelerate. To wait until the speed is reached, use
         await_speed. To set speed and wait in the same call, see
         set_speed.
        """
        await self.wait_for_is_running()
        await self._driver.set_rpm(rpm)

    async def await_speed(self, awaiting_speed: int) -> None:
        """
        Await speed in RPM
        Polls heater/shaker module's speed until the specified
        speed is reached.
        """
        if self.is_simulated:
            return

        await self.wait_for_is_running()
        await self.wait_next_poll()

        async def _await_speed():
            if self.speed_status == types.SpeedStatus.ACCELERATING:
                while self.speed < awaiting_speed:
                    await self.wait_next_poll()
            elif self.speed_status == types.SpeedStatus.DECELERATING:
                while self.speed > awaiting_speed:
                    await self.wait_next_poll()

        t = self._loop.create_task(_await_speed())
        await self.make_cancellable(t)
        await t

    async def await_speed_and_temperature(self, temperature: float, speed: int) -> None:
        """Wait for previously-started speed and temperature commands to complete.

        To set speed, use start_set_speed. To set temperature,
        use start_set_temperature.
        """
        await asyncio.gather(
            self.await_speed(speed), self.await_temperature(temperature)
        )

    async def _wait_for_plate_lock(self, status: HeaterShakerPlateLockStatus):
        current_status = await self._driver.get_plate_lock_status()
        while status != current_status:
            current_status = await self._driver.get_plate_lock_status()

    async def deactivate(self):
        """Stop heating/cooling; stop shaking and home the plate"""
        await self.wait_for_is_running()
        await self._driver.set_temperature(0)
        await self._driver.home()

    async def open_plate_lock(self):
        await self.wait_for_is_running()
        await self._driver.open_plate_lock()
        await self._wait_for_plate_lock(HeaterShakerPlateLockStatus.IDLE_OPEN)

    async def close_plate_lock(self):
        await self.wait_for_is_running()
        await self._driver.close_plate_lock()
        await self._wait_for_plate_lock(HeaterShakerPlateLockStatus.IDLE_CLOSED)

    async def prep_for_update(self) -> str:
        return "no"


@dataclass
class PollResult:
    temperature: Temperature
    rpm: RPM


class PollerReader(Reader[PollResult]):
    """Polled data reader."""

    def __init__(self, driver: AbstractHeaterShakerDriver) -> None:
        """Constructor."""
        self._driver = driver

    async def read(self) -> PollResult:
        """Poll the heater/shaker."""

        return PollResult(
            temperature=await self._driver.get_temperature(),
            rpm=await self._driver.get_rpm(),
        )


class HeaterShakerListener(WaitableListener[PollResult]):
    """Tempdeck state listener."""

    def __init__(
        self,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        interrupt_callback: Callable[[Exception], None] = None,
    ) -> None:
        """Constructor."""
        super().__init__(loop=loop)
        self._callback = interrupt_callback
        self._polled_data = PollResult(
            temperature=Temperature(current=25, target=None),
            rpm=RPM(current=0, target=None),
        )

    @property
    def state(self) -> PollResult:
        return self._polled_data

    def on_poll(self, result: PollResult) -> None:
        """On new poll."""
        self._polled_data = result
        return super().on_poll(result)

    def on_error(self, exc: Exception) -> None:
        """On error."""
        if self._callback:
            self._callback(exc)