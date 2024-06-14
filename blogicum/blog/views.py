from django.db.models.functions import Now
from django.db.models import Count
from django.views.generic import (
    CreateView, DetailView, DeleteView, ListView, UpdateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse


from .forms import CommentForm, PostForm
from .models import Category, Comment, Post, User


MAX_POSTS_ON_PAGE = 10


def get_filtered_posts(posts=Post.objects, filter=True, select_related=True):
    if select_related:
        posts = posts.select_related(
            'author', 'location', 'category'
        )
    if filter:
        posts = posts.filter(
            pub_date__lte=Now(),
            is_published=True,
            category__is_published=True
        )
    return posts.annotate(
        comment_count=Count('comments')
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
    queryset = get_filtered_posts()
    paginate_by = MAX_POSTS_ON_PAGE


class PostDetailView(DetailView):
    model = Post
    form_class = PostForm
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self):
        post = super().get_object()
        if self.request.user != post.author:
            return get_object_or_404(get_filtered_posts(select_related=False),
                                     pk=self.kwargs[self.pk_url_kwarg])
        return post

    def get_context_data(self, **kwargs):
        post = self.get_object()
        context = super().get_context_data(**kwargs)
        context['post'] = post
        context['comments'] = post.comments.select_related('author')
        context['form'] = CommentForm()
        return context


class CategoryListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = MAX_POSTS_ON_PAGE

    def get_category(self):
        category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return category

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.get_category()
        return context

    def get_queryset(self):
        return get_filtered_posts(posts=self.get_category().posts)


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile',
                       args=[self.request.user.username])


class PostUpdateView(UserIsAuthorMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse('blog:profile',
                       args=[self.request.user.username])


class PostDeleteView(UserIsAuthorMixin, DeleteView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    success_url = reverse_lazy('blog:index')


class ProfileDetailView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    pk_url_kwarg = 'username'
    paginate_by = MAX_POSTS_ON_PAGE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User, username=self.kwargs['username'])
        return context

    def get_queryset(self):
        author = get_object_or_404(User,
                                   username=self.kwargs[self.pk_url_kwarg])
        return get_filtered_posts(posts=author.posts,
                                  filter=self.request.user != author)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'username', 'email']
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile',
                       args=[self.request.user.username])


class CommentCreateView(LoginRequiredMixin, CreateView):
    post_ = None
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', args=[self.kwargs['post_id']])


class CommentUpdateView(UserIsAuthorMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'
    success_url = reverse_lazy('blog:index')


class CommentDeleteView(UserIsAuthorMixin, DeleteView):
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'
    success_url = reverse_lazy('blog:index')
