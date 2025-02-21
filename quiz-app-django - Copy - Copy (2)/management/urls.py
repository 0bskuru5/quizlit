from django.urls import path
from .views import (
    management_login, management_dashboard, approve_payment, management_logout,
    quiz_activity, data_visualization, check_payment, user_activity_log, statistics_view, candidate_detail
)

urlpatterns = [
    path("login/", management_login, name="management_login"),
    path("dashboard/", management_dashboard, name="management_dashboard"),
    path("approve-payment/<int:user_id>/", approve_payment, name="approve_payment"),
    path("logout/", management_logout, name="management_logout"),
    path("quiz-activity/", quiz_activity, name="quiz_activity"),
    path("data-visualization/", data_visualization, name="data_visualization"),
    path("check-payment/<int:category_id>/", check_payment, name="check_payment"),
    path("", management_dashboard, name="management_dashboard"),
    path('user-activity-log/', user_activity_log, name='user_activity_log'),
    path('statistics/', statistics_view, name='statistics'),
    path('candidate/<int:id>/', candidate_detail, name='candidate_detail'),



]
