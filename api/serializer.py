from .models import (
    CustomUser,
    Strategy,
    Subscription,
    Profile,
    UserDocuments,
    Brokers,
    Trade,
    Result,
    Ticket,
    Message
)
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from rest_framework import exceptions, serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings


class PasswordField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("style", {})

        kwargs["style"]["input_type"] = "password"
        kwargs["write_only"] = True

        super().__init__(*args, **kwargs)


class MyTokenObtainSerializer(serializers.Serializer):
    username_field = "email"

    def __init__(self, *args, **kwargs):
        super(MyTokenObtainSerializer, self).__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField()
        self.fields['password'] = PasswordField()

    def validate(self, attrs):
        # self.user = authenticate(**{
        #     self.username_field: attrs[self.username_field],
        #     'password': attrs['password'],
        # })
        print(attrs)
        self.user = CustomUser.objects.filter(email=attrs[self.username_field]).first(
        ) or CustomUser.objects.filter(username=attrs[self.username_field]).first()
        print(self.user)

        if not self.user:
            raise ValidationError('The user is not valid.')

        if self.user:
            print("password here")
            print(self.user.password)
            if not self.user.check_password(attrs['password']):
                raise ValidationError('Incorrect credentials.')

        # Prior to Django 1.10, inactive users could be authenticated with the
        # default `ModelBackend`.  As of Django 1.10, the `ModelBackend`
        # prevents inactive users from authenticating.  App designers can still
        # allow inactive users to authenticate by opting for the new
        # `AllowAllUsersModelBackend`.  However, we explicitly prevent inactive
        # users from authenticating to enforce a reasonable policy and provide
        # sensible backwards compatibility with older Django versions.
        if self.user is None or not self.user.is_active:
            raise ValidationError(
                'No active account found with the given credentials')

        return {}

    @classmethod
    def get_token(cls, user):
        raise NotImplemented(
            'Must implement `get_token` method for `MyTokenObtainSerializer` subclasses')


class MyTokenObtainPairSerializer(MyTokenObtainSerializer):
    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        data = super(MyTokenObtainPairSerializer, self).validate(attrs)

        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        print("here")
        print(data)

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        return data


class AdmBrokerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brokers
        fields = "__all__"


class UserSerializer(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = "__all__"
        extra_kwargs = {'password': {'write_only': True, 'required': True}}


class CreatorSerializer(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "username", "name", "email","is_superuser","isInvestor"]


class StrategySerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source='creator.username')
    subs = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()
    broker = serializers.SerializerMethodField()

    class Meta:
        model = Strategy
        fields = '__all__'

    def get_subs(self, instance):
        return Subscription.objects.filter(strategy=instance).count()

    def get_creator(self, instance):
        return CreatorSerializer(instance.creator).data

    def get_broker(self, instance):
        return AdmBrokerSerializer(instance.broker).data


class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = '__all__'


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = "__all__"


class ResultWithoutMonthsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ["strategy",
                  "timestamp",
                  "annual_return_percentage",
                  "max_drawdown_percentage",
                  "total_trades",
                  "win_percentage",
                  "profit_factor",
                  "winning_months",
                  "monthly_pl",
                  "todays_pl",
                  "date"]


class VerboseStrategySerializer(StrategySerializer):
    trades = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()

    def get_trades(self, instance):
        limit = 10
        trades = Trade.objects.filter(strategy=instance)
        if len(trades) > limit:
            trades = trades[:10]
        return TradeSerializer(trades, many=True).data

    def get_result(self, instance):
        result = Result.objects.filter(strategy=instance).order_by("-date")
        if len(result) == 0:
            return {
                "strategy": instance.id,
                "timestamp": "2024-09-04T16:59:17.000Z",
                "annual_return_percentage": 0.00,
                "max_drawdown_percentage": 0.00,
                "total_trades": 0,
                "win_percentage": 0.00,
                "profit_factor": 0.00,
                "winning_months": 0,
                "monthly_pl": {},
                "todays_pl": 0.00,
                "date": "2024-09-04"
            }
        else:
            return ResultSerializer(result[0]).data


class SubscriptionSerializer(serializers.ModelSerializer):
    strategy = serializers.SerializerMethodField()
    subscriber = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = '__all__'

    def get_strategy(self, instance):
        return StrategySerializer(instance.strategy).data

    def get_subscriber(self, instance):
        return CreatorSerializer(instance.subscriber).data
    
    def get_result(self, instance):
        result = Result.objects.filter(strategy=instance.strategy).order_by("-date")
        if len(result) == 0:
            return {
                "strategy": instance.id,
                "timestamp": "2024-09-04T16:59:17.000Z",
                "annual_return_percentage": 0.00,
                "max_drawdown_percentage": 0.00,
                "total_trades": 0,
                "win_percentage": 0.00,
                "profit_factor": 0.00,
                "winning_months": 0,
                "monthly_pl": {},
                "todays_pl": 0.00,
                "date": "2024-09-04"
            }
        else:
            return ResultWithoutMonthsSerializer(result[0]).data


class WatchListSerializer(serializers.ModelSerializer):
    strategy = serializers.SerializerMethodField()
    subscriber = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = '__all__'

    def get_strategy(self, instance):
        return StrategySerializer(instance.strategy).data

    def get_subscriber(self, instance):
        return CreatorSerializer(instance.subscriber).data
    
    def get_result(self, instance):
        result = Result.objects.filter(strategy=instance.strategy).order_by("-date")
        if len(result) == 0:
            return {
                "strategy": instance.id,
                "timestamp": "2024-09-04T16:59:17.000Z",
                "annual_return_percentage": 0.00,
                "max_drawdown_percentage": 0.00,
                "total_trades": 0,
                "win_percentage": 0.00,
                "profit_factor": 0.00,
                "winning_months": 0,
                "monthly_pl": {},
                "todays_pl": 0.00,
                "date": "2024-09-04"
            }
        else:
            return ResultWithoutMonthsSerializer(result[0]).data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords do not match.")
        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'


class DocumentSerialzier(serializers.ModelSerializer):
    class Meta:
        model = UserDocuments
        fields = '__all__'


class AdmUserSerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    subscriptions = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = "__all__"
        extra_kwargs = {'password': {'write_only': True, 'required': True}}

    def get_documents(self, instance):
        docs = UserDocuments.objects.filter(user=instance).first()
        if docs:
            return DocumentSerialzier(docs).data
        else:
            return None

    def get_profile(self, instance):
        profile = Profile.objects.filter(user=instance).first()
        if profile:
            return ProfileSerializer(profile).data
        else:
            return None

    def get_subscriptions(self, instance):
        subs = Subscription.objects.filter(subscriber=instance)
        return SubscriptionSerializer(subs, many=True).data
    
class MessageUserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ["id", "username", "name", "email","is_superuser","isInvestor","profile"]

    def get_profile(self, instance):
        profile = Profile.objects.filter(user=instance).first()
        if profile:
            return ProfileSerializer(profile).data
        else:
            return None

class MessageSerializer(serializers.ModelSerializer):
    sender = MessageUserSerializer( read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'message', 'date_sent']

class TicketSerializer(serializers.ModelSerializer):
    user = CreatorSerializer( read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = ['id', 'user', 'subject', 'description', 'date_created', 'isClosed', 'messages']

class CreateTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['subject', 'description']