from django.db import models
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from django.core.paginator import Paginator


class TimestampedModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class SoftDeleteModelMixin(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    @classmethod
    def active_objects(cls):
        return cls.objects.filter(is_deleted=False)


class AuthorTrackingMixin(models.Model):
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
    )

    class Meta:
        abstract = True


class ValidationMixin:
    def validate_required_fields(self, data, required_fields):
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return False, {
                'error': f'Brakujące wymagane pola: {", ".join(missing_fields)}',
                'missing_fields': missing_fields
            }

        return True, {}

    def validate_positive_integer(self, value, field_name, min_value=1, max_value=None):
        try:
            int_value = int(value)

            if int_value < min_value:
                return False, {
                    'error': f'{field_name} musi wynosić co najmniej {min_value}'
                }

            if max_value and int_value > max_value:
                return False, {
                    'error': f'{field_name} nie może przekraczać {max_value}'
                }

            return True, int_value

        except (ValueError, TypeError):
            return False, {
                'error': f'{field_name} musi być liczbą całkowitą'
            }

    def validate_choice(self, value, choices, field_name):
        if value not in choices:
            return False, {
                'error': f'{field_name} musi być jedną z wartości: {", ".join(choices)}',
                'valid_choices': choices
            }

        return True, value

    def validate_string_length(self, value, field_name, min_length=1, max_length=None):
        if not isinstance(value, str):
            return False, {'error': f'{field_name} musi być tekstem'}

        if len(value) < min_length:
            return False, {
                'error': f'{field_name} musi mieć co najmniej {min_length} znaków'
            }

        if max_length and len(value) > max_length:
            return False, {
                'error': f'{field_name} nie może przekraczać {max_length} znaków'
            }

        return True, value


class PaginationMixin:
    default_page_size = 10
    max_page_size = 100

    def get_page_params(self, request):
        try:
            page = int(request.GET.get('page', 1))
            page = max(1, page)
        except (ValueError, TypeError):
            page = 1

        try:
            page_size = int(request.GET.get('page_size', self.default_page_size))
            page_size = min(max(1, page_size), self.max_page_size)
        except (ValueError, TypeError):
            page_size = self.default_page_size

        return page, page_size

    def paginate_queryset(self, queryset, request, serializer_class=None):
        page_num, page_size = self.get_page_params(request)

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page_num)

        pagination_meta = {
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_num,
            'page_size': page_size,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }

        if serializer_class:
            serialized_data = serializer_class(page_obj.object_list, many=True).data
            return serialized_data, pagination_meta

        return page_obj.object_list, pagination_meta

    def build_paginated_response(self, data, pagination_meta):
        return Response({
            'results': data,
            **pagination_meta
        })


class PermissionCheckMixin:
    def is_owner_or_admin(self, obj, user):
        if hasattr(obj, 'user'):
            is_owner = obj.user == user
        elif hasattr(obj, 'created_by'):
            is_owner = obj.created_by == user
        else:
            is_owner = False

        is_admin = hasattr(user, 'profile') and user.profile.role == 'admin'

        return is_owner or is_admin

    def require_owner_or_admin(self, obj, user):
        from core.exceptions import PermissionDenied

        if not self.is_owner_or_admin(obj, user):
            raise PermissionDenied()

    def is_admin(self, user):
        return hasattr(user, 'profile') and user.profile.role == 'admin'

    def require_admin(self, user):
        from core.exceptions import PermissionDenied

        if not self.is_admin(user):
            raise PermissionDenied()


class QuerysetFilterMixin:
    def filter_by_date_range(self, queryset, field_name, start_date=None, end_date=None):
        if start_date:
            queryset = queryset.filter(**{f'{field_name}__gte': start_date})

        if end_date:
            queryset = queryset.filter(**{f'{field_name}__lte': end_date})

        return queryset

    def filter_by_search(self, queryset, search_fields, search_term):
        if not search_term:
            return queryset

        from django.db.models import Q

        query = Q()
        for field in search_fields:
            query |= Q(**{f'{field}__icontains': search_term})

        return queryset.filter(query)

    def apply_ordering(self, queryset, request, allowed_fields):
        order_by = request.GET.get('order_by')

        if not order_by:
            return queryset

        is_descending = order_by.startswith('-')
        field_name = order_by.lstrip('-')

        if field_name not in allowed_fields:
            return queryset

        return queryset.order_by(order_by)


class ResponseMixin:
    def success_response(self, data=None, message=None, status_code=status.HTTP_200_OK):
        response_data = {}

        if message:
            response_data['message'] = message

        if data is not None:
            response_data['data'] = data

        return Response(response_data, status=status_code)

    def error_response(self, message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        response_data = {'error': message}

        if errors:
            response_data['errors'] = errors

        return Response(response_data, status=status_code)

    def created_response(self, data, message='Zasób został utworzony pomyślnie'):
        return self.success_response(
            data=data,
            message=message,
            status_code=status.HTTP_201_CREATED
        )

    def deleted_response(self, message='Zasób został usunięty pomyślnie'):
        return self.success_response(
            message=message,
            status_code=status.HTTP_204_NO_CONTENT
        )


class CacheMixin:
    cache_timeout = 300

    def get_cache_key(self, *args):
        return ':'.join(str(arg) for arg in args)

    def get_from_cache(self, cache_key):
        from django.core.cache import cache
        return cache.get(cache_key)

    def set_to_cache(self, cache_key, value, timeout=None):
        from django.core.cache import cache
        timeout = timeout or self.cache_timeout
        cache.set(cache_key, value, timeout)

    def delete_from_cache(self, cache_key):
        from django.core.cache import cache
        cache.delete(cache_key)

    def clear_pattern_cache(self, pattern):
        from django.core.cache import cache
        cache.delete_pattern(pattern)