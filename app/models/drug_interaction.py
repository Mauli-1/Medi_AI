from ..extensions import db


class DrugInteraction(db.Model):
    __tablename__ = 'drug_interactions'

    id = db.Column(db.Integer, primary_key=True)
    drug_a_generic = db.Column(db.String(150), nullable=False, index=True)
    drug_b_generic = db.Column(db.String(150), nullable=False, index=True)
    severity = db.Column(db.Enum('minor', 'moderate', 'major', 'contraindicated'), nullable=False)
    description = db.Column(db.Text)
    recommendation = db.Column(db.Text)
    source = db.Column(db.String(100))

    def __repr__(self):
        return f'<DrugInteraction {self.drug_a_generic} + {self.drug_b_generic}: {self.severity}>'

    def to_dict(self):
        return {
            'id': self.id,
            'drug_a': self.drug_a_generic,
            'drug_b': self.drug_b_generic,
            'severity': self.severity,
            'description': self.description,
            'recommendation': self.recommendation,
        }
