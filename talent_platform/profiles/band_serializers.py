from rest_framework import serializers
from .models import Band, BandMembership, BandInvitation, TalentUserProfile


# Serializer for BandMembership model
class BandMembershipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='talent_user.user.username', read_only=True)
    email = serializers.CharField(source='talent_user.user.email', read_only=True)
    
    class Meta:
        model = BandMembership
        fields = ['id', 'username', 'email', 'role', 'position', 'date_joined']
        read_only_fields = ['id', 'date_joined']

# Note: BandMembershipCreateSerializer was removed as it's not used anywhere in the codebase
# Member creation is now handled through the band invitation system

# Serializer for Band model with minimal information
class BandListSerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(source='creator.user.username', read_only=True)
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Band
        fields = ['id', 'name', 'description', 'creator_name', 'member_count', 'profile_picture', 'band_type']
        read_only_fields = ['id', 'creator_name', 'member_count']
    
    def get_member_count(self, obj):
        return obj.members.count()

# Detailed serializer for Band model
class BandDetailSerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(source='creator.user.username', read_only=True)
    members = BandMembershipSerializer(source='bandmembership_set', many=True, read_only=True)
    class Meta:
        model = Band
        fields = [
            'id', 'name', 'description', 'creator_name', 'members',
            'profile_picture', 'contact_email', 'contact_phone', 'location', 'website',
            'created_at', 'updated_at', 'band_type'
        ]
        read_only_fields = ['id', 'creator_name', 'members', 'created_at', 'updated_at']

# Serializer for updating a band with member roles
class BandUpdateWithMembersSerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(source='creator.user.username', read_only=True)
    members = serializers.ListField(child=serializers.DictField(), required=False, write_only=True)
    members_data = BandMembershipSerializer(source='bandmembership_set', many=True, read_only=True)
    members_to_remove = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True)
    
    class Meta:
        model = Band
        fields = [
            'id', 'name', 'description', 'creator_name', 'members', 'members_data',
            'profile_picture', 'contact_email', 'contact_phone', 'location', 'website',
            'band_type', 'members_to_remove'
        ]
        read_only_fields = ['id', 'creator_name', 'members_data', 'band_type']
    
    def update(self, instance, validated_data):
        members_data = validated_data.pop('members', None)
        members_to_remove = validated_data.pop('members_to_remove', None)
        
        # Prevent band_type from being changed
        if 'band_type' in validated_data:
            validated_data.pop('band_type')
        
        # Update the band instance with the validated data
        instance = super().update(instance, validated_data)
        
        # Get the user profile
        user = self.context['request'].user
        try:
            admin_profile = TalentUserProfile.objects.get(user=user)
        except TalentUserProfile.DoesNotExist:
            raise serializers.ValidationError("Talent profile not found.")
        
        # Check if the user is the creator of the band
        is_creator = instance.creator == admin_profile
        if not is_creator:
            raise serializers.ValidationError("Only the band creator can update the band details and member roles.")
        
        # Track changes for response message
        removed_members = []
        updated_roles = []
        
        # If members to remove are provided, remove them from the band
        if members_to_remove is not None:
            for member_id in members_to_remove:
                try:
                    membership = BandMembership.objects.get(id=member_id, band=instance)
                    # Don't allow removing the creator
                    if membership.talent_user == instance.creator:
                        raise serializers.ValidationError("Cannot remove the band creator from the band.")
                    
                    # Store member info before deletion
                    removed_members.append({
                        'id': membership.id,
                        'username': membership.talent_user.user.username
                    })
                    
                    membership.delete()
                except BandMembership.DoesNotExist:
                    # Skip non-existent memberships without error
                    continue
        
        # If members data is provided, update member roles
        if members_data is not None:
            # Process each member's role update
            for member_data in members_data:
                member_id = member_data.get('id')
                new_role = member_data.get('role')
                
                # Skip if required fields are missing
                if not member_id or not new_role:
                    continue
                
                # Validate role value
                if new_role not in ['admin', 'member']:
                    raise serializers.ValidationError("Invalid role. Must be 'admin' or 'member'.")
                
                # Find the membership record
                try:
                    membership = BandMembership.objects.get(id=member_id, band=instance)
                except BandMembership.DoesNotExist:
                    raise serializers.ValidationError(f"Member with ID {member_id} not found in this band.")
                
                # Don't allow changing the creator's role
                if membership.talent_user == instance.creator:
                    raise serializers.ValidationError("Cannot change the band creator's role.")
                
                # Skip if role is not changing
                if membership.role == new_role:
                    continue
                
                # Check if we're promoting to admin and if that's allowed
                if new_role == 'admin' and membership.role != 'admin':
                    if not instance.can_add_admin():
                        max_admins = instance.get_max_admins()
                        current_admins = instance.bandmembership_set.filter(role='admin').count()
                        raise serializers.ValidationError(
                            f"Maximum number of admins ({max_admins}) reached for this band. "
                            f"Current admin count: {current_admins}. "
                            f"Band size: {instance.member_count} members."
                        )
                
                # Store old role for tracking changes
                old_role = membership.role
                
                # Update the role
                membership.role = new_role
                membership.save()
                
                # Track the change
                updated_roles.append({
                    'id': membership.id,
                    'username': membership.talent_user.user.username,
                    'old_role': old_role,
                    'new_role': new_role
                })
        
        # Add change tracking to instance for access in the view
        instance._removed_members = removed_members
        instance._updated_roles = updated_roles
        
        return instance
    
    def validate_members(self, value):
        """Validate the members data structure"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Members data must be a list.")
            
        for i, member in enumerate(value):
            if not isinstance(member, dict):
                raise serializers.ValidationError(f"Member at position {i} must be an object.")
                
            if 'id' not in member:
                raise serializers.ValidationError(f"Member at position {i} is missing the 'id' field.")
                
            if 'role' not in member:
                raise serializers.ValidationError(f"Member at position {i} is missing the 'role' field.")
                
            if member.get('role') not in ['admin', 'member']:
                raise serializers.ValidationError(f"Role for member at position {i} must be either 'admin' or 'member'.")
                
        return value
    
    def validate_members_to_remove(self, value):
        """Validate the members to remove"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Members to remove must be a list of IDs.")
            
        # Check for duplicate IDs
        if len(value) != len(set(value)):
            raise serializers.ValidationError("The list of members to remove contains duplicate IDs.")
            
        return value

# Serializer for creating a band
class BandCreateSerializer(serializers.ModelSerializer):
    band_type = serializers.CharField(required=False)
    
    class Meta:
        model = Band
        fields = [
            'name', 'description', 'profile_picture',
            'contact_email', 'contact_phone', 'location', 'website', 'band_type'
        ]
    
    def validate(self, data):
        """Validate that user has bands subscription for creating bands"""
        user = self.context['request'].user
        
        # Check if user has bands subscription (required for creating bands)
        from payments.models import Subscription
        has_bands_subscription = Subscription.objects.filter(
            user=user,
            plan__name='bands',
            is_active=True,
            status='active'
        ).exists()
        
        if not has_bands_subscription:
            raise serializers.ValidationError(
                "You need an active Bands subscription to create a band. "
                "You can join existing bands for free, or subscribe to the Bands plan to create your own band."
            )
        
        return data
    
    def create(self, validated_data):
        # Get the user from the context
        user = self.context['request'].user
        
        # Get the talent profile
        try:
            talent_profile = TalentUserProfile.objects.get(user=user)
        except TalentUserProfile.DoesNotExist:
            raise serializers.ValidationError("Talent profile not found.")
        
        # Check if user is already in any band (one band only rule)
        existing_membership = BandMembership.objects.filter(talent_user=talent_profile).first()
        if existing_membership:
            raise serializers.ValidationError(f"You are already a member of '{existing_membership.band.name}'. Users can only be in one band at a time. Leave your current band first to create a new one.")
        
        # Check if user already has a band (as creator) - redundant but keeping for clarity
        if Band.objects.filter(creator=talent_profile).exists():
            raise serializers.ValidationError("You can only create one band per user.")
        
        # Create the band with the user as creator
        band = Band.objects.create(
            creator=talent_profile,
            **validated_data
        )
        
        # Add the creator as an admin member
        BandMembership.objects.create(
            talent_user=talent_profile,
            band=band,
            role='admin',
            position='Creator'
        )
        
        return band

# Note: BandInvitationCreateSerializer was removed as it's not used anywhere in the codebase
# Invitation creation is now handled directly in the GenerateBandInvitationView

# Serializer for using band invitations
class BandInvitationUseSerializer(serializers.Serializer):
    invitation_code = serializers.CharField(max_length=8)
    
    def validate(self, data):
        invitation_code = data.get('invitation_code')
        
        # Check if invitation exists
        try:
            invitation = BandInvitation.objects.get(invitation_code=invitation_code)
        except BandInvitation.DoesNotExist:
            raise serializers.ValidationError("Invalid invitation code.")
        
        # Check if invitation is still valid
        if not invitation.is_valid():
            if invitation.is_used:
                raise serializers.ValidationError("This invitation code has already been used.")
            else:
                raise serializers.ValidationError("This invitation code has expired.")
        
        # Add the invitation to the validated data
        data['invitation'] = invitation
        return data


# Serializer for displaying band invitations
class BandInvitationSerializer(serializers.ModelSerializer):
    band_name = serializers.CharField(source='band.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.user.username', read_only=True)
    is_valid = serializers.SerializerMethodField()
    used_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = BandInvitation
        fields = ['id', 'band', 'band_name', 'created_by_name', 'invitation_code', 
                 'created_at', 'expires_at', 'is_used', 'position', 'is_valid',
                 'status', 'used_by_name']
        read_only_fields = ['id', 'band_name', 'created_by_name', 'invitation_code', 
                           'created_at', 'expires_at', 'is_used', 'is_valid',
                           'used_by_name']
    
    def get_is_valid(self, obj):
        return obj.is_valid()
    
    def get_used_by_name(self, obj):
        if obj.used_by:
            return obj.used_by.user.email
        return None

# Main serializer for Band model
class BandSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    creator_name = serializers.SerializerMethodField()
    profile_score = serializers.SerializerMethodField()
    
    class Meta:
        model = Band
        fields = [
            'id', 'name', 'description', 'band_type', 'profile_picture',
            'contact_email', 'contact_phone', 'location', 'website',
            'creator_name', 'members', 'created_at', 'updated_at', 'profile_score'
        ]
        read_only_fields = ['id', 'creator_name', 'created_at', 'updated_at']
    
    def get_members(self, obj):
        memberships = BandMembership.objects.filter(band=obj).select_related('talent_user__user')
        return BandMembershipSerializer(memberships, many=True).data
    
    def get_creator_name(self, obj):
        if obj.creator and hasattr(obj.creator, 'user'):
            user = obj.creator.user
            if user.first_name and user.last_name:
                return f"{user.first_name} {user.last_name}"
            return user.email
        return "Unknown"
        
    def get_profile_score(self, obj):
        """Get the profile score from the model's method"""
        return obj.get_profile_score()

