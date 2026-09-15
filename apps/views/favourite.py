from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import Favorite, Listing


@extend_schema(summary="Sevimli e'lonlar ID ro'yxati", tags=["Favourites"])
class FavouriteListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ids = Favorite.objects.filter(user=request.user).values_list("listing_id", flat=True)
        return Response([str(i) for i in ids])


@extend_schema(summary="Sevimlilarga qo'shish/o'chirish", tags=["Favourites"])
class FavouriteToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        listing = get_object_or_404(Listing, pk=product_id)
        Favorite.objects.get_or_create(user=request.user, listing=listing)
        return Response(status=204)

    def delete(self, request, product_id):
        Favorite.objects.filter(user=request.user, listing_id=product_id).delete()
        return Response(status=204)
