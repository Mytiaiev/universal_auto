import pytest
from app.models import User


@pytest.mark.django_db
@pytest.mark.parametrize('email', 'phone_number', 'chat_id', [("admin@admin.com", "+380964525445", "123"),
                                                              ("admin1@admin.com", "+380964234445", "312"),
                                                              ("admin2@admin.com", "+380964525412", "213")])
def test_users_create(email, phone_number, chat_id):

    user = User.objects.create(email=email, phone_number=phone_number, chat_id=chat_id)
    assert user.email == email
    assert user.phone_number == phone_number
    assert user.chat_id == chat_id
    assert user.objects.count() == 1


@pytest.mark.django_db
def test_get_by_chat_id():
    assert get_by_chat_id("123").chat_id == "123"


@pytest.mark.django_db
def test_fill_deleted_at_by_number():
    assert fill_deleted_at_by_number("+380964525445").deleted_at != null

