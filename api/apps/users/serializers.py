from rest_framework import serializers
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from api.apps.users.models import User, ActiveSession
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer, TokenBlacklistSerializer



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'role', 'deposit')
        read_only_fields = ('id', 'deposit')


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password_confirm', 'role')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            role=validated_data['role']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer to validate active sessions."""

    
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        session_count = user.active_sessions.count()
        if session_count >= settings.MAX_USER_SESSIONS:
            raise serializers.ValidationError({
                'detail': 'There is already an active session using your account.',
                'active_sessions': True
            })

        refresh = self.get_token(self.user)
        jti = refresh['jti']

        access_token = refresh.access_token
        access_token['sid'] = str(jti)

        request = self.context.get('request')
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')

        expiry_datetime = timezone.datetime.fromtimestamp(
            refresh['exp'], 
            tz=timezone.utc 
        )
        ActiveSession.objects.create(
            user=self.user,
            session_id=jti,
            ip_address=ip_address,
            user_agent=user_agent,
            expiry_date=expiry_datetime
        )  
        data['refresh'] = str(refresh)
        data['access'] = str(access_token)
        data['expiry'] = access_token['exp']
        return data
    

class CustomTokenRefreshSerializer(TokenRefreshSerializer):

    def validate(self, attrs):
        try:
            old_refresh = self.token_class(attrs["refresh"])
            old_jti = str(old_refresh['jti'])
        except Exception:
            old_jti = None 

        try:
            ActiveSession.objects.get(session_id=old_jti)
        except ActiveSession.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Session is no longer active.", "active_sessions": False}
            )
        
        refresh = self.token_class(attrs["refresh"])
        access_token = refresh.access_token
        access_token['sid'] = str(old_jti)

        data = {"access": str(access_token)}
        return data
    

class DepositSerializer(serializers.Serializer):
    amount = serializers.IntegerField()

    def validate_amount(self, value):
        valid_coins = (5, 10, 20, 50, 100)
        if value not in valid_coins:
            raise serializers.ValidationError(
                _(f"Deposit amount must be one of the following: {valid_coins}.")
            )
        return value

