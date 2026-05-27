import math
import time
import serial



def motor_command(id="d001A", angle=0, rpm=5, cur="0000", mode="Position", enable=1, kp=5, kd=5):
    """
    Creates the command to send to the motor.
    
    Parameters
    ----------
    id: int
        The motor ID.
    angle: float
        The desired angle in degrees.
        With the encoding on 10bits, the numerical precision is 1e-3 degree
        # In practice, it seems that 
    rpm: float
        The rotation speed in rotations per minutes. Maximum 800.
    cur: str
        The current (proportionnal to torque). Not implemented so set to "0000"
    mode: str
        The mode can be "Position", "Velocity" or "Torque". I only implemented "Position" for now.
    enable: int
        if set to 0, it sends a command to disable the motor. Else it enables it.
    kp, kd: int
        gain and damping of the closed loop, between 0 and 255. 
    """
    mode_sel = {"Torque":"00", "Velocity":"01", "Position":"02"}[mode]

    pos = degrees_to_position_hex_10bit(angle)
    vel = rpm_to_velocity_hex_32bit(rpm)
    # print(f"Commande : {id} {pos} {vel} {cur} {mode_sel} {enable:02X} {kd:02X} {kp:02X}")
    return f"{id}{pos}{vel}{cur}{mode_sel}{enable:02X}{kd:02X}{kp:02X}00\r"

def degrees_to_position_hex_10bit(degrees: float) -> str:
    """
    Converts degrees to a 10-digit hexadecimal position command (20-bit
    turns + 20-bit single-turn position).
    Negative angles use 20-bit two's complement to represent turns, and the
    single-turn position is rounded.
    Parameters
    ----
    degrees : float
    Target angle, can be positive or negative.
    Returns
    ----
    str
    A 10-digit hexadecimal string, e.g., 'FFFF19999A'.
    """

    POS_PER_CIRCLE = 1 << 20 # 1048576
    MASK_20BIT = (1 << 20) - 1 # 0xFFFFF = 1048575
    # 1. Total turns (can be negative, with decimals)
    total_circles = degrees / 360.0
    # 2. Floor the integer turns to ensure frac is in [0,1)
    circles = math.floor(total_circles)
    frac = total_circles - circles # Decimal part

    # 3. Single-turn position: round to the nearest integer
    pos = round(frac * POS_PER_CIRCLE)
    # 4. If rounding hits 2^20, reset to 0 and add 1 turn
    if pos == POS_PER_CIRCLE:
        pos = 0
        circles += 1
    # 5. Convert turns to 20-bit two's complement
    circles_twos = circles & MASK_20BIT
    # 6. Combine into 5+5 digit hexadecimal
    return f"{circles_twos:05X}{pos:05X}"


def hex_to_degrees(hex_string):
    POS_PER_CIRCLE = 1 << 20  # 1048576
    # MASK_20BIT = (1 << 20) - 1  # 0xFFFFF = 1048575
    # 1. Extraire les deux parties de 5 digits
    circles_twos = int(hex_string[:5], 16)
    pos = int(hex_string[5:], 16)
    # 2. Reconvertir circles depuis le complément à deux 20-bit vers un entier signé
    # Si le bit de signe (bit 19) est à 1, c'est un nombre négatif
    if circles_twos & (1 << 19):  # Teste si bit 19 = 1
        circles = circles_twos - (1 << 20)  # Soustraire 2^20 pour obtenir la valeur négative
    else:
        circles = circles_twos
    # 3. Calculer la partie fractionnaire
    frac = pos / POS_PER_CIRCLE
    
    # 4. Reconstituer l'angle total
    total_circles = circles + frac
    degrees = total_circles * 360.0
    return degrees

def rpm_to_velocity_hex_32bit(rpm: float, pole_pairs: int = 14) -> str:
    """
    Converts mechanical speed (RPM) to a 32-bit velocity command, returning
    an 8-digit hexadecimal string (uppercase).
    Parameters
    ----
    rpm : float
    Target mechanical speed in RPM; can be positive or negative.
    pole_pairs : int, optional
    Motor pole pairs, default is 14 (3507 motor). Modify this value if
    changing the motor.
    Returns
    ----
    str
    An 8-digit hexadecimal string, e.g., '0059999A' or 'FFD33333' (two's
    complement when rpm is negative).
    """
    POS_PER_FREQ = 8_388_608 # 8388608 in the protocol
    DIVISOR = 60_000 # 60 * 1000
    MAX_UINT32 = 0xFFFFFFFF # Saturation limit
    # 1. Calculate Velocity (float) according to the protocol formula
    velocity = rpm * pole_pairs * POS_PER_FREQ / DIVISOR
    # 2. Round to the nearest integer
    velocity_int = int(round(velocity))
    # 3. If negative speeds are supported, convert to 32-bit two's complement; if only positive speeds are allowed, skip this step
    velocity_int &= MAX_UINT32
    # 4. Format as 8-digit hexadecimal (pad high bits with 0)
    return f"{velocity_int:08X}"


def read_response(cmd):
    # print(cmd)
    ID = cmd[0:5]
    angle = cmd[5:15]
    vel = cmd[15:23]
    curr = cmd[23:27]
    mode = cmd[27:29]
    run = cmd[29:31]
    reserved = cmd[31:33]
    temperature = cmd[33:35]
    slave_id = cmd[35:]

    # print(f"{ID} {angle} {vel} {curr} {mode} {run} {reserved} {temperature} {slave_id}")
    # print(f"{temperature}")
    return(hex_to_degrees(angle), temperature)


class MRM:

    def __init__(self, id="d001A", COM="COM5"):
        self.id = id
        self.COM = COM
        self.epsilon = 1e-2
        self.timeout = 1

    def open(self):
        self.ser = serial.Serial(self.COM, 1000000, timeout=0.1)
        self.ser.write(b"S8\r")
        self.ser.write(b"Y5\r")
        self.ser.write(b"O\r\n")
        self.ser.write(b"d001A00000000000000000000000200000000\r")
        self.ser.write(b"d001A00000000000000000000000200000000\r")  
        #Don't know why it needs to be repeated, but it doesn't work otherwhise... 
        self.last_command = "d001A00000000000000000000000200000000\r"

        self.angle = self.get_position()

    def close(self):
        response = self.send_command(enable=0)
        angle, temperature = read_response(response)
        print(f"{angle:.3f}°, {temperature}°C")
        self.ser.close()
        print("Motor closed succesfully.")


    def send_command(self, **kwargs):

        command = motor_command(self.id, **kwargs)
        self.last_command = command

        self.ser.write(bytes(command, encoding="utf-8"))
        return self.ser.readline().decode("utf-8")
        
    def get_position(self):
        # response = self.send_command(enable=0)
        self.ser.write(bytes(self.last_command, encoding="utf-8"))

        response = self.ser.readline().decode("utf-8")
        angle, temperature = read_response(response)
        self.temperature = temperature
        return(angle)

    def move(self, target_angle, rpm, kp=5, kd=5):
        response = self.send_command(angle=target_angle, rpm=rpm, kp=kp, kd=kd, enable=1)

        # time.sleep(abs(target_angle-self.angle)/(rpm*6))   #*6 to convert rotation/min to degrees/s

        # response = self.send_command(angle=target_angle, rpm=rpm, kp=kp, kd=kd, enable=1)
        # self.angle, _ = read_response(response)
        # start_time = time.time()
        # print(f"current angle : {self.angle:.3f}")

        # while abs(self.angle - target_angle) > self.epsilon and abs(time.time()-start_time) < self.timeout and not self.stop_command:
        #     print("loop")
        #     time.sleep(abs(target_angle-self.angle)/(rpm*6))
        #     response = self.send_command(angle=target_angle, rpm=rpm, kp=kp, kd=kd, enable=1)
        #     self.angle, _ = read_response(response)

        #     print(f"    current angle : {self.angle:.3f}")
        #     # print(abs(self.angle - target_angle) > self.epsilon)
        #     # print(abs(time.time()-start_time) < self.timeout)
        #     if time.time()-start_time > self.timeout:
        #         print("timeout")
        #     if abs(self.angle - target_angle) < self.epsilon:
        #         print("Reached position !")
        # response = self.send_command(enable=0)
        # self.angle, self.temperature = read_response(response)
        ### No need for all this right now but could be reused for something else later... 

    def on_move_done(self):
        response = self.send_command(enable=0)
        self.angle, self.temperature = read_response(response)


if __name__ == "__main__":

    motor = MRM(COM="COM6")

    motor.open()
    motor.timeout = 10
    try:
        print(f"angle : {motor.angle:.3f}")
        position = motor.get_position()
        print(f"get position : {position}")
        # motor.close()
        motor.move(target_angle=180, rpm=120, kd=30)
        position = motor.get_position()
        print(f"middle angle : {motor.angle:.3f}")


        time.sleep(5)
        motor.move(target_angle=0, rpm=120, kd=30)
        position = motor.get_position()
        print(f"end angle : {motor.angle:.3f}")

        motor.close()
    except Exception as e:
        print(e)
        motor.ser.close()
    