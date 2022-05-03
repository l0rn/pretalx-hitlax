from django.urls import path

from .views import (
    MarkExpenseView,
    SpeakerExpenseDetail,
    SpeakerExpenseList,
    SpeakerList,
    SpeakerTourManagement,
    TourListView
)

urlpatterns = [
    path(
        "orga/event/<slug:event>/speakers-by-expense/",
        view=SpeakerList.as_view(),
        name="speakers_by_expense.view",
    ),
    path(
        "orga/event/<slug:event>/speakers/<int:pk>/tours/",
        view=SpeakerTourManagement.as_view(),
        name="tours.view",
    ),
    path(
        "orga/event/<slug:event>/tours/",
        view=TourListView.as_view(),
        name="tours.view",
    ),
    path(
        "orga/event/<slug:event>/speakers/<int:speaker_id>/expenses/",
        view=SpeakerExpenseList.as_view(),
        name="expenses.view",
    ),
    path(
        "orga/event/<slug:event>/speakers/<int:speaker_id>/expenses/new",
        view=SpeakerExpenseDetail.as_view(),
        name="expenses.create",
    ),
    path(
        "orga/event/<slug:event>/speakers/<int:speaker_id>/expense/<int:pk>",
        view=SpeakerExpenseDetail.as_view(),
        name="expense.view",
    ),
    path(
        "orga/event/<slug:event>/speakers/<int:speaker_id>/expense/<int:pk>/mark",
        view=MarkExpenseView.as_view(),
        name="expense.mark",
    ),
]
