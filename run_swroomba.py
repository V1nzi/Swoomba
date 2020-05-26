import serial
from swroomba import main

try:
    main()
except serial.SerialException as sex:
    print(sex)