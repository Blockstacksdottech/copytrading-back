from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.status import *
from rest_framework import permissions
from django.db.models.functions import TruncMonth, TruncWeek
from django.db.models import Sum
from django.utils import timezone
from collections import defaultdict
from rest_framework.decorators import action

# serializers imports
from .serializer import *

# models imports
from .models import *

from rest_framework_simplejwt.views import TokenObtainPairView

# Create your views here.


class TestSession(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        return Response(UserSerializer(user).data)


class CustomTokenObtain(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class Register(APIView):
    def post(self, request, format=None):
        data = request.data
        print(data)
        # del temp_data['pin']
        u = UserSerializer(data=data)
        if u.is_valid():
            u_data = u.save()
            u_data.set_password(data["password"])
            u_data.save()
            return Response(UserSerializer(u_data).data)
        else:
            print(u.error_messages)
            return Response({"failed": True}, status=HTTP_400_BAD_REQUEST)
        
# admin views
class AdmUserList(ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = UserSerializer

    def get_queryset(self):
        return CustomUser.objects.filter(is_superuser=False)


# user views

class StrategyViewSet(ModelViewSet):
    
    serializer_class = StrategySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
    
    def get_queryset(self):
        return Strategy.objects.filter(creator=self.request.user)
    
    @action(detail=True, methods=['post'], url_path='update-status')
    def updateStatus(self,request,pk=None):
        strat = self.get_object()
        if strat:
            strat.enabled = not strat.enabled
            strat.save()
            return Response({"detail": "Updated successfully."}, status=HTTP_200_OK)
        else:
            return Response({"detail": "Failed."}, status=HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['get'], url_path='my-strategies')
    def my_strategies(self, request):
        creator = request.user
        strategies = Strategy.objects.filter(creator=creator)
        serializer = self.get_serializer(strategies, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='all')
    def all_strats(self, request):
        creator = request.user
        strategies = Strategy.objects.filter(enabled=True)
        res = []
        for strat in strategies:
            if strat.creator.username == creator.username:
                continue
            sub = Subscription.objects.filter(strategy=strat).first()
            if not sub:
                res.append(strat)
        serializer = self.get_serializer(res, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='subscribed')
    def sub_strat(self, request):
        creator = request.user
        subs = Subscription.objects.filter(subscriber = creator)
        
        serializer = SubscriptionSerializer(subs,many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='subscribe')
    def subscribe(self, request, pk=None):
        print(pk)
        strategy = Strategy.objects.filter(id=pk).first()
        if not strategy:
            return Response({"detail": "Not Found."}, status=HTTP_400_BAD_REQUEST)
        subscriber = request.user

        # Check if maxSubscribers limit has been reached
        current_subscribers = Subscription.objects.filter(strategy=strategy).count()
        if strategy.maxSubscribers is not None and current_subscribers >= strategy.maxSubscribers:
            return Response({"detail": "Maximum number of subscribers reached."}, status=HTTP_400_BAD_REQUEST)

        # Check if user is already subscribed
        if Subscription.objects.filter(strategy=strategy, subscriber=subscriber).exists():
            return Response({"detail": "Already subscribed."}, status=HTTP_400_BAD_REQUEST)

        subscription = Subscription(strategy=strategy, subscriber=subscriber)
        subscription.save()
        return Response({"detail": "Subscribed successfully."}, status=HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='unsubscribe')
    def unsubscribe(self, request, pk=None):
        print(pk)
        strategy = Strategy.objects.filter(id=pk).first()
        if not strategy:
            return Response({"detail": "Not Found."}, status=HTTP_400_BAD_REQUEST)
        subscriber = request.user

        subscription = Subscription.objects.filter(strategy=strategy, subscriber=subscriber).first()
        if not subscription:
            return Response({"detail": "Not subscribed."}, status=HTTP_400_BAD_REQUEST)

        subscription.delete()
        return Response({"detail": "Unsubscribed successfully."}, status=HTTP_200_OK)



class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Password updated successfully."}, status=HTTP_200_OK)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
class ProfileViewSet(ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer
    
    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user).first()