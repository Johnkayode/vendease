from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from api.apps.products.models import Product


class ProductSerializer(serializers.ModelSerializer):
    amount_available = serializers.IntegerField(min_value=1)
    
    class Meta:
        model = Product
        fields = ('id', 'name', 'cost', 'amount_available')
        read_only_fields = ('id', 'created_at', 'seller')

    def validate_cost(self, value):
        if not value % 5 == 0:
            raise serializers.ValidationError(
                _("Cost must be in multiples of 5.")
            )
        return value   
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        validated_data['seller'] = self.context['request'].user
        return validated_data

    def create(self, validated_data):
        return super().create(validated_data)


class BuyProductSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_product(self, value):
        try:
            product = Product.objects.get(id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError(
                _("Product with the given ID does not exist.")
            )
        return product
