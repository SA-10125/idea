from django.db import models as m
from django.db.models import Q,UniqueConstraint  #this is for a conditional unique constraint on closed_with field
from django.contrib.auth.models import User
from django.db.models.signals import post_save,pre_delete
from django.dispatch import receiver 
from csv import writer #for the data.csv file.
import random

#I have used the term Vibe-coding in past comments, I did not know the meaning at the time and thought it meant coding for da vibes without worrying about efficiency and stuff. Just getting it to work.

#This is just coded for da vibes, not to be used in prod.

#TODO: When a company valuation changes, everyone with their stocks should have net worth change? (OR Calculate net worths when needed using current valuations of companies?)

class GeneralData(m.Model): #a model for general data
    peak=m.BigIntegerField(default=0)
    totalmarketvalue=m.BigIntegerField(default=0) #shows overall market value, #TODO: somehow use to analyze trends over time.


class UsersID(m.Model): #a model for unique IDs (btw, User.id is a django given unique ID)
    user=m.OneToOneField(User,on_delete=m.CASCADE,related_name='UserforID') #since onetoonefield, a user may only have one ID.
    IDNum=m.CharField(max_length=500000,blank=False,null=False,unique=True)
    Money=m.DecimalField(max_digits=20, decimal_places=2, default=0) #cash in hand for investing. (liquid)

    class Meta:
        unique_together=[['user','IDNum'],['IDNum']] #no repetetion of IDs allowed. 

    def __str__(self):
        return f"{self.user.username}-{self.IDNum}"

@receiver(post_save,sender=User)
def makeID(sender, instance, created, **kwargs):
    if created:
        #yes i know this is inneficient, just roll with it for now.
        while True:
            newID=str(random.randint(10000000,99999999))
            if not UsersID.objects.filter(IDNum=newID).exists():
                break

        UsersID.objects.create(user=instance,IDNum=newID)

def find_net_worth(user_id):
    #This is currently working on a system where a users net worth is defined by his teams value and his personal investments.
    #TODO: But does the user own a portion of the teams valuation or do the shareholders own that amount of the teams valuation? discuss with E-club
    
    net=user_id.Money
    teams_part_of=Induvidual_LinktoTeam.objects.filter(user_id=user_id)
    for team in teams_part_of:
        #TODO: go through this again with E-club and decide which parts to keep/remove
        if team.is_user_in_team: #user in team owns a portion of the teams valuation.
            #net+= total_market_value_of_team/number_of_people_in_team (usually 4)
            net+=(team.team_linked.Money+(0.34*team.team_linked.Induvidual_Unit_Share_Price)+(0.66*(team.team_linked.Team_valuation/team.team_linked.Teams_Number_of_shares_in_market)))/team.objects.filter(is_user_in_team=True,team_linked=team.team_linked).count()
        else:
            #net+= induvidual_assets
            net+=(team.stocks*team.team_linked.Induvidual_Unit_Share_Price)

#I am building a model that has two completely seperate sections. One for induvidual investors, and one for the teams to invest in each other. 
#Each section/market has its own 1000 shares with its own seperate unit_share_prices.
#The total valuation of a company is taken as a weighted avg of both the markets. 
#valuation = 0.34 * (Induvidual_unit_share_price * 1000) + 0.66 * (teams_unit_share_price_price * 1000)
#This creates a simpler system to make for me, and a simpler gamified system for the users, easy to grasp and play.
#In the end, the teams with highest valuation get prizes, so do the induviduals with the highest net worth.


class Team(m.Model): #a team is a company
    Name=m.CharField(max_length=50,null=False,unique=True)
    Base_Valuation=m.DecimalField(max_digits=200, decimal_places=2) #as provided by judges.

    #An induvidual does not have as much money as a company.
    #Hence, a Induvidual_unit_share_price is small and a Team_unit_share_price is higher.
    #This feels intuitive and also makes it easier for the user to mentally manage both markets as he/she can know which market he is seeing just based on the price.

    #There are two ways to achieve this. 
    # 1)    We could have different Base valuations for each such as 100000$ for Team_base_valuation and 1000$ for induviduals_base_valuation.
    #       Then split each up into 1000 shares. but this is unrealistic, wierd and incosnistent. 
    #       It could be confusing for a user to see two base valuations for the same company. 
    #       Further, total_valuation = Treasury+(0.34*induvidual_valuation)+(0.66*team_valuation)
    #       where induvidual_valuation=(induvidual_number_of_shares*induvidual_unit_share_price)*100 which is just wierd.
    
    # 2)    We keep one common base valuation, say 100000$. 
    #       Then we split up into 1000 shares for teams aspect, and 10000 shares for induviduals aspect.
    #       Hence, consistent, clear, intuitive and total_valuation = Treasury+(0.34*induvidual_valuation)+(0.66*team_valuation)
    #       individual valuation = induvidual_number_of_shares*induvidual_unit_share_price which is intuitive and makes sense.
    #Hence we are following the second model.

    Induvidual_Number_of_shares_in_market=m.BigIntegerField(default=10000) #this is number of total shares
    #we dont really care about how many shares are still owned by the company.
    Induvidual_Unit_Share_Price=m.DecimalField(max_digits=100, decimal_places=2) 

    #induvidual aspect:
    #   initially, all 10000 shares are with the company. The users have to buy it from the company at base_valuation/10000. Amount from that goes into the treasury.
    #   if there are any shares still left with the company, it doesnt matter for valuation calculations as we are doing unit_share_price*10000 anyways.
    #   we achieve this by having the company place 10000 bids at base_valuation/10000 at first.
    #same thing for teams aspect where the money from selling the shares go into company trasury.

    Teams_Number_of_shares_in_market=m.BigIntegerField(default=1000) #this is total number of shares
    Teams_number_of_shares_with_company=m.BigIntegerField(default=1000) #this is number of unsold shares. (still with company)
    Teams_current_valuation=m.DecimalField(max_digits=100, decimal_places=2) #unit share price is valuation/number of shares in market

    News_and_updates=m.TextField(max_length=100000,blank=True,null=True) #not creating a table for now, manage with protocols and norms for now while dealing with this data.

    Money=m.DecimalField(max_digits=100, decimal_places=2, default=0) #Treasury in hand for investing. (liquid)

    #total valuation = Money (aka treasury)+(0.34*induvidual_valuation)+(0.66*team_valuation)
    #induvidual_valuation = induvidual_number_of_shares*induvidual_unit_share_price
    #initially team_valuation is given by judges. 
    #Later, team_valuation is calculated using:
    #   New_valuation_of_invested_company= Base_valuation_of_invested_company((1+Number_of_Companies_investing(.3))+(1+Number_of_Shares_bought(.002)))

    #so at first, the base_valuation = Money (aka treasury.) (fully liquid.)
    #Then the company starts buying other company's shares. (some liquid, some non liquid) (from the company itself or from other teams)
    #   they can then sell these shares at a profit and increase their treasury and hence their valuation. or sell at loss and decrease. (sell to other teams)
    #The treasury can also decrease when they lose money according to the dice roll and hence, the valuation decreases.
    #The valuation can also increase based on the formula as more teams invest in them and buy more of their shares.

    #at first, the company sells the induvidual_valuations and hence gets that money directly into treasury increasing valuation.
    #after that, the induvidual valuation is based purely on the unit_share_price as in the real world.

    def __str__(self): #TODO: make this more readable in future.
        return f"{self.Name}-{self.Money+(0.34*self.Induvidual_Unit_Share_Price)+(0.66*(self.Team_valuation/self.Teams_Number_of_shares_in_market))}-{self.Team_valuation/self.Teams_Number_of_shares_in_market}-{self.Induvidual_Unit_Share_Price}-{self.Money}"


#Following are the induvidual specific:

@receiver(post_save,sender=Team)
def make_initial_induvidual_asks_by_team(sender, instance, created, **kwargs):
    if created: #this is run when the team is first created. It places asks at askrpice=base_valuation/number_of_shares.
                #the ask is then placed into the orderbook by the addask function.
                #the ask matching is handled by the check_orders function wich makes a new ask with howmanyever shares are left and then stores the completed ask in the completed asks
        initial_unit_share_price=(instance.Base_Valuation/instance.Induvidual_Number_of_shares_in_market)
        price_to_place_ask_at=instance.Induvidual_Unit_Share_Price
        Induvidual_Ask.objects.create(asking_team=instance,team_to_ask_on=instance,askprice=price_to_place_ask_at,noaskedshares=instance.Induvidual_Number_of_shares_in_market)

class Induvidual_LinktoTeam(m.Model): #A user links to any team via this. Team the user is part of, and teams the user has stocks in or has any data with.
    curuser=m.ForeignKey(User,on_delete=m.CASCADE,null=False)
    curuser_ID=m.ForeignKey(UsersID,on_delete=m.CASCADE,null=False) #when automating creation of this, must fill this.
    team_linked=m.ForeignKey(Team,on_delete=m.CASCADE,null=False) 
    is_user_in_team=m.BooleanField(default=False,null=False)
    alert_prices=m.CharField(max_length=100000,blank=True,null=True) #set alert prices following a norm. #consider using json fields
    stocks=m.BigIntegerField(default=0) #number of shares user has in the company currently

    class Meta:
        unique_together=[['curuser_ID','team_linked']] #each user can only be linked to the team once.

    def __str__(self):
        return f"{self.curuser.username}-{self.team_linked.Name}-{'In team' if self.is_user_in_team else 'Not in team'}"
    

class Induvidual_CommentonTeam(m.Model): #a model for users to comment on any team.
    commentinguser=m.ForeignKey(User,on_delete=m.CASCADE,null=False) #one to one field means user can comment only once.
    userid=m.ForeignKey(UsersID,on_delete=m.CASCADE,null=False)
    commentedteam=m.ForeignKey(Team,on_delete=m.CASCADE,null=False)
    comment=m.TextField(max_length=1000,blank=False)
    whencommented=m.DateTimeField(auto_now_add=True)
    last_interacted_with=m.DateTimeField(auto_now=True)

    class Meta:
        unique_together=[['userid','commentedteam','comment']] #cant spam same comment in same team.

    def __str__(self):
        return f"{self.commentinguser.username}-{self.commentedteam.Name}-{self.comment}"

class Induvidual_Bid(m.Model):
    bidder=m.ForeignKey(User,on_delete=m.CASCADE,null=False)
    bidder_ID=m.ForeignKey(UsersID,on_delete=m.CASCADE,null=False)
    team_to_bid_on=m.ForeignKey(Team,on_delete=m.CASCADE,null=False) #redundant for safety
    bidprice=m.DecimalField(max_digits=20, decimal_places=2,null=False)
    nobidshares=m.BigIntegerField(null=False)
    bidwhen=m.DateTimeField(auto_now_add=True)
    last_interacted_with=m.DateTimeField(auto_now=True)
    closed_with=m.CharField(max_length=500000,blank=True,null=True)

    class Meta: #In some dbs like postgres, if 2 closed_with are null, it considers them not unique so will throw error if we keep 
                #closed_with=m.CharField(max_length=500,blank=True,null=True,unique=True)
                #i.e bids that are not closed yet would cause error.
                #To avoid this, we put the unique=True constraint only if its not null.
        constraints = [ #CHECK THIS ONCE, GPT MADE IT
            UniqueConstraint(fields=["closed_with"], condition=Q(closed_with__isnull=False), name="unique_closed_with_when_not_null_bid")
        ]

    def __str__(self):
        return f"{self.bidder.username}-{self.team_to_bid_on.Name}-{self.nobidshares} shares at {self.bidprice} each"

class Induvidual_Ask(m.Model): 
    asker=m.ForeignKey(User,on_delete=m.CASCADE,null=True,blank=True) #putting null=True since we can also have an asking team without an asking person as initially.
    asker_ID=m.ForeignKey(UsersID,on_delete=m.CASCADE,null=True,blank=True)

    asking_team=m.ForeignKey(Team,on_delete=m.CASCADE,null=True,blank=True,related_name="asks_by_team") #initially, all shares are owned by the company, hence it needs to place many bids.

    team_to_ask_on=m.ForeignKey(Team,on_delete=m.CASCADE,null=False,related_name="asks_on_team") #redundant for safety
    askprice=m.DecimalField(max_digits=20, decimal_places=2,null=False)
    noaskedshares=m.BigIntegerField(null=False)
    askedwhen=m.DateTimeField(auto_now_add=True)
    last_interacted_with=m.DateTimeField(auto_now=True)
    closed_with=m.CharField(max_length=500000,blank=True,null=True)

    class Meta: #In some dbs like postgres, if 2 closed_with are null, it considers them not unique so will throw error if we keep 
                #closed_with=m.CharField(max_length=500,blank=True,null=True,unique=True)
                #i.e bids that are not closed yet would cause error.
                #To avoid this, we put the unique=True constraint only if its not null.
        constraints = [ #CHECK THIS ONCE, GPT MADE IT
            UniqueConstraint(fields=["closed_with"], condition=Q(closed_with__isnull=False), name="unique_closed_with_when_not_null_ask")
        ]

    def __str__(self):
        return f"{self.asker.username if self.asker is not None else self.asking_team}-{self.team_to_ask_on.Name}-{self.noaskedshares} shares at {self.askprice} each"

#Consider this: (consider it for completed_asks also)
# from django.core.exceptions import ValidationError

# def clean(self):
#     if self.asker and self.asking_team:
#         raise ValidationError("Cannot set both 'asker' and 'asking_team'. Choose one.")
#     if not self.asker and not self.asking_team:
#         raise ValidationError("Either 'asker' or 'asking_team' must be set.")
#And don't forget to call .full_clean() before saving in custom logic (if needed), or rely on Django admin/forms to enforce it.

@receiver(post_save,sender=Induvidual_Bid)
def addbid(sender, instance, created, **kwargs): #adding ask to order book of the team the moment it is saved. 
    #(BIDS CANNOT BE EDITED AS IT WILL BE RE ADDED TO THE ORDER BOOK WITHOUT ANY CHANGE. INSTEAD BIDS MUST BE DELETED AND NEW ASK MADE.)
    if created:
        mylink=Induvidual_LinktoTeam.objects.filter(team_linked=instance.team_to_bid_on,curuser=instance.bidder)
        if mylink.exists(): 
            mylink=mylink[0]
        else: #creating a link if the link doesnt exist
            mylink=Induvidual_LinktoTeam.objects.create(team_linked=instance.team_to_bid_on,curuser=instance.bidder,curuser_ID=instance.bidder_ID)
        
        if mylink.curuser_ID.Money>=(instance.nobidshares*instance.bidprice): #making sure the user has the money to place a bid
                orderbook,created= Induvidual_OrderBook.objects.get_or_create(team=instance.team_to_bid_on)
                orderbook.bids.add(instance)
                Induvidual_OrderTransaction.objects.create(order_book=Induvidual_OrderBook.objects.get(team=instance.team_to_bid_on),bid=instance,executed_price=instance.bidprice)

@receiver(post_save,sender=Induvidual_Ask) #to place an ask, you must already have shares in the company and hence already have a teamlink
def addask(sender, instance,created, **kwargs): #adding ask to order book of the team the moment it is saved. 
    #(ASKS CANNOT BE EDITED AS IT WILL BE RE ADDED TO THE ORDER BOOK WITHOUT ANY CHANGE. INSTEAD ASK MUST BE DELETED AND NEW ASK MADE.)
    if created:
        if instance.asker is not None: #This is for induviduals placing the ask.
            mylink=Induvidual_LinktoTeam.objects.filter(team_linked=instance.team_to_ask_on,curuser=instance.asker)
            if mylink.exists() and mylink[0].stocks>=instance.noaskedshares: #making sure the user has the stocks to place an ask
                orderbook,created=Induvidual_OrderBook.objects.get_or_create(team=instance.team_to_ask_on)
                orderbook.asks.add(instance)
                Induvidual_OrderTransaction.objects.create(order_book=Induvidual_OrderBook.objects.get(team=instance.team_to_ask_on),ask=instance,executed_price=instance.askprice)
        else: #If a team places the ask as in the initial condition, there is no link. The ask just gets added to the orderbook and ordertransaction.
            orderbook,created=Induvidual_OrderBook.objects.get_or_create(team=instance.team_to_ask_on)
            orderbook.asks.add(instance)
            Induvidual_OrderTransaction.objects.create(order_book=Induvidual_OrderBook.objects.get(team=instance.team_to_ask_on),ask=instance,executed_price=instance.askprice)
            #TODO: make this more efficient by removing the unnessecary get of order book while creating order transaction. as we already have orderbook.

class Induvidual_OrderBook(m.Model): #maybe this method of doing it is making the db a little too complicated. But using this for now.
    team=m.ForeignKey(Team,on_delete=m.DO_NOTHING,null=False)
    bids=m.ManyToManyField(Induvidual_Bid)
    asks=m.ManyToManyField(Induvidual_Ask)
    placedwhen=m.DateTimeField(auto_now_add=True)
    last_interacted_with=m.DateTimeField(auto_now=True)
    other_deets=m.TextField(max_length=10000000,blank=True,null=True) #consider JSONField

    def __str__(self):
        return f"{self.team.Name}'s current OrderBook"
    
    #consider adding unique together bids asks and team so that the same bid isnt spammed many times?

#This is a through model for Induvidual_order_book.
class Induvidual_OrderTransaction(m.Model):
    order_book = m.ForeignKey(Induvidual_OrderBook, on_delete=m.CASCADE)
    bid = m.ForeignKey(Induvidual_Bid, on_delete=m.CASCADE,blank=True,null=True)
    ask = m.ForeignKey(Induvidual_Ask, on_delete=m.CASCADE,blank=True,null=True)
    executed_price = m.DecimalField(max_digits=20, decimal_places=2)
    executed_at = m.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.bid:
            return f"bid at {self.executed_price}"
        else:
            return f"ask at {self.executed_price}"
    

class Induvidual_CompletedBids(m.Model):
    bidder=m.ForeignKey(User,on_delete=m.CASCADE,null=False)
    bidder_ID=m.ForeignKey(UsersID,on_delete=m.CASCADE,null=False)
    team_to_bid_on=m.ForeignKey(Team,on_delete=m.CASCADE,null=False) #redundant for safety
    bidprice=m.DecimalField(max_digits=20, decimal_places=2,null=False)
    nobidshares=m.BigIntegerField(null=False)
    bidwhen=m.DateTimeField()
    last_interacted_with=m.DateTimeField()
    closed_with=m.CharField(max_length=500000,blank=True,null=True,unique=True)

    def __str__(self):
        return f"{self.bidder.username}-{self.team_to_bid_on.Name}-{self.nobidshares} shares at {self.bidprice} each"

class Induvidual_CompletedAsks(m.Model): 
    asker=m.ForeignKey(User,on_delete=m.CASCADE,null=True,blank=True)
    asker_ID=m.ForeignKey(UsersID,on_delete=m.CASCADE,null=True,blank=True)

    asking_team=m.ForeignKey(Team,on_delete=m.CASCADE,null=True,blank=True,related_name="completed_asks_by_team") #initially, all shares are owned by the company, hence it needs to place many bids.

    team_to_ask_on=m.ForeignKey(Team,on_delete=m.CASCADE,null=False,related_name="completed_asks_on_team") #redundant for safety
    askprice=m.DecimalField(max_digits=20, decimal_places=2,null=False)
    noaskedshares=m.BigIntegerField(null=False)
    askedwhen=m.DateTimeField()
    last_interacted_with=m.DateTimeField()
    closed_with=m.CharField(max_length=500000,blank=True,null=True,unique=True)

    def __str__(self):
        return f"{self.asker.username if self.asker is not None else self.asking_team}-{self.team_to_ask_on.Name}-{self.noaskedshares} shares at {self.askprice} each"

class Induvidual_CompletedTransaction(m.Model): #order book not needed since its just data and pairs of bids and asks being added together.
    completed_bid = m.ForeignKey(Induvidual_CompletedBids, on_delete=m.CASCADE,blank=False,null=False)
    completed_ask = m.ForeignKey(Induvidual_CompletedAsks, on_delete=m.CASCADE,blank=False,null=False)
    executed_price = m.DecimalField(max_digits=20, decimal_places=2)
    made_at = m.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"completed ask-bid at {self.executed_price}"
 
@receiver(post_save,sender=Induvidual_OrderTransaction) #matches and executes orders #TODO:IMP initial team asks condition to be implimented here.
def check_orders(sender, instance, **kwargs): #yes i know its innefficient, im just doing it for da vibes. (fr tho, fix it.)
    IOB=instance.order_book #IOB as in induvidual order book
    for bid in IOB.bids.all():
        for ask in IOB.asks.all():
            if ask.askprice<=bid.bidprice:
                if ask.asker is not None: #For asks placed by people
                    linkbid=Induvidual_LinktoTeam.objects.filter(curuser=bid.bidder, team_linked=IOB.team)
                    linkask=Induvidual_LinktoTeam.objects.filter(curuser=ask.asker, team_linked=IOB.team)
                    if linkbid.exists() and linkask.exists():
                        linkbid,linkask=linkbid[0],linkask[0]

                        if ask.noaskedshares>bid.nobidshares:
                            moneytobecutfrombidder=(bid.nobidshares*ask.askprice)
                            stockstoberemovedfromasker=bid.nobidshares
                            #make a new ask with how many ever remain.
                        elif ask.noaskedshares==bid.nobidshares:
                            moneytobecutfrombidder=(bid.nobidshares*ask.askprice)
                            stockstoberemovedfromasker=bid.nobidshares
                        elif ask.noaskedshares<bid.nobidshares:
                            moneytobecutfrombidder=(ask.noaskedshares*ask.askprice)
                            stockstoberemovedfromasker=ask.noaskedshares
                            #make a new bid with howmanyever remain

                        if linkask.stocks>=stockstoberemovedfromasker and linkbid.curuser_ID.Money>=moneytobecutfrombidder: #if both parties are able to follow through:
                            linkask.stocks-=stockstoberemovedfromasker 
                            linkbid.curuser_ID.Money-=moneytobecutfrombidder 
                            linkask.curuser_ID.Money+=moneytobecutfrombidder
                            linkbid.stocks+=stockstoberemovedfromasker 

                            IOB.team.Induvidual_Unit_Share_Price=ask.askprice #market value to reflect latest sold value.

                            bid.closed_with=str(ask.id) #(will not trigger a orderbook save dw.)
                            ask.closed_with=str(bid.id)

                            completedbid=Induvidual_CompletedBids.objects.create(bidder=bid.bidder,bidder_ID=bid.bidder_ID,team_to_bid_on=IOB.team,bidprice=bid.bidprice,nobidshares=bid.nobidshares,bidwhen=bid.bidwhen,last_interacted_with=bid.last_interacted_with,closed_with=bid.closed_with)
                            completedask=Induvidual_CompletedAsks.objects.create(asker=ask.asker,asker_ID=ask.asker_ID,team_to_ask_on=IOB.team,askprice=ask.askprice,noaskedshares=ask.noaskedshares,askedwhen=ask.askedwhen,last_interacted_with=ask.last_interacted_with,closed_with=ask.closed_with)
                            Induvidual_CompletedTransaction.objects.create(completed_bid=completedbid,completed_ask=completedask,executed_price=ask.askprice)

                            #Transaction book will be deleted by cascade
                            #Order book automatically doesnt have them.

                            IOB.save()
                            IOB.team.save()
                            linkask.save()
                            linkbid.save()
                            linkbid.curuser_ID.save()
                            linkask.curuser_ID.save()
                            bid.save()
                            ask.save()
                            

                            bid.delete() #im hoping to god this wont trigger a new ordertransaction save. in case it does, god help.
                            ask.delete()


                            if completedask.noaskedshares>completedbid.nobidshares:
                                #make a new ask with how many ever remain.                            
                                Induvidual_Ask.objects.create(asker=completedask.asker,asker_ID=completedask.asker_ID,team_to_ask_on=IOB.team,askprice=completedask.askprice,noaskedshares=completedask.noaskedshares-completedbid.nobidshares)
                                #when new ask created, it will trigger an ask save which will trigger a orderbook save which will trigger this to start all over so all the recent biddings get checked again.
                            elif completedask.noaskedshares<completedbid.nobidshares:
                                #make a new bid with howmanyever remain                            
                                Induvidual_Bid.objects.create(bidder=completedbid.bidder,bidder_ID=completedbid.bidder_ID,team_to_bid_on=IOB.team,bidprice=completedbid.bidprice,nobidshares=completedbid.nobidshares-completedask.noaskedshares)
                                #when new bid created, it will trigger an bid save which will trigger a orderbook save which will trigger this to start all over so all the recent biddings get checked again.

                else: #if its the team that has made the ask as in intial condition where team has all the shares:
                    linkbid=Induvidual_LinktoTeam.objects.filter(curuser=bid.bidder, team_linked=IOB.team)
                    if linkbid.exists() and ask.asking_team is not None:
                        asking_team=ask.asking_team
                        linkbid=linkbid[0]
                        
                        if ask.noaskedshares>bid.nobidshares:
                            moneytobecutfrombidder=(bid.nobidshares*ask.askprice)
                            stockstoberemovedfromasker=bid.nobidshares
                            #make a new ask with how many ever remain.
                        elif ask.noaskedshares==bid.nobidshares:
                            moneytobecutfrombidder=(bid.nobidshares*ask.askprice)
                            stockstoberemovedfromasker=bid.nobidshares
                        elif ask.noaskedshares<bid.nobidshares:
                            moneytobecutfrombidder=(ask.noaskedshares*ask.askprice)
                            stockstoberemovedfromasker=ask.noaskedshares
                            #make a new bid with howmanyever remain

                        if linkbid.curuser_ID.Money>=moneytobecutfrombidder: #if buyer has the money to buy it: 
                            linkbid.curuser_ID.Money-=moneytobecutfrombidder 
                            asking_team.Money+=moneytobecutfrombidder
                            linkbid.stocks+=stockstoberemovedfromasker 

                            IOB.team.Induvidual_Unit_Share_Price=ask.askprice #market value to reflect latest sold value.

                            bid.closed_with=str(ask.id) #(will not trigger a orderbook save dw.)
                            ask.closed_with=str(bid.id)

                            completedbid=Induvidual_CompletedBids.objects.create(bidder=bid.bidder,bidder_ID=bid.bidder_ID,team_to_bid_on=IOB.team,bidprice=bid.bidprice,nobidshares=bid.nobidshares,bidwhen=bid.bidwhen,last_interacted_with=bid.last_interacted_with,closed_with=bid.closed_with)
                            completedask=Induvidual_CompletedAsks.objects.create(asking_team=asking_team,team_to_ask_on=IOB.team,askprice=ask.askprice,noaskedshares=ask.noaskedshares,askedwhen=ask.askedwhen,last_interacted_with=ask.last_interacted_with,closed_with=ask.closed_with)
                            Induvidual_CompletedTransaction.objects.create(completed_bid=completedbid,completed_ask=completedask,executed_price=ask.askprice)

                            #Transaction book will be deleted by cascade
                            #Order book automatically doesnt have them.

                            IOB.save()
                            IOB.team.save()
                            linkbid.save()
                            linkbid.curuser_ID.save()
                            asking_team.save()
                            bid.save()
                            ask.save()
                            

                            bid.delete() #im hoping to god this wont trigger a new ordertransaction save. in case it does, god help.
                            ask.delete()


                            if completedask.noaskedshares>completedbid.nobidshares:
                                #make a new ask with how many ever remain.                            
                                Induvidual_Ask.objects.create(asking_team=completedask.asking_team,team_to_ask_on=IOB.team,askprice=completedask.askprice,noaskedshares=completedask.noaskedshares-completedbid.nobidshares)
                                #when new ask created, it will trigger an ask save which will trigger a orderbook save which will trigger this to start all over so all the recent biddings get checked again.
                            elif completedask.noaskedshares<completedbid.nobidshares:
                                #make a new bid with howmanyever remain                            
                                Induvidual_Bid.objects.create(bidder=completedbid.bidder,bidder_ID=completedbid.bidder_ID,team_to_bid_on=IOB.team,bidprice=completedbid.bidprice,nobidshares=completedbid.nobidshares-completedask.noaskedshares)
                                #when new bid created, it will trigger an bid save which will trigger a orderbook save which will trigger this to start all over so all the recent biddings get checked again.


#Following are all the team models:

#in this system, shares are bought at market price. there are no bids and asks. a company just decides to buy x shares of another company.
#



#Following are all the deleted data saving:

#Saving deleted data cause stocks meaning it seems sensitive... (not fully done) #TODO: Complete this IMP

# @receiver(pre_delete,sender=User) #YET TO TEST
# def saveuserhistory(sender, instance, **kwargs): #idk how to handle multiple deletes happening at the same time.
#     deluser=instance
#     f=open('deleted_data.csv','a')
#     w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
#     affected={"deleted_obj":"User"}
#     affected['User']=[deluser.username]
#     affected['ID']=[f"{i.IDNum}-{i.Money}" for i in UsersID.objects.filter(user=deluser)]
#     affected['teamlinks']=[f"teamlinked-{i.team_linked}, is user in team={i.is_user_in_team}, alertprices={i.alert_prices}, stocks={i.stocks} at {i.team_linked.Market_Value} each at time of deletion" for i in LinktoTeam.objects.filter(curuser=deluser)]
#     affected['comments']=[f"{i.commentinguser} commented on {i.commentedteam} at {i.whencommented} saying {i.comment}" for i in CommentonTeam.objects.filter(commentinguser=deluser)]
#     affected['bids']=[f"{i.bidder} bid {i.bidprice} on {i.nobidshares} shares of {i.team_to_bid_on} at {i.bidwhen}" for i in Bid.objects.filter(bidder=deluser)]
#     affected['asks']=[f"{i.asker} bid {i.askprice} on {i.noaskedshares} shares of {i.team_to_ask_on} at {i.askedwhen}" for i in Ask.objects.filter(asker=deluser)]
#     #good luck to whoever has to retrieve data from this ngl. Its all there, just not in a convinient way. (since not ensured working for prod.)
#     w.writerow(list[affected.items()])
#     f.close()

# @receiver(pre_delete,sender=Team) #YET TO TEST
# def saveteamhistory(sender, instance, **kwargs):
#     delTeam=instance
#     f=open('deleted_data.csv','a')
#     w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
#     affected={"deleted_obj":"Team"}
#     affected['Team']=[delTeam.Name]
#     affected['Shares in market']=[delTeam.Number_of_shares_in_market]
#     affected['Market Value']=[delTeam.Market_Value]
#     affected["News"]=[delTeam.News_and_updates]
#     affected['teamlinks']=[f"user-{i.curuser.username}, is user in team={i.is_user_in_team}, alertprices={i.alert_prices}, stocks={i.stocks} at {i.team_linked.Market_Value} each at time of deletion" for i in LinktoTeam.objects.filter(team_linked=delTeam)]
#     affected['comments']=[f"{i.commentinguser} commented on {i.commentedteam} at {i.whencommented} saying {i.comment}" for i in CommentonTeam.objects.filter(commentedteam=delTeam)]
#     #not adding OrderBook as I feel theres no point, instead ill add the Bids and Asks directly.
#     affected['bids']=[f"{i.bidder} bid {i.bidprice} on {i.nobidshares} shares of {i.team_to_bid_on} at {i.bidwhen}" for i in Bid.objects.filter(team_to_bid_on=delTeam)]
#     affected['asks']=[f"{i.asker} bid {i.askprice} on {i.noaskedshares} shares of {i.team_to_ask_on} at {i.askedwhen}" for i in Ask.objects.filter(team_to_ask_on=delTeam)]
#     w.writerow(list[affected.items()])
#     f.close()
#     #good luck to whoever has to retrieve data from this ngl. Its all there, just not in a convinient way. (will get into later)

# @receiver(pre_delete,sender=LinktoTeam) #YET TO TEST
# def saveteamlinkhistory(sender, instance, **kwargs):
#     delteamlink=instance
#     f=open('deleted_data.csv','a')
#     w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
#     affected={"deleted_obj":"teamlink"}
#     affected['teamlinks']=[f"user-{delteamlink.curuser.username},team-{delteamlink.team_linked.Name}, is user in team={delteamlink.is_user_in_team}, alertprices={delteamlink.alert_prices}, stocks={delteamlink.stocks} at {delteamlink.team_linked.Market_Value} each at time of deletion"]
#     w.writerow(list[affected.items()])
#     f.close()
#     #(nothing to cascade)

# @receiver(pre_delete,sender=CommentonTeam) #YET TO TEST
# def savecommenthistory(sender, instance, **kwargs):
#     i=instance
#     f=open('deleted_data.csv','a')
#     w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
#     affected={"deleted_obj":"commentonteam"}
#     affected['comments']=[f"{i.commentinguser} commented on {i.commentedteam} at {i.whencommented} saying {i.comment}"]
#     w.writerow(list[affected.items()])
#     f.close()
#     #(nothing to cascade)

# @receiver(pre_delete,sender=UsersID) #YET TO TEST
# def saveIDhistory(sender, instance, **kwargs): #idk how to handle multiple deletes happening at the same time.
#     delID=instance
#     f=open('deleted_data.csv','a')
#     w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
#     affected={"deleted_obj":"UsersID"}
#     affected['ID']=[delID.IDNum]
#     affected['User']=[delID.user]
#     affected['Money']=[delID.Money]
#     w.writerow(list[affected.items()])
#     f.close()
#     #(nothing to cascade)

# @receiver(pre_delete,sender=Bid) #YET TO TEST
# def savebidhistory(sender, instance, **kwargs):
#     i=instance
#     f=open('deleted_data.csv','a')
#     w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
#     affected={"deleted_obj":"bid"}
#     affected['bid']=[f"{i.UsersID}-{i.bidder} bid {i.bidprice} on {i.nobidshares} shares of {i.team_to_bid_on} at {i.bidwhen}, closed with {i.closed_with}"]
#     w.writerow(list[affected.items()])
#     f.close()
#     #(nothing to cascade)


# @receiver(pre_delete,sender=Ask) #YET TO TEST
# def saveaskhistory(sender, instance, **kwargs):
#     i=instance
#     f=open('deleted_data.csv','a')
#     w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
#     affected={"deleted_obj":"ask"}
#     affected['ask']=[f"{i.UsersID}-{i.asker} bid {i.askprice} on {i.noaskedshares} shares of {i.team_to_ask_on} at {i.askedwhen}, closed with {i.closed_with}"]
#     w.writerow(list[affected.items()])
#     f.close()
#     #(nothing to cascade)