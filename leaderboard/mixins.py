from rest_framework.exceptions import MethodNotAllowed


class ReadOnlySerializerMixin:
    def update(self, instance, validated_data):
        raise MethodNotAllowed('update')

    def create(self, validated_data):
        raise MethodNotAllowed('create')
