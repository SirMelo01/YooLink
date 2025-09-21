from django.shortcuts import render
from django.views.generic import ListView, DetailView
from yoolink.ycms.models import Blog
from django.utils.translation import get_language_from_request, activate
from django.conf import settings

def get_active_language(request):
    """Holt die aktuelle Sprache aus dem Request oder setzt Fallback auf 'en'"""
    lang = get_language_from_request(request)
    available_languages = dict(settings.LANGUAGES)

    if lang not in available_languages:
        lang = "en"

    activate(lang)
    return lang

class Load_Index_Blog(ListView):
    model = Blog
    template_name = 'blog/index_blog.html'
    context_object_name = 'blogs'

    def get_queryset(self):
        lang = get_active_language(self.request)

        # Lade nur Original-Blogs (ohne original-Relation)
        original_blogs = Blog.objects.filter(original__isnull=True)

        blogs_with_lang_variants = []
        for blog in original_blogs:
            # Suche Sprachvariante für Browser-Sprache
            translated = blog.translations.filter(language=lang).first()
            if translated:
                blogs_with_lang_variants.append(translated)
            else:
                blogs_with_lang_variants.append(blog)

        return blogs_with_lang_variants

class BlogDetailView(DetailView):
    model = Blog
    template_name = 'blog/blog_detail.html'