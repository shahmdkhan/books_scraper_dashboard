from rest_framework import serializers

from .models import Source, History, Detail


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = "__all__"


class HistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = History
        fields = "__all__"


class DetailSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Detail
        fields = ["detail_id", "image", "isbn", "name", "price", "condition", "seller", "url", "date_scraped",
                  "first_seen", "interest", "contact", ]

    def get_image(self, obj):
        """Return only the first image URL."""
        if isinstance(obj.images, list) and obj.images:
            return obj.images[0]
        return ""


class InterestUpdateSerializer(serializers.Serializer):
    """
    Validates the payload for PATCH /api/interest/<detail_id>/

    Accepted values:
        "interested"     — star clicked (was pending or not_interested)
        "not_interested" — dislike / X clicked
        "pending"        — reset to default
    """
    interest = serializers.ChoiceField(
        choices=[Detail.PENDING, Detail.INTERESTED, Detail.NOT_INTERESTED]
    )