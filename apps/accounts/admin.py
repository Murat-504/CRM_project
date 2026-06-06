from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.accounts.models import CustomUser
from apps.clients.models import Client, Contact, Comment, Document
from apps.requests_app.models import ClientRequest
from apps.deals.models import Deal
from apps.tasks.models import Task


# ── CustomUser ────────────────────────────────────────────────────────────────

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display  = ['username', 'get_full_name', 'email', 'role', 'department', 'is_active']
    list_filter   = ['role', 'is_active', 'department']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    fieldsets     = UserAdmin.fieldsets + (
        ('CRM', {'fields': ('role', 'phone', 'department', 'avatar', 'bio')}),
    )


# ── Clients ───────────────────────────────────────────────────────────────────

class ContactInline(admin.TabularInline):
    model  = Contact
    extra  = 0
    fields = ['full_name', 'position', 'phone', 'email', 'is_primary']


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display   = ['name', 'client_type', 'category', 'phone', 'manager', 'is_active', 'created_at']
    list_filter    = ['client_type', 'category', 'is_active', 'manager']
    search_fields  = ['name', 'phone', 'email', 'inn']
    inlines        = [ContactInline]
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']


# ── Requests ──────────────────────────────────────────────────────────────────

@admin.register(ClientRequest)
class ClientRequestAdmin(admin.ModelAdmin):
    list_display   = ['__str__', 'client', 'manager', 'status', 'priority', 'deadline', 'created_at']
    list_filter    = ['status', 'priority', 'request_type', 'manager']
    search_fields  = ['subject', 'client__name']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'closed_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'manager')


# ── Deals ─────────────────────────────────────────────────────────────────────

@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display   = ['name', 'client', 'manager', 'stage', 'amount', 'probability', 'created_at']
    list_filter    = ['stage', 'manager']
    search_fields  = ['name', 'client__name']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']


# ── Tasks ─────────────────────────────────────────────────────────────────────

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display   = ['title', 'assigned_to', 'status', 'priority', 'due_date', 'created_at']
    list_filter    = ['status', 'priority', 'assigned_to']
    search_fields  = ['title']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'completed_at']


# ── Comment / Document ────────────────────────────────────────────────────────
admin.site.register(Comment)
admin.site.register(Document)
