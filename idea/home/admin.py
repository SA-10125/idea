from django.contrib import admin

# Register your models here.
from .models import GeneralData,ID,Team,LinktoTeam,CommentonTeam,Bid,Ask,OrderBook,OrderTransaction,CompletedAsks,CompletedBids,CompletedTransaction

admin.site.register(GeneralData)
admin.site.register(ID)
admin.site.register(Team)
admin.site.register(LinktoTeam)
admin.site.register(CommentonTeam)
admin.site.register(Bid)
admin.site.register(Ask)
admin.site.register(OrderBook)
admin.site.register(OrderTransaction)
admin.site.register(CompletedAsks)
admin.site.register(CompletedBids)
admin.site.register(CompletedTransaction)

#I come into the website, I see the total's trends and news, and the top performing teams, there is a login button, if logged in, let it be a profile button.
#in the side panel, is a list of all the teams based on performance and/or volume. all clickable.
#click on it, go into its page. 
#see buy button, ask button.