import factory
from django.utils import timezone
from api.users.test.factories import UserFactory
from api.plans.models import Plan, Workout


class PlanFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating Plan instances for testing.
    """
    class Meta:
        model = Plan
    
    user = factory.SubFactory(UserFactory)
    plan_info = factory.Dict({"type": "training", "weeks": 12})


class WorkoutFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating Workout instances for testing.
    """
    class Meta:
        model = Workout
    
    plan = factory.SubFactory(PlanFactory)
    date = factory.LazyFunction(lambda: timezone.now().date())
    workout_info = factory.Dict({"type": "run", "distance": "5km"})