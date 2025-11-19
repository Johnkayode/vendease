from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from api.apps.users.models import User, ActiveSession


class SessionAuthentication(JWTAuthentication):
    """
    This authentication class implements session management with JWT
    """
    def get_user(self, validated_token):
        user: "User" = super().get_user(validated_token)
        token_sid = validated_token.get('sid')

        if not token_sid:
            raise InvalidToken("Token is missing session ID claim.")

        try:
            ActiveSession.objects.get(user=user, session_id=token_sid)
        except ActiveSession.DoesNotExist:
            # This token's session is no longer active.
            raise InvalidToken("This session has been terminated.")
            
        return user

    def authenticate(self, request):
        resp =  super().authenticate(request)
        if resp is None:
            request.session_id = None
            return None
        
        user, validated_token = resp
        if (user and validated_token):
            request.session_id = validated_token.get('sid')
        else:
            request.session_id = None
        return resp