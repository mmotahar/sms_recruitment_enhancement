import gatt
from odoo.addons.hw_drivers.controllers.driver import BtDriver

class SylvacBtDriver(BtDriver):

    def supported(self):
        return self.dev.alias() == "SY295" or self.dev.alias() == "SY304" or self.dev.alias() == "SY276"

    def connect(self):
        self.gatt_device = GattSylvacBtDriver(mac_address=self.dev.mac_address, manager=self.manager)
        self.gatt_device.btdriver = self
        self.gatt_device.connect()


class GattSylvacBtDriver(gatt.Device):
    btdriver = False

    def services_resolved(self):
        super().services_resolved()

        device_information_service = next(
            s for s in self.services
            if s.uuid == '00005000-0000-1000-8000-00805f9b34fb')

        measurement_characteristic = next(
            c for c in device_information_service.characteristics if c.uuid == '00005020-0000-1000-8000-00805f9b34fb')
        measurement_characteristic.enable_notifications()

    def characteristic_value_updated(self, characteristic, value):
        total = value[0] + value[1] * 256 + value[2] * 256 * 256 + value[3] * 256 * 256 * 256
        if total > 256 ** 4 / 2:
            total = total - 256 ** 4
        self.btdriver.value = total / 1000000.0

    def characteristic_enable_notification_succeeded(self):
        print("Success pied à coulisse Bluetooth!")

    def characteristic_enable_notification_failed(self):
        print("Problem connecting")

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        self.btdriver.disconnect()