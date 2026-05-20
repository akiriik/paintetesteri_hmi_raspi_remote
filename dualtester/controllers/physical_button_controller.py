# controllers/physical_button_controller.py


class PhysicalButtonController:
    """
    Fyysisten nappien ja nappivalojen yhteinen controller.

    Oletusmalli:
    - STATION1_START: käynnistää/pysäyttää ForTest 1:n
    - STATION2_START: käynnistää/pysäyttää ForTest 2:n
    - EMERGENCY_STOP: pysäyttää molemmat asemat ohjelmallisesti
    - SPARE1-4: varalla, ei toimintoa

    Nappivalot:
    - station 1 valo: HardwareService output 4
    - station 2 valo: HardwareService output 5

    Huom:
    Tämä ei korvaa oikeaa hätäseis-turvapiiriä.
    """

    def __init__(self, station_controllers, hardware_service):
        self.station_controllers = station_controllers
        self.hardware_service = hardware_service

        self.station_button_map = {
            "STATION1_START": 1,
            "STATION2_START": 2,

            # Vanhojen nimien yhteensopivuus:
            "START": 1,
            "STOP": 1,
        }

        self.station_light_outputs = {
            1: 4,
            2: 5,
        }

        self.spare_buttons = {
            "SPARE1",
            "SPARE2",
            "SPARE3",
            "SPARE4",
        }

    def handle_button_press(self, button_name, is_pressed):
        if not is_pressed:
            return

        if button_name in self.station_button_map:
            station_id = self.station_button_map[button_name]
            self.toggle_station(station_id)
            return

        if button_name == "EMERGENCY_STOP":
            self.handle_emergency_stop_button()
            return

        if button_name in self.spare_buttons:
            print(f"Vara-/lisänappi painettu: {button_name}")
            return

        print(f"Tuntematon fyysinen nappi: {button_name}")

    def toggle_station(self, station_id):
        station = self.station_controllers.get(station_id)

        if not station:
            print(f"Fyysinen nappi: asemaa {station_id} ei löydy")
            return

        if station.is_running:
            station.stop_test()
        else:
            station.start_test()

    def handle_emergency_stop_button(self):
        for station_id, station in self.station_controllers.items():
            if station:
                try:
                    station.stop_test()
                    station.update_status(
                        "HÄTÄSEIS-NAPPI PAINETTU, TESTI PYSÄYTETTY",
                        "ERROR",
                    )
                except Exception as e:
                    print(f"Hätäseis-napin käsittely epäonnistui asemalla {station_id}: {e}")

    def update_station_light_state(self, station_id, is_running, ready):
        """
        Päivittää fyysisen start-napin valon.

        Nykyinen yksinkertainen logiikka:
        - valo päällä, jos asema on valmis tai testi käy
        - valo pois, jos asema ei ole valmis eikä käy
        """

        output_number = self.station_light_outputs.get(station_id)

        if output_number is None:
            return

        light_on = bool(is_running or ready)
        self.hardware_service.set_output(output_number, light_on)

    def cleanup(self):
        for output_number in self.station_light_outputs.values():
            try:
                self.hardware_service.set_output(output_number, False)
            except Exception:
                pass