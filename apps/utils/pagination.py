from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class BarePagination(LimitOffsetPagination):
    """
    limit/offset query parametrlarini qo'llab-quvvatlaydi, lekin
    javobni count/next/previous'siz, TO'G'RIDAN-TO'G'RI massiv
    sifatida qaytaradi — mobil ilova shu shaklni kutadi.
    """
    default_limit = 20
    max_limit = 100

    def get_paginated_response(self, data):
        return Response(data)
