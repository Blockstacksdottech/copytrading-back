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



class IsAdminUserOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view): 
        print("hello")
        return request.user.is_authenticated and (request.user.is_superuser or request.method in ['GET', 'HEAD', 'OPTIONS'])

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

        
class UserDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            try:
                user_details = Profile.objects.get(user=request.user)
            except:
                user_details = Profile.objects.create(user=request.user)
                user_details.save()
            serializer = ProfileSerializer(user_details)
            return Response(serializer.data, status=HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({'error': 'User details not found'}, status=HTTP_404_NOT_FOUND)

    def post(self, request):
        try:
            user_details = Profile.objects.get(user=request.user)
            serializer = ProfileSerializer(
                user_details, data=request.data, partial=True)

        except Profile.DoesNotExist:
            data = request.data
            data["user"] = request.user.id

            serializer = ProfileSerializer(data=data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
    
class UserDocumentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            try:
                user_documents = UserDocuments.objects.get(user=request.user)
            except:
                user_documents = UserDocuments.objects.create(user=request.user)
                user_documents.save()
            serializer = DocumentSerialzier(user_documents)
            return Response(serializer.data, status=HTTP_200_OK)
        except UserDocuments.DoesNotExist:
            return Response({'error': 'User details not found'}, status=HTTP_404_NOT_FOUND)

    def post(self, request):
        if (request.user.isVerified):
            return Response({"reason" : "already verified"}, status=HTTP_400_BAD_REQUEST)
        try:
            user_documents = UserDocuments.objects.get(user=request.user)
            serializer = DocumentSerialzier(
                user_documents, data=request.data, partial=True)

        except UserDocuments.DoesNotExist:
            data = request.data
            data["user"] = request.user.id
            serializer = DocumentSerialzier(data=data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
# admin views
class AdmUserList(ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdmUserSerializer

    def get_queryset(self):
        return CustomUser.objects.filter(is_superuser=False)
    
class AdmBrokerViewSet(ModelViewSet):
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = AdmBrokerSerializer

    def get_queryset(self):
        return Brokers.objects.all()


# user views

class VerboseStrategyViewSet(ModelViewSet):
    serializer_class = VerboseStrategySerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']

    def get_queryset(self):
        return Strategy.objects.all()
    
class StrategyCreator(ModelViewSet):
    serializer_class = MinStrategySerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['post']

class StrategyViewSet(ModelViewSet):
    
    serializer_class = StrategySerializer
    permission_classes = [permissions.IsAuthenticated]

    """ def perform_create(self, serializer):
        #data = self.request.data 
         data['creator'] = self.request.user.id
        new_data = {
            'creator': data['creator'],
            **data,  # Unpack the original request data (without modification)
        } 
         d = MinStrategySerializer(data=data)
        if d.is_valid():
             res = d.save()
            print(res)
            return res 
            return True
        else:
            print("failed")
            print(d.error_messages)
            return False 
        return True """
    
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
        serializer = VerboseStrategySerializer(res, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='subscribed')
    def sub_strat(self, request):
        creator = request.user
        subs = Subscription.objects.filter(subscriber = creator)
        
        serializer = SubscriptionSerializer(subs,many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='watched')
    def watch_strat(self, request):
        creator = request.user
        subs = WatchList.objects.filter(subscriber = creator)
        
        serializer = WatchListSerializer(subs,many=True)
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
        print("this one")
        strategy = Strategy.objects.filter(id=pk).first()
        if not strategy:
            return Response({"detail": "Not Found."}, status=HTTP_400_BAD_REQUEST)
        subscriber = request.user

        subscription = Subscription.objects.filter(strategy=strategy, subscriber=subscriber).first()
        if not subscription:
            return Response({"detail": "Not subscribed."}, status=HTTP_400_BAD_REQUEST)

        subscription.delete()
        return Response({"detail": "Unsubscribed successfully."}, status=HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='watch')
    def watch(self, request, pk=None):
        print(pk)
        strategy = Strategy.objects.filter(id=pk).first()
        if not strategy:
            return Response({"detail": "Not Found."}, status=HTTP_400_BAD_REQUEST)
        subscriber = request.user

        

        # Check if user is already subscribed
        if WatchList.objects.filter(strategy=strategy, subscriber=subscriber).exists():
            return Response({"detail": "Already watching it."}, status=HTTP_400_BAD_REQUEST)

        subscription = WatchList(strategy=strategy, subscriber=subscriber)
        subscription.save()
        return Response({"detail": "Added."}, status=HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='unwatch')
    def unwatch(self, request, pk=None):
        print(pk)
        strategy = Strategy.objects.filter(id=pk).first()
        if not strategy:
            return Response({"detail": "Not Found."}, status=HTTP_400_BAD_REQUEST)
        subscriber = request.user

        subscription = WatchList.objects.filter(strategy=strategy, subscriber=subscriber).first()
        if not subscription:
            return Response({"detail": "Not watched."}, status=HTTP_400_BAD_REQUEST)

        subscription.delete()
        return Response({"detail": "Removed successfully."}, status=HTTP_200_OK)



class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Password updated successfully."}, status=HTTP_200_OK)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        

class TicketViewSet(ModelViewSet):
    queryset = Ticket.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Ticket.objects.all()
        else:
            return Ticket.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateTicketSerializer
        return TicketSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        ticket = self.get_object()
        if request.user.is_staff:
            # Only admins can close tickets
            ticket.isClosed = request.data.get('isClosed', ticket.isClosed)
            ticket.save()
        return super().update(request, *args, **kwargs)

class MessageViewSet(ModelViewSet):
    queryset = Message.objects.all().order_by("date_sent")
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        ticket_id = self.request.query_params.get('ticket')
        print(ticket_id)
        ticket = Ticket.objects.get(id=ticket_id)
        print(ticket)

        # Check if the user is either the admin or the ticket creator
        if self.request.user.is_superuser or ticket.user == self.request.user:
            serializer.save(sender=self.request.user, ticket=ticket)
        else:
            raise Exception("You do not have permission to send a message to this ticket.")