from pymodbus.client import ModbusSerialClient
import time

def main():
    client = ModbusSerialClient(
        port='/dev/ttyUSB0',     # Muuta tarvittaessa oikeaksi portiksi
        baudrate=19200,
        bytesize=8,
        parity='N',
        stopbits=1,
        timeout=0.5
    )

    if not client.connect():
        print("Modbus-yhteys epäonnistui.")
        return

    print("Modbus-yhteys muodostettu. Seurataan kytkimiä...")
    
    # Rekisterien osoitteet ja nimet
    register_map = {
        16999: "STOP",
        17000: "START",
        17001: "AKTIIVINEN 1",
        17002: "AKTIIVINEN 2",
        17003: "AKTIIVINEN 3"
    }

    # Viimeisimmät tilat
    last_values = {addr: None for addr in register_map}

    try:
        while True:
            for addr, name in register_map.items():
                result = client.read_holding_registers(address=addr, count=1)
                
                if not result or not hasattr(result, 'registers'):
                    print(f"[VIRHE] Ei voitu lukea rekisteriä {addr} ({name})")
                    continue

                value = result.registers[0]
                if last_values[addr] != value:
                    print(f"[MUUTOS] {name} (rekisteri {addr}): {value}")
                    last_values[addr] = value

            time.sleep(0.2)  # 200 ms välein
    except KeyboardInterrupt:
        print("\nLopetetaan...")
    finally:
        client.close()

if __name__ == '__main__':
    main()
