from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.viewsets import ModelViewSet

from yoolink.ycms.models import Blog, DeveloperApiKey

from .authentication import DeveloperApiKeyAuthentication
from .permissions import HasDeveloperApiKeyScope
from .serializers import ExternalBlogListSerializer, ExternalBlogSerializer


class ExternalBlogViewSet(ModelViewSet):
    serializer_class = ExternalBlogSerializer
    authentication_classes = [DeveloperApiKeyAuthentication]
    permission_classes = [HasDeveloperApiKeyScope]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    api_app_code = DeveloperApiKey.APP_BLOG

    def get_serializer_class(self):
        if self.action == "list":
            return ExternalBlogListSerializer

        return ExternalBlogSerializer

    def get_queryset(self):
        queryset = (
            Blog.objects
            .select_related("author", "original")
            .prefetch_related("translations")
            .order_by("-date", "-id")
        )

        query = (self.request.query_params.get("q") or "").strip()
        if query:
            queryset = queryset.filter(title__icontains=query)

        language = (self.request.query_params.get("language") or "").strip()
        if language:
            queryset = queryset.filter(language=language)

        active = (self.request.query_params.get("active") or "").lower()
        if active in ("true", "1", "yes"):
            queryset = queryset.filter(active=True)
        elif active in ("false", "0", "no"):
            queryset = queryset.filter(active=False)

        original_only = (self.request.query_params.get("original_only") or "").lower()
        if original_only in ("true", "1", "yes"):
            queryset = queryset.filter(original__isnull=True)

        return queryset
