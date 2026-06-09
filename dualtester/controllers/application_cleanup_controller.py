# controllers/application_cleanup_controller.py


class ApplicationCleanupController:
    """
    Sovelluksen hallittu sulkeminen.

    Tehtävät:
    - pysäyttää controllerit
    - sulkee näkymien cleanupit
    - sulkee servicet
    - pitää MainWindowin closeEventin kevyenä
    """

    def __init__(self, main_window):
        self.main_window = main_window

    def cleanup(self):
        window = self.main_window

        try:
            cleanup_order = [
                "top_bar_controller",
                "navigation_controller",
                "fortest_result_controller",
                "modbus_result_controller",
                "physical_button_controller",
                "emergency_stop_controller",
            ]

            for attr_name in cleanup_order:
                obj = getattr(window, attr_name, None)
                if obj and hasattr(obj, "cleanup"):
                    obj.cleanup()

            station_controllers = getattr(window, "station_controllers", None)
            if station_controllers:
                for controller in station_controllers.values():
                    if controller and hasattr(controller, "cleanup"):
                        controller.cleanup()

            cleanup_widgets = [
                "environment_status_bar",
                "manual_screen",
                "main_screen",
            ]

            for attr_name in cleanup_widgets:
                obj = getattr(window, attr_name, None)
                if obj and hasattr(obj, "cleanup"):
                    obj.cleanup()

            cleanup_services = [
                "result_storage_service",
                "fortest_service",
                "hardware_service",
            ]

            for attr_name in cleanup_services:
                obj = getattr(window, attr_name, None)
                if obj and hasattr(obj, "cleanup"):
                    obj.cleanup()

        except Exception as e:
            print(f"Virhe sovelluksen sulkemisessa: {e}")
