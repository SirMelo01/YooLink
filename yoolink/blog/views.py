from django.shortcuts import render
from django.views.generic import ListView, DetailView
from yoolink.ycms.models import Blog


class Load_Index_Blog(ListView):
    model = Blog
    template_name = 'blog/index_blog.html'

class BlogDetailView(DetailView):
    model = Blog
    template_name = 'blog/blog_detail.html'