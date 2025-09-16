from urllib.parse import parse_qs
from channels.db import database_sync_to_async


@database_sync_to_async
def get_user_by_id(user_id):
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import AnonymousUser
    User = get_user_model()
    try:
        return User.objects.get(id=user_id)
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware:
    """
    ASGI middleware that authenticates WebSocket connections via JWT.
    Supports ?token=<jwt> query param or Authorization header.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Default anonymous
        from django.contrib.auth.models import AnonymousUser
        scope["user"] = AnonymousUser()

        # Lazy import JWT tools
        from rest_framework_simplejwt.tokens import UntypedToken
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

        # Extract token (query string first)
        query_string = scope.get("query_string", b"").decode()
        qs = parse_qs(query_string)
        token = qs.get("token", [None])[0]

        # Or Authorization header
        if not token:
            headers = dict(scope.get("headers") or [])
            auth_header = headers.get(b"authorization")
            if auth_header:
                try:
                    scheme, token = auth_header.decode().split()
                    if scheme.lower() != "bearer":
                        token = None
                except ValueError:
                    token = None

        if token:
            try:
                validated_token = UntypedToken(token)
                user_id = validated_token.get("user_id")
                if user_id:
                    scope["user"] = await get_user_by_id(user_id)
            except (InvalidToken, TokenError) as e:
                print("❌ Invalid JWT:", e)

        # Hand over to next app
        return await self.inner(scope, receive, send)
