from django.db.models.functions import Now
from django.shortcuts import get_object_or_404, render

from .models import Post, Category


def post_filter(posts):
    return posts.select_related(
        'author', 'location', 'category'
    ).filter(
        pub_date__lte=Now(),
        is_published=True,
        category__is_published=True
    )


def index(request):
    return render(request, 'blog/index.html', {
        'post_list': post_filter(Post.objects)[0:5],
    })


def post_detail(request, post_id):
    return render(request, 'blog/detail.html', {
        'post': get_object_or_404(post_filter(Post.objects), pk=post_id),
    })


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    return render(request, 'blog/category.html', {
        'category': category,
        'post_list': post_filter(category.posts),
    })
