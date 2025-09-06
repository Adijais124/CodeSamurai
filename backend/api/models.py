from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser, Group, Permission

# -------------------------------
# 1. Custom User Model
# -------------------------------
class CustomUser(AbstractUser):
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  # changed from default 'user_set'
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',  # changed from default 'user_set'
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    def __str__(self):
        return self.username

# -------------------------------
# 2. Product Model
# -------------------------------
CATEGORY_CHOICES = [
    ('Electronics', 'Electronics'),
    ('Clothing', 'Clothing'),
    ('Books', 'Books'),
    ('Home', 'Home'),
    ('Other', 'Other'),
]

class Product(models.Model):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# -------------------------------
# 3. Cart & CartItem Models
# -------------------------------
class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username}'s Cart"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    # Optional: store snapshot info for easy access
    product_name = models.CharField(max_length=100, blank=True)
    seller_name = models.CharField(max_length=150, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        # auto-fill snapshot info
        if self.product:
            self.product_name = self.product.title
            self.seller_name = self.product.owner.username
            self.amount = self.product.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} in {self.cart.user.username}'s Cart"

# -------------------------------
# 4. Buyer & Seller Purchase History
# -------------------------------
class BuyerPurchaseHistory(models.Model):
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='buyer_history')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    seller = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='sold_to_buyers')
    purchased_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.product and not self.seller:
            self.seller = self.product.owner
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.buyer.username} bought {self.product.title if self.product else 'Deleted Product'} from {self.seller.username if self.seller else 'Unknown'}"

class SellerPurchaseHistory(models.Model):
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='seller_history')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    sold_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='purchased_products')
    sold_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.seller.username} sold {self.product.title if self.product else 'Deleted Product'} to {self.sold_to.username if self.sold_to else 'Unknown'}"

# -------------------------------
# 5. Review Model
# -------------------------------
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews_made')
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.buyer.username} rated {self.product.title} ({self.rating}⭐)"

    @staticmethod
    def get_average_rating(product):
        reviews = product.reviews.all()
        if reviews.exists():
            return round(sum([r.rating for r in reviews]) / reviews.count(), 2)
        return 0
