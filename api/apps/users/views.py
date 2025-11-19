from django.db import transaction
from rest_framework import status, generics, permissions
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.apps.users.models import User, ActiveSession
from api.apps.users.serializers import (
    UserCreateSerializer, CustomTokenObtainPairSerializer, CustomTokenRefreshSerializer, DepositSerializer,
)
from api.apps.users.permissions import IsBuyer


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer


class UserView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response({"session_id": request.session_id})


class LogoutView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        session_id = getattr(request, 'session_id', None)
        if session_id:
            ActiveSession.objects.filter(user=request.user, session_id=session_id).delete()
            del request.session_id

        return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)


class LogoutAllView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        user = request.user

        if hasattr(request, 'session_id'):
            del request.session_id

        user.active_sessions.all().delete()
        return Response({"detail": "Logged out from all sessions successfully."}, status=status.HTTP_200_OK)


class DepositView(GenericAPIView):
    """
    Deposit coints into buyer's account.
    """
    permission_classes = [IsBuyer]
    serializer_class = DepositSerializer

    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
    
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        amount = serializer.validated_data['amount']
        
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            user.deposit += amount
            user.save(update_fields=['deposit'])
        
        return Response({
            'message': f'{amount} cents deposited successfully.',
            'current_deposit': user.deposit
        }, status=status.HTTP_200_OK)
    

class ResetDepositView(GenericAPIView):
    """
    Reset buyer's deposit to zero.
    """
    permission_classes = [IsBuyer]

    def post(self, request: Request) -> Response:
        user = request.user
        previous_deposit = user.deposit
        new_deposit = user.reset_deposit()
        return Response({
            'message': 'Deposit reset successfully.',
            'previous_deposit': previous_deposit,
            "current_deposit": new_deposit
        }, status=status.HTTP_200_OK)