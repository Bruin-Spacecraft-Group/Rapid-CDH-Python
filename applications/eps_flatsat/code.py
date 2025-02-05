"""
Software entry point for the control application for the EPS flatsat PCB from June 2024.
"""

import asyncio

datastore = {
    "battery_s1a_voltage": 4,
    "battery_s1b_voltage": 4,
    # etc.
}


async def battery_management_task():
    """
    Task which controls string protection and balancing circuits.

    Uses the most recent data in the `datastore` as inputs. Controls circuits to cutoff
    charging and discharging for each battery string. Also controls when power is dissipated
    from each individual cell to maintain a balanced battery pack.
    """
    while True:
        await asyncio.sleep(0)


async def output_bus_control_task():
    """
    Task which controls output buses to the rest of the satellite.

    Uses the most recent data in the `datastore` as inputs. Controls enable pins for the 3V3,
    5V, 12VLP, and 12VHP power supplies. Manages startup sequence, overcurrent conditions,
    and any relevant commands from CDH that should activate or deactivate a particular bus.
    """
    while True:
        await asyncio.sleep(0)


async def data_recording_task():
    """
    Task to read all analog and digital data in the system and place it into the `datastore`.
    """
    while True:
        await asyncio.sleep(0)


async def intersubsystem_communication_task():
    """
    Task to communicate with CDH.

    Appropriately loads all buffers to be received by CDH and sent in return at the appropriate
    times. Controls inter-subsystem communication hardware in accordance with the protocol's
    specification. Transmitted data is pulled from the `datastore` and received commands are
    placed into the `datastore`.
    """
    while True:
        await asyncio.sleep(0)


async def gathered_task():
    """
    Runs all top-level tasks in parallel.

    Currently includes battery management, output bus control, data recording to the `datastore`,
    and intersubsystem communication.
    """
    await asyncio.gather(
        battery_management_task(),
        output_bus_control_task(),
        data_recording_task(),
        intersubsystem_communication_task(),
    )


if __name__ == "__main__":
    asyncio.run(gathered_task())
