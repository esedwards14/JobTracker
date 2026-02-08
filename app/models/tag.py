"""Tag model."""

from app.extensions import db


# Association table for many-to-many relationship
application_tags = db.Table(
    'application_tags',
    db.Column('application_id', db.Integer, db.ForeignKey('job_applications.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)


class Tag(db.Model):
    """Model for categorizing applications with tags."""

    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    color = db.Column(db.String(7), default='#6B7280')  # Hex color

    def __repr__(self):
        return f'<Tag {self.name}>'

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
        }
