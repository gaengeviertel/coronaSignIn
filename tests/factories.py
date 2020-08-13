from faker import Faker

fake = Faker()


def makeSignInData(**overrides):
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "street_and_house_number": f"{fake.street_name()} {fake.building_number()}",
        "plz_and_city": f"{fake.random_int(10000, 99999)} {fake.city()}",
        "phone_number": fake.phone_number(),
        **overrides,
    }
