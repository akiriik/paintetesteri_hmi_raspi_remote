# test_program_change.py
from pymodbus.client import ModbusSerialClient

def change_program(program_number=5):
    """Vaihda testeriohjelma haluttuun numeroon."""
    # USB1 alustus
    client = ModbusSerialClient(
        port='/dev/ttyUSB1',
        baudrate=19200,
        bytesize=8,
        parity='N',
        stopbits=1,
        timeout=1
    )
    
    if not client.connect():
        print("Yhteys epäonnistui")
        return False
    
    try:
        # Vaihda ohjelma (rekisteri 0x0060)
        result = client.write_register(address=0x0060, value=program_number)
        if result and hasattr(result, 'isError') and not result.isError():
            print(f"Ohjelma vaihdettu numeroon {program_number} onnistuneesti")
            return True
        else:
            print("Ohjelman vaihto epäonnistui")
            return False
    except Exception as e:
        print(f"Virhe: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    change_program(5)