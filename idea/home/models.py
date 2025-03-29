from django.db import models as m
from django.contrib.auth.models import User
from django.db.models.signals import post_save,pre_delete
from django.dispatch import receiver 
from csv import writer #for the data.csv file.
import random

#This is vibe-coded, not to be used in prod.

class GeneralData(m.Model): #a model for general data
    peak=m.BigIntegerField(default=0)
    totalmarketvalue=m.BigIntegerField(default=0) #shows overall market value, #TODO: somehow use to analyze trends over time.

class ID(m.Model): #a model for unique IDs (btw, User.id is a django given unique ID)
    user=m.OneToOneField(User,on_delete=m.CASCADE,related_name='UserforID') #since onetoonefield, a user may only have one ID.
    IDNum=m.CharField(max_length=500,blank=False,null=False,unique=True)
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
    Completed_orders_book=m.TextField(max_length=100000000,blank=True,null=True) #not creating a class for this for now, manage with norms using user IDs and all.

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

class Bid(m.Model):  #consider adding unique bid IDs
    bidder=m.ForeignKey(User,on_delete=m.CASCADE,null=False)
    bidder_ID=m.ForeignKey(ID,on_delete=m.CASCADE,null=False)
    team_to_bid_on=m.ForeignKey(Team,on_delete=m.CASCADE,null=False) #redundant for safety
    bidprice=m.DecimalField(max_digits=20, decimal_places=2,null=False)
    nobidshares=m.BigIntegerField(null=False)
    bidwhen=m.DateTimeField(auto_now_add=True)
    last_interacted_with=m.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bidder.username}-{self.team_to_bid_on.Name}-{self.nobidshares} shares at {self.bidprice} each"

class Ask(m.Model): #consider adding unique ask IDs
    asker=m.ForeignKey(User,on_delete=m.CASCADE,null=False)
    asker_ID=m.ForeignKey(ID,on_delete=m.CASCADE,null=False)
    team_to_ask_on=m.ForeignKey(Team,on_delete=m.CASCADE,null=False) #redundant for safety
    askprice=m.DecimalField(max_digits=20, decimal_places=2,null=False)
    noaskedshares=m.BigIntegerField(null=False)
    askedwhen=m.DateTimeField(auto_now_add=True)
    last_interacted_with=m.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.asker.username}-{self.team_to_ask_on.Name}-{self.noaskedshares} shares at {self.askprice} each"


@receiver(post_save,sender=Bid)
def addbid(sender, instance, **kwargs): #adding ask to order book of the team the moment it is saved. 
    #(ASKS CANNOT BE EDITED AS IT WILL BE RE ADDED TO THE ORDER BOOK WITHOUT ANY CHANGE. INSTEAD ASK MUST BE DELETED AND NEW ASK MADE.)
    mylink=LinktoTeam.objects.filter(team_linked=instance.team_to_bid_on,curuser=instance.bidder)
    print(mylink)
    if mylink.exists(): #creating a link if the link doesnt exist.
        mylink=mylink[0]
    else:
        mylink=LinktoTeam.objects.create(team_linked=instance.team_to_bid_on,curuser=instance.bidder,curuser_ID=instance.bidder_ID)
    if mylink.curuser_ID.Money>=(instance.nobidshares*instance.bidprice): #making sure the user has the money to place a bid
            orderbook,created= OrderBook.objects.get_or_create(team=instance.team_to_bid_on)
            orderbook.bids.add(instance)
            OrderTransaction.objects.create(order_book=OrderBook.objects.get(team=instance.team_to_bid_on),bid=instance,executed_price=instance.bidprice)

@receiver(post_save,sender=Ask) #to place an ask, you must already have shares in the company and hence already have a teamlink
def addask(sender, instance, **kwargs): #adding ask to order book of the team the moment it is saved. 
    #(ASKS CANNOT BE EDITED AS IT WILL BE RE ADDED TO THE ORDER BOOK WITHOUT ANY CHANGE. INSTEAD ASK MUST BE DELETED AND NEW ASK MADE.)
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


#Saving deleted data cause stocks meaning it seems sensitive...

@receiver(pre_delete,sender=User) #YET TO TEST
def saveuserhistory(sender, instance, **kwargs): #idk how to handle multiple deletes happening at the same time.
    deluser=instance
    f=open('deleted_data.csv','a')
    w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
    affected={"deleted_obj":"User"}
    affected['User']=[deluser.username]
    affected['ID']=[f"{i.IDNum}-{i.Money}" for i in ID.objects.filter(user=deluser)]
    affected['teamlinks']=[f"teamlinked-{i.team_linked}, is user in team={i.is_user_in_team}, alertprices={i.alert_prices}, stocks={i.stocks} at {i.team_linked.Market_Value} each at time of deletion" for i in LinktoTeam.objects.filter(curuser=deluser)]
    affected['comments']=[f"{i.commentinguser} commented on {i.commentedteam} at {i.whencommented} saying {i.comment}" for i in CommentonTeam.objects.filter(commentinguser=deluser)]
    affected['bids']=[f"{i.bidder} bid {i.bidprice} on {i.nobidshares} shares of {i.team_to_bid_on} at {i.bidwhen}" for i in Bid.objects.filter(bidder=deluser)]
    affected['asks']=[f"{i.asker} bid {i.askprice} on {i.noaskedshares} shares of {i.team_to_ask_on} at {i.askedwhen}" for i in Ask.objects.filter(asker=deluser)]
    #good luck to whoever has to retrieve data from this ngl. Its all there, just not in a convinient way. (since vibe coded, not for prod.)
    w.writerow(list[affected.items()])
    f.close()

@receiver(pre_delete,sender=Team) #YET TO TEST
def saveteamhistory(sender, instance, **kwargs):
    delTeam=instance
    f=open('deleted_data.csv','a')
    w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
    affected={"deleted_obj":"Team"}
    affected['Team']=[delTeam.Name]
    affected['Shares in market']=[delTeam.Number_of_shares_in_market]
    affected['Market Value']=[delTeam.Market_Value]
    affected["News"]=[delTeam.News_and_updates]
    affected['Completed_orders_book']=[delTeam.Completed_orders_book]
    affected['teamlinks']=[f"user-{i.curuser.username}, is user in team={i.is_user_in_team}, alertprices={i.alert_prices}, stocks={i.stocks} at {i.team_linked.Market_Value} each at time of deletion" for i in LinktoTeam.objects.filter(team_linked=delTeam)]
    affected['comments']=[f"{i.commentinguser} commented on {i.commentedteam} at {i.whencommented} saying {i.comment}" for i in CommentonTeam.objects.filter(commentedteam=delTeam)]
    #not adding OrderBook as I feel theres no point, instead ill add the Bids and Asks directly.
    affected['bids']=[f"{i.bidder} bid {i.bidprice} on {i.nobidshares} shares of {i.team_to_bid_on} at {i.bidwhen}" for i in Bid.objects.filter(team_to_bid_on=delTeam)]
    affected['asks']=[f"{i.asker} bid {i.askprice} on {i.noaskedshares} shares of {i.team_to_ask_on} at {i.askedwhen}" for i in Ask.objects.filter(team_to_ask_on=delTeam)]
    w.writerow(list[affected.items()])
    f.close()
    #good luck to whoever has to retrieve data from this ngl. Its all there, just not in a convinient way. (since vibe coded, not for prod.)

@receiver(pre_delete,sender=LinktoTeam) #YET TO TEST
def saveteamlinkhistory(sender, instance, **kwargs):
    delteamlink=instance
    f=open('deleted_data.csv','a')
    w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
    affected={"deleted_obj":"teamlink"}
    affected['teamlinks']=[f"user-{delteamlink.curuser.username},team-{delteamlink.team_linked.Name}, is user in team={delteamlink.is_user_in_team}, alertprices={delteamlink.alert_prices}, stocks={delteamlink.stocks} at {delteamlink.team_linked.Market_Value} each at time of deletion"]
    w.writerow(list[affected.items()])
    f.close()
    #(nothing to cascade)

@receiver(pre_delete,sender=CommentonTeam) #YET TO TEST
def savecommenthistory(sender, instance, **kwargs):
    i=instance
    f=open('deleted_data.csv','a')
    w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
    affected={"deleted_obj":"commentonteam"}
    affected['comments']=[f"{i.commentinguser} commented on {i.commentedteam} at {i.whencommented} saying {i.comment}"]
    w.writerow(list[affected.items()])
    f.close()
    #(nothing to cascade)

@receiver(pre_delete,sender=ID) #YET TO TEST
def saveIDhistory(sender, instance, **kwargs): #idk how to handle multiple deletes happening at the same time.
    delID=instance
    f=open('deleted_data.csv','a')
    w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
    affected={"deleted_obj":"ID"}
    affected['ID']=[delID.IDNum]
    affected['User']=[delID.user]
    affected['Money']=[delID.Money]
    w.writerow(list[affected.items()])
    f.close()
    #(nothing to cascade)

@receiver(pre_delete,sender=Bid) #YET TO TEST
def savebidhistory(sender, instance, **kwargs):
    i=instance
    f=open('deleted_data.csv','a')
    w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
    affected={"deleted_obj":"bid"}
    affected['bid']=[f"{i.bidder} bid {i.bidprice} on {i.nobidshares} shares of {i.team_to_bid_on} at {i.bidwhen}"]
    w.writerow(list[affected.items()])
    f.close()
    #(nothing to cascade)


@receiver(pre_delete,sender=Ask) #YET TO TEST
def saveaskhistory(sender, instance, **kwargs):
    i=instance
    f=open('deleted_data.csv','a')
    w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
    affected={"deleted_obj":"ask"}
    affected['ask']=[f"{i.asker} bid {i.askprice} on {i.noaskedshares} shares of {i.team_to_ask_on} at {i.askedwhen}"]
    w.writerow(list[affected.items()])
    f.close()
    #(nothing to cascade)