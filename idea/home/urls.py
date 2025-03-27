from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('',views.homepage,name='home'),
    path('view/<str:pk>/',views.seeteam,name='seeteam'),
    path('login',views.login_page,name='login'),
    path('logout',views.logout_page,name='logout'),
]


#ok so lets have users, 
#then teams, each team can have up to 4 users, a user can only be part of 1 team at once
#then each team has initial_no_of_shares shares at initial_value each.

#have a main invest page where you can see the graphs and market values of all companies at a glance.
#could also have a game index showing the avg movement of all stocks in the market. (ex if 70% stocks are rising, index is upward.)

#stock page of any given team (public view):
    #a graph and a time range (1 day to idk) (can choose how much the range of the graph is.) (x axis is time, y axis is market value)
    #market price of 1 share of that company (and rise/drop (green/red)) (same rise/drop in %) (these rise and drops could be based on the latest trade to the second latest trade. Or this could be latest trade:trade 30 min ago, further, there could be another for latest trade to when the event started. )
    #(can also show activity stats, aka number of shares traded per hour or per minute in that team. (hence, low volume and rising price could be risky and high volume with rising price could be good. (idk how, dont ask me.)))
    #Stock details:
        #current price
        #price 30m ago
        #market volume (aka activity stats)
        #market volume 30m ago (shows trend of how interest of ppl changing)
        #info:
            #next earnings-report/change/something that will make the market react. (consider our market here is students and hence maybe they release a political take or smthn.)
            #news highlights (ex: Apple’s stock has declined over 10% in 2025, contributing to the poor performance of the Magnificent Seven group. or Tesla Is Headed to Saudi Arabia, Years After Infamous Tweet )
        
    #Have an option to see the timeline of news dropping or earnings changing of the stocks side by side with the market price (both over time). That way we can see what events caused what kind of change.
    #(theres also those wierd graphs with red lines instead of one continous line and all idk what that is.)
    #can also show number of employees or smthn to show the kind of stakes they have if they dump many stocks etc.
    #can also have a comments section
    #can also have predictors/analysis
    
    #view ordering book (real time, to be updated after each trade):
             #Example Order Book for "Team Alpha"
                # Bid Price (Buyers) | Quantity  ||  Ask Price (Sellers) | Quantity
                #   $95	                10                     $100	          5
                #   $90	                20	                   $105	          15
                #   $85	                30	                   $110	          10
        #show lowest ask price = current market price

    #now to buy shares from this team's stock:
        #pick a price from the asks table (and place a market order at that price)
        #To buy immediatly, accept the lowest Ask Price in the order book (and no of shares somehow) (aka market order button)
        #Or Limit Buy Order at a lower price option: enter the price that you will buy at and number of shares and click order, when there is an ask price equal to that (or lower), it will buy until the number of shares you wanted at that price is bought.
    
    #to sell:
        #pick a price from the bids table (and sell at that price)
        #To sell immediatly, accept the highest Bid Price in the order book (and no of shares) (aka market order button)
        #Or Limit Sell Order at a higher price option: enter the price that you will sell at and number of shares and click sell, when there is a bid price equal to that (or higher), it will sell until the number of shares is sold.


#have users get alerted when price increases/decreases beyond the alert prices they kept. (gmail)

#im thinking like a signup page with a team name and team members and their details.
#alternatively, we could have each member sign up as a user, then make teams with them, maybe even by sending out requests or smthn, but user can join team only once during event. 
# 

#  Price increases when buy orders consume all available shares at a given price level, forcing new trades at higher prices.
#  Price decreases when sell orders consume all bids at a given price level, forcing new trades at lower prices.
#  Price remains stable if buyers and sellers continue trading at the same price level.
#   If teams buy aggressively, stock prices rise because they clear out the cheap shares.
#   If teams sell aggressively, stock prices drop because they clear out high bids.
#   If a stock has low trading volume, a small trade can cause big price changes.
#   If a stock has high trading volume, it’s more stable because there are many buyers and sellers at different levels.

#Cancellation:
#If a bid/ask is still in the order book and has not yet been matched, the user can cancel it.
#If a bid/ask has been partially matched, only the remaining unmatched portion can be canceled.
#If a bid/ask is fully matched, it cannot be canceled.



#say 40 teams
# all have initial value
# each team can have buy, sell shares of other teams. (funcs)
# buying increases value, selling decreases it.
#Platform must have live updates of all the teams valuations.

#There must also be a system where startups are listed, ppl can trade using virtual money.
#(value will go up by a certain amount.)
# (discord is an option)


#brainstorming:
#If many participants buy Startup A’s stock, its price rises (e.g., ₹100 → ₹120).
# If many sell, its price drops (e.g., ₹100 → ₹80).

# 2️⃣ Event-Based Price Changes (Bonus Rule)
# If a startup wins a pitch competition, its stock gains +10% value.
# If a startup fails to deliver a project, its stock loses -15% value.
# This simulates real-world events impacting stocks.


#see a stock page:
    #current stock price
    # price chart
    # buy and sell options
    # order book (highest bids first, lowest asks after)
#buy: 
    # buy immideatly at best price (market order)
    # limit order, buy only if price is X or lower.
    # quantity
#now you own the shares