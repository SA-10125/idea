from django.db import models as m
from django.contrib.auth.models import User
from django.db.models.signals import post_save,pre_delete
from django.dispatch import receiver 
from csv import writer #for the data.csv file.

#This is vibe-coded, not to be used in prod.
#TODO: automations for deletion cascadings.

class GeneralData(m.Model): #a model for general data
    peak=m.BigIntegerField(default=0)

class ID(m.Model): #a model for unique IDs (btw, User.id is a django given unique ID)
    user=m.OneToOneField(User,on_delete=m.DO_NOTHING,related_name='UserforID') #since onetoonefield, a user may only have one ID.
    IDNum=m.CharField(max_length=500,blank=False,null=False,unique=True)

    class Meta:
        unique_together=[['User','IDNum'],['IDNum']] #no repetetion of IDs allowed. 

    def __str__(self):
        return f"{self.User.username}-{self.IDNum}"

class Team(m.Model): #a team is a company
    Name=m.CharField(max_length=50,null=False,unique=True)
    Number_of_shares_in_market=m.BigIntegerField(default=0)
    Market_Value=m.FloatField(default=0.0)
    News_and_updates=m.TextField(max_length=100000,blank=True,null=True) #not creating a table for now, manage with protocols and norms for now while dealing with this data.
    Completed_orders_book=m.TextField(max_length=100000000,blank=True,null=True) #not creating a class for this for now, manage with norms using user IDs and all.

    def __str__(self):
        return f"{self.Name}-{self.Market_Value}"

class LinktoTeam(m.Model): #A user links to any team via this. Team the user is part of, and teams the user has stocks in or has any data with.
    curuser=m.ForeignKey(User,on_delete=m.CASCADE,null=False)
    curuser_ID=m.ForeignKey(ID,on_delete=m.DO_NOTHING,null=False) #when automating creation of this, must fill this.
    team_linked=m.ForeignKey(Team,on_delete=m.DO_NOTHING,null=False) 
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
    commentedteam=m.ForeignKey(Team,on_delete=m.DO_NOTHING,null=False)
    comment=m.TextField(max_length=1000,blank=False)
    whencommented=m.DateTimeField(auto_now_add=True)
    last_interacted_with=m.DateTimeField(auto_now=True)

    class Meta:
        unique_together=[['userid','commentedteam','comment']] #cant spam same comment in same team.

    def __str__(self):
        return f"{self.commentinguser.username}-{self.commentedteam.Name}-{self.comment}"

class Bid(m.Model): #add on delete cascade once the deletion as been automated right. #consider adding unique bid IDs
    bidder=m.ForeignKey(User,on_delete=m.DO_NOTHING,null=False)
    bidder_ID=m.ForeignKey(ID,on_delete=m.DO_NOTHING,null=False)
    team_to_bid_on=m.ForeignKey(Team,on_delete=m.DO_NOTHING,null=False) #redundant for safety
    bidprice=m.FloatField(null=False)
    nobidshares=m.BigIntegerField(null=False)
    bidwhen=m.DateTimeField(auto_now_add=True)
    last_interacted_with=m.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bidder.username}-{self.team_to_bid_on.Name}-{self.nobidshares} shares at {self.bidprice} each"

class Ask(m.Model):#add on delete cascade once the deletion as been automated right. #consider adding unique ask IDs
    asker=m.ForeignKey(User,on_delete=m.DO_NOTHING,null=False)
    asker_ID=m.ForeignKey(ID,on_delete=m.DO_NOTHING,null=False)
    team_to_ask_on=m.ForeignKey(Team,on_delete=m.DO_NOTHING,null=False) #redundant for safety
    askprice=m.FloatField(null=False)
    noaskedshares=m.BigIntegerField(null=False)
    askedwhen=m.DateTimeField(auto_now_add=True)
    last_interacted_with=m.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.asker.username}-{self.team_to_ask_on.Name}-{self.noaskedshares} shares at {self.askprice} each"


@receiver(post_save,sender=Bid)
def addbid(sender, instance, **kwargs): #adding ask to order book of the team the moment it is saved. 
    #(ASKS CANNOT BE EDITED AS IT WILL BE RE ADDED TO THE ORDER BOOK WITHOUT ANY CHANGE. INSTEAD ASK MUST BE DELETED AND NEW ASK MADE.)
    OrderBook.objects.create(team=instance.team_to_bid_on,bids=instance)

@receiver(post_save,sender=Ask)
def addask(sender, instance, **kwargs): #adding ask to order book of the team the moment it is saved. 
    #(ASKS CANNOT BE EDITED AS IT WILL BE RE ADDED TO THE ORDER BOOK WITHOUT ANY CHANGE. INSTEAD ASK MUST BE DELETED AND NEW ASK MADE.)
    OrderBook.objects.create(team=instance.team_to_ask_on,asks=instance)

class OrderBook(m.Model): #maybe this method of doing it is making the db a little too complicated. But using this for now.
    #add on delete cascade once the deletion as been automated right.
    team=m.ForeignKey(Team,on_delete=m.DO_NOTHING,null=False)
    bids=m.ManyToManyField(Bid)
    asks=m.ManyToManyField(Ask)
    placedwhen=m.DateTimeField(auto_now_add=True)
    last_interacted_with=m.DateTimeField(auto_now=True)
    other_deets=m.TextField(max_length=10000000,blank=True,null=True) #consider JSONField

    def __str__(self):
        return f"{self.team.Name}'s current OrderBook"
    
    #consider adding unique together bids asks and team so that the same bid isnt spammed many times?

#Saving deleted data cause stocks meaning it seems sensitive...

@receiver(pre_delete,sender=User) #YET TO TEST
def saveuserhistory(sender, instance, **kwargs): #idk how to handle multiple deletes happening at the same time.
    deluser=instance
    f=open('deleted_data.csv','a')
    w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
    affected={"deleted_obj":"User"}
    affected['User']=[deluser.username]
    affected['ID']=[i.IDNum for i in ID.objects.filter(user=deluser)]
    affected['teamlinks']=[f"teamlinked-{i.team_linked}, is user in team={i.is_user_in_team}, alertprices={i.alert_prices}, stocks={i.stocks} at {i.team_linked.Market_Value} each at time of deletion" for i in LinktoTeam.objects.filter(curuser=deluser)]
    affected['comments']=[f"{i.commentinguser} commented on {i.commentedteam} at {i.whencommented} saying {i.comment}" for i in CommentonTeam.objects.filter(commentinguser=deluser)]
    affected['bids']=[f"{i.bidder} bid {i.bidprice} on {i.nobidshares} shares of {i.team_to_bid_on} at {i.bidwhen}" for i in Bid.objects.filter(bidder=deluser)]
    affected['asks']=[f"{i.asker} bid {i.askprice} on {i.noaskedshares} shares of {i.team_to_ask_on} at {i.askedwhen}" for i in Ask.objects.filter(asker=deluser)]
    #good luck to whoever has to retrieve data from this ngl. Its all there, just not in a convinient way. (since vibe coded, not for prod.)
    w.writerow(affected.items())
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
    w.writerow(affected.items())
    f.close()
    #good luck to whoever has to retrieve data from this ngl. Its all there, just not in a convinient way. (since vibe coded, not for prod.)

@receiver(pre_delete,sender=LinktoTeam) #YET TO TEST
def saveteamlinkhistory(sender, instance, **kwargs):
    delteamlink=instance
    f=open('deleted_data.csv','a')
    w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
    affected={"deleted_obj":"teamlink"}
    affected['teamlinks']=[f"user-{delteamlink.curuser.username},team-{delteamlink.team_linked.Name}, is user in team={delteamlink.is_user_in_team}, alertprices={delteamlink.alert_prices}, stocks={delteamlink.stocks} at {delteamlink.team_linked.Market_Value} each at time of deletion"]
    w.writerow(affected.items())
    f.close()
    #(nothing to cascade)

@receiver(pre_delete,sender=CommentonTeam) #YET TO TEST
def saveteamlinkhistory(sender, instance, **kwargs):
    i=instance
    f=open('deleted_data.csv','a')
    w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
    affected={"deleted_obj":"commentonteam"}
    affected['comments']=[f"{i.commentinguser} commented on {i.commentedteam} at {i.whencommented} saying {i.comment}"]
    w.writerow(affected.items())
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
    w.writerow(affected.items())
    f.close()
    #(nothing to cascade)

@receiver(pre_delete,sender=Bid) #YET TO TEST
def saveteamlinkhistory(sender, instance, **kwargs):
    i=instance
    f=open('deleted_data.csv','a')
    w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
    affected={"deleted_obj":"bid"}
    affected['bid']=[f"{i.bidder} bid {i.bidprice} on {i.nobidshares} shares of {i.team_to_bid_on} at {i.bidwhen}"]
    w.writerow(affected.items())
    f.close()
    #(nothing to cascade)


@receiver(pre_delete,sender=Ask) #YET TO TEST
def saveteamlinkhistory(sender, instance, **kwargs):
    i=instance
    f=open('deleted_data.csv','a')
    w=writer(f,lineterminator="\r")#if this still leaves blanks bw lines, use newline=''
    affected={"deleted_obj":"ask"}
    affected['ask']=[f"{i.asker} bid {i.askprice} on {i.noaskedshares} shares of {i.team_to_ask_on} at {i.askedwhen}"]
    w.writerow(affected.items())
    f.close()
    #(nothing to cascade)