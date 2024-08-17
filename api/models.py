from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class CustomUser(AbstractUser):
    username = models.CharField(max_length=255, default="", unique=True)
    name = models.CharField(max_length=255, default="")
    isInvestor = models.BooleanField(default=False)

    def __str__(self):
        return self.username
    
class Profile(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    government_id_type = models.CharField(max_length=100)
    government_id_number = models.CharField(max_length=50)
    tin = models.CharField(max_length=50)
    
    def __str__(self):
        return self.full_name
    
class Strategy(models.Model):
    
    
    name = models.CharField(max_length=255)
    tradeType = models.CharField(max_length=10)
    accountSize = models.CharField(max_length=20)
    broker = models.CharField(max_length=50)
    controlModel = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    briefDescription = models.CharField(max_length=20)
    detailedDescription = models.TextField()
    maxSubscribers = models.IntegerField(null=True, blank=True)
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="created_strategies")
    enabled = models.BooleanField(default=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Subscription(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    subscriber = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_subscribed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subscriber.username} subscribed to {self.strategy.name}"
