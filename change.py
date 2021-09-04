
import datetime
import hashlib
import os
import random
import re
import sqlite3
import sys
from http.client import BAD_REQUEST

from flask import Flask, abort, g, request
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from lxml import etree
from sqlalchemy.exc import IntegrityError

from exception import MyException

# 使用Flask构建web对象app
app = Flask(__name__)
# 激活app环境(with app_context()也行)
app.app_context().push()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PROPAGATE_EXCEPTIONS'] = True
app.logger.setLevel('ERROR')


db = SQLAlchemy(app)
admin = Admin(app)

# 存储所有收到的后台信息
class Message(db.Model):
	'timestamp 用来实现定期清除'
	msgId = db.Column(db.Integer(), primary_key=True, autoincrement=False)
	timestamp = db.Column(db.DateTime(), default=datetime.datetime.now, nullable=False)
	def __repr__(self):
		return '<Message {} at {}>'.format(self.msgId, self.timestamp)

# 用户类, name是用户输入的名字
class User(db.Model):
	id = db.Column(db.Integer(), primary_key=True)
	openId = db.Column(db.String(), unique=True, nullable=True) #null一般为手动录入但没登记的老师
	name = db.Column(db.String(), nullable=False)
	authorized = db.Column(db.Integer(), nullable=True)
	administrator = db.Column(db.Integer(), nullable=True)
	def __repr__(self):
		return '<User {} {} {}>'.format(self.openId, self.name, self.authorized)

# 登录信息
class Registration(db.Model):
	id = db.Column(db.Integer(), primary_key=True)
	openId = db.Column(db.String(), unique=True, nullable=False)
	name = db.Column(db.String(), nullable=False)
	def __repr__(self):
		return '<Registration {} {}>'.format(self.openId, self.name)

# 琴房信息,name是琴房的名字,B250,B252,B253
class Room(db.Model):
	id = db.Column(db.Integer(), primary_key=True)
	name = db.Column(db.String(collation='NOCASE'), unique=True, nullable=False)
	def __repr__(self):
		return '<Room {}>'.format(self.name)

# 预订琴房的信息
class Reservation(db.Model):
	id = db.Column(db.Integer(), primary_key=True)
	userId = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
	user = db.relationship('User', backref=db.backref('reservations', lazy='dynamic'))
	roomId = db.Column(db.Integer(), db.ForeignKey('room.id'), nullable=False)
	room = db.relation('Room', backref=db.backref('reservations', lazy='dynamic'))
	start = db.Column(db.DateTime(), nullable=False)
	end = db.Column(db.DateTime(), nullable=False)
	def __repr__(self):
		return '{} {}'.format(self.user.name, self.getDateRoom())

	def getDateRoom(self):
		return '{}年{}月{}日 {}:{:02}~{}:{:02} {}'.format(
				self.start.year, self.start.month, self.start.day,
				self.start.hour, self.start.minute,
				self.end.hour, self.end.minute,
				self.room.name)

# 钢琴课的信息
class Course(db.Model):
	id = db.Column(db.Integer(), primary_key=True)
	teacherId = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
	teacher = db.relation('User', backref=db.backref('courses', lazy='dynamic'))
	roomId = db.Column(db.Integer(), db.ForeignKey('room.id'), nullable=False)
	room = db.relation('Room', backref=db.backref('courses', lazy='dynamic'))
	weekday = db.Column(db.Integer(), nullable=False)
	startDate = db.Column(db.Date(), nullable=False)
	endDate = db.Column(db.Date(), nullable=False)
	startTime = db.Column(db.Time(), nullable=False)
	endTime = db.Column(db.Time(), nullable=False)
	def __repr__(self):
		return '<Course {} {}月{}日~{}月{}日 {} {}:{:02}~{}:{:02}>'.format(
				self.teacher.name,
				self.startDate.month, self.startDate.day,
				self.endDate.month, self.endDate.day,
				'周一 周二 周三 周四 周五 周六 周日'.split()[self.weekday],
				self.startTime.hour, self.startTime.minute,
				self.endTime.hour, self.endTime.minute)

admin.add_view(ModelView(Course, db.session))
admin.add_view(ModelView(Reservation, db.session))
admin.add_view(ModelView(Room, db.session))
admin.add_view(ModelView(Registration, db.session))
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Message, db.session))

migrate = Migrate(app,db)

if __name__ == '__main__' :
	u = User.query
	for r in u :
		print(r)