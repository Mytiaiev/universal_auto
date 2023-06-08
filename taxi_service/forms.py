from django import forms
from django.forms import ModelForm
from app.models import Order, SubscribeUsers, User, Comment
from django.utils.translation import gettext_lazy as _


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('comment',)
        widgets = {'comment': forms.Textarea(attrs={'rows': 5, 'cols': 50})}


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
        fields = (
            'from_address', 'to_the_address', 'phone_number',
            'order_time', 'latitude', 'longitude', 'to_latitude',
            'to_longitude', 'status_order'
        )

        widgets = {
            'from_address': forms.TextInput(attrs={
                'id': 'address', 'class': 'form-control', 'placeholder': _('Звідки вас забрати?'), 'style': 'font-size: medium'}),
            'to_the_address': forms.TextInput(attrs={
                'id': 'to_address', 'class': 'form-control', 'placeholder': _('Куди їдемо?'), 'style': 'font-size: medium'}),
            'phone_number': PhoneInput(attrs={
                'id': 'phone', 'class': 'form-control', 'placeholder': _('Номер телефону'), 'style': 'font-size: medium'}),
            'order_time': forms.TextInput(attrs={
                'id': 'delivery_time', 'class': 'form-control', 'placeholder': _('На яку годину? формат HH:MM(напр. 18:45)'), 'style': 'font-size: medium'}),
        }

    def save(self, payment=None, on_time=None):
        order = super().save(commit=False)
        if on_time is not None:
            order.order_time = on_time
            order.status_order = Order.ON_TIME
        if payment is not None:
            order.payment_method = payment
        order.save()
        return order


class SubscriberForm(ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Введіть пошту'),
            'style': 'font-size: medium',
            'id': 'sub_email'
        }),
        error_messages={'required': _('Введіть ел.пошту, будь ласка'),
                        'invalid': _('Введіть коректну ел.пошту')}
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
