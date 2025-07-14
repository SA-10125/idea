from django.shortcuts import render, redirect
from .models import*
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth import authenticate,login,logout #imported for the user login
from django.contrib import messages #this is what we import to get flash messages.

#dont forget to think about volumes, not just values. (for all)
#TODO: Have messages for each page. not just login.

#TODO: FIX THE DAMN ORDER BOOKS THINGS MAN. ;-; 

# Create your views here.
@login_required(login_url='login')
def homepage(request):
    context={'admin':False} #default
    if request.user.is_superuser: 
        context["admin"]=True #this is passed to a check in the HTML as the UI is different for admin
        
    context['teams']=Team.objects.all()
    return(render(request,'homepage.html',context))

@login_required(login_url='login')
def seeteam(request,pk):
    context={"is_superuser": False, "user": False,"team":None}

    if user_passes_test(lambda u: u.is_superuser):
        context["is_superuser"]= True
    if request.user.is_authenticated:
        context["user"]=request.user #add if the user is the author of the blog in html etc.

    context["team"]=Team.objects.get(Name=pk) #might change this to UID if needed.
    context["current_valuation"]=find_current_valuation(context["team"])

    members={}
    for i in Individual_LinktoTeam.objects.filter(team_linked=context["team"],is_user_in_team=True):
        members[i.curuser]=i.curuser_ID

    context["members"]=members
    context["base_valuation"]=context["team"].Base_Valuation
    context["unsold_shares"]=context["team"].Teams_Number_of_shares_with_company
    context["treasury"]=context["team"].Money
    loans={}
    for i in Loans.objects.filter(team_taking_loan=context["team"]):
        loans[i.principal]=i.when_taken
    context["Loans"]=loans
    context["team_links"]=Team_LinktoTeam.objects.filter(team_investing=context["team"])
    context["investing_team_links"]=Team_LinktoTeam.objects.filter(invested_in_team=context["team"])
    return render(request, 'seeteam.html',context)

def view_member(request, pk): #TODO: make this with proper checks and all.
    ID=UsersID.objects.get(IDNum=pk)
    curuser=ID.user
    net_worth=find_net_worth(ID)
    context={"ID":ID,"user":curuser,"net_worth":net_worth} #in the future, also pass what companies he has the most stock in.
    context["teams"]=Individual_LinktoTeam.objects.filter(curuser=curuser,is_user_in_team=True)
    context["invested_in"]=[i for i in Individual_LinktoTeam.objects.filter(curuser=curuser) if i.stocks>0]
    context["email"]=curuser.email
    context["joined_date"]=curuser.date_joined
    return render(request, 'seeperson.html',context)


#TODO: impliment signup (as in nemo codefusion)
def login_page(request): #can add login feautures like error handling
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('Username')
        password = request.POST.get('Password')
        user=User.objects.filter(username=username)
        user = authenticate(request,username=username,password=password)
        if user:
            login(request,user)
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect(referer)
            else:
                # Fallback to a specific URL, e.g., the home page
                return redirect('home')
        else:
            messages.info(request,'Username or password is incorrect.')
    return render(request,'login.html')

@login_required(login_url='login')
def logout_page(request):
    #consider general data record(logouts)?
    logout(request)
    return(redirect('login'))

#TODO: I was here.
#TODO: For now, i will keep it extremely simple for UI. Where i assume the end user is smart and can type out all details properly.
#      when i have help, ill use help to do the frontend properly including proper and better forms and what will be accepted from them.
@login_required(login_url='login')#TODO: Do this properly with all checks and all making sure they can place.
def placebid(request,pk):
    context={}
    context["team"]=Team.objects.get(Name=pk)
    if request.method == 'POST':
        bidprice = float(request.POST.get('bidprice'))
        nobidshares = int(request.POST.get('nobidshares'))
        if nobidshares <= 0 or bidprice <= 0:
            messages.error(request, 'Invalid bid details. Please enter positive values.')
            return redirect('seeteam', pk=pk)
        Individual_Bid.objects.create(bidder=request.user,bidder_ID=(UsersID.objects.get(user=request.user)),team_to_bid_on=context["team"],bidprice=bidprice,nobidshares=nobidshares)
        messages.success(request, 'Bid placed successfully.') #TODO: V IMP Figure out a better way for this. also configure this to work.
        
        return redirect('seeteam', pk=pk)
        
    return render(request,'placebid.html',context)

@login_required(login_url='login')
def placeask(request,pk):
    context={}
    context["team"]=Team.objects.get(Name=pk)
    if request.method == 'POST':
        askprice = float(request.POST.get('askprice'))
        noaskshares = int(request.POST.get('noaskshares'))
        if noaskshares <= 0 or askprice <= 0:
            messages.error(request, 'Invalid ask details. Please enter positive values.')
            return redirect('seeteam', pk=pk)
        Individual_Ask.objects.create(asker=request.user,asker_ID=(UsersID.objects.get(user=request.user)),team_to_ask_on=context["team"],askprice=askprice,noaskedshares=noaskshares)
        messages.success(request, 'Ask placed successfully.') #TODO: V IMP Figure out a better way for this. also configure this to work.
        
        return redirect('seeteam', pk=pk)
        
    return render(request,'placeask.html',context)

