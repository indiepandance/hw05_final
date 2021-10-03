from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect, reverse
from .models import Post, Group, User, Follow
from django.contrib.auth.decorators import login_required
from .forms import PostForm, CommentForm
from django.conf import settings


def index(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, settings.PAGINATOR_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = 'Последние обновления на сайте'
    context = {
        'page_obj': page_obj,
        'title': title,
        'posts': posts,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)

    posts = group.posts.all()
    paginator = Paginator(posts, settings.PAGINATOR_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'group': group,
        'posts': posts,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    template = 'posts/profile.html'
    user = get_object_or_404(User, username=username)
    posts = user.posts.all()
    paginator = Paginator(posts, settings.PAGINATOR_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'count_posts': user.posts.count(),
        'username': user,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post_detail = get_object_or_404(
        Post.objects.select_related(
            'author').select_related('group'), pk=post_id)
    amount = post_detail.author.posts.count()
    username = post_detail.author
    comments = post_detail.comments.all()
    form = CommentForm()
    context = {
        'post_detail': post_detail,
        'amount': amount,
        'username': username,
        'comments': comments,
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, template, {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=request.user.username)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_edit', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    # post = Post.objects.get(id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, settings.PAGINATOR_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        'posts/follow.html',
        {
            'page_number': page_number,
            'page_obj': page_obj,
            'paginator': paginator
        }
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(
        User,
        username=username
    )
    if author.following.filter(user=request.user).exists():
        return redirect(
            reverse(
                'posts:profile',
                kwargs={'username': username}
            )
        )
    if author != request.user:
        Follow.objects.create(user=request.user, author=author)
    return redirect(
        reverse(
            'posts:profile',
            kwargs={'username': username}
        )
    )


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    delited_follow = get_object_or_404(
        Follow,
        user=request.user,
        author=author
    )
    delited_follow.delete()
    return redirect(
        reverse(
            'posts:profile',
            kwargs={'username': username}
        )
    )
