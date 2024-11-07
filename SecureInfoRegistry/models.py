from app import db
from sqlalchemy.dialects.postgresql import JSONB

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    encrypted_data = db.Column(JSONB, nullable=False)
    overlap_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Contact Information
    perpetrator_name = db.Column(db.String(255), nullable=True)  # Changed to nullable=True
    perpetrator_email = db.Column(db.String(255))
    perpetrator_phone = db.Column(db.String(20))
    perpetrator_x_username = db.Column(db.String(255))
    perpetrator_telegram_username = db.Column(db.String(255))

    # Physical Description
    hair_color = db.Column(db.String(50))
    eye_color = db.Column(db.String(50))
    skin_color = db.Column(db.String(50))
    ethnicity = db.Column(db.String(100))
    height = db.Column(db.String(20))
    age = db.Column(db.Integer)

    # Vehicle Information
    vehicle_license_plate = db.Column(db.String(20))
    vehicle_model = db.Column(db.String(100))
    vehicle_make = db.Column(db.String(100))

    # Location Information
    locations = db.Column(db.String(500))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))

    # Occupation/Role
    occupation = db.Column(db.String(100))
    job_title = db.Column(db.String(100))
    organizations = db.Column(db.String(500))

    # Additional Information
    incident_details = db.Column(db.Text)
    additional_info = db.Column(db.Text)
    victim_email = db.Column(db.String(255))

    def __repr__(self):
        return f'<Report {self.id}>'
