from django import forms
from django.contrib.auth import get_user_model
from .models import Post, Comment


User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': 'Напишите текст',
            'group': 'Выберите группу',
            'image': 'Загрузите картинку',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', )
