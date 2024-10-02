from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

# Create your models here.


class CustomUser(AbstractUser):
    username = models.CharField(max_length=255, default="", unique=True)
    name = models.CharField(max_length=255, default="")
    isInvestor = models.BooleanField(default=False)
    isVerified = models.BooleanField(default=False)
    reason = models.TextField(default="",blank=True)

    def __str__(self):
        return self.username

class RecoveryRequest(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    recovery_id = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RecoveryRequest for {self.user.username}"
    
    
class Profile(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100,blank=True)
    mobile = models.CharField(max_length=15,blank=True)
    address = models.CharField(max_length=255,blank=True)
    city = models.CharField(max_length=100,blank=True)
    state = models.CharField(max_length=100,blank=True)
    country = models.CharField(max_length=100,blank=True)
    postal_code = models.CharField(max_length=20,blank=True)
    government_id_type = models.CharField(max_length=100,blank=True)
    government_id_number = models.CharField(max_length=50,blank=True)
    tin = models.CharField(max_length=50,blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', null=True, blank=True)
    
    def __str__(self):
        return self.full_name

class UserDocuments(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    front = models.ImageField(
        upload_to='documents/', null=True, blank=True)
    back = models.ImageField(
        upload_to='documents/', null=True, blank=True)
    tin = models.ImageField(
        upload_to='documents/', null=True, blank=True)

    def __str__(self):
        return self.user.username
    
class Brokers(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    image = models.ImageField(
        upload_to='brokers/')
    
    def __str__(self):
        return self.name
    
class Strategy(models.Model):
    name = models.CharField(max_length=255)
    broker = models.ForeignKey(Brokers,on_delete=models.CASCADE)
    tradeType = models.CharField(max_length=10)
    accountSize = models.CharField(max_length=20)
    #broker = models.CharField(max_length=50)
    controlModel = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    briefDescription = models.CharField(max_length=20)
    detailedDescription = models.TextField()
    maxSubscribers = models.IntegerField(null=True, blank=True)
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="created_strategies")
    sheetUrl = models.URLField(default="")
    enabled = models.BooleanField(default=True)
    date = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name

class SubscriptionRequest(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    subscriber = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    approved = models.BooleanField(default=False)
    date_requested = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subscriber.username} requested to subscribe to {self.strategy.name}"

class Subscription(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    subscriber = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_subscribed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subscriber.username} subscribed to {self.strategy.name}"
    
class WatchList(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    subscriber = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_subscribed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subscriber.username} subscribed to {self.strategy.name}"



class Trade(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    open_time_et = models.DateTimeField()
    side = models.CharField(max_length=10)
    qty_open = models.IntegerField()
    symbol = models.CharField(max_length=20)
    descrip = models.CharField(max_length=255)
    avg_price_open = models.DecimalField(max_digits=15, decimal_places=4)
    qty_closed = models.IntegerField()
    closed_time_et = models.DateTimeField()
    avg_price_closed = models.DecimalField(max_digits=15, decimal_places=4)
    dd_as_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    dd_dollars = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    dd_time_et = models.DateTimeField(null=True, blank=True)
    dd_quant = models.IntegerField(null=True, blank=True)
    dd_worst_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    trade_pl = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"Trade {self.symbol} on {self.closed_time_et}"


class Result(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    annual_return_percentage = models.DecimalField(max_digits=10, decimal_places=2)
    win_trades = models.IntegerField(default=0)
    max_drawdown_percentage = models.DecimalField(max_digits=10, decimal_places=2)
    total_trades = models.IntegerField()
    win_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    profit_factor = models.DecimalField(max_digits=10, decimal_places=2)
    winning_months = models.IntegerField()
    monthly_pl = models.JSONField()  # Store monthly P/L as a JSON object
    todays_pl = models.DecimalField(default=0,max_digits=10, decimal_places=2)
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # New field for Sharpe Ratio
    sortino_ratio = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # New field for Sortino Ratio
    date = models.DateField()

    def __str__(self):
        return f"Result on {self.timestamp}"
    

class Ticket(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    isClosed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.subject} - {self.user.username}"

class Message(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField()
    date_sent = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message by {self.sender.username} on {self.date_sent}"