import math

import constants as const
from nutrition_requirements import NutritionReq
from person_profile import PersonProfile
from utils import convert_to_kg, convert_to_meters, convert_to_inch, convert_to_lbs


def compute_nutritional_needs(person):
    """
    Given a person profile, compute the nutritional needs.
    :param person: person profile
    :return: nutritional needs
    """
    weight_in_kg = convert_to_kg(person.unit, person.weight)
    height_in_meters = convert_to_meters(person.unit, person.height)
    waist_size_in_inch = convert_to_inch(person.unit, person.waist_size)
    weight_in_lbs = convert_to_lbs(person.unit, person.weight)

    # sex factor : factor_sex
    # age factor : factor_age
    # Physical Activity  Factor (PA) : factor_pa
    # weight factor : factor_w
    # height factor : factor_h
    if const.SEX_MALE == person.sex:
        factor_sex = 662
        factor_age = -9.53 * person.age
        if const.ACTIVITY_LEVEL_INACTIVE == person.activity_level:
            factor_pa = 1.00
        elif const.ACTIVITY_LEVEL_LOW == person.activity_level:
            factor_pa = 1.10
        elif const.ACTIVITY_LEVEL_HIGH == person.activity_level:
            factor_pa = 1.35
        else:  # if const.ACTIVITY_LEVEL_MODERATE == person.activity_level:
            factor_pa = 1.15
        factor_w = 15.91 * weight_in_kg
        factor_h = 539.68 * height_in_meters
        body_fat = -98.42 + 4.15 * waist_size_in_inch - .082 * weight_in_lbs
    else:
        factor_sex = 354
        factor_age = -6.91 * person.age
        if const.ACTIVITY_LEVEL_INACTIVE == person.activity_level:
            factor_pa = 1.00
        elif const.ACTIVITY_LEVEL_LOW == person.activity_level:
            factor_pa = 1.12
        elif const.ACTIVITY_LEVEL_HIGH == person.activity_level:
            factor_pa = 1.35
        else:  # const.ACTIVITY_LEVEL_MODERATE == person.activity_level:
            factor_pa = 1.20
        factor_w = 9.36 * weight_in_kg
        factor_h = 726 * height_in_meters
        body_fat = -76.76 + (4.15 * waist_size_in_inch) - (.082 * weight_in_lbs)

    # Height   factor    for BMI calculation
    factor_h2 = height_in_meters * height_in_meters
    # Weight-factor for BMI calculation
    factor_w2 = weight_in_kg
    factor_bmi = (factor_w2 / factor_h2) * 10
    bmi = math.floor(factor_bmi) / 10

    factor_pah = factor_pa * factor_h
    factor_paw = factor_pa * factor_w
    factor_pahw = factor_pah + factor_paw
    total_eer = round(factor_sex + factor_age + factor_pahw)

    # Calculate    the    body-fat    percentage
    body_fat_percent = body_fat / weight_in_lbs
    body_fat_percent = round(body_fat_percent * 100)

    fat_mass = round(weight_in_lbs * body_fat_percent * .01)
    lean_body_mass = round(weight_in_lbs - fat_mass)

    if const.SEX_MALE == person.sex:
        basal_metabolic_rate = round(lean_body_mass * 11)
        if const.EXPECTATION_LOSE == person.expectation:
            calories = basal_metabolic_rate * 1.4
        elif const.EXPECTATION_GAIN == person.expectation:
            calories = basal_metabolic_rate * 1.8
        else:  # if person.expectation == "MAINTAIN":
            calories = basal_metabolic_rate * 1.6
    else:
        basal_metabolic_rate = round(lean_body_mass * 10)
        if const.EXPECTATION_LOSE == person.expectation:
            calories = basal_metabolic_rate * 1.2
        elif const.EXPECTATION_GAIN == person.expectation:
            calories = basal_metabolic_rate * 1.6
        else:  # if person.expectation == "MAINTAIN":
            calories = basal_metabolic_rate * 1.4

    carb_calories, fat_calories, protein_calories = get_nutrient_calories(calories, person)
    carb_grams, fat_grams, protein_grams = get_nutrient_grams(carb_calories, fat_calories, protein_calories)
    return NutritionReq(fat_mass, lean_body_mass, basal_metabolic_rate, protein_calories, carb_calories,
                        fat_calories, protein_grams, carb_grams, fat_grams, bmi, total_eer, body_fat_percent)


def get_nutrient_grams(carb_calories, fat_calories, protein_calories):
    """
    Compute carb, fat and protein requirements in grams
    :param carb_calories: required carb in calories
    :param fat_calories: required fat in calories
    :param protein_calories: required protein in calories
    :return: carb, fat and protein requirements in grams
    """
    protein_grams = round(protein_calories / 4)
    carb_grams = round((carb_calories / 4))
    fat_grams = round(fat_calories / 9)
    return carb_grams, fat_grams, protein_grams


def get_nutrient_calories(calories, person):
    """
    Compute required amount of carb, fat and protein from total calories and preferences
    :param calories: total calorie required
    :param person: person profile. Has preferred protein, carb and fat percentages
    :return: protein, carb and fat calories
    """
    protein_calories = round(calories * person.protein_percent * .01)
    carbohydrates_calories = round(calories * person.carb_percent * .01)
    fat_calories = round(calories * person.fat_percent * .01)
    return carbohydrates_calories, fat_calories, protein_calories


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    pid = 1
    name = "Smith"
    age = 20
    sex = const.SEX_MALE
    height = 170
    weight = 70
    unit = const.UNIT_METRIC
    activity_level = const.ACTIVITY_LEVEL_LOW
    waist_size = 40
    expectation = const.EXPECTATION_GAIN
    protein_percent = 20
    carb_percent = 55
    fat_percent = 25
    smith = PersonProfile(pid, name, age, sex, height, weight, unit, activity_level, waist_size, expectation,
                          protein_percent, carb_percent, fat_percent)
    nutrition_requirements = compute_nutritional_needs(smith)
    print(nutrition_requirements)
