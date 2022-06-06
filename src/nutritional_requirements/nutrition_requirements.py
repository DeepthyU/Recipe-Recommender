class NutritionReq:
    def __init__(self, fat_mass, lean_body_mass, basal_metabolic_rate, protein_calories, carb_calories,
                 fat_calories, protein_grams, carb_grams, fat_grams, bmi, total_eer, body_fat_percent):
        self.fat_mass = fat_mass
        self.lean_body_mass = lean_body_mass
        self.basal_metabolic_rate = basal_metabolic_rate
        self.protein_calories = protein_calories
        self.carb_calories = carb_calories
        self.fat_calories = fat_calories
        self.protein_grams = protein_grams
        self.carb_grams = carb_grams
        self.fat_grams = fat_grams
        self.bmi = bmi
        self.total_eer = total_eer
        self.body_fat_percent = body_fat_percent

    def __str__(self) -> str:
        return 'NutritionRequirements(fat_mass = ' + str(self.fat_mass) + \
               ', lean_body_mass = ' + str(self.lean_body_mass) + \
               ', basal_metabolic_rate = ' + str(self.basal_metabolic_rate) + \
               ', protein_calories = ' + str(self.protein_calories) + \
               ', carb_calories = ' + str(self.carb_calories) + \
               ', fat_calories = ' + str(self.fat_calories) + \
               ', protein_grams = ' + str(self.protein_grams) + \
               ', carb_grams = ' + str(self.carb_grams) + \
               ', fat_grams = ' + str(self.fat_grams) + \
               ', bmi = ' + str(self.bmi) + \
               ', total_eer = ' + str(self.total_eer) + \
               ', body_fat_percent = ' + str(self.body_fat_percent) + ')'
