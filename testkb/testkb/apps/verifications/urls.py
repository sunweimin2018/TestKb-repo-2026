# from django.urls import re_path as url
from . import views
from django.urls import path ,re_path

urlpatterns = [
    # 发短信
    re_path('sms_codes/(?P<mobile>1[3-9]\d{9})/', views.SMSCodeView.as_view()),

]