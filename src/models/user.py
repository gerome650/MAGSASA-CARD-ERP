from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from src.database import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="farmer")  # Simple role as string
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(
            password, method="pbkdf2:sha256", salt_length=16
        )

    def check_password(self, password):
        """Check if the provided password matches the user's password"""
        return check_password_hash(self.password_hash, password)

    def get_permissions(self):
        """Get all permissions for this user based on their role"""
        # Simple role-based permissions
        if self.role == "admin":
            return ["all"]
        elif self.role == "manager":
            return ["view_farmers", "manage_loans", "view_reports"]
        elif self.role == "officer":
            return ["view_farmers", "create_loans", "update_farmers"]
        elif self.role == "farmer":
            return ["view_own_loans", "make_payments"]
        return []

    def has_permission(self, permission_name):
        """Check if the user has a specific permission"""
        permissions = self.get_permissions()
        return "all" in permissions or permission_name in permissions

    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    role_permissions = db.relationship(
        "RolePermission", backref="role", cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Convert role object to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "permissions": [rp.permission.name for rp in self.role_permissions],
        }


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    module = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(20), nullable=False)  # CREATE, READ, UPDATE, DELETE
    description = db.Column(db.Text)

    def to_dict(self):
        """Convert permission object to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "module": self.module,
            "action": self.action,
            "description": self.description,
        }


class RolePermission(db.Model):
    __tablename__ = "role_permissions"

    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), primary_key=True)
    permission_id = db.Column(
        db.Integer, db.ForeignKey("permissions.id"), primary_key=True
    )

    # Relationships
    permission = db.relationship("Permission", backref="role_permissions")
