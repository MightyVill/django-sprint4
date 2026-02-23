from django import forms

from .models import Comment, Post, User


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {
            'pub_date': forms.DateInput(attrs={'type': 'datetime-local'})
        }


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
