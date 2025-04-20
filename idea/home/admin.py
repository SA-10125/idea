from django.contrib import admin

# Register your models here.
from .models import GeneralData,UsersID,Team,Induvidual_LinktoTeam,Induvidual_CommentonTeam,Induvidual_Bid,Induvidual_Ask,Induvidual_OrderBook,Induvidual_OrderTransaction,Induvidual_CompletedAsks,Induvidual_CompletedBids,Induvidual_CompletedTransaction

admin.site.register(GeneralData)
admin.site.register(UsersID)
admin.site.register(Team)
admin.site.register(Induvidual_LinktoTeam)
admin.site.register(Induvidual_CommentonTeam)
admin.site.register(Induvidual_Bid)
admin.site.register(Induvidual_Ask)
admin.site.register(Induvidual_OrderBook)
admin.site.register(Induvidual_OrderTransaction)
admin.site.register(Induvidual_CompletedAsks)
admin.site.register(Induvidual_CompletedBids)
admin.site.register(Induvidual_CompletedTransaction)

#I come into the website, I see the total's trends and news, and the top performing teams, there is a login button, if logged in, let it be a profile button.
#in the side panel, is a list of all the teams based on performance and/or volume. all clickable.
#click on it, go into its page. 
#see buy button, ask button.