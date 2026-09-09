# simple helper function for rssi-to-distance computation

"""
solver/distance.py
------------------
Converts raw RSSI (dBm) values into physical distance (feet)
using the Log-Distance Path Loss model:
d = 10 ^ ((TxPower - RSSI) / (10 * n))
"""

def rssi_to_distance(rssi: int, tx_power: float, path_loss_exponent: float) -> float:
    """
    Calculates distance in feet from raw RSSI.
    
    :param rssi: Received Signal Strength Indicator in dBm (e.g., -65)
    :param tx_power: Expected RSSI at 1 meter/foot distance (e.g., -59)
    :param path_loss_exponent: Signal attenuation factor 'n' (typically 2.0 to 4.0)
    :return: Estimated distance in feet
    """
    if rssi >= 0:
        return 0.0
    return 10 ** ((tx_power - rssi) / (10 * path_loss_exponent))
