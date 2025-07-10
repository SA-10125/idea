from django.db import models as m
from django.db.models import Q,UniqueConstraint  #this is for a conditional unique constraint on closed_with field
from django.contrib.auth.models import User
from django.db.models.signals import post_save,pre_delete
from django.dispatch import receiver 
from csv import writer #for the data.csv file.
import random
import secrets #a better random.
from django.utils.timezone import now #for current time (for loan calcis)
from decimal import Decimal

def dice_roll():
    return secrets.randbelow(12) + 1  # 1-12

#TODO: IMP possible major idea issue at make_initial_individual_asks_by_team
#TODO: Discuss with team. Should the money in each induviudals wallet be 1/4th of their company's initial valuation/treasury before the event starts?
#      Or should it start with all 100 to keep playing field more level or should it be 0?

#I have used the term Vibe-coding in past comments, I did not know the meaning at the time and thought it meant coding for da vibes without worrying about efficiency and stuff. Just getting it to work.

#This is just coded for da vibes, not to be used in prod.

#TODO: When a company valuation changes, everyone with their stocks should have net worth change? (OR Calculate net worths when needed using current valuations of companies?)
#TODO: Calculate peak and total_market_v4alue dynamically to show btw.

class GeneralData(m.Model): #a model for general data
    temp=m.CharField(max_length=50000,blank=True,null=True) #general data will be added in later. if anything needed for now, put here.

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

def find_current_valuation(team):
    C=len(Team_LinktoTeam.objects.filter(invested_in_team=team)) #number of teams invested in this company
    S=team.Teams_Number_of_shares_in_market-team.Teams_Number_of_shares_with_company #number of shares this company has sold

    Initial_Unit_Share_Price=team.Base_Valuation/team.Individual_Number_of_shares_in_market #(assuming no new shares are added in the market)
    individuals_market_sentiment=(team.Individual_Unit_Share_Price-Initial_Unit_Share_Price)/team.Individual_Number_of_shares_in_market
    
    current_valuation=(team.Base_Valuation*Decimal((1+(C*0.3))*(1+(S*0.002)))*(Decimal(1)+(individuals_market_sentiment*Decimal(0.05)))) #the 0.05 is changable.
    
    return(current_valuation)
    #so, treasury, price that the company's shares were bought at, etc dont directly influence current valuation. 
    #But they do play roles as they do influence how much money anyone has at any point.
    #Valuation only depends on:
        #how many teams have invested in this company. (30% change)
        #how many shares of this company are in the teams market. (0.2% change)
        #individual_market_sentiment. (5% change)
        

def find_net_worth(user_id):
    #TODO: But does the user own a portion of the teams valuation or do the shareholders own that amount of the teams valuation? discuss with E-club

    #individual's net worth is defined by his personal investments in the companies in the individual market and his team's valuation.

    net=user_id.Money
    teams_part_of=Individual_LinktoTeam.objects.filter(curuser_ID=user_id)
    for team in teams_part_of:
        #TODO: go through this again with E-club and decide which parts to keep/remove
        if team.is_user_in_team: #user in team owns a portion of the teams valuation.
            #net+= total_valuation_of_team/number_of_people_in_team (usually 4)
            net+=(find_current_valuation(team.team_linked))/Individual_LinktoTeam.objects.filter(is_user_in_team=True,team_linked=team.team_linked).count()
        else:
            #net+= individual_assets
            net+=(team.stocks*team.team_linked.Individual_Unit_Share_Price)

    return(net)

#In the end, the teams with highest valuation get prizes, so do the individuals with the highest net worth.

#TODO: On save, make it calculate market price by itself or make market price optional.
class Team(m.Model): #a team is a company 
    Name=m.CharField(max_length=50,null=False,unique=True)
    Base_Valuation=m.DecimalField(max_digits=200, decimal_places=2) #as provided by judges.

    #An individual does not have as much money as a company.
    #Hence, a Individual_unit_share_price is small and a Team_unit_share_price is higher.
    #This feels intuitive and also makes it easier for the user to mentally manage both markets as he/she can know which market he is seeing just based on the price.
    #To impliment this, we are having the same base valuation, and having the individual_number_of_shares_in_market=10xhigher than the teams_number_of_shares_in_the_market
    #then placing individual asks at base_valuation/individual_number_of_shares_in_market
    #other teams can buy shares from the company at current_valuation/Teams_Number_of_shares_in_market

    Individual_Number_of_shares_in_market=m.BigIntegerField(default=10000) #this is number of total shares
    #we dont really care about how many shares are still owned by the company.
    Individual_Unit_Share_Price=m.DecimalField(max_digits=100, decimal_places=2) 

    Teams_Number_of_shares_in_market=m.BigIntegerField(default=1000) #this is total number of shares
    Teams_Number_of_shares_with_company=m.BigIntegerField(default=1000) #this is number of unsold shares. (still with company)

    News_and_updates=m.TextField(max_length=100000,blank=True,null=True) #not creating a table for now, manage with protocols and norms for now while dealing with this data.

    Money=m.DecimalField(max_digits=100, decimal_places=2, default=0) #Treasury in hand for investing. (liquid)

    def __str__(self): #TODO: Make this better for the love of god, maybe triggered by the save you could then later make a name?
        try:
            return f"{self.Name}-{find_current_valuation(self)}"
        except AttributeError:
            return f"{self.Name}"

class Loans(m.Model):
    team_taking_loan=m.ForeignKey(Team,null=False,on_delete=m.CASCADE,related_name="taking_loan")
    principal=m.DecimalField(max_digits=100, decimal_places=2) 
    interest=m.DecimalField(max_digits=5,decimal_places=4, default=0.15) #(default=15% interest)
    #consider creditworthyness to raise a warning when taking the loan? 
    #consider approvals of loans by admins before they are handed out.
    # is_approved_by_admin = m.BooleanField(default=False)
    drawn=m.BooleanField(default=False) #wether the amount has been added to the team's treasury after loan is approved.
    #no tenure, should be checked if its repayed by end of event. interest to be calculated per hour? 
    # (calculate net payable amount with compound interest at the end of the event btw. if they have it at that moment, reduce it from their treasury, else reduce their collateral stocks if its enough?, talk to E-club)
    #talk with E-club about collateral to keep or not.
    collateral_shares_of_company=m.ForeignKey(Team,on_delete=m.DO_NOTHING,null=True,blank=True,related_name="collateral") #the team should have shares in this company that they keep as collateral.
    # since this is m.DO_NOTHING, loan.collateral_shares_of_company.name  Will throw error if thats deleted.
    #Total Payable=𝑃*((1+𝑟)**𝑡)
    when_taken=m.DateTimeField(auto_now_add=True) #subtract this from current time at end of event to check t (in hours)
    has_been_payed=m.BooleanField(default=False,null=False) #update at end of event. that way, easy to check who to disqualify.

    def calculate_total_payable(self, current_time=None): #this is from chatgpt, remove later.
        if current_time is None: 
            current_time = now() #now is from django-timezone
        elapsed_hours = (current_time - self.when_taken).total_seconds() / 3600
        return self.principal*((1 + float(self.interest)) ** elapsed_hours) #Total Payable=𝑃*((1+𝑟)**𝑡)

@receiver(post_save,sender=Loans)
def add_loan_amt_to_treasury(sender, instance, created, **kwargs):
    if not instance.drawn: #and instance.is_approved_by_admin:
        instance.team_taking_loan.Money+=instance.principal
        instance.drawn=True
        instance.team_taking_loan.save(update_fields=["Money"]) #update_fields=["Money"] is to only change that and improve performance
        #TODO: impliment such update_fields=["Money"] in other places too to increase efficiency.
        instance.save(update_fields=["drawn"])

#Following are all the team models:

#in this system, shares are bought at unit_share_price. there are no bids and asks. a company just decides to buy x shares of another company.
# when a team buys a company's shares, the amount is deducted from the Money of the team and added to the Money of the company.
# A team can invest in only one other team at a time. 
#There is buying (only from the company youre investing in (any number of times)) and no selling.
    
class Team_LinktoTeam(m.Model): #used to store data about the relation of the teams
    team_investing=m.ForeignKey(Team,on_delete=m.CASCADE, null=False, related_name="team_buying_shares")
    invested_in_team=m.ForeignKey(Team,on_delete=m.CASCADE, null=False, related_name="Investing_in_this_team")
    numberofshares=m.BigIntegerField()
    price_bought_at=m.DecimalField(max_digits=20, decimal_places=2,null=False)
    bought_when=m.DateTimeField(auto_now_add=True)
    last_interacted_with=m.DateTimeField(auto_now=True)
    timeouts=m.DateTimeField(null=True,blank=True) #set using norms like 20 mins from now(), etc.
    alert_prices=m.CharField(max_length=100000,blank=True,null=True) #set alert prices following a norm. #consider using json fields
    #TODO: handle same team investing in same company by updating the same linkage.

    class Meta:
        unique_together=[['team_investing','invested_in_team']] #each team can only be linked to the company once.

#This is to be interacted in views. when a team wants to invest in a particular company, this is created. Dice roll is to be used then.
#The only thing i am considering affecting worth of any company is find_current_valuation which only uses formula. 

#Following are the individual models:

#TODO: consider adding a small cut per transaction to ensure no spam transactions causing market manipulations.

#MAJOR ISSUE, IMP
#TODO: Possible issue, please discuss with Patro. If all the 10k shares are sold at the price_to_place_ask_at instead of market value, wont the market cap at that value until all 10k shares are bought, and only then can the market value go higher than that price_to_place_ask_at!!!
@receiver(post_save,sender=Team)
def make_initial_individual_asks_by_team(sender, instance, created, **kwargs):
    if created: #this is run when the team is first created. It places asks at askrpice=base_valuation/number_of_shares.
                #the ask is then placed into the orderbook by the addask function.
                #the ask matching is handled by the check_orders function wich makes a new ask with howmanyever shares are left and then stores the completed ask in the completed asks
        price_to_place_ask_at=instance.Individual_Unit_Share_Price #whatever price is set first (supposed to be base valuation/10000)
        Individual_Ask.objects.create(asking_team=instance,team_to_ask_on=instance,askprice=price_to_place_ask_at,noaskedshares=instance.Individual_Number_of_shares_in_market)

class Individual_LinktoTeam(m.Model): #A user links to any team via this. Team the user is part of, and teams the user has stocks in or has any data with.
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
    

class Individual_CommentonTeam(m.Model): #a model for users to comment on any team.
    commentinguser=m.ForeignKey(User,on_delete=m.CASCADE,null=False) #one to one field means user can comment only once.
    userid=m.ForeignKey(UsersID,on_delete=m.CASCADE,null=False)
    commentedteam=m.ForeignKey(Team,on_delete=m.CASCADE,null=False)
    comment=m.TextField(max_length=1000,blank=False)
    whencommented=m.DateTimeField(auto_now_add=True)
    last_interacted_with=m.DateTimeField(auto_now=True)

    class Meta:
        unique_together=[['userid','commentedteam','comment']] #cant spam same comment in same team. (however, can spam as long as 1-2 characters differ also. maybe fix?)

    def __str__(self):
        return f"{self.commentinguser.username}-{self.commentedteam.Name}-{self.comment}"

class Individual_Bid(m.Model):
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

class Individual_Ask(m.Model): 
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
        return f"{self.asker.username if self.asker is not None else str(self.asking_team)}-{self.team_to_ask_on.Name}-{self.noaskedshares} shares at {self.askprice} each"

#Consider this: (consider it for completed_asks also)
# from django.core.exceptions import ValidationError

# def clean(self):
#     if self.asker and self.asking_team:
#         raise ValidationError("Cannot set both 'asker' and 'asking_team'. Choose one.")
#     if not self.asker and not self.asking_team:
#         raise ValidationError("Either 'asker' or 'asking_team' must be set.")
#And don't forget to call .full_clean() before saving in custom logic (if needed), or rely on Django admin/forms to enforce it.

@receiver(post_save,sender=Individual_Bid)
def addbid(sender, instance, created, **kwargs): #adding ask to order book of the team the moment it is saved. 
    #(BIDS CANNOT BE EDITED AS IT WILL BE RE ADDED TO THE ORDER BOOK WITHOUT ANY CHANGE. INSTEAD BIDS MUST BE DELETED AND NEW ASK MADE.)
    if created:
        mylink=Individual_LinktoTeam.objects.filter(team_linked=instance.team_to_bid_on,curuser=instance.bidder)
        if mylink.exists(): 
            mylink=mylink[0]
        else: #creating a link if the link doesnt exist
            mylink=Individual_LinktoTeam.objects.create(team_linked=instance.team_to_bid_on,curuser=instance.bidder,curuser_ID=instance.bidder_ID)
        
        if mylink.curuser_ID.Money>=(instance.nobidshares*instance.bidprice): #making sure the user has the money to place a bid
                orderbook,created= Individual_OrderBook.objects.get_or_create(team=instance.team_to_bid_on)
                orderbook.bids.add(instance)
                Individual_OrderTransaction.objects.create(order_book=Individual_OrderBook.objects.get(team=instance.team_to_bid_on),bid=instance,executed_price=instance.bidprice)

@receiver(post_save,sender=Individual_Ask) #to place an ask, you must already have shares in the company and hence already have a teamlink
def addask(sender, instance,created, **kwargs): #adding ask to order book of the team the moment it is saved. 
    #(ASKS CANNOT BE EDITED AS IT WILL BE RE ADDED TO THE ORDER BOOK WITHOUT ANY CHANGE. INSTEAD ASK MUST BE DELETED AND NEW ASK MADE.)
    if created:
        if instance.asker is not None: #This is for individuals placing the ask.
            mylink=Individual_LinktoTeam.objects.filter(team_linked=instance.team_to_ask_on,curuser=instance.asker)
            if mylink.exists() and mylink[0].stocks>=instance.noaskedshares: #making sure the user has the stocks to place an ask
                orderbook,created=Individual_OrderBook.objects.get_or_create(team=instance.team_to_ask_on)
                orderbook.asks.add(instance)
                Individual_OrderTransaction.objects.create(order_book=Individual_OrderBook.objects.get(team=instance.team_to_ask_on),ask=instance,executed_price=instance.askprice)
        else: #If a team places the ask as in the initial condition, there is no link. The ask just gets added to the orderbook and ordertransaction.
            orderbook,created=Individual_OrderBook.objects.get_or_create(team=instance.team_to_ask_on)
            orderbook.asks.add(instance)
            Individual_OrderTransaction.objects.create(order_book=Individual_OrderBook.objects.get(team=instance.team_to_ask_on),ask=instance,executed_price=instance.askprice)
            #TODO: make this more efficient by removing the unnessecary get of order book while creating order transaction. as we already have orderbook.

class Individual_OrderBook(m.Model): #maybe this method of doing it is making the db a little too complicated. But using this for now.
    team=m.ForeignKey(Team,on_delete=m.DO_NOTHING,null=False)
    bids=m.ManyToManyField(Individual_Bid)
    asks=m.ManyToManyField(Individual_Ask)
    placedwhen=m.DateTimeField(auto_now_add=True)
    last_interacted_with=m.DateTimeField(auto_now=True)
    other_deets=m.TextField(max_length=10000000,blank=True,null=True) #consider JSONField

    def __str__(self):
        return f"{self.team.Name}'s current OrderBook"
    
    #consider adding unique together bids asks and team so that the same bid isnt spammed many times?

#This is a through model for Individual_order_book.
class Individual_OrderTransaction(m.Model):
    order_book = m.ForeignKey(Individual_OrderBook, on_delete=m.CASCADE)
    bid = m.ForeignKey(Individual_Bid, on_delete=m.CASCADE,blank=True,null=True)
    ask = m.ForeignKey(Individual_Ask, on_delete=m.CASCADE,blank=True,null=True)
    executed_price = m.DecimalField(max_digits=20, decimal_places=2)
    executed_at = m.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.bid:
            return f"bid at {self.executed_price}"
        else:
            return f"ask at {self.executed_price}"
    

class Individual_CompletedBids(m.Model):
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

class Individual_CompletedAsks(m.Model): 
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
        return f"{self.asker.username if self.asker is not None else str(self.asking_team)}-{self.team_to_ask_on.Name}-{self.noaskedshares} shares at {self.askprice} each"

class Individual_CompletedTransaction(m.Model): #order book not needed since its just data and pairs of bids and asks being added together.
    completed_bid = m.ForeignKey(Individual_CompletedBids, on_delete=m.CASCADE,blank=False,null=False)
    completed_ask = m.ForeignKey(Individual_CompletedAsks, on_delete=m.CASCADE,blank=False,null=False)
    executed_price = m.DecimalField(max_digits=20, decimal_places=2)
    made_at = m.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"completed ask-bid at {self.executed_price}"
 
 #figure out async implimentations and ensure no race condition issues. 
 # (also, if any one of the saves fails, it might mess up the rest, etc. some django_atomic is a solution apparently.)

@receiver(post_save,sender=Individual_OrderTransaction) #matches and executes orders #TODO:IMP initial team asks condition to be implimented here.
def check_orders(sender, instance, **kwargs): #yes i know its innefficient, im just doing it for da vibes. (fr tho, fix it eventually.)
    IOB=instance.order_book #IOB as in individual order book
    for bid in IOB.bids.all():
        for ask in IOB.asks.all():
            if ask.askprice<=bid.bidprice:
                if ask.asker is not None: #For asks placed by people
                    linkbid=Individual_LinktoTeam.objects.filter(curuser=bid.bidder, team_linked=IOB.team)
                    linkask=Individual_LinktoTeam.objects.filter(curuser=ask.asker, team_linked=IOB.team)
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

                            IOB.team.Individual_Unit_Share_Price=ask.askprice #market value to reflect latest sold value.

                            bid.closed_with=str(ask.id) #(will not trigger a orderbook save dw.)
                            ask.closed_with=str(bid.id)

                            completedbid=Individual_CompletedBids.objects.create(bidder=bid.bidder,bidder_ID=bid.bidder_ID,team_to_bid_on=IOB.team,bidprice=bid.bidprice,nobidshares=bid.nobidshares,bidwhen=bid.bidwhen,last_interacted_with=bid.last_interacted_with,closed_with=bid.closed_with)
                            completedask=Individual_CompletedAsks.objects.create(asker=ask.asker,asker_ID=ask.asker_ID,team_to_ask_on=IOB.team,askprice=ask.askprice,noaskedshares=ask.noaskedshares,askedwhen=ask.askedwhen,last_interacted_with=ask.last_interacted_with,closed_with=ask.closed_with)
                            Individual_CompletedTransaction.objects.create(completed_bid=completedbid,completed_ask=completedask,executed_price=ask.askprice)

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
                                Individual_Ask.objects.create(asker=completedask.asker,asker_ID=completedask.asker_ID,team_to_ask_on=IOB.team,askprice=completedask.askprice,noaskedshares=completedask.noaskedshares-completedbid.nobidshares)
                                #when new ask created, it will trigger an ask save which will trigger a orderbook save which will trigger this to start all over so all the recent biddings get checked again.
                            elif completedask.noaskedshares<completedbid.nobidshares:
                                #make a new bid with howmanyever remain                            
                                Individual_Bid.objects.create(bidder=completedbid.bidder,bidder_ID=completedbid.bidder_ID,team_to_bid_on=IOB.team,bidprice=completedbid.bidprice,nobidshares=completedbid.nobidshares-completedask.noaskedshares)
                                #when new bid created, it will trigger an bid save which will trigger a orderbook save which will trigger this to start all over so all the recent biddings get checked again.

                else: #if its the team that has made the ask as in intial condition where team has all the shares:
                    linkbid=Individual_LinktoTeam.objects.filter(curuser=bid.bidder, team_linked=IOB.team)
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

                            IOB.team.Individual_Unit_Share_Price=ask.askprice #market value to reflect latest sold value.

                            bid.closed_with=str(ask.id) #(will not trigger a orderbook save dw.)
                            ask.closed_with=str(bid.id)

                            completedbid=Individual_CompletedBids.objects.create(bidder=bid.bidder,bidder_ID=bid.bidder_ID,team_to_bid_on=IOB.team,bidprice=bid.bidprice,nobidshares=bid.nobidshares,bidwhen=bid.bidwhen,last_interacted_with=bid.last_interacted_with,closed_with=bid.closed_with)
                            completedask=Individual_CompletedAsks.objects.create(asking_team=asking_team,team_to_ask_on=IOB.team,askprice=ask.askprice,noaskedshares=ask.noaskedshares,askedwhen=ask.askedwhen,last_interacted_with=ask.last_interacted_with,closed_with=ask.closed_with)
                            Individual_CompletedTransaction.objects.create(completed_bid=completedbid,completed_ask=completedask,executed_price=ask.askprice)

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
                                Individual_Ask.objects.create(asking_team=completedask.asking_team,team_to_ask_on=IOB.team,askprice=completedask.askprice,noaskedshares=completedask.noaskedshares-completedbid.nobidshares)
                                #when new ask created, it will trigger an ask save which will trigger a orderbook save which will trigger this to start all over so all the recent biddings get checked again.
                            elif completedask.noaskedshares<completedbid.nobidshares:
                                #make a new bid with howmanyever remain                            
                                Individual_Bid.objects.create(bidder=completedbid.bidder,bidder_ID=completedbid.bidder_ID,team_to_bid_on=IOB.team,bidprice=completedbid.bidprice,nobidshares=completedbid.nobidshares-completedask.noaskedshares)
                                #when new bid created, it will trigger an bid save which will trigger a orderbook save which will trigger this to start all over so all the recent biddings get checked again.



#Following are all the deleted data saving:

#Was going to do this:
    #Saving deleted data cause stocks meaning it seems sensitive... (not fully done) #TODO: Complete this IMP
    #Please optimize these to reduce as much as possible and keep it minimal.
#But I am not because:
    #This is because the data is just a backup and is fully optional.
    #We need to reduce the network usage and server load as much as possible

# @receiver(pre_delete,sender=User) #users ID will be cascaded, so accounting for both.
# def savegeneral(sender, instance, **kwargs):
#     f=open('deleted_data.csv','a')
#     w=writer(f,lineterminator="\r")
#     affected={}
#     affected['deleted_obj']='User'
#     affected['User']=instance
#     affected['Time_of_deletion']=now()
#     affected['username']=instance.username
#     ID=UsersID.objects.get(user=instance)
#     affected['User_ID_IDNum']=ID.IDNum
#     affected['User_ID_Money']=ID.Money
#     affected['net_worth']=find_net_worth(ID)
#     affected['teams_linked_to']=[f"team-{i.team_linked.Name}, is user in team={i.is_user_in_team}, alertprices={i.alert_prices}, stocks={i.stocks} at {i.team_linked.Individual_Unit_Share_Price} each at time of deletion" for i in Individual_LinktoTeam.objects.filter(curuser=instance)]
#     affected['comments']=[f"{i.commentinguser} commented on {i.commentedteam.Name} at {i.whencommented} saying {i.comment}" for i in Individual_CommentonTeam.objects.filter(commentinguser=instance)]
#     affected['bids']=[f" bidprice={i.bidprice} no_of_shares={i.nobidshares} team={i.team_to_bid_on.Name} when={i.bidwhen}, closed_with={i.closed_with}" for i in Individual_Bid.objects.filter(bidder=instance)]
#     # asks, completed asks, bids

#and so on for each model and each effected attribute of other models too.