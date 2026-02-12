from django.contrib import admin
from django.db.models import F


class AccuracyFilter(admin.SimpleListFilter):
    title = "accuracy level"
    parameter_name = "accuracy"

    def lookups(self, request, model_admin):
        return (
            ("high", "High (80-100%)"),
            ("medium", "Medium (50-79%)"),
            ("low", "Low (0-49%)"),
        )

    def queryset(self, request, queryset):
        if self.value() == "high":
            return queryset.filter(
                total_questions__gt=0,
                correct_answers__gte=0.8 * F("total_questions"),
            )
        if self.value() == "medium":
            return queryset.filter(
                total_questions__gt=0,
                correct_answers__gte=0.5 * F("total_questions"),
                correct_answers__lt=0.8 * F("total_questions"),
            )
        if self.value() == "low":
            return queryset.filter(
                total_questions__gt=0,
                correct_answers__lt=0.5 * F("total_questions"),
            )
        return queryset
