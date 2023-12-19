from django.shortcuts import render

def testUp(request):

    return render(request, "test.html")