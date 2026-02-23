from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .constants import DISPLAY_POSTS
from .forms import CommentForm, PostForm
from .models import Category, Comment, Post

User = get_user_model()


class PostListView(ListView):
    paginate_by = DISPLAY_POSTS
    template_name = 'blog/index.html'
    pk_url_kwarg = 'post_id'
    queryset = Post.published_posts.all()


class PostDetailView(DetailView):
    template_name = 'blog/detail.html'
    model = Post
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        return dict(
            **super().get_context_data(**kwargs),
            form=CommentForm(),
            comments=self.object.comments.all()
        )

    def get_object(self):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if self.request.user == post.author:
            return post
        return get_object_or_404(Post.published_posts,
                                 pk=self.kwargs['post_id'])


class ProfileListView(ListView):
    paginate_by = DISPLAY_POSTS
    template_name = 'blog/profile.html'
    profile = None

    def get_queryset(self):
        self.profile = get_object_or_404(User,
                                         username=self.kwargs['username'])
        queryset = self.profile.posts.order_by('-pub_date').annotate(
            comment_count=Count('comments')
        )
        return queryset

    def get_context_data(self, **kwargs):
        return dict(
            **super().get_context_data(**kwargs),
            profile=self.profile
        )


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['username', 'first_name', 'last_name', 'email']
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class CategoryListView(ListView):
    paginate_by = DISPLAY_POSTS
    template_name = 'blog/category.html'
    category = None

    def get_context_data(self, **kwargs):
        return dict(
            **super().get_context_data(**kwargs),
            category=self.category
        )

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        # Менеджер делает не то же самое.
        return self.category.posts(manager='published_posts').all()


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse('blog:profile', kwargs={
            'username': self.request.user.username
        })

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class BasePostView(LoginRequiredMixin, TemplateView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    form_class = PostForm

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if instance.author != self.request.user:
            return redirect('blog:post_detail',
                            post_id=self.kwargs['post_id'])
        self.object = instance
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostUpdateView(BasePostView, UpdateView):
    pass


class PostDeleteView(BasePostView, DeleteView):
    pass


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_context_data(self, **kwargs):
        return dict(**super().get_context_data(**kwargs), form=CommentForm())

    def get_success_url(self):
        return reverse('blog:post_detail',
                       args=[self.kwargs['post_id']])

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post,
                                               pk=self.kwargs['post_id'])
        return super().form_valid(form)


class CommentMixin(LoginRequiredMixin):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            get_object_or_404(Comment,
                              pk=self.kwargs['comment_id'],
                              author=self.request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class CommentDeleteView(CommentMixin, DeleteView):
    pass


class CommentUpdateView(CommentMixin, UpdateView):
    fields = ['text']
