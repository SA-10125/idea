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
    User=m.OneToOneField(User,on_delete=m.DO_NOTHING,related_name='UserforID') #since onetoonefield, a user may only have one ID.
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
    Old_order_book=m.TextField(max_length=100000000,blank=True,null=True) #not creating a class for this for now, manage with norms using user IDs and all.

    def __str__(self):
        return f"{self.Name}-{self.Market_Value}"

class LinktoTeam(m.Model): #A user links to any team via this. Team the user is part of, and teams the user has stocks in or has any data with.
    curuser=m.ForeignKey(User,on_delete=m.DO_NOTHING,null=False)
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

class OrderBook(m.Model): #maybe this method of doing it is making the db a little too complicated. But using this for now.
    #add on delete cascade once the deletion as been automated right.
    team=m.ForeignKey(Team,on_delete=m.DO_NOTHING,null=False)
    bids=m.ManyToManyField(Bid)
    asks=m.ManyToManyField(Ask)
    placedwhen=m.DateTimeField(auto_now_add=True)
    last_interacted_with=m.DateTimeField(auto_now=True)
    other_deets=m.TextField(max_length=10000000) #consider JSONField

    def __str__(self):
        return f"{self.team.Name}'s current OrderBook"
    
    #consider adding unique together bids asks and team so that the same bid isnt spammed many times?


