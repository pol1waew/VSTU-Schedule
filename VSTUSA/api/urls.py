from django.urls import include, path
from api.views import (
    EventKindListView,
    EventViewSet,
    GroupViewSet,
    JSONImportAPIView,
    DBImportAPIView,
    LessonRoomViewSet,
    ObtainAPIUserToken,
    ScheduleViewSet,
    SchedulesAPIRootView,
    SubjectViewSet,
    TeacherViewSet,
)
from rest_framework.routers import DefaultRouter


router = DefaultRouter(trailing_slash=True)
router.APIRootView = SchedulesAPIRootView
router.register(r"subjects", SubjectViewSet, basename="subjects")
router.register(r"events", EventViewSet, basename="events")
router.register(r"lessonrooms", LessonRoomViewSet, basename="lessonrooms")
router.register(r"groups", GroupViewSet, basename="groups")
router.register(r"teachers", TeacherViewSet, basename="teachers")
router.register(r"schedules", ScheduleViewSet, basename="schedules")


urlpatterns = [
    path("session-auth/", include("rest_framework.urls")),
    path("events/kind/", EventKindListView.as_view()),
    path("import/json/", JSONImportAPIView.as_view()),
    path("import/db/", DBImportAPIView.as_view()),
    path("obtain-token/", ObtainAPIUserToken.as_view()),
]

urlpatterns += router.urls
