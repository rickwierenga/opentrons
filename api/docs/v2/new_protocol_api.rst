.. _protocol-api-reference:

API Version 2 Reference
=======================

.. _protocol_api-protocols-and-instruments:

Protocols and Instruments
-------------------------
.. module:: opentrons.protocol_api

.. autoclass:: opentrons.protocol_api.ProtocolContext
   :members:
   :exclude-members: location_cache, _hw_manager

.. autoclass:: opentrons.protocol_api.InstrumentContext
   :members:

.. _protocol-api-labware:

Labware and Wells
-----------------
.. automodule:: opentrons.protocol_api.labware
   :members:
   :exclude-members: _depth, _width, _length

.. _protocol-api-modules:

Modules
-------
.. autoclass:: opentrons.protocol_api.TemperatureModuleContext
   :members:
   :exclude-members: start_set_temperature
   :inherited-members:

.. autoclass:: opentrons.protocol_api.MagneticModuleContext
   :members:
   :inherited-members:

.. autoclass:: opentrons.protocol_api.ThermocyclerContext
   :members:
   :exclude-members: total_step_count, current_cycle_index, total_cycle_count, hold_time, ramp_rate, current_step_index, flag_unsafe_move
   :inherited-members:
   
.. autoclass:: opentrons.protocol_api.HeaterShakerContext
   :members:
   :inherited-members:


.. _protocol-api-types:

Useful Types and Definitions
----------------------------
.. automodule:: opentrons.types
   :members:


Executing and Simulating Protocols
----------------------------------

.. automodule:: opentrons.execute
   :members:

.. automodule:: opentrons.simulate
   :members:


