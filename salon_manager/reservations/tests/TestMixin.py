from users.models import CustomUser


class UserMixin:
    @classmethod
    def create_user_(
        cls,
        first_name="Test",
        last_name="Case",
        email="test.case@test.com",
        phone_number="+48600700800",
    ):
        return CustomUser.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            emial=email,
            phone_number=phone_number,
        )
