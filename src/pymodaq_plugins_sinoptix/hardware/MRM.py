import math
import time




def motor_command(id="d001A", angle=0, rpm=5, cur="0000", mode="Position", enable=1, kp=5, kd=5):
    mode_sel = {"Torque":"00", "Velocity":"01", "Position":"02"}[mode]

    pos = degrees_to_position_hex_10bit(angle)
    vel = rpm_to_velocity_hex_32bit(rpm)
    print(f"Commande : {id} {pos} {vel} {cur} {mode_sel} {enable:02X} {kd:02X} {kp:02X}")
    return f"{id}{pos}{vel}{cur}{mode_sel}{enable:02X}{kd:02X}{kp:02X}\r"

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


class MRM:

    def __init__(self, id="d001A"):
        self.id = id


    def open(self):
        pass

    def close(self):
        pass

    def motor_command(self, **kwargs):
        return (self.motor_command(self.id, **kwargs))

    def open(self):
        pass

    def open(self):
        pass

    def open(self):
        pass

    def open(self):
        pass


