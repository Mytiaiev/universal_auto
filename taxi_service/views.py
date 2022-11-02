from django.shortcuts import render
    
def index(request):
    return render(request,'index.html')

def about(request):
    return render(request,'about.html')

def blog(request):
    return render(request,'blog.html')

def why(request):
    return render(request,'why.html')