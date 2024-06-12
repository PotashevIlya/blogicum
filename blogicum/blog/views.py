from django.db.models.functions import Now
from django.utils import timezone
from django.db.models import Count
from django.views.generic import (
    CreateView, DetailView, DeleteView, ListView, UpdateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone


from .models import Category, Comment, Post, User
from .forms import CommentForm, PostForm

POST_ON_PAGE = 10


def post_filter(posts):
    return posts.select_related(
        'author', 'location', 'category'
    ).filter(
        pub_date__lte=Now(),
        is_published=True,
        category__is_published=True
    ).order_by(*Post._meta.ordering)


class UserIsAuthorMixin:

    def dispatch(self, request, *args, **kwargs):
        if request.user == self.get_object().author:
            return super().dispatch(request, *args, **kwargs)
        return redirect('blog:post_detail',
                        self.kwargs['post_id'])


class IndexListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'paje_obj'
    paginate_by = POST_ON_PAGE

    def get_queryset(self):
        return post_filter(Post.objects).annotate(
            comment_count=Count('comments')
        )


class PostDetailView(DetailView):
    model = Post
    form_class = PostForm
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if ((not post.is_published
            or not post.category.is_published
            or post.pub_date >= timezone.now())
                and request.user != post.author):
            raise Http404('Такого поста не существует')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = get_object_or_404(
            Post,
            id=self.kwargs['post_id']
        )
        context['comments'] = self.object.comments.select_related(
            'author').order_by(*Comment._meta.ordering)
        context['form'] = CommentForm()
        return context


class CategoryListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = POST_ON_PAGE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        context['category'] = category
        return context

    def get_queryset(self):
        return post_filter(Post.objects).filter(
            category__slug=self.kwargs['category_slug']
        ).annotate(comment_count=Count('comments'))


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        username = self.request.user.username
        return reverse_lazy(
            'blog:profile',
            args=[username]
        )


class PostUpdateView(UserIsAuthorMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        username = self.request.user.username
        return reverse_lazy(
            'blog:profile',
            args=[username]
        )


class PostDeleteView(UserIsAuthorMixin, DeleteView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    success_url = reverse_lazy('blog:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = self.get_object()
        form = PostForm(self.request.POST or None,
                        instance=instance)
        context['form'] = form
        return context


class ProfileDetailView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    pk_url_kwarg = 'username'
    paginate_by = POST_ON_PAGE

    def get_queryset(self):
        if self.request.user.username == self.kwargs['username']:
            return Post.objects.select_related('author').filter(
                author__username=self.kwargs['username']
            ).annotate(comment_count=Count('comments')
                       ).order_by(*Post._meta.ordering)
        return Post.objects.select_related('author').filter(
            author__username=self.kwargs['username'],
            pub_date__lte=Now()
        ).annotate(comment_count=Count('comments')
                   ).order_by(*Post._meta.ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User, username=self.kwargs['username'])
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    pk_url_kwarg = 'username'
    fields = ['first_name', 'last_name', 'username', 'email']
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        username = self.request.user.username
        return reverse_lazy(
            'blog:profile',
            args=[username]
        )


class CommentCreateView(LoginRequiredMixin, CreateView):
    post_ = None
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        self.post_ = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'post_id': self.object.post.id})


class CommentUpdateView(UpdateView):
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        if request.user == self.get_object().author:
            return super().dispatch(request, *args, **kwargs)
        return redirect('blog:post_detail',
                        self.kwargs['pk'])


class CommentDeleteView(DeleteView):
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        if request.user == self.get_object().author:
            return super().dispatch(request, *args, **kwargs)
        return redirect('blog:post_detail',
                        self.kwargs['pk'])
