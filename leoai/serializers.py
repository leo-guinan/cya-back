from rest_framework import serializers

from leoai.models import Collection, Item, FactItem, Facts


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ('id', 'collection', 'name', 'link', 'description', 'recommendation', 'uuid', 'created_at', 'updated_at')
class CollectionSerializer(serializers.ModelSerializer):
    items = ItemSerializer(many=True, read_only=True)
    class Meta:
        model = Collection
        fields = ('id', 'name', 'description', 'created_at', 'updated_at', 'items')

class FactItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactItem
        fields = ('id', 'question', 'answer', 'uuid', 'created_at', 'updated_at')

class FactsSerializer(serializers.ModelSerializer):
    items = FactItemSerializer(many=True, read_only=True)
    class Meta:
        model = Facts
        fields = ('id', 'name', 'description', 'created_at', 'updated_at', 'items')