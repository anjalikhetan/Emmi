from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.views import defaults as default_views

from drf_spectacular.views import SpectacularAPIView
from drf_spectacular.views import SpectacularSwaggerView

from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from api.users.views import HealthCheckView, UserViewSet, VerificationCodeView, VerifyCodeView
from api.plans.views import (
    TrainingPlanGenerateView, PlanDetailView, 
    WorkoutListView, WorkoutDetailView
)


urlpatterns = [
    # Django Admin
    path(settings.ADMIN_URL, admin.site.urls),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]

# API Router
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'health', HealthCheckView, basename='health')

# API URLS
urlpatterns += [
    # Verification code endpoints
    path('api/v1/users/verification-code/', VerificationCodeView.as_view(), name='verification-code'),
    path('api/v1/users/verify-code/', VerifyCodeView.as_view(), name='verify-code'),
    # Plan generation endpoint
    path('api/v1/plans/generate/', TrainingPlanGenerateView.as_view(), name='generate-plan'),
    # New Plan and Workout endpoints
    path('api/v1/plans/<uuid:plan_id>/', PlanDetailView.as_view(), name='plan-detail'),
    path('api/v1/plans/<uuid:plan_id>/workouts/', WorkoutListView.as_view(), name='workout-list'),
    path('api/v1/plans/<uuid:plan_id>/workouts/<uuid:workout_id>/', WorkoutDetailView.as_view(), name='workout-detail'),
    # API base url
    path('api/v1/', include(router.urls)),
    # DRF auth token
    path("api/auth-token/", obtain_auth_token),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns