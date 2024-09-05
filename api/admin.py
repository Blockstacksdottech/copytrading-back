from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Profile)
admin.site.register(Strategy)
admin.site.register(Subscription)
admin.site.register(Trade)
admin.site.register(Result)