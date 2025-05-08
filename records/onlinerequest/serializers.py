from onlinerequest.models import Document, Request, Record, Purpose
from rest_framework import serializers

class PurposeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purpose
        fields = ['id', 'description', 'active']

class RequestSerializer(serializers.ModelSerializer):
    document = serializers.CharField()
    purpose = serializers.SerializerMethodField()

    class Meta:
        model = Request
        fields = ['id', 'description', 'files_required', 'document', 'purpose', 'price', 'active']

    def get_purpose(self, obj):
        purposes = Purpose.objects.filter(active=True)
        purpose_serializer = PurposeSerializer(purposes, many=True)
        return purpose_serializer.data

class RecordSerializer(serializers.ModelSerializer):
    user_number = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    middle_name = serializers.CharField(required=False, allow_blank=True)
    course_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    contact_no = serializers.CharField(required=False, allow_blank=True)
    entry_year_from = serializers.IntegerField(required=False, allow_null=True)
    entry_year_to = serializers.IntegerField(required=False, allow_null=True)

    def validate_user_number(self, value):
        if not value:
            raise serializers.ValidationError("Please enter student number.")
        
        if len(value) < 9:
            raise serializers.ValidationError("Please enter 10-digit student number.")
        
        # Check if user-number is already taken
        if value:
            record = Record.objects.filter(user_number = value)

            if record:
                raise serializers.ValidationError("Student already taken.")

        return value
    
    def validate_first_name(self, value):
        if not value:
            raise serializers.ValidationError("Please enter first name.")
        return value
          
    def validate_last_name(self, value):
        if not value:
            raise serializers.ValidationError("Please enter last name.")
        return value
        
    def validate_contact_no(self, value):
        if not value:
            raise serializers.ValidationError("Please enter the contact number.")
        
        if value:
            first_two_digits = str(value)[:2]

            if first_two_digits != "09":
                raise serializers.ValidationError("Please enter a valid contact number.")
        return value

    def validate_course_code(self, value):
        if not value:
            raise serializers.ValidationError("Please specify user course code")    
        return value
        
    def create(self, validated_data):
        return Record.objects.create(**validated_data)

    class Meta:
        model = Record
        fields = ['user_number', 'first_name', 'last_name', 'course_code', 'middle_name', 'contact_no', 'entry_year_from', 'entry_year_to']

