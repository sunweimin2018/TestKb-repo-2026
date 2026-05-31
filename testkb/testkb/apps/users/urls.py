# from rest_framework_jwt.views import obtain_jwt_token
from rest_framework_simplejwt.views import token_obtain_pair, TokenObtainSlidingView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView, )

from django.urls import path, re_path, include
from . import views

urlpatterns = [
    # 注册用户
    path('users/', views.UserView.as_view()),
    # 判断用户名是否已注册
    re_path('usernames/(?P<username>\w{5,20})/count/', views.UsernameCountView.as_view()),
    # 判断手机号是否已注册
    re_path('mobiles/(?P<mobile>1[3-9]\d{9})/count/', views.MobileCountView.as_view()),

    # JWT登录
    # path('authorizations/', obtain_jwt_token),  # 内部认证代码还是Django  登录成功生成token

    # path('authorizations/',  ObtainJSONWebToken.as_view()),
    # 新加的

    # path('authorizations/', TokenObtainSlidingView.as_view()),  # 内部认证代码还是Django  登录成功生成token
    # path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('authorizations/', views.MyTokenObtainPairView.as_view(), name='token_obtain_sliding'),
    path('user/',views.UserDetailView.as_view()),
    path('email/', views.EmailView.as_view()),
    # 更新邮箱
    path('emails/verification/', views.EmailVerifyView.as_view()),

# (testkb) D:\testkb_registry\testkb>celery -A celery_tasks.main worker -l info



]
