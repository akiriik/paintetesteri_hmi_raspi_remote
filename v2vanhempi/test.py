#!/usr/bin/env python3
"""
Yksinkertainen testiohjelma ForTest-käynnistykselle
"""
from pymodbus.client import ModbusSerialClient
import time

def test_start_command():
    print("ForTest käynnistyskomennon testi")
    print("============================")
    
    # Yhteyden asetukset
    port = '/dev/ttyUSB1'
    baudrate = 19200
    
    print(f"Yhdistetään porttiin: {port}")
    print(f"Baudrate: {baudrate}")
    
    # Muodosta yhteys
    client = ModbusSerialClient(
        port=port,
        baudrate=baudrate,
        bytesize=8,
        parity='N',
        stopbits=1,
        timeout=2.0  # Riittävästi aikaa vastaukselle
    )
    
    try:
        # Yhdistäminen
        connected = client.connect()
        print(f"Yhteys: {'OK' if connected else 'VIRHE'}")
        
        if not connected:
            print("Ei voida jatkaa - yhteys ei toimi")
            return
        
        # Odota pieni hetki ennen komentoa
        time.sleep(0.5)
        
        # Käynnistyskomento rekisteriin 0x0A (Start test)
        print("\nLähetetään käynnistyskomento...")
        print("Rekisteri: 0x0A (10)")
        print("Arvo: True (0xFF00)")
        
        # Lähetä komento
        result = client.write_coil(
            address=0x0A,
            value=True,  # True = 0xFF00
            slave=1      # Laitteen tunnus
        )
        
        print(f"\nVastaus: {result}")
        
        if hasattr(result, 'isError'):
            print(f"Virhe: {result.isError()}")
        
        # Odota pieni hetki vastausta varten
        time.sleep(1)
        
        print("\nKoe valmis!")
        
    except Exception as e:
        print(f"\nVIRHE: {e}")
        
    finally:
        # Sulje yhteys
        client.close()
        print("Yhteys suljettu.")

if __name__ == "__main__":
    test_start_command()