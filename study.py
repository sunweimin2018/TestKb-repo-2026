




from django.shortcuts import render, HttpResponse
# Create your views here.
#FBV
def book(request):
    if request.method == "'GET":
        return HttpResponse("GET请求...")
    else:
        return HttpResponse("POST请求...")

from django views import View
class BookView(View):
    def dispatch(self,request,*args,**kwargs):
        print("hello world")
        ret =super().dispatch(request,*args,**kwargs)
        return ret
    def get(self,request):
        print("get方法已经执行")
        return HttpResponse("View GET请求...")
    def post(self, request):
        return HttpResponse("View POST请求...")
    def delete(self,request):
        return HttpResponse("VieW DELETE请求...")