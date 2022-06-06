from nutritional_requirements import constants as const


def convert_to_kg(unit, weight):
    """
    Given the unit and weight, convert weight to weight in kilograms
    :param unit: unit of weight
    :param weight:
    :return: weight in kg
    """
    convert_pounds = 0.4536
    convert_kilograms = 1

    if const.UNIT_STD == unit:
        conversion_factor = convert_pounds
    else:  # if (unit == "metric"): # default unit to kg
        conversion_factor = convert_kilograms
    weight_in_kg = weight * conversion_factor

    return weight_in_kg


def convert_to_meters(unit, height):
    """
    Given the unit and height, convert weight to height in meters
    :param unit: unit of height
    :param height:
    :return: height in meters
    """
    convert_inches = 0.0254
    convert_cm = 0.01

    conversion_factor = 1  # default unit to meters
    if const.UNIT_STD == unit:  # centimeters
        conversion_factor = convert_inches
    elif const.UNIT_METRIC == unit:  # inches
        conversion_factor = convert_cm

    height_in_meters = height * conversion_factor

    return height_in_meters


def convert_to_inch(unit, value):
    """
    Given a value and its unit, convert it to inches
    :param unit: unit of value
    :param value: value to be converted
    :return: value in inches
    """
    convert_cm = .393701
    if const.UNIT_METRIC == unit:
        conversion_factor = convert_cm
    else:
        conversion_factor = 1

    return value * conversion_factor


def convert_to_lbs(unit, weight):
    """
    Given a weight and unit, convert weight to lbs
    :param unit: unit of weight
    :param weight: weight value to be converted
    :return: weight in lbs
    """
    convert_kg = 2.20462
    if const.UNIT_METRIC == unit:
        conversion_factor = convert_kg
    else:
        conversion_factor = 1
    return weight * conversion_factor