from django import forms
from .models import fileentry, Blog

class fileform(forms.ModelForm):
    label = ''                      ### This hides the label next to the "Browse..." button
    class Meta:
        model = fileentry           ### Specify the model to connect to
        fields = ('file', )         ### This trailing comma is neccessary
        widgets = {
            'file':                 ### This is what allows you to select multiple files
                forms.ClearableFileInput(attrs={'multiple': True})}
        
class Blogform(forms.ModelForm):
    label = ''
    class Meta:
        model = Blog
        fields = ('__all__')