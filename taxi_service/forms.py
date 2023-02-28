from django import forms
from django.forms import ModelForm
from app.models import Order, SubscribeUsers, User


class MainOrderForm(ModelForm):

    class Meta:
        model = Order
        fields = ('from_address', 'phone_number')
        help_texts = {
            'phone_number': 'Enter phone ex.80991234567',
        }
        error_messages = {
            "from_address": {
                "required": "Enter your address please",
            },
            "phone_number": {
                "required": "Enter your phone please",
            },
        }


        widgets = {
            'from_address': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Pickup Location', 'style': 'font-size: medium'}),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Phone Number', 'style': 'font-size: medium'})
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if User.phone_number_validator(phone_number) is None:
            raise forms.ValidationError("Wrong phone format")
        else:
            return User.phone_number_validator(phone_number)

    def clean_from_address(self):
        from_address = self.cleaned_data.get('from_address')
        if not len(from_address):
            raise forms.ValidationError("Wrong address")
        else:
            return from_address


class SubscriberForm(ModelForm):
    email = forms.EmailField(widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email',
            'style': 'font-size: medium'
        }),
        error_messages={'required': 'Enter your email please',
                        'invalid': 'Enter correct email'}
    )

    class Meta:
        model = SubscribeUsers
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.email_validator(email) is None:
            raise forms.ValidationError("Wrong email address")
        elif SubscribeUsers.get_by_email(email) is not None:
            raise forms.ValidationError("You are subscriber already")
        else:
            return email
