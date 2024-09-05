from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.urls import path, re_path, include
from rest_framework import routers


router = routers.SimpleRouter()
router.register("adminvestors",AdmUserList,basename='admuserlist')
router.register(r'strategies', StrategyViewSet,basename='strategies')
router.register(r'create-strategy',StrategyCreator,basename="strat-creator")
router.register(r'detailedstrategies', VerboseStrategyViewSet,basename='strategies-detailed')
router.register(r'brokers',AdmBrokerViewSet,basename='admin-brokers')
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'messages', MessageViewSet, basename='message')
#router.register(r'profile', UserDetailsView,basename='profile')
# router.register("data", DataHandler, basename="data-handler")


urlpatterns = [
    path("", include(router.urls)),
    path('token', CustomTokenObtain.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('session', TestSession.as_view()),
    path("register", Register.as_view()),
    path('change-password', ChangePasswordView.as_view(), name='change-password'),
    path("profile",UserDetailsView.as_view(),name="profile"),
    path("documents",UserDocumentView.as_view(),name="documents")
]
