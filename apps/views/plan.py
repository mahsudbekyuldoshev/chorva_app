from drf_spectacular.utils import extend_schema
from rest_framework import generics

from apps.models import Plan
from apps.serializers.plan import PlanSerializer


@extend_schema(summary="Tarif rejalari ro'yxati", responses={200: PlanSerializer(many=True)}, tags=["Plans"])
class PlanListView(generics.ListAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = []
    pagination_class = None
