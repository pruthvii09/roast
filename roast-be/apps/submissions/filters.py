import django_filters

from .models import Submission, SubmissionStatus, SubmissionType, SubmissionVisibility


class SubmissionFilter(django_filters.FilterSet):
    submission_type = django_filters.ChoiceFilter(choices=SubmissionType.choices)
    status = django_filters.ChoiceFilter(choices=SubmissionStatus.choices)
    visibility = django_filters.ChoiceFilter(choices=SubmissionVisibility.choices)

    class Meta:
        model = Submission
        fields = ["submission_type", "status", "visibility"]
