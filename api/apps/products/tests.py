import json
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from api.apps.products.models import Product
from api.apps.products.utils import amount_to_denominations

User = get_user_model()


class UtilsTestCase(TestCase):
    """Test utility functions."""

    def setUp(self):
        self.to_change = amount_to_denominations
    
    def test_calculate_change_exact(self):
        """Test change calculation with exact denominations."""
        self.assertEqual(self.to_change(100), [100])
        self.assertEqual(self.to_change(50), [50])
        self.assertEqual(self.to_change(5), [5])
    
    def test_calculate_change_mixed(self):
        """Test change calculation with mixed denominations."""
        result = self.to_change(85)
        self.assertEqual(result, [50, 20, 10, 5])
        
        result = self.to_change(195)
        self.assertEqual(result, [100, 50, 20, 20, 5])
    
    def test_calculate_change_zero(self):
        """Test change calculation with zero amount."""
        self.assertEqual(self.to_change(0), [])


class ProductTestCase(TestCase):
    """
    Test products: create, read, update, and buy.
    """
    def setUp(self):
        self.client = APIClient()
        self.create_url = reverse("product-list")

        self.seller = User.objects.create_user(
            username="test_seller",
            password="StrongPassword123!",  # noqa: S106
            role="seller"
        )
        self.buyer = User.objects.create_user(
            username="test_buyer",
            password="StrongPassword123!",  # noqa: S106
            role="buyer"
        )
        self.payload = {
            "name": "Test Product",
            "cost": 50,
            "amount_available": 10
        }
            
    def test_create_valid_product(self):
        """Test logging in with valid credentials"""
        self.client.force_authenticate(user=self.seller)
        response = self.client.post(
            self.create_url, data=json.dumps(self.payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.all().count(), 1)

    def test_list_products_authenticated(self):
        """Test listing products as authenticated user."""
        self.client.force_authenticate(user=self.buyer)
        response = self.client.get(reverse('product-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

        Product.objects.create(name="Test Product", cost=50, amount_available=10, seller=self.seller)

        response = self.client.get(reverse('product-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_create_product_invalid_cost(self):
        """Test create product negative cost that's not a multiple of 5"""
        self.client.force_authenticate(user=self.seller)
        self.payload["cost"] = 102
        response = self.client.post(
            self.create_url, data=json.dumps(self.payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_invalid_amount(self):
        """Test create product with negative amount available"""
        self.client.force_authenticate(user=self.seller)
        self.payload["amount_available"] = -50
        response = self.client.post(
            self.create_url, data=json.dumps(self.payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_buyer(self):
        self.client.force_authenticate(user=self.buyer)
        response = self.client.post(
            self.create_url, data=json.dumps(self.payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_buy_product_insufficient_funds(self):
        self.client.force_authenticate(user=self.seller)
        response = self.client.post(
            self.create_url, data=json.dumps(self.payload), content_type="application/json"
        )

        self.client.force_authenticate(user=self.buyer)
        self.buyer.deposit = 10
        self.buyer.save()

        url = reverse("buy_product")
        payload = {"quantity": 5, "product": response.data["id"]}
        response = self.client.post(
            url, data=json.dumps(payload), content_type="application/json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_buy_missing_product(self):
        self.client.force_authenticate(user=self.seller)
        response = self.client.post(
            self.create_url, data=json.dumps(self.payload), content_type="application/json"
        )

        self.client.force_authenticate(user=self.buyer)
        self.buyer.deposit = 10
        self.buyer.save()

        url = reverse("buy_product")
        payload = {"quantity": 20, "product": 5}
        response = self.client.post(
            url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_buy_product_insufficient_stock(self):
        self.client.force_authenticate(user=self.seller)
        response = self.client.post(
            self.create_url, data=json.dumps(self.payload), content_type="application/json"
        )

        self.client.force_authenticate(user=self.buyer)
        self.buyer.deposit = 10
        self.buyer.save()

        url = reverse("buy_product")
        payload = {"quantity": 20, "product": response.data["id"]}
        response = self.client.post(
            url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_buy_product(self):
        self.client.force_authenticate(user=self.seller)
        response = self.client.post(
            self.create_url, data=json.dumps(self.payload), content_type="application/json"
        )

        self.client.force_authenticate(user=self.buyer)
        self.buyer.deposit = 165
        self.buyer.save()

        url = reverse("buy_product")
        payload = {"product": response.data["id"], "quantity": 2}
        response = self.client.post(
            url, data=json.dumps(payload), content_type="application/json"
        )
 
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_spent"], 50*2)
        self.assertEqual(response.data["change"], [50, 10, 5])

    def test_update_own_product(self):
        """Test updating own product as seller."""
        product = Product.objects.create(
            name="Test Product", cost=100, 
            amount_available=1, seller=self.seller
        )

        self.assertEqual(product.cost, 100)
        self.assertEqual(product.amount_available, 1)

        self.client.force_authenticate(user=self.seller)
        response = self.client.put(
            reverse('product-detail', args=[product.id]),
            self.payload
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product.refresh_from_db()

        self.assertEqual(product.cost, 50)
        self.assertEqual(product.amount_available, 10)
    
    def test_update_other_seller_product(self):
        """Test updating another seller's product (should fail)."""
        product = Product.objects.create(
            name="Test Product", cost=100, 
            amount_available=1, seller=self.seller
        )
        other_seller = User.objects.create_user(
            username='seller2',
            password='pass123',
            role='seller'
        )

        self.client.force_authenticate(user=other_seller)
        response = self.client.put(
            reverse('product-detail', args=[product.id]),
            self.payload
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_own_product(self):
        """Test deleting own product as seller."""
        self.client.force_authenticate(user=self.seller)
        product = Product.objects.create(
            name="Test Product", cost=100, 
            amount_available=1, seller=self.seller
        )
        response = self.client.delete(
            reverse('product-detail', args=[product.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 0)