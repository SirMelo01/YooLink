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
    paginate_by = 6
    ordering = '-date'

    def get_queryset(self):
        self._lang = get_active_language(self.request)
        return (Blog.objects
                .filter(original__isnull=True, active=True)   # << nur aktive
                .order_by(self.ordering)
                .prefetch_related('translations'))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lang = getattr(self, '_lang', None)
        originals_on_page = ctx['object_list']
        mapped = []
        for blog in originals_on_page:
            variant = blog.translations.filter(language=lang).first() if lang else None
            mapped.append(variant or blog)
        ctx['object_list'] = mapped
        ctx['blogs'] = mapped
        return ctx


class BlogDetailView(DetailView):
    model = Blog
    template_name = 'blog/blog_detail.html'