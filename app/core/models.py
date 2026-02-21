from .database import Base
# In deiner core/database.py oder models.py ergänzen:
# Ein User-Model könnte so aussehen:

ENTITY_TYPE_USER = "User"
"""
{
    "username": "admin",
    "email": "admin@local.host",
    "roles": ["superadmin"],
    "groups": ["it-dept"],
    "identities": {
        "local": {"uid": "1"},
        "ldap": {"dn": "cn=admin,dc=example,dc=org"}
    }
}
"""