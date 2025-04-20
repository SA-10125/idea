from django.contrib import admin

# Register your models here.
from .models import GeneralData,UsersID,Team,Individual_LinktoTeam,Individual_CommentonTeam,Individual_Bid,Individual_Ask,Individual_OrderBook,Individual_OrderTransaction,Individual_CompletedAsks,Individual_CompletedBids,Individual_CompletedTransaction,completed_investments

admin.site.register(GeneralData)
admin.site.register(UsersID)
admin.site.register(Team)
admin.site.register(Individual_LinktoTeam)
admin.site.register(Individual_CommentonTeam)
admin.site.register(Individual_Bid)
admin.site.register(Individual_Ask)
admin.site.register(Individual_OrderBook)
admin.site.register(Individual_OrderTransaction)
admin.site.register(Individual_CompletedAsks)
admin.site.register(Individual_CompletedBids)
admin.site.register(Individual_CompletedTransaction)
admin.site.register(completed_investments)

#I come into the website, I see the total's trends and news, and the top performing teams, there is a login button, if logged in, let it be a profile button.
#in the side panel, is a list of all the teams based on performance and/or volume. all clickable.
#click on it, go into its page. 
#see buy button, ask button.