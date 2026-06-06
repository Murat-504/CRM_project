from rest_framework import serializers
from apps.accounts.models import CustomUser
from apps.clients.models import Client, Contact, Comment, Document
from apps.requests_app.models import ClientRequest
from apps.deals.models import Deal
from apps.tasks.models import Task


# ─── Users ────────────────────────────────────────────────────────────────────

class UserMinimalSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'email', 'role', 'avatar']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'first_name', 'last_name',
                  'email', 'role', 'phone', 'department', 'avatar', 'date_joined']
        read_only_fields = ['date_joined']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


# ─── Comment ──────────────────────────────────────────────────────────────────

class CommentSerializer(serializers.ModelSerializer):
    author = UserMinimalSerializer(read_only=True)
    interaction_type_display = serializers.CharField(
        source='get_interaction_type_display', read_only=True
    )

    class Meta:
        model = Comment
        fields = ['id', 'author', 'text', 'interaction_type', 'interaction_type_display',
                  'created_at', 'content_type', 'object_id']
        read_only_fields = ['author', 'created_at']


# ─── Document ─────────────────────────────────────────────────────────────────

class DocumentSerializer(serializers.ModelSerializer):
    author = UserMinimalSerializer(read_only=True)
    doc_type_display = serializers.CharField(source='get_doc_type_display', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['id', 'title', 'doc_type', 'doc_type_display', 'file', 'file_url',
                  'author', 'uploaded_at', 'content_type', 'object_id']
        read_only_fields = ['author', 'uploaded_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


# ─── Contact ──────────────────────────────────────────────────────────────────

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'client', 'full_name', 'position', 'phone',
                  'email', 'is_primary', 'notes', 'created_at']
        read_only_fields = ['created_at']


# ─── Client ───────────────────────────────────────────────────────────────────

class ClientListSerializer(serializers.ModelSerializer):
    """Лёгкий сериализатор для списка клиентов."""
    manager = UserMinimalSerializer(read_only=True)
    manager_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), source='manager', write_only=True,
        required=False, allow_null=True
    )
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    client_type_display = serializers.CharField(source='get_client_type_display', read_only=True)
    open_requests_count = serializers.IntegerField(read_only=True, default=0)
    active_deals_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Client
        fields = ['id', 'name', 'client_type', 'client_type_display', 'category',
                  'category_display', 'phone', 'email', 'manager', 'manager_id',
                  'is_active', 'created_at', 'open_requests_count', 'active_deals_count']


class ClientDetailSerializer(serializers.ModelSerializer):
    """Полный сериализатор для карточки клиента."""
    manager = UserMinimalSerializer(read_only=True)
    manager_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), source='manager', write_only=True,
        required=False, allow_null=True
    )
    contacts = ContactSerializer(many=True, read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    client_type_display = serializers.CharField(source='get_client_type_display', read_only=True)

    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# ─── ClientRequest ────────────────────────────────────────────────────────────

class ClientRequestSerializer(serializers.ModelSerializer):
    manager = UserMinimalSerializer(read_only=True)
    manager_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), source='manager', write_only=True,
        required=False, allow_null=True
    )
    client_name = serializers.CharField(source='client.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    priority_color = serializers.CharField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = ClientRequest
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'closed_at']


class ClientRequestStatusSerializer(serializers.ModelSerializer):
    """Только смена статуса (для Kanban drag-and-drop)."""
    class Meta:
        model = ClientRequest
        fields = ['status']


# ─── Deal ─────────────────────────────────────────────────────────────────────

class DealSerializer(serializers.ModelSerializer):
    manager = UserMinimalSerializer(read_only=True)
    manager_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), source='manager', write_only=True,
        required=False, allow_null=True
    )
    client_name = serializers.CharField(source='client.name', read_only=True)
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    weighted_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )

    class Meta:
        model = Deal
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class DealFunnelSerializer(serializers.Serializer):
    """Данные воронки продаж для Chart.js."""
    stage = serializers.CharField()
    stage_display = serializers.CharField()
    count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    weighted_amount = serializers.DecimalField(max_digits=14, decimal_places=2)


# ─── Task ─────────────────────────────────────────────────────────────────────

class TaskSerializer(serializers.ModelSerializer):
    assigned_to = UserMinimalSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), source='assigned_to', write_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'completed_at', 'created_by']
