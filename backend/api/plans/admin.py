from django.contrib import admin
from django.db import models
from django_json_widget.widgets import JSONEditorWidget
from api.plans.models import Plan, Workout


class WorkoutInline(admin.TabularInline):
    """
    Inline admin for Workouts within a Plan
    """
    model = Workout
    extra = 0
    fields = ('date', 'completion_status', 'difficulty', 'additional_notes', 'workout_info')
    readonly_fields = ('id',)

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)

        if db_field.name == 'workout_info':
            formfield.widget = JSONEditorWidget(options={'mode': 'code'})
            formfield.widget.attrs['style'] = 'width: 800px; min-width: 800px; height: 300px;'  # Add height here

        elif db_field.name == 'additional_notes':
            formfield.widget.attrs.update({
                'cols': '20',
                'rows': '2',
                'style': 'max-width: 200px;'
            })

        return formfield


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Plan model
    """
    list_display = ('id', 'user', 'user_id', 'username', 'created_at')
    list_filter = ('user',)
    search_fields = ('user__email',)
    readonly_fields = ('id', 'created_at')
    inlines = [WorkoutInline]

    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    def user_id(self, obj):
        """
        Display the user ID in the admin.
        """
        return obj.user.id
    user_id.admin_order_field = 'user__id'
    user_id.short_description = 'User ID'

    def username(self, obj):
        """
        Display the username in the admin.
        """
        return obj.user.first_name
    username.admin_order_field = 'user__first_name'
    username.short_description = 'Username'
