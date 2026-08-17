from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "success": True,
                "data": data,
                "meta": {
                    "count": self.page.paginator.count,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "page_size": self.get_page_size(self.request),
                },
            }
        )

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "example": True},
                "data": schema,
                "meta": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer", "example": 42},
                        "next": {"type": "string", "nullable": True, "format": "uri"},
                        "previous": {"type": "string", "nullable": True, "format": "uri"},
                        "page_size": {"type": "integer", "example": 20},
                    },
                },
            },
        }
