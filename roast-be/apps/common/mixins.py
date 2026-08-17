from rest_framework.response import Response


class EnvelopeMixin:
    """
    Wraps every successful JSON response in the project's standard envelope:
        {"success": true, "data": <payload>, "meta": {...}}
    Paginated responses already produce this shape themselves (see
    StandardResultsSetPagination) and are left untouched. Non-JSON
    responses (e.g. streaming file downloads) are also left untouched
    since the envelope only applies to JSON API responses.
    """

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if (
            isinstance(response, Response)
            and response.exception is False
            and response.data is not None
            and response.status_code != 204
            and not (isinstance(response.data, dict) and "success" in response.data)
        ):
            response.data = {"success": True, "data": response.data, "meta": {}}
        return response
