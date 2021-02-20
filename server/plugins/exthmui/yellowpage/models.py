from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class YellowPageData(db.Model):
    __tablename__ = 'exthmui_yellowpage_data'

    id = db.Column(db.Integer(), primary_key=True, nullable=False, autoincrement=True)
    name = db.Column(db.String(), unique=True, index=True)
    lastUpdated = db.Column(db.BigInteger, index=True)
    avatar = db.Column(db.UnicodeText(), default='')
    phone = db.relationship('Phone', cascade='all, delete, delete-orphan')
    address = db.relationship('Address', cascade='all, delete, delete-orphan')
    website = db.relationship('Website', cascade='all, delete, delete-orphan')


class Address(db.Model):
    __tablename__ = 'exthmui_yellowpage_address'

    id = db.Column(db.Integer(), primary_key=True, nullable=False, autoincrement=True)

    data = db.Column(db.Text())
    label = db.Column(db.String())

    masterid = db.Column(db.String(20), db.ForeignKey('exthmui_yellowpage_data.id'))


class Phone(db.Model):
    __tablename__ = 'exthmui_yellowpage_phone'

    id = db.Column(db.Integer(), primary_key=True, nullable=False, autoincrement=True)

    number = db.Column(db.String())
    label = db.Column(db.String())

    masterid = db.Column(db.String(20), db.ForeignKey('exthmui_yellowpage_data.id'))


class Website(db.Model):
    __tablename__ = 'exthmui_yellowpage_website'

    id = db.Column(db.Integer(), primary_key=True, nullable=False, autoincrement=True)

    __mapper_args__ = {
        'primary_key': [id]
    }

    url = db.Column(db.UnicodeText())
    label = db.Column(db.String())

    masterid = db.Column(db.String(20), db.ForeignKey('exthmui_yellowpage_data.id'))
