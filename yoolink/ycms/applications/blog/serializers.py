from django.utils.text import slugify
from rest_framework import serializers

from yoolink.ycms.models import Blog

from .services import (
    build_default_code_from_html,
    normalize_blog_code,
    render_blog_code_to_html,
    strip_generated_blog_intro,
)


class ExternalBlogListSerializer(serializers.ModelSerializer):
    absolute_url = serializers.SerializerMethodField()
    api_url = serializers.SerializerMethodField()
    title_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Blog
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "active",
            "language",
            "original",
            "title_image_url",
            "absolute_url",
            "api_url",
            "date",
            "last_updated",
        ]
        read_only_fields = fields

    def get_absolute_url(self, obj):
        request = self.context.get("request")
        if not request:
            return obj.get_absolute_url()
        return request.build_absolute_uri(obj.get_absolute_url())

    def get_api_url(self, obj):
        request = self.context.get("request")
        path = f"/api/cms/blog/{obj.pk}/"
        if not request:
            return path
        return request.build_absolute_uri(path)

    def get_title_image_url(self, obj):
        if not obj.title_image:
            return ""

        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.title_image.url)

        return obj.title_image.url


class ExternalBlogSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    absolute_url = serializers.SerializerMethodField()
    title_image_url = serializers.SerializerMethodField()
    translations = serializers.SerializerMethodField()
    code = serializers.JSONField(required=False)
    title_image = serializers.ImageField(required=False, allow_null=True)
    original = serializers.PrimaryKeyRelatedField(
        queryset=Blog.objects.filter(original__isnull=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Blog
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "body",
            "code",
            "active",
            "language",
            "original",
            "author",
            "title_image",
            "title_image_url",
            "absolute_url",
            "translations",
            "date",
            "last_updated",
        ]
        read_only_fields = ["id", "slug", "author", "absolute_url", "title_image_url", "translations", "date", "last_updated"]

    def get_absolute_url(self, obj):
        request = self.context.get("request")
        if not request:
            return obj.get_absolute_url()
        return request.build_absolute_uri(obj.get_absolute_url())

    def get_title_image_url(self, obj):
        if not obj.title_image:
            return ""

        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.title_image.url)

        return obj.title_image.url

    def get_translations(self, obj):
        root = obj.original if obj.original_id else obj
        variants = [root, *list(root.translations.all())]

        return [
            {
                "id": variant.id,
                "title": variant.title,
                "language": variant.language,
                "active": variant.active,
                "is_current": variant.pk == obj.pk,
                "is_original": variant.pk == root.pk,
                "api_url": self._absolute_api_url(variant),
                "absolute_url": self.get_absolute_url(variant),
            }
            for variant in variants
        ]

    def _absolute_api_url(self, obj):
        request = self.context.get("request")
        path = f"/api/cms/blog/{obj.pk}/"
        if not request:
            return path
        return request.build_absolute_uri(path)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        initial_data = getattr(self, "initial_data", {}) or {}
        instance = self.instance

        body_provided = "body" in initial_data
        code_provided = "code" in initial_data

        body = attrs.get("body")
        if body is None and instance:
            body = instance.body
        body = (body or "").strip()

        if code_provided:
            try:
                normalized_code = normalize_blog_code(attrs.get("code"), body)
            except (TypeError, ValueError) as exc:
                raise serializers.ValidationError({"code": str(exc)}) from exc

            attrs["code"] = normalized_code
            if not body_provided:
                body = render_blog_code_to_html(normalized_code)
                attrs["body"] = body
        elif body_provided or instance is None:
            attrs["code"] = build_default_code_from_html(body)

        if instance is None and not (body or attrs.get("code")):
            raise serializers.ValidationError({"body": "body oder code muss gesetzt sein."})

        description = attrs.get("description")
        if description is None and instance:
            description = instance.description
        if not (description or "").strip():
            raise serializers.ValidationError({"description": "Die Beschreibung darf nicht leer sein."})

        title = attrs.get("title")
        if title is None and instance:
            title = instance.title
        if not (title or "").strip():
            raise serializers.ValidationError({"title": "Der Titel darf nicht leer sein."})

        original = attrs.get("original")
        if original is None and instance:
            original = instance.original
        language = attrs.get("language")
        if language is None and instance:
            language = instance.language
        language = language or "de"

        if original:
            root = original.original or original
            duplicate = root.translations.filter(language=language)
            if instance:
                duplicate = duplicate.exclude(pk=instance.pk)
            if duplicate.exists() or (root.language == language and (not instance or instance.pk != root.pk)):
                raise serializers.ValidationError(
                    {"language": "Für diese Sprache existiert bereits eine Variante dieses Blogs."}
                )

        if "body" in attrs:
            attrs["body"] = strip_generated_blog_intro(attrs["body"], title, description)

        return attrs

    def create(self, validated_data):
        title_image = validated_data.pop("title_image", None)
        request = self.context["request"]
        if validated_data.get("original"):
            base_slug = slugify(validated_data.get("title") or "blog")
            language = (validated_data.get("language") or "de").lower()
            validated_data["slug"] = f"{base_slug}-{language}"

        blog = Blog.objects.create(author=request.user, **validated_data)

        if title_image:
            blog.title_image = title_image
            blog.save(update_fields=["title_image", "last_updated"])

        return blog

    def update(self, instance, validated_data):
        title_image_supplied = "title_image" in validated_data
        title_image = validated_data.pop("title_image", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if title_image_supplied:
            instance.title_image = title_image or ""

        instance.save()
        return instance
