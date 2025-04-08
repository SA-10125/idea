from django.db import models as m
from django.contrib.auth.models import User
from django.db.models.signals import post_save,pre_delete
from django.dispatch import receiver 
from csv import writer #for the data.csv file.
import random

#I have used the term Vibe-coding in past comments, I did not know the meaning at the time and thought it meant coding for da vibes without worrying about efficiency and stuff. Just getting it to work.
#There was no AI involved in writing any of this code at any point.

#This is just coded for da vibes, not to be used in prod.

class GeneralData(m.Model): #a model for general data
    peak=m.BigIntegerField(default=0)
    totalmarketvalue=m.BigIntegerField(default=0) #shows overall market value, #TODO: somehow use to analyze trends over time.

class ID(m.Model): #a model for unique IDs (btw, User.id is a django given unique ID)
    user=m.OneToOneField(User,on_delete=m.CASCADE,related_name='UserforID') #since onetoonefield, a user may only have one ID.
    IDNum=m.CharField(max_length=500000,blank=False,null=False,unique=True)
    Money=m.DecimalField(max_digits=20, decimal_places=2, default=0)

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
            if not ID.objects.filter(IDNum=newID).exists():
                break

        ID.objects.create(user=instance,IDNum=newID)

class Team(m.Model): #a team is a company
    Name=m.CharField(max_length=50,null=False,unique=True)
    Number_of_shares_in_market=m.BigIntegerField(default=0)
    Market_Value=m.DecimalField(max_digits=20, decimal_places=2,default=0)
    News_and_updates=m.TextField(max_length=100000,blank=True,null=True) #not creating a table for now, manage with protocols and norms for now while dealing with this data.

    def __str__(self):
        return f"{self.Name}-{self.Market_Value}"

class LinktoTeam(m.Model): #A user links to any team via this. Team the user is part of, and teams the user has stocks in or has any data with.
    curuser=m.ForeignKey(User,on_delete=m.CASCADE,null=False)
    curuser_ID=m.ForeignKey(ID,on_delete=m.CASCADE,null=False) #when automating creation of this, must fill this.
    team_linked=m.ForeignKey(Team,on_delete=m.CASCADE,null=False) 
    is_user_in_team=m.BooleanField(default=False,null=False)
    alert_prices=m.CharField(max_length=100000,blank=True,null=True) #set alert prices following a norm.
    stocks=m.BigIntegerField(default=0) #number of shares user has in the company currently

    class Meta:
        unique_together=[['curuser_ID','team_linked']] #each user can only be linked to the team once.

    def __str__(self):
        return f"{self.curuser.username}-{self.team_linked.Name}-{self.is_user_in_team}"
    

class CommentonTeam(m.Model): #a model for comments.
    commentinguser=m.ForeignKey(User,on_delete=m.CASCADE,null=False) #one to one field means user can comment only once.
    userid=m.ForeignKey(ID,on_delete=m.CASCADE,null=False)
    commentedteam=m.ForeignKey(Team,on_delete=m.CASCADE,null=False)
    comment=m.TextField(max_length=1000,blank=False)
    whencommented=m.DateTimeField(auto_now_add=True)
    last_interacted_with=m.DateTimeField(auto_now=True)

    class Meta:
        unique_together=[['userid','commentedteam','comment']] #cant spam same comment in same team.

    def __str__(self):
        return f"{self.commentinguser.username}-{self.commentedteam.Name}-{self.comment}"

class Bid(m.Model):
    b_ID=m.CharField(max_length=500,blank=False,null=False,unique=True)
    bidder=m.ForeignKey(User,on_delete=m.CASCADE,null=False)
    bidder_ID=m.ForeignKey(ID,on_delete=m.CASCADE,null=False)
    team_to_bid_on=m.ForeignKey(Team,on_delete=m.CASCADE,null=False) #redundant for safety
    bidprice=m.DecimalField(max_digits=20, decimal_places=2,null=False)
    nobidshares=m.BigIntegerField(null=False)
    bidwhen=m.DateTimeField(auto_now_add=True)
    last_interacted_with=m.DateTimeField(auto_now=True)
    closed_with=m.CharField(max_length=500,blank=True,null=True,unique=True)

    def __str__(self):
        return f"{self.bidder.username}-{self.team_to_bid_on.Name}-{self.nobidshares} shares at {self.bidprice} each"

class Ask(m.Model): 
    a_ID=m.CharField(max_length=500000,blank=False,null=False,unique=True)
    asker=m.ForeignKey(User,on_delete=m.CASCADE,null=False)
    asker_ID=m.ForeignKey(ID,on_delete=m.CASCADE,null=False)
    team_to_ask_on=m.ForeignKey(Team,on_delete=m.CASCADE,null=False) #redundant for safety
    askprice=m.DecimalField(max_digits=20, decimal_places=2,null=False)
    noaskedshares=m.BigIntegerField(null=False)
    askedwhen=m.DateTimeField(auto_now_add=True)
    last_interacted_with=m.DateTimeField(auto_now=True)
    closed_with=m.CharField(max_length=500,blank=True,null=True,unique=True)

    def __str__(self):
        return f"{self.asker.username}-{self.team_to_ask_on.Name}-{self.noaskedshares} shares at {self.askprice} each"


@receiver(post_save,sender=Bid)
def addbid(sender, instance, created, **kwargs): #adding ask to order book of the team the moment it is saved. 
    #(BIDS CANNOT BE EDITED AS IT WILL BE RE ADDED TO THE ORDER BOOK WITHOUT ANY CHANGE. INSTEAD BIDS MUST BE DELETED AND NEW ASK MADE.)
    if created:
        mylink=LinktoTeam.objects.filter(team_linked=instance.team_to_bid_on,curuser=instance.bidder)
        if mylink.exists(): #creating a link if the link doesnt exist.
            mylink=mylink[0]
        else:
            mylink=LinktoTeam.objects.create(team_linked=instance.team_to_bid_on,curuser=instance.bidder,curuser_ID=instance.bidder_ID)
        if mylink.curuser_ID.Money>=(instance.nobidshares*instance.bidprice): #making sure the user has the money to place a bid
                orderbook,created= OrderBook.objects.get_or_create(team=instance.team_to_bid_on)
                orderbook.bids.add(instance)
                OrderTransaction.objects.create(order_book=OrderBook.objects.get(team=instance.team_to_bid_on),bid=instance,executed_price=instance.bidprice)

@receiver(post_save,sender=Ask) #to place an ask, you must already have shares in the company and hence already have a teamlink
def addask(sender, instance,created, **kwargs): #adding ask to order book of the team the moment it is saved. 
    #(ASKS CANNOT BE EDITED AS IT WILL BE RE ADDED TO THE ORDER BOOK WITHOUT ANY CHANGE. INSTEAD ASK MUST BE DELETED AND NEW ASK MADE.)
    if created:
        mylink=LinktoTeam.objects.filter(team_linked=instance.team_to_ask_on,curuser=instance.asker)
        if mylink.exists() and mylink[0].stocks>=instance.noaskedshares: #making sure the user has the stocks to place an ask
            orderbook,created=OrderBook.objects.get_or_create(team=instance.team_to_ask_on)
            orderbook.asks.add(instance)
            OrderTransaction.objects.create(order_book=OrderBook.objects.get(team=instance.team_to_ask_on),ask=instance,executed_price=instance.askprice)

class OrderBook(m.Model): #maybe this method of doing it is making the db a little too complicated. But using this for now.
    
    team=m.ForeignKey(Team,on_delete=m.DO_NOTHING,null=False)
    bids=m.ManyToManyField(Bid)
    asks=m.ManyToManyField(Ask)
    placedwhen=m.DateTimeField(auto_now_add=True)
    last_interacted_with=m.DateTimeField(auto_now=True)
    other_deets=m.TextField(max_length=10000000,blank=True,null=True) #consider JSONField

    def __str__(self):
        return f"{self.team.Name}'s current OrderBook"
    
    #consider adding unique together bids asks and team so that the same bid isnt spammed many times?

#GPT Asked me to add this, idk what it means yet but i DID use a through model for events, so...
class OrderTransaction(m.Model):
    order_book = m.ForeignKey(OrderBook, on_delete=m.CASCADE)
    bid = m.ForeignKey(Bid, on_delete=m.CASCADE,blank=True,null=True)
    ask = m.ForeignKey(Ask, on_delete=m.CASCADE,blank=True,null=True)
    executed_price = m.DecimalField(max_digits=20, decimal_places=2)
    executed_at = m.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.bid:
            return f"bid-{self.bid.b_ID} at {self.executed_price}"
        else:
            return f"ask-{self.ask.a_ID} at {self.executed_price}"
    

class CompletedBids(m.Model):
    b_ID=m.CharField(max_length=500,blank=False,null=False,unique=True)
    bidder=m.ForeignKey(User,on_delete=m.CASCADE,null=False)
    bidder_ID=m.ForeignKey(ID,on_delete=m.CASCADE,null=False)
    team_to_bid_on=m.ForeignKey(Team,on_delete=m.CASCADE,null=False) #redundant for safety
    bidprice=m.DecimalField(max_digits=20, decimal_places=2,null=False)
    nobidshares=m.BigIntegerField(null=False)
    bidwhen=m.DateTimeField()
    last_interacted_with=m.DateTimeField()
    closed_with=m.CharField(max_length=500000,blank=True,null=True,unique=True)

    def __str__(self):
        return f"{self.bidder.username}-{self.team_to_bid_on.Name}-{self.nobidshares} shares at {self.bidprice} each"

class CompletedAsks(m.Model): 
    a_ID=m.CharField(max_length=500000,blank=False,null=False,unique=True)
    asker=m.ForeignKey(User,on_delete=m.CASCADE,null=False)
    asker_ID=m.ForeignKey(ID,on_delete=m.CASCADE,null=False)
    team_to_ask_on=m.ForeignKey(Team,on_delete=m.CASCADE,null=False) #redundant for safety
    askprice=m.DecimalField(max_digits=20, decimal_places=2,null=False)
    noaskedshares=m.BigIntegerField(null=False)
    askedwhen=m.DateTimeField()
    last_interacted_with=m.DateTimeField()
    closed_with=m.CharField(max_length=500000,blank=True,null=True,unique=True)

    def __str__(self):
        return f"{self.asker.username}-{self.team_to_ask_on.Name}-{self.noaskedshares} shares at {self.askprice} each"

class CompletedTransaction(m.Model): #order book not needed since its just data and pairs of bids and asks being added together.
    completed_bid = m.ForeignKey(CompletedBids, on_delete=m.CASCADE,blank=False,null=False)
    completed_ask = m.ForeignKey(CompletedAsks, on_delete=m.CASCADE,blank=False,null=False)
    executed_price = m.DecimalField(max_digits=20, decimal_places=2)
    made_at = m.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ask {self.completed_ask.a_ID}-bid {self.completed_bid.b_ID} at {self.executed_price}"
 
@receiver(post_save,sender=OrderTransaction) 
def check_orders(sender, instance, **kwargs): #yes i know its innefficient, im just doing it for da vibes. (fr tho, fix it.)
    OB=instance.order_book
    for bid in OB.bids.all():
        for ask in OB.asks.all():
            if ask.askprice<=bid.bidprice:
                linkbid=LinktoTeam.objects.filter(curuser=bid.bidder, team_linked=OB.team)
                linkask=LinktoTeam.objects.filter(curuser=ask.asker, team_linked=OB.team)
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
                        moneytobecutfrombidder=(ask.noaskshares*ask.askprice)
                        stockstoberemovedfromasker=ask.noaskedshares
                        #make a new bid with howmanyever remain

                    if linkask.stocks>=stockstoberemovedfromasker and linkbid.curuser_ID.Money>=moneytobecutfrombidder: #if both parties are able to follow through:
                        linkask.stocks-=stockstoberemovedfromasker 
                        linkbid.curuser_ID.Money-=moneytobecutfrombidder 
                        linkask.curuser_ID.Money+=moneytobecutfrombidder
                        linkbid.stocks+=stockstoberemovedfromasker 

                        OB.team.Market_Value=ask.askprice 

                        bid.closed_with=ask.a_ID #(will not trigger a orderbook save dw.)
                        ask.closed_with=bid.b_ID

                        completedbid=CompletedBids.objects.create(b_ID=bid.b_ID,bidder=bid.bidder,bidder_ID=bid.bidder_ID,team_to_bid_on=OB.team,bidprice=bid.bidprice,nobidshares=bid.nobidshares,bidwhen=bid.bidwhen,last_interacted_with=bid.last_interacted_with,closed_with=bid.closed_with)
                        completeask=CompletedAsks.objects.create(a_ID=ask.a_ID,asker=ask.asker,asker_ID=ask.asker_ID,team_to_ask_on=OB.team,askprice=ask.askprice,noaskedshares=ask.noaskedshares,askedwhen=ask.askedwhen,last_interacted_with=ask.last_interacted_with,closed_with=ask.closed_with)
                        CompletedTransaction.objects.create(completed_bid=completedbid,completed_ask=completeask,executed_price=ask.askprice)

                        #Transaction book will be deleted by cascade
                        #Order book automatically doesnt have them.

                        OB.save()
                        OB.team.save()
                        linkask.save()
                        linkbid.save()
                        linkbid.curuser_ID.save()
                        linkask.curuser_ID.save()
                        bid.save()
                        ask.save()
                        

                        bid.delete() #im hoping to god this wont trigger a new ordertransaction save. in case it does, god help.
                        ask.delete()


                        if completeask.noaskedshares>completedbid.nobidshares:
                            #make a new ask with how many ever remain.
                            #yes i know this is inneficient, just roll with it for now.
                            while True:
                                newID=str(random.randint(10000000,99999999))
                                if not Ask.objects.filter(a_ID=newID).exists():
                                    break
                            
                            Ask.objects.create(a_ID=newID,asker=completeask.asker,asker_ID=completeask.asker_ID,team_to_ask_on=OB.team,askprice=completeask.askprice,noaskedshares=completeask.noaskedshares-completedbid.nobidshares)
                            #when new ask created, it will trigger an ask save which will trigger a orderbook save which will trigger this to start all over so all the recent biddings get checked again.
                        elif completeask.noaskedshares<completedbid.nobidshares:
                            #make a new bid with howmanyever remain
                                                        #yes i know this is inneficient, just roll with it for now.
                            while True:
                                newID=str(random.randint(10000000,99999999))
                                if not Bid.objects.filter(b_ID=newID).exists():
                                    break
                            
                            Bid.objects.create(b_ID=newID,bidder=completedbid.bidder,bidder_ID=completedbid.bidder_ID,team_to_bid_on=OB.team,bidprice=completedbid.bidprice,nobidshares=completedbid.nobidshares-completeask.noaskedshares)
                            #when new bid created, it will trigger an bid save which will trigger a orderbook save which will trigger this to start all over so all the recent biddings get checked again.



#Saving deleted data cause stocks meaning it seems sensitive... (not fully done) #TODO: Complete this IMP

# @receiver(pre_delete,sender=User) #YET TO TEST
# def saveuserhistory(sender, instance, **kwargs): #idk how to handle multiple deletes happening at the same time.
#     deluser=instance
#     f=open('deleted_data.csv','a')
#     w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
#     affected={"deleted_obj":"User"}
#     affected['User']=[deluser.username]
#     affected['ID']=[f"{i.IDNum}-{i.Money}" for i in ID.objects.filter(user=deluser)]
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

# @receiver(pre_delete,sender=ID) #YET TO TEST
# def saveIDhistory(sender, instance, **kwargs): #idk how to handle multiple deletes happening at the same time.
#     delID=instance
#     f=open('deleted_data.csv','a')
#     w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
#     affected={"deleted_obj":"ID"}
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
#     affected['bid']=[f"{i.ID}-{i.bidder} bid {i.bidprice} on {i.nobidshares} shares of {i.team_to_bid_on} at {i.bidwhen}, closed with {i.closed_with}"]
#     w.writerow(list[affected.items()])
#     f.close()
#     #(nothing to cascade)


# @receiver(pre_delete,sender=Ask) #YET TO TEST
# def saveaskhistory(sender, instance, **kwargs):
#     i=instance
#     f=open('deleted_data.csv','a')
#     w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
#     affected={"deleted_obj":"ask"}
#     affected['ask']=[f"{i.ID}-{i.asker} bid {i.askprice} on {i.noaskedshares} shares of {i.team_to_ask_on} at {i.askedwhen}, closed with {i.closed_with}"]
#     w.writerow(list[affected.items()])
#     f.close()
#     #(nothing to cascade)