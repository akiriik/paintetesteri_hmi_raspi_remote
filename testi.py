#!/usr/bin/env python3
from pymodbus.client import ModbusSerialClient

def main():
    # Modbus-yhteyden alustus
    client = ModbusSerialClient(
        port='/dev/ttyUSB1',  # ForTest laite
        baudrate=19200,
        bytesize=8,
        parity='N',
        stopbits=1,
        timeout=1
    )
    
    if not client.connect():
        print("Yhteys epäonnistui!")
        return

    try:
        # Lue tulosrekisteri 0x0040 (ForTest Results)
        result = client.read_holding_registers(address=0x0040, count=32)
        
        if result and hasattr(result, 'registers'):
            print("Tulosrekisterin tiedot:")
            print(f"Aika: {result.registers[0]}h {result.registers[1]}min {result.registers[2]}s")
            print(f"Päivämäärä: {result.registers[3]}.{result.registers[4]}.{result.registers[5]}")
            print(f"Ohjelma: {result.registers[6]}")
            print(f"Testin tulos (19-20): {result.registers[9]}")  # 1=Good, 2=Bad jne.
            print(f"Testin vaihe (21-22): {result.registers[10]}")
            
            # Painearvo ja yksikkö
            pressure_sign = result.registers[15]  # Position 31-32
            pressure_high = result.registers[16]  # Position 33-34
            pressure_low = result.registers[17]   # Position 35-36
            unit_measure = result.registers[18]   # Position 37-38
            decimal_points = result.registers[19] # Position 39-40
            
            print(f"\nPaine:")
            print(f"Etumerkki (31-32): {pressure_sign}")
            print(f"Arvo korkea (33-34): {pressure_high}")
            print(f"Arvo matala (35-36): {pressure_low}")
            print(f"Mittayksikkö (37-38): {unit_measure}")
            print(f"Desimaalipisteet (39-40): {decimal_points}")
            
            # Vuotoarvo ja yksikkö
            decay_sign = result.registers[20]     # Position 41-42
            decay_high = result.registers[21]     # Position 43-44
            decay_low = result.registers[22]      # Position 45-46
            decay_unit = result.registers[23]     # Position 47-48
            decay_decimals = result.registers[24] # Position 49-50
            
            print(f"\nVuoto:")
            print(f"Etumerkki (41-42): {decay_sign}")
            print(f"Arvo korkea (43-44): {decay_high}")
            print(f"Arvo matala (45-46): {decay_low}")
            print(f"Vuodon mittayksikkö (47-48): {decay_unit}")
            print(f"Vuodon desimaalipisteet (49-50): {decay_decimals}")
            
            # Laske todellinen arvo
            if decay_high == 0:
                # Jos korkea osa on 0, käytetään vain matala-arvoa
                decay_value = decay_low
            else:
                # Yhdistetään korkea ja matala arvo
                decay_value = (decay_high << 16) | decay_low
                
            # Sovelletaan etumerkki ja desimaalipisteet
            if decay_sign == 1:
                decay_value = -decay_value
                
            # Sovelletaan desimaalipisteen paikka (esim. jos decimals=3, jaa 1000:lla)
            if decay_decimals > 0:
                divisor = 10 ** decay_decimals
                decay_value = decay_value / divisor
                
            print(f"\nLaskettu vuotoarvo: {decay_value} mbar/s")
            
            # Tulosta kaikki rekisterit debug-tarkoituksiin
            print("\nKaikki rekisterit:")
            for i, reg in enumerate(result.registers):
                print(f"Rekisteri {i}: {reg}")

    except Exception as e:
        print(f"Virhe: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()