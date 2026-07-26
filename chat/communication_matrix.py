COMMUNICATION_MATRIX = {
    'student': {
        'can_chat_with': ['employer', 'supervisor', 'institution', 'coordinator'],
        'cannot_chat_with': ['student', 'admin'],
        'conditions': {
            'employer': 'Only after applying or by invitation',
            'supervisor': 'Only assigned supervisor',
            'institution': 'Only their institution',
            'coordinator': 'Only assigned coordinator',
        }
    },
    'employer': {
        'can_chat_with': ['employer', 'student', 'supervisor', 'coordinator', 'institution'],
        'cannot_chat_with': ['admin'],
        'conditions': {
            'employer': 'Only within same organization',
            'student': 'Only applicants or accepted interns',
            'supervisor': 'Only assigned supervisors',
            'coordinator': 'Only assigned coordinators',
            'institution': 'Only partner institutions',
        }
    },
    'supervisor': {
        'can_chat_with': ['student', 'employer', 'coordinator', 'institution', 'admin'],
        'cannot_chat_with': [],
        'conditions': {
            'student': 'Only assigned students',
            'employer': 'Only employers hosting their students',
            'coordinator': 'Only assigned coordinators',
            'institution': 'Only partner institutions',
            'admin': 'For support only',
        }
    },
    'coordinator': {
        'can_chat_with': ['student', 'employer', 'supervisor', 'institution', 'admin'],
        'cannot_chat_with': [],
        'conditions': {
            'student': 'Only assigned students',
            'employer': 'Only partner employers',
            'supervisor': 'Only assigned supervisors',
            'institution': 'Only partner institutions',
            'admin': 'For support only',
        }
    },
    'institution': {
        'can_chat_with': ['student', 'employer', 'supervisor', 'coordinator', 'admin'],
        'cannot_chat_with': [],
        'conditions': {
            'student': 'Only their students',
            'employer': 'Only partner employers',
            'supervisor': 'Only assigned supervisors',
            'coordinator': 'Only assigned coordinators',
            'admin': 'For support only',
        }
    },
    'admin': {
        'can_chat_with': ['student', 'employer', 'supervisor', 'coordinator', 'institution'],
        'cannot_chat_with': [],
        'conditions': {
            'student': 'Announcements & Support',
            'employer': 'Announcements & Support',
            'supervisor': 'Announcements & Support',
            'coordinator': 'Announcements & Support',
            'institution': 'Announcements & Support',
        }
    }
}


def get_user_role(user):
    try:
        from users.models import UserProfile
        profile = UserProfile.objects.get(user=user)
        return profile.role
    except:
        return None


def can_communicate(user1, user2):
    role1 = get_user_role(user1)
    role2 = get_user_role(user2)

    if not role1 or not role2:
        return False

    if role2 in COMMUNICATION_MATRIX.get(role1, {}).get('can_chat_with', []):
        return True

    if role1 in COMMUNICATION_MATRIX.get(role2, {}).get('can_chat_with', []):
        return True

    return False


def get_eligible_contacts(user):
    role = get_user_role(user)
    if not role:
        return []

    eligible_roles = COMMUNICATION_MATRIX.get(role, {}).get('can_chat_with', [])

    from django.contrib.auth.models import User
    from users.models import UserProfile

    eligible_users = []
    for user_role in eligible_roles:
        profiles = UserProfile.objects.filter(role=user_role)
        for profile in profiles:
            if profile.user != user:
                eligible_users.append(profile.user)

    return eligible_users


def get_communication_rules(user):
    role = get_user_role(user)
    if not role:
        return {}
    return COMMUNICATION_MATRIX.get(role, {})