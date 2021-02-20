from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from plugins.cloud_drive import drive_util
from plugins.cloud_drive.errors import InvalidResourceURIException

db = SQLAlchemy()
ma = Marshmallow()


class Update(db.Model):
    __tablename__ = 'exthmui_updates'
    id = db.Column(db.String(100), primary_key=True)

    name = db.Column(db.String(20), index=True, nullable=False)
    device = db.Column(db.String(20), index=True, nullable=False)
    packagetype = db.Column(db.String(5), index=True, default="full", nullable=False)
    requirement = db.Column(db.BigInteger, default=0, nullable=False)
    changelog = db.Column(db.UnicodeText(), default='None', nullable=False)
    timestamp = db.Column(db.BigInteger, unique=True, nullable=False)
    filename = db.Column(db.UnicodeText(), index=True, nullable=False)
    releasetype = db.Column(db.String(20), index=True, nullable=False)
    size = db.Column(db.BigInteger, nullable=False)
    url = db.Column(db.UnicodeText(), unique=True, nullable=False)
    imageurl = db.Column(db.UnicodeText(), nullable=True)
    version = db.Column(db.String(1000), nullable=False)
    maintainer = db.Column(db.String(20), nullable=False)

    @property
    def url(self):
        try:
            url = drive_util.get_dl_url_by_uri(self.url)
        except InvalidResourceURIException:
            url = self.url
        return url


class UpdateSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Update
        load_instance = True
