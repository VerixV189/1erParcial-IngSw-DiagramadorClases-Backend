from datetime import datetime, timezone
from sqlalchemy import JSON, UUID, Text, DateTime, ForeignKey, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import db
import uuid

# Define una clase base abstracta para todos los modelos
class BaseModel(db.Model):
    __abstract__ = True
    
    # Columnas compartidas por todos los modelos
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def soft_delete(self):
        """Marca el registro como eliminado lógicamente"""
        self.is_deleted = True
        db.session.flush()

    @classmethod
    def get_active(cls):
        """Filtra solo registros no eliminados"""
        return cls.query.filter_by(is_deleted=False)

# Modelo para la tabla 'users'
class Users(BaseModel):
    __tablename__ = 'users'
    name: Mapped[str] = mapped_column(Text, nullable=False)
    username: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(Text, nullable=False)

    # Relación con la bitácora
    # Corregido: 'back_populates' debe ser "user_entry" para que coincida con la propiedad en BitacoraUsers
    bitacora_entries: Mapped[list["BitacoraUsers"]] = relationship(back_populates="user_entry", cascade="all, delete-orphan")

    # Relación con proyectos (un usuario puede tener varios proyectos)
    projects: Mapped[list["Project"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<User {self.username}>'

# Modelo para la tabla 'bitacora_users'
class BitacoraUsers(BaseModel):
    __tablename__ = 'bitacora_users'
    ip: Mapped[str] = mapped_column(Text, nullable=False)
    tipo_accion: Mapped[str] = mapped_column(Text, nullable=False)
    # Se añade la clave foránea que apunta a la tabla 'users'
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Crea una relación para acceder fácilmente al objeto Usuario
    # Corregido: 'back_populates' debe ser "bitacora_entries" para que coincida con la propiedad en Users
    user_entry: Mapped["Users"] = relationship(back_populates="bitacora_entries")

    def __repr__(self):
        return f'<BitacoraUser {self.tipo_accion}>'

# Modelo para la tabla 'projects'
class Project(BaseModel):
    __tablename__ = 'projects'
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # Corregido: La clave foránea apunta a la tabla 'users'
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    diagram_data: Mapped[dict] = mapped_column(JSON, default=lambda: {})

    # Relación con Usuario (un proyecto pertenece a un usuario)
    user: Mapped["Users"] = relationship("Users", back_populates="projects")

    # Relaciones con Classes y Relationships (un proyecto tiene muchas clases y relaciones)
    classes: Mapped[list["Class"]] = relationship("Class", back_populates="project", cascade="all, delete-orphan")
    relationships: Mapped[list["Relationship"]] = relationship(back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Project {self.name}>'

# Modelo para la tabla 'classes'
class Class(BaseModel):
    __tablename__ = 'classes'
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    stereotype: Mapped[str] = mapped_column(Text, nullable=True)
    attributes: Mapped[list] = mapped_column(JSON, default=lambda: [])
    methods: Mapped[list] = mapped_column(JSON, default=lambda: [])
    position: Mapped[dict] = mapped_column(JSON, default=lambda: {"x": 0, "y": 0})

    # Relación con Project
    project: Mapped["Project"] = relationship("Project", back_populates="classes")

    # Relaciones para Source y Target Relationships
    source_relationships: Mapped[list["Relationship"]] = relationship(
        "Relationship", foreign_keys="[Relationship.source_class_id]", back_populates="source_class", cascade="all, delete-orphan"
    )
    target_relationships: Mapped[list["Relationship"]] = relationship(
        "Relationship", foreign_keys="[Relationship.target_class_id]", back_populates="target_class", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f'<Class {self.name}>'

# Modelo para la tabla 'relationships'
class Relationship(BaseModel):
    __tablename__ = 'relationships'
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    source_class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('classes.id', ondelete='CASCADE'), nullable=False)
    target_class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('classes.id', ondelete='CASCADE'), nullable=False)
    relationship_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_multiplicity: Mapped[str] = mapped_column(Text, nullable=True)
    target_multiplicity: Mapped[str] = mapped_column(Text, nullable=True)
    label: Mapped[str] = mapped_column(Text, nullable=True)

    # Relación con Project
    project: Mapped["Project"] = relationship("Project", back_populates="relationships")

    # Relaciones con Class para source y target
    source_class: Mapped["Class"] = relationship("Class", foreign_keys="[Relationship.source_class_id]", back_populates="source_relationships")
    target_class: Mapped["Class"] = relationship("Class", foreign_keys="[Relationship.target_class_id]", back_populates="target_relationships")

    def __repr__(self):
        return f'<Relationship {self.relationship_type}>'