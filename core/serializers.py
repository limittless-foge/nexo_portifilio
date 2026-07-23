from rest_framework import serializers

class EngagementDataSerializer(serializers.Serializer):
    date = serializers.DateField(format='%Y-%m-%d')
    score = serializers.IntegerField()

class ServiceDataSerializer(serializers.Serializer):
    category = serializers.CharField()
    count = serializers.IntegerField()

class ClientAnalyticsSerializer(serializers.Serializer):
    client_name = serializers.CharField()
    registration_date = serializers.DateTimeField(format='%Y-%m-%d')
    project_lead_assigned = serializers.BooleanField()
    current_step = serializers.IntegerField()
    services_selected_status = serializers.CharField()
    team_assignment_status = serializers.CharField()
    kickoff_call_status = serializers.CharField()
    deliverables_begin_status = serializers.CharField()
    progress_percentage = serializers.IntegerField()
    engagement_data = EngagementDataSerializer(many=True)
    service_data = ServiceDataSerializer(many=True)
