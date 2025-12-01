from django.shortcuts import redirect
from django.views.generic import ListView, DetailView
from yoolink.ycms.models import Blog
from django.utils.translation import get_language_from_request, activate
from django.conf import settings

from django.utils.translation import get_language

def get_active_language(request):
    """
    Liefert die „aktive“ Sprache:
    - bevorzugt das, was LocaleMiddleware gesetzt hat (request.LANGUAGE_CODE)
    - Fallback: get_language()
    - Fallback 2: settings.LANGUAGE_CODE
    """
    lang = getattr(request, "LANGUAGE_CODE", None) or get_language()
    available_languages = dict(settings.LANGUAGES)

    if lang not in available_languages:
        # Für dich: default ist Deutsch
        lang = settings.LANGUAGE_CODE  # z.B. "de"

    # WICHTIG: KEIN activate(lang) hier!
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
    context_object_name = 'blog'

    def get(self, request, *args, **kwargs):
        # Objekt laden
        self.object = self.get_object()

        # 1) Canonical Slug sicherstellen
        url_slug = kwargs.get('slug_title')
        if url_slug != self.object.slug:
            return redirect(self.object.get_absolute_url())

        # 2) Sprachvariante prüfen → ggf. Redirect
        lang = get_active_language(request)

        # „Familie“: Original + Übersetzungen
        root = self.object.original or self.object  # Original ist Root, sonst self
        if root.language == lang:
            target = root
        else:
            target = root.translations.filter(language=lang, active=True).first() or root

        if target.pk != self.object.pk:
            return redirect(target.get_absolute_url())

        # passt → normal rendern
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)