class PersonProfile:
    def __init__(self, id, name, age, sex, height, weight, unit, activity_level, waist_size, expectation,
                 protein_percent = 20, carb_percent = 55, fat_percent = 25):
        self.id = id
        self.name = name
        self.age = age
        self.sex = sex
        self.height = height
        self.weight = weight
        self.unit = unit
        self.activity_level = activity_level
        self.waist_size = waist_size
        self.expectation = expectation
        # Daily calorie percentage
        self.protein_percent = protein_percent
        self.carb_percent = carb_percent
        self.fat_percent = fat_percent

