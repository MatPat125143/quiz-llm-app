from django.core.paginator import Paginator


def _get_request_params(request):
    params = getattr(request, 'query_params', None)
    if params is None:
        params = request.GET
    return params


def paginate_queryset(request, queryset, default_size=20, max_size=None):
    params = _get_request_params(request)
    try:
        page = int(params.get('page', 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(params.get('page_size', default_size))
    except (TypeError, ValueError):
        page_size = default_size
    if max_size is not None:
        page_size = min(page_size, max_size)
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    return paginator, page_obj, page_size
