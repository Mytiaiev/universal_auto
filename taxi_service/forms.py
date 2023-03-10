from django import forms
from django.forms import ModelForm
from app.models import Order, SubscribeUsers, User
from django.utils.translation import gettext_lazy as _


class PhoneInput(forms.NumberInput):
    input_type = 'tel'

    def build_attrs(self, attrs, extra_attrs=None, **kwargs):
        attrs = super().build_attrs(attrs, extra_attrs, **kwargs)
        attrs['pattern'] = r'^[\d+]*$'
        attrs['onkeypress'] = 'return event.charCode >= 48 && event.charCode <= 57 || event.charCode == 43;'
        attrs['oninput'] = r"this.value = this.value.replace(/[^0-9+]/g, '');".replace("'", r'"')
        return attrs


class MainOrderForm(ModelForm):

    class Meta:
        model = Order
        fields = ('from_address', 'phone_number')
        error_messages = {
            "from_address": {
                "required": _("Введіть будь-ласка адресу"),
            },
            "phone_number": {
                "required": _("Введіть будь-ласка ваш номер телефону"),
            },
        }

        widgets = {
            'from_address': forms.TextInput(attrs={
                'id': 'address', 'class': 'form-control', 'placeholder': _('Ваша адреса'), 'style': 'font-size: medium'}),
            'phone_number': PhoneInput(attrs={
                'id': 'phone', 'class': 'form-control', 'placeholder': _('Номер телефону'), 'style': 'font-size: medium'})
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if User.phone_number_validator(phone_number) is None:
            raise forms.ValidationError(_("Номер телефону невірний"))
        else:
            return User.phone_number_validator(phone_number)

    def clean_from_address(self):
        from_address = self.cleaned_data.get('from_address')
        if not len(from_address):
            raise forms.ValidationError(_("Неправильна адреса"))
        else:
            return from_address


class SubscriberForm(ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Введіть пошту'),
            'style': 'font-size: medium',
            'id': 'sub_email'
        }),
        error_messages={'required': _('Введіть ел.пошту будь-ласка'),
                        'invalid': _('Введіть корректну ел.пошту')}
    )

    class Meta:
        model = SubscribeUsers
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.email_validator(email) is None:
            raise forms.ValidationError(_("Невірний формат ел.пошти"))
        elif SubscribeUsers.get_by_email(email) is not None:
            raise forms.ValidationError(_("Ви вже підписались"))
        else:
            return email
