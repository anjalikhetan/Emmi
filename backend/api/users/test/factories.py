import factory
import random
from phonenumber_field.phonenumber import PhoneNumber
import datetime


class UserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'users.User'
        django_get_or_create = ('username',)

    id = factory.Faker('uuid4')
    username = factory.Sequence(lambda n: f'testuser{n}')
    password = factory.Faker(
        'password',
        length=10,
        special_chars=True,
        digits=True,
        upper_case=True,
        lower_case=True
    )
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False


class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'users.Profile'

    user = factory.SubFactory(UserFactory)
    phone_number = "+12025550109"
    
    # Basic information fields
    age = factory.Faker('random_int', min=18, max=80)
    
    # Height fields
    feet = factory.Faker('random_int', min=4, max=6)
    inches = factory.Faker('random_int', min=0, max=11)
    heightCm = factory.LazyAttribute(lambda o: (o.feet * 30.48) + (o.inches * 2.54))
    
    # Weight fields
    weightKg = factory.Faker('random_int', min=45, max=120)
    weightLbs = factory.LazyAttribute(lambda o: o.weightKg * 2.20462)
    
    # Goals and details
    goals = factory.LazyFunction(lambda: ["improve_fitness", "run_faster"])
    goalsDetails = factory.Faker('text', max_nb_chars=200)
    
    # Race information
    raceName = factory.Faker('word')
    raceDate = factory.Faker('future_date')
    distance = factory.LazyFunction(lambda: random.choice(["5K", "10K", "Half Marathon", "Marathon"]))
    timeGoal = factory.LazyFunction(lambda: f"{random.randint(1, 5)}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}")
    
    # Running experience
    runningExperience = factory.Faker('text', max_nb_chars=200)
    
    # Current routine
    routineDaysPerWeek = factory.LazyFunction(lambda: str(random.randint(1, 7)))
    routineMilesPerWeek = factory.LazyFunction(lambda: str(random.randint(1, 20)))
    routineEasyPace = factory.LazyFunction(lambda: f"{random.randint(5, 12)}:{random.randint(0, 59):02d}")
    routineLongestRun = factory.LazyFunction(lambda: f"{random.randint(1, 30)} miles")
    
    # Race results
    recentRaceResults = factory.Faker('text', max_nb_chars=200)
    
    # Additional training and diet
    extraTraining = factory.LazyFunction(lambda: ["strength_training", "yoga"])
    diet = factory.LazyFunction(lambda: ["omnivore"])
    
    # Health information
    injuries = factory.Faker('text', max_nb_chars=100)
    
    # Schedule preferences
    daysCommitTraining = factory.LazyFunction(lambda: ["monday", "wednesday", "friday", "saturday"])
    preferredLongRunDays = factory.LazyFunction(lambda: ["saturday"])
    preferredWorkoutDays = factory.LazyFunction(lambda: ["tuesday", "thursday"])
    preferredRestDays = factory.LazyFunction(lambda: ["sunday"])
    
    # Additional information
    otherObligations = factory.Faker('text', max_nb_chars=150)
    pastProblems = factory.LazyFunction(lambda: ["none"])
    moreInfo = factory.Faker('text', max_nb_chars=150)


class PhoneVerificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'users.PhoneVerification'

    phone_number = "+12025550109"
    verification_code = factory.LazyFunction(lambda: ''.join([str(random.randint(0, 9)) for _ in range(6)]))
    created_at = factory.Faker('date_time_this_month')