from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUserModel, DeleteAccuntsList, UserProfile


class CustomUserAdmin(UserAdmin):
    """
    Custom admin for the CustomUser model
    """
    model = CustomUserModel
    list_display = ('email', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

from django.contrib import admin
from .models import UserProfile

class CustomUserProfileAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'district', 'upozila', 'city', 'profile_image_tag', 'created_at', 'updated_at')
    list_filter = ('district', 'upozila', 'city', 'created_at')
    search_fields = ('user__email', 'first_name', 'last_name', 'phone_number')
    ordering = ('user__email',)
    readonly_fields = ('created_at', 'updated_at', 'profile_image_tag')
    
    def email(self, obj):
        return obj.user.email
    
    email.short_description = 'Email'
    email.admin_order_field = 'user__email'
    
    def profile_image_tag(self, obj):
        from django.utils.html import format_html
        if obj.profile_image:
            return format_html('<img src="{}" width="50" height="50" />', obj.profile_image.url)
        return "No Image"
    profile_image_tag.short_description = 'Profile Image'

class DeleteAccuntsListAdmin(admin.ModelAdmin):
    models = DeleteAccuntsList
    list_display = ('email', 'delete_at')
    list_filter = ('delete_at',)

    ordering = ('-delete_at',)


admin.site.register(CustomUserModel, CustomUserAdmin)
admin.site.register(UserProfile, CustomUserProfileAdmin)
admin.site.register(DeleteAccuntsList, DeleteAccuntsListAdmin)