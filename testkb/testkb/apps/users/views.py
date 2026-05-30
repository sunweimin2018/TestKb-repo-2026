from django.shortcuts import render
from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import GenericAPIView, CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import CreateUserSerializer, UserDetailSerializer, EmailSerializer
from .models import User
# Create your views here.
from rest_framework_simplejwt.views import TokenObtainSlidingView, TokenObtainPairView

from .utils import MyTokenObtainSlidingSerializer1,MyTokenObtainPairSerializer


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer  # 只需修改其序列化器为刚刚自定义的即可

class UserView(CreateAPIView):
    """用户注册"""
    # 指定序列化器
    serializer_class = CreateUserSerializer
class UsernameCountView(APIView):
    """判断用户是否已注册"""

    def get(self, request, username):
        # 查询user表
        # print("ok"*20)
        # print(type(request.user))
        count = User.objects.filter(username=username).count()

        # 包装响应数据
        data = {
            'username': username,
            'count': count
        }
        print("data:",data)
        # 响应
        return Response(data)


class MobileCountView(APIView):
    """判断手机号是否已注册"""

    def get(self, request, mobile):
        # 查询数据库
        count = User.objects.filter(mobile=mobile).count()
        # 构造响应数据
        data = {
            'mobile': mobile,
            'count': count
        }
        # 响应
        return Response(data)





# GET /user/
class UserDetailView(RetrieveAPIView):
    """用户详细信息展示"""
    serializer_class = UserDetailSerializer
    # queryset = User.objects.all()
    permission_classes = [IsAuthenticated]  # 指定权限,只有通过认证的用户才能访问当前视图

    def get_object(self):
        """重写此方法返回 要展示的用户模型对象"""
        print("mon"*20)
        print(self.request.user)
        print(type(self.request.user))
        print("self.request.user.password")
        print(self.request.user.password)
        return self.request.user



# PUT /email/
class EmailView(UpdateAPIView):
    """更新用户邮箱"""
    permission_classes = [IsAuthenticated]
    serializer_class = EmailSerializer

    def get_object(self):
        return self.request.user


class EmailVerifyView(APIView):
    """激活用户邮箱"""

    def get(self, request):
        # 获取前端查询字符串中传入的token
        token = request.query_params.get('token')
        if not token:
            return Response({'message': '缺少token'}, status=status.HTTP_400_BAD_REQUEST)

        # 把token解密 并查询对应的user
        user = User.check_verify_email_token(token)
        # 修改当前user的email_active为True
        if user is None:
            return Response({'message': '激活失败'}, status=status.HTTP_400_BAD_REQUEST)
        user.email_active = True
        user.save()
        # 响应
        return Response({'message': 'ok'})
#
#
#
# class AddressViewSet(GenericAPIView):
#     """用户收货地址增删改查"""
#     permission_classes = [IsAuthenticated]
#     serializer_class = ''
#     # queryset = ''
#
#
#     def create(self, request):
#         user = request.user
#         # count = user.addresses.all().count()
#         count = Address.objects.filter(user=user).count()
#         # 用户收货地址数量有上限  最多只能有20
#         if count >= 20:
#             return Response({'message': '收货地址数量上限'}, status=status.HTTP_400_BAD_REQUEST)
#
#         # 创建序列化器进行反序列化
#         serializer = self.get_serializer(data=request.data)
#         # 调用序列化器的is_valid()
#         serializer.is_valid(raise_exception=True)
#         # 调用序列化器的save()
#         serializer.save()
#         # 响应
#         return Response(serializer.data, status=status.HTTP_201_CREATED)