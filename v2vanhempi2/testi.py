from pymodbus.client import ModbusSerialClient
import time

def test_fortest():
    print("ForTest-testeri - Komentojen testaus")
    
    # Alusta yhteys
    client = ModbusSerialClient(
        port='/dev/ttyUSB0',
        baudrate=19200,
        bytesize=8,
        parity='N',
        stopbits=1,
        timeout=1.0  # Pidempi timeout
    )
    
    connected = client.connect()
    print(f"Yhteys: {'OK' if connected else 'VIRHE'}")
    
    if not connected:
        print("Yhteysvirhe! Tarkista kaapelit ja portit.")
        return
    
    # TESTI 1: Käynnistä testi vakioparametreilla
    print("\n--- TESTI 1: Käynnistä testi ---")
    try:
        result = client.write_coil(0x0A, True)
        print(f"Tulos: {result}")
        print("Odotetaan 5 sekuntia...")
        time.sleep(5)  # Anna testille aikaa alkaa
    except Exception as e:
        print(f"VIRHE: {e}")
    
    # TESTI 2: Pysäytä testi vakioparametreilla
    print("\n--- TESTI 2: Pysäytä testi ---")
    try:
        result = client.write_coil(0x14, True)
        print(f"Tulos: {result}")
        print("Odotetaan 2 sekuntia...")
        time.sleep(2)
    except Exception as e:
        print(f"VIRHE: {e}")
    
    # TESTI 3: Lue tilan tiedot
    print("\n--- TESTI 3: Lue tila (0x30) ---")
    try:
        result = client.read_holding_registers(0x30, 10)
        if result:
            print(f"Tulos: {result.registers}")
        else:
            print("Ei vastausta tai virhe")
    except Exception as e:
        print(f"VIRHE: {e}")
    
    # TESTI 4: Lue tulokset
    print("\n--- TESTI 4: Lue tulokset (0x40) ---")
    try:
        result = client.read_holding_registers(0x40, 10)
        if result:
            print(f"Tulos: {result.registers}")
        else:
            print("Ei vastausta tai virhe")
    except Exception as e:
        print(f"VIRHE: {e}")
    
    # Sulje yhteys
    client.close()
    print("\nYhteys suljettu.")

if __name__ == "__main__":
    test_fortest()