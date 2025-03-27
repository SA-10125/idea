from django.contrib import admin

# Register your models here.
from .models import GeneralData,ID,Team,LinktoTeam,CommentonTeam,Bid,Ask,OrderBook

admin.site.register(GeneralData)
admin.site.register(ID)
admin.site.register(Team)
admin.site.register(LinktoTeam)
admin.site.register(CommentonTeam)
admin.site.register(Bid)
admin.site.register(Ask)
admin.site.register(OrderBook)
