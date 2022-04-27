from django.urls import path

from .views import SpeakerExpenseList, SpeakerExpenseDetail, MarkExpenseView

urlpatterns = [
    path(
        "orga/event/<slug:event>/speakers/<int:speaker_id>/expenses/",
        view=SpeakerExpenseList.as_view(),
        name='expenses.view'
    ),
    path(
        "orga/event/<slug:event>/speakers/<int:speaker_id>/expenses/new",
        view=SpeakerExpenseDetail.as_view(),
        name='expenses.create'
    ),
    path(
        "orga/event/<slug:event>/speakers/<int:speaker_id>/expense/<int:pk>",
        view=SpeakerExpenseDetail.as_view(),
        name='expense.view'
    ),
    path(
        "orga/event/<slug:event>/speakers/<int:speaker_id>/expense/<int:pk>/mark",
        view=MarkExpenseView.as_view(),
        name='expense.mark'
    ),

]
