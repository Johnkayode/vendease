from django.db import transaction
from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response
from api.apps.users.models import User
from api.apps.products.models import Product
from api.apps.users.permissions import IsBuyer, IsSeller, IsProductOwner
from api.apps.products.serializers import ProductSerializer, BuyProductSerializer
from api.apps.products.utils import amount_to_denominations


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    def get_permissions(self):
        """
        GET requests can be made by anyone authenticated.
        POST requires seller role.
        PUT/DELETE require seller role and ownership.
        """
        if self.action == 'list' or self.action == 'retrieve':
            return [permissions.IsAuthenticated()]
        elif self.action == 'create':
            return [IsSeller()]
        else:  
            return [IsProductOwner()]
    
    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)


class BuyProductView(generics.GenericAPIView):
    queryset = Product.objects.all()
    permission_classes = [IsBuyer]
    serializer_class = BuyProductSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
    
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']

        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=product.pk)
            user = User.objects.select_for_update().get(pk=request.user.pk)
        
            if product.amount_available < quantity:
                return Response(
                    {'detail': f'Only {product.amount_available} items available.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            total_cost = product.cost * quantity
            
            # check sufficient funds
            if user.deposit < total_cost:
                return Response(
                    {
                        'detail': 'Insufficient funds.',
                        'required': total_cost,
                        'available': user.deposit,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        
            change_amount = user.deposit - total_cost
            change = amount_to_denominations(change_amount)
        
            
            product.amount_available -= quantity
            product.save(update_fields=['amount_available'])
        
            user.deposit = 0
            user.save(update_fields=['deposit'])
    
        response_data = {
            'total_spent': total_cost,
            'product_name': product.name,
            'quantity': quantity,
            'change': change
        }
    
        return Response(response_data, status=status.HTTP_200_OK)

        