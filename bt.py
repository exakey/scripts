import asyncio
from enum import Enum

from dbus_fast import BusType
from dbus_fast.aio import MessageBus


class BluetoothStatus(Enum):
    UNDEFINED = 0
    DISABLED = 1
    ENABLED = 2
    CONNECTED = 3


def format_status(bluetooth_status: BluetoothStatus):
    if bluetooth_status == BluetoothStatus.DISABLED:
        return "%{F#707880}"
    elif bluetooth_status == BluetoothStatus.ENABLED:
        return "%{F#C5C8C6}"
    elif bluetooth_status == BluetoothStatus.CONNECTED:
        return "%{F#2193ff}"
    elif bluetooth_status == BluetoothStatus.UNDEFINED:
        return "%{F#707880}?"


async def _main():
    bluetooth_status = BluetoothStatus.UNDEFINED

    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    # the introspection xml would normally be included in your project, but
    # this is convenient for development
    introspection = await bus.introspect("org.bluez", "/")

    obj = bus.get_proxy_object("org.bluez", "/", introspection)
    object_manager = obj.get_interface("org.freedesktop.DBus.ObjectManager")

    async def handle_interfaces_updated():
        # print("handle_interfaces_updated")
        interfaces = await object_manager.call_get_managed_objects()
        # print("interfaces", interfaces)
        powered_adapters = [
            name
            for name, interface in interfaces.items()
            if "org.bluez.Adapter1" in interface.keys()
            and interface["org.bluez.Adapter1"]["Powered"].value is True
        ]
        connected_devices = [
            name
            for name, interface in interfaces.items()
            if "org.bluez.Device1" in interface.keys()
            and interface["org.bluez.Device1"]["Connected"].value is True
        ]
        # print("powered", powered_adapters)
        # print("connected", connected_devices)

        if len(connected_devices) > 0:
            bluetooth_status = BluetoothStatus.CONNECTED
        elif len(powered_adapters) > 0:
            bluetooth_status = BluetoothStatus.ENABLED
        else:
            bluetooth_status = BluetoothStatus.DISABLED

        # print(f"status {bluetooth_status}")
        print(format_status(bluetooth_status), flush=True)

    object_manager.on_interfaces_added(
        lambda _path, _objects: handle_interfaces_updated()
    )
    object_manager.on_interfaces_removed(
        lambda _path, _interfaces: handle_interfaces_updated()
    )

    await handle_interfaces_updated()

    await asyncio.Event().wait()


def main():
    asyncio.run(_main())
