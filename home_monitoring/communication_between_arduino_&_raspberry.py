import serial
import json

# Nastavení sériové komunikace (USB port Arduina, doplníme až při samotném testování)
ser = serial.Serial('/dev/ttyUSB0', 9600)

while True:
    try:
        # Čtení řádku ze sériové linky
        line = ser.readline().decode('utf-8').strip()
        print(f"Raw data: {line}")

        # Parsování JSON
        data = json.loads(line)
        print(f"Teplota: {data['temperature']} °C")
        print(f"Vlhkost vzduchu: {data['humidity']} %")
        print(f"Vlhkost půdy: {data['soil_moisture_percent']} %")
        
        #eventuelně přidat 'break' pro přerušení měření
        
    except json.JSONDecodeError:
        print("Chyba při parsování JSON!")
    except Exception as e:
        print(f"Nastala chyba: {e}")
