from django.shortcuts import render, redirect
from .models import*
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth import authenticate,login,logout #imported for the user login
from django.contrib import messages #this is what we import to get flash messages.

#dont forget to think about volumes, not just values.

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

    return render(request, 'seeteam.html',context)

#TODO: impliment signup (as in nemo codefusion)
def login_page(request): #can add login feautures like error handling
    if request.method == 'POST':
        username = request.POST.get('Username')
        password = request.POST.get('Password')
        user=User.objects.filter(username=username)
        user = authenticate(request,username=username,password=password)
        if user:
            login(request,user)
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect('home')
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