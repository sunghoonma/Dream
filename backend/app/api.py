__author__ = 'masunghoon'

# Libraries
import random, datetime

from flask import request, g
from flask.ext.httpauth import HTTPBasicAuth
from flask.ext.restful import Resource, reqparse, fields, marshal
from flask.ext.uploads import UploadSet, IMAGES, configure_uploads, patch_request_class

from hashlib import md5
from rauth.service import OAuth2Service
# Source
from app import db, api, app
from models import User, Bucket, Plan, File, ROLE_ADMIN, ROLE_USER
from emails import send_awaiting_confirm_mail, send_reset_password_mail
from config import FB_CLIENT_ID, FB_CLIENT_SECRET

photos = UploadSet('photos',IMAGES)
configure_uploads(app, photos)
patch_request_class(app, size=2097152) #File Upload Size = Up to 2MB

##### AUTHENTICATION #######################################

auth = HTTPBasicAuth()

graph_url = 'https://graph.facebook.com/'
facebook = OAuth2Service(name='facebook',
                         authorize_url='https://www.facebook.com/dialog/oauth',
                         access_token_url=graph_url+'oauth/access_token',
                         client_id=FB_CLIENT_ID,
                         client_secret=FB_CLIENT_SECRET,
                         base_url=graph_url);

@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    if password == "facebook":
        auth = facebook.get_session(token=username_or_token)
        resp = auth.get('/me')
        if resp.status_code == 200:
            fb_user = resp.json()
            # user = User.query.filter_by(email=fb_user.get('email')).first()
            birthday = fb_user['birthday'][6:10] + fb_user['birthday'][0:2] + fb_user['birthday'][3:5]
            user = User.get_or_create(fb_user['email'], fb_user['name'], fb_user['id'], birthday)
        else:
            return False
    else:
        user = User.verify_auth_token(username_or_token)

    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(email = username_or_token).first()
        if not user:
            return False
        if user.password == None:
            return False
        if not user.verify_password(password):
            return False
    g.user = user
    return True




class VerificationAPI(Resource):
    def __init__(self):
        super(VerificationAPI, self).__init__()

    def get(self,emailAddr):
        try:
            if User.email_exists(emailAddr):
                return {'status':'success',
                        'code':'0',
                        'description':'Email already exists'}, 200
            else:
                return {'status':'success',
                        'code':'1',
                        'description':'Available Email Address'}, 200
        except:
            return {'status':'error',
                    'description':'Something went wrong'}, 500

api.add_resource(VerificationAPI, '/api/valid_email/<emailAddr>', endpoint='verifyEmail')


class ResetPassword(Resource):
    def __init__(self):
        super(ResetPassword, self).__init__()

    # def get(self,string):
    #     u = User.query.filter_by(email = string).first()
    #     u.key = md5('RESET_PASSWORD'+str(int(random.random()*10000))).hexdigest()
    #
    #     db.session.commit()
    #     send_reset_password_mail(u)
    #
    #     return {'status':'success',
    #             'description':'Reset Password Mail Sent'}, 200



    def post(self,string):
        u = User.query.filter_by(email = string).first()
        if not u:
            return {'status':'error',
                    'description':'Invalid User Email'}, 400
        u.key = md5('RESET_PASSWORD'+str(int(random.random()*10000))).hexdigest()

        db.session.commit()
        send_reset_password_mail(u)

        return {'status':'success',
                'description':'Reset Password Mail Sent'}, 200


    def put(self,string):
        if request.json:
            params = request.json
        elif request.form:
            params = request.form
        else:
            return {'status':'error',
                    'description':'Request Failed'}, 400

        u = User.query.filter_by(key = string).first()
        if not u:
            return {'status':'error',
                    'description':'Invalid Key'}, 400

        # if
        if 'password' not in params:
            return {'status':'error',
                    'description':'Password Missing'}, 400

        try:
            u.hash_password(params['password'])
            u.key = None
            db.session.commit()
        except:
            return {'status':'error',
                    'description':'Something went wrong'}, 500

        return {'status':'success',
                'description':'Password successfully reset'}, 200

api.add_resource(ResetPassword, '/api/reset_password/<string>', endpoint='resetPassword')


##### USER / USERLIST ##################################

user_fields = {
    'id': fields.Integer,
    'username': fields.String,
    'email': fields.String,
    'about_me': fields.String,
    'last_seen': fields.String,
    'birthday': fields.String,
    'is_following': fields.Boolean,
    'pic': fields.String,
    'uri': fields.Url('user'),
}

class UserAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        super(UserAPI, self).__init__()

    #get specific User's Profile
    def get(self, id):
        u = User.query.filter_by(id=id).first()
        # return marshal(u, user_fields), 200
        return {'status':'success',
                  'data':marshal(u, user_fields)}, 200
    #modify My User Profile
    def put(self, id):
        if request.json:
            params = request.json
        elif request.form:
            params = request.form
        else:
            return {'status':'error','description':'Request Failed'}, 400

        u = User.query.filter_by(id=id).first()
        if u != g.user:
            return {'error': 'Unauthorized'}, 401

        for key in params:
            value = None if params[key]=="" else params[key]    # Or Use (params[key],None)[params[key]==""] Sam Hang Yeonsanja

            # Nobody can change id, email, fb_id, last_seen
            if key in ['id', 'email', 'fb_id', 'last_seen']:
                return {'error':'Cannot change ' + key}, 400

            # Just ROLE_ADMIN user can change 'role', 'login_fault'
            if key in ['login_fault', 'role'] and g.user.role == ROLE_USER:
                return {'error':'Only Admin can change ' + key}, 401

            # Validate & hash Password
            if key == 'password':
                if len(value) < 4:
                    return {'error':'Password is too short'}, 400
                u.hash_password(value)
                continue                                        # if not continue hash will be reset.

            # Birthday can only be None or 8-digit integer(between 1900/01/01 ~ currentYear's 12/31)
            elif key == 'birthday' and value is not None:
                if len(value) != 8 or \
                    int(value[0:4]) < 1900 or int(value[0:4]) > int(datetime.datetime.now().strftime("%Y")) or \
                    int(value[4:6]) < 0 or int(value[4:6]) > 12 or \
                    int(value[6:8]) < 0 or int(value[6:8]) > 31:
                        return {"error":"Invalid value for Birthday: " + value[0:4] + '/' + value[4:6] + '/' + value [6:8]}, 400

            # Username cannot be null
            elif key == 'username':
                if value == None:
                    return {'error':'Username cannot be blank'}, 400


            elif key not in ['about_me']:
                return {'error':'Invalid user key'}, 400

            setattr(u, key, value)
        db.session.commit()

        return marshal(u, user_fields), 201

    #delete a User
    def delete(self, id):
        u = User.query.filter_by(id=id).first()
        if u != g.user:
            return {'error':'Unauthorized'}, 401
        else:
            try:
                db.session.delete(u)
                db.session.commit()
            except:
                {'error':'Something went wrong'}, 500

        return {'status':'success'}, 201


class UserListAPI(Resource):
    def __init__(self):
        super(UserListAPI, self).__init__()

    @auth.login_required
    def get(self):
        u = User.query.all()
        return {'status':'success',
                'data':map(lambda t:marshal(t, user_fields), u)}, 200

    def post(self):
        if request.json:
            params = request.json
        elif request.form:
            params = request.form
        else:
            return {'status':'error',
                    'description':'Request Failed!'}, 400

        # Check Requirements <Email, Password>
        if not 'email' in params:
            return {'status':'error',
                    'description':'Email Address input error!'}, 400
        elif not 'password' in params:
            return {'status':'error',
                    'description':'Password Missing'}, 400

        # Check email address is unique
        if User.email_exists(params['email']):
            return {'status':'error',
                    'description':'Already registered Email address'}, 400

        # Make username based on email address when it was not submitted.
        if not 'username' in params or params['username'] == "" or params['username'] == None:
            username = params['email'].split('@')[0]
            username = User.make_valid_username(username)
            # username = User.make_unique_username(username)
        else:
            username = params['username']
            if User.username_exists(username):
                return {'status':'error',
                        'description':'Username already exists.'}, 400

        # Check User Birthday
        if not 'birthday' in params or params['birthday']=="":
            birthday = None
        else:
            birthday = params['birthday']

        u = User(email=params['email'],
                 username=username,
                 fb_id=None,
                 birthday=birthday)

        # Password Hashing
        u.hash_password(params['password'])

        u.key = md5('ACTIVATION'+str(int(random.random()*10000))).hexdigest()

        # Database Insert/Commit
        try:
            db.session.add(u)
            db.session.commit()
        except:
            return {'status':'error',
                    'description':'Something went wrong.'}, 500

        send_awaiting_confirm_mail(u)
        g.user = u
        token = g.user.generate_auth_token()

        return {'status':'success',
                'data':{'user':{'id': g.user.id,
                                'username': g.user.username,
                                'email': g.user.email,
                                'birthday': g.user.birthday,
                                'confirmed_at':g.user.confirmed_at.strftime("%Y-%m-%d %H:%M:%S") if g.user.confirmed_at else None},
                        'token': token.decode('ascii')}}, 201



api.add_resource(UserAPI, '/api/user/<int:id>', endpoint='user')
api.add_resource(UserListAPI, '/api/users', endpoint='users')


##### about BUCKET / BUCKETLIST ####################################

class BucketAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        super(BucketAPI, self).__init__()

    def get(self, id):
        b = Bucket.query.filter(Bucket.id==id, Bucket.status!='9').first()
        if b == None:
            return {'error':'No data found'}, 204

        data={
            'id': b.id,
            'user_id': b.user_id,
            'title': b.title,
            'description': b.description,
            'level': b.level,
            'status': b.status,
            'private': b.private,
            'parent_id': b.parent_id,
            'reg_dt': b.reg_dt.strftime("%Y-%m-%d %H:%M:%S"),
            'deadline': b.deadline.strftime("%Y-%m-%d"),
            'scope': b.scope,
            'range': b.range,
            'rpt_type': b.rpt_type,
            'rpt_cndt': b.rpt_cndt,
            'lst_mod_dt': None if b.lst_mod_dt is None else b.lst_mod_dt.strftime("%Y-%m-%d %H:%M:%S"),
            'cvr_img_url': None if b.cvr_img_id is None else photos.url(File.query.filter_by(id=b.cvr_img_id).first().name)
        }

        return {'status':'success',
                'description':'GET Success',
                'data':data}, 200

    def put(self, id):
        if request.json:
            params = request.json
        elif request.form:
            params = {}
            for key in request.form:
                params[key] = request.form[key]
        else:
            return {'status':'error','description':'Request Failed'}, 500

        b = Bucket.query.filter_by(id=id).first()
        if b.user_id != g.user.id:
            return {'status':'error','description':'Unauthorized'}, 401

        for key in params:
            value = None if params[key]=="" else params[key]

            # Editable Fields
            if key not in ['title','status','private','deadline','description','parent_id','scope','range','rpt_type','rpt_cndt']:
                return {'status':'error','description':'Invalid key: '+key}, 403

            # Nobody can modify id, user_id, reg_dt
            if key in ['id','user_id','reg_dt']:
                return {'status':'error','description':'Cannot change '+key}, 403

            # Just ROLE_ADMIN user can change 'language', 'level'
            if key in ['language','level'] and g.user.role == ROLE_USER:
                return {'status':'error','description':'Only Admin can change' + key}, 401

            # When modify user's parent_id adjusts its level
            if key == 'parent_id':
                if value == None:
                    params['level'] = '0'
                else:
                    pb = Bucket.query.filter_by(id=int(value)).first() # pb = parent bucket
                    if pb == None:
                        return {'status':'error','description':'Parent does not exists'}, 400
                    else:
                        params['level'] = str(int(pb.level)+1)

            # Set other key's validation
            if key == 'title' and len(value) > 128:
                return {'status':'error','description':'Title length must be under 128'}, 400

            if key == 'description' and len(value) > 512:
                return {'status':'error','description':'Description too long (512)'}, 400

            if key == 'deadline':
                value = datetime.datetime.strptime(value,'%Y-%m-%d')

            if key == 'scope' and value not in ['DECADE','YEARLY','MONTHLY']:
                return {'status':'error','description':'Invalid scope value'}, 400

            if key == 'rpt_type' and value not in ['WKRP','WEEK','MNTH']:
                return {'status':'error','description':'Invalid repeat-type value'}, 400

            if key == 'rpt_cndt':
                dayOfWeek = datetime.date.today().weekday()
                if b.rpt_type == 'WKRP' and b.rpt_cndt[dayOfWeek] != value[dayOfWeek]:
                    if value[dayOfWeek] == '1':
                        p = Plan(date=datetime.date.today().strftime("%Y%m%d"),
                                 user_id=b.user_id,
                                 bucket_id=id,
                                 status=0,
                                 lst_mod_dt=datetime.datetime.now())
                        db.session.add(p)
                    else:
                        p = Plan.query.filter_by(date=datetime.date.today().strftime("%Y%m%d"),bucket_id=id).first()
                        db.session.delete(p)

            setattr(b, key, value)

        if 'photo' in request.files:
            upload_type = 'photo'

            if len(request.files[upload_type].filename) > 64:
                return {'status':'error',
                        'description':'Filename is too long (Max 64bytes include extensions)'}, 403
            upload_files = UploadSet('photos',IMAGES)
            configure_uploads(app, upload_files)

            filename = upload_files.save(request.files[upload_type])
            splits = []

            for item in filename.split('.'):
                splits.append(item)
            extension = filename.split('.')[len(splits) -1]

            f = File(filename=filename, user_id=g.user.id, extension=extension, type=upload_type)
            db.session.add(f)
            db.session.flush()
            db.session.refresh(f)

            setattr(b, 'cvr_img_id', f.id)

        b.lst_mod_dt = datetime.datetime.now()
        try:
            db.session.commit()
            data={
                'id': b.id,
                'user_id': b.user_id,
                'title': b.title,
                'description': b.description,
                'level': b.level,
                'status': b.status,
                'private': b.private,
                'parent_id': b.parent_id,
                'reg_dt': b.reg_dt.strftime("%Y-%m-%d %H:%M:%S"),
                'deadline': b.deadline.strftime("%Y-%m-%d"),
                'scope': b.scope,
                'range': b.range,
                'rpt_type': b.rpt_type,
                'rpt_cndt': b.rpt_cndt,
                'lst_mod_dt': None if b.lst_mod_dt is None else b.lst_mod_dt.strftime("%Y-%m-%d %H:%M:%S"),
                'cvr_img_url': None if b.cvr_img_id is None else photos.url(File.query.filter_by(id=b.cvr_img_id).first().name)
            }
            return {'status':'success',
                    'description':'Bucket put success.',
                    'data':data}, 201
        except:
            db.session.rollback()
            return {'error':'Something went wrong'}, 500


    def delete(self, id):
        b = Bucket.query.filter_by(id=id).first()

        # Only bucket's owner can delete action.
        if b.user_id != g.user.id:
            return {'error':'Unauthorized'}, 401

        try:
            b.status = '9'
            b.lst_mod_dt = datetime.datetime.now()
            db.session.commit()
            return {'status':'success'}, 200
        except:
            return {'status':'error',
                    'description':'delete failed'}, 500


class UserBucketAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        super(UserBucketAPI, self).__init__()

    def get(self, id):
        u = User.query.filter_by(id=id).first()
        if not g.user.is_following(u):
            if g.user == u:
                pass
            else:
                return {'error':'User unauthorized'}, 401

        data = []
        if g.user == u:
            b = Bucket.query.filter(Bucket.user_id==u.id,Bucket.status!='9',Bucket.level=='0').all()
        else:
            b = Bucket.query.filter(Bucket.user_id==u.id,Bucket.status!='9',Bucket.level=='0',Bucket.private=='0').all()

        if len(b) == 0:
            return {'error':'No data Found'}, 204

        for i in b:
            data.append({
                'id': i.id,
                'user_id': i.user_id,
                'title': i.title,
                'description': i.description,
                'level': i.level,
                'status': i.status,
                'private': i.private,
                'parent_id': i.parent_id,
                'reg_dt': i.reg_dt.strftime("%Y-%m-%d %H:%M:%S"),
                'deadline': i.deadline.strftime("%Y-%m-%d"),
                'scope': i.scope,
                'range': i.range,
                'rpt_type': i.rpt_type,
                'rpt_cndt': i.rpt_cndt,
                'lst_mod_dt': None if i.lst_mod_dt is None else i.lst_mod_dt.strftime("%Y-%m-%d %H:%M:%S"),
                'cvr_img_url': None if i.cvr_img_id is None else photos.url(File.query.filter_by(id=i.cvr_img_id).first().name)
            })

        return {'status':'success',
                'description':'normal',
                'data':data}, 200


    def post(self, id):
        u = User.query.filter_by(id=id).first()
        if u.id != g.user.id:
            return {'status':'error',
                    'description':'Unauthorized'}, 401

        if request.json:
            params = request.json
        elif request.form:
            params = {}
            for key in request.form:
                params[key] = request.form[key]
        else:
            return {'status':'error','description':'Request Failed'}, 400

        # Replace blank value to None(null) in params
        for key in params:
            params[key] = None if params[key] == "" else params[key]

            if key in ['id', 'user_id', 'reg_dt', 'language']:
                return {'error': key + ' cannot be entered manually.'}, 401

        # Bucket Title required
        if not 'title' in params:
            return {'error':'Bucket title required'}, 401

        # Check ParentID is Valid & set level based on ParentID
        if not 'parent_id' in params or params['parent_id'] == None:
            level = 0
        else:
            b = Bucket.query.filter_by(id=params['parent_id']).first()
            if b is None:
                return {'error':'Invalid ParentID'}, 401
            elif b.user_id != g.user.id:
                return {'error':'Cannot make sub_bucket with other user\'s Bucket'}, 401
            else:
                level = int(b.level) + 1

        if 'rpt_cndt' in params:
            dayOfWeek = datetime.date.today().weekday()
            if params['rpt_type'] == 'WKRP':
                if params['rpt_cndt'][dayOfWeek] == '1':
                    p = Plan(date=datetime.date.today().strftime("%Y%m%d"),
                             user_id=g.user.id,
                             bucket_id=None,
                             status=0,
                             lst_mod_dt=datetime.datetime.now())
                    db.session.add(p)

        if 'photo' in request.files:
            upload_type = 'photo'

            if len(request.files[upload_type].filename) > 64:
                return {'status':'error','description':'Filename is too long (Max 64bytes include extensions)'}, 403
            upload_files = UploadSet('photos',IMAGES)
            configure_uploads(app, upload_files)

            filename = upload_files.save(request.files[upload_type])
            splits = []

            for item in filename.split('.'):
                splits.append(item)
            extension = filename.split('.')[len(splits) -1]

            f = File(filename=filename, user_id=g.user.id, extension=extension, type=upload_type)
            db.session.add(f)
            db.session.flush()
            db.session.refresh(f)

        bkt = Bucket(title=params['title'],
                     user_id=g.user.id,
                     level=str(level),
                     status= params['status'] if 'status' in params else True,
                     private=params['private'] if 'private' in params else False,
                     reg_dt=datetime.datetime.now(),
                     lst_mod_dt=datetime.datetime.now(),
                     deadline=datetime.datetime.strptime(params['deadline'],'%Y-%m-%d').date() if 'deadline' in params \
                                                                                      else datetime.datetime.now(),
                     description=params['description'] if 'description' in params else None,
                     parent_id=params['parent_id'] if 'parent_id' in params else None,
                     scope=params['scope'] if 'scope' in params else None,
                     range=params['range'] if 'range' in params else None,
                     rpt_type=params['rpt_type'] if 'rpt_type' in params else None,
                     rpt_cndt=params['rpt_cndt'] if 'rpt_cndt' in params else None,
                     cvr_img_id=f.id if 'photo' in request.files else None)
                     # cvr_img_id=f.id if 'cvr_img' in params and params['cvr_img'] == 'true' else None)
        db.session.add(bkt)
        db.session.flush()
        db.session.refresh(bkt)

        if 'photo' in request.files and 'rpt_cndt' in params:
            p.bucket_id = bkt.id
        db.session.commit()

        data={
            'id': bkt.id,
            'user_id': bkt.user_id,
            'title': bkt.title,
            'description': bkt.description,
            'level': bkt.level,
            'status': bkt.status,
            'private': bkt.private,
            'parent_id': bkt.parent_id,
            'reg_dt': bkt.reg_dt.strftime("%Y-%m-%d %H:%M:%S"),
            'deadline': bkt.deadline.strftime("%Y-%m-%d"),
            'scope': bkt.scope,
            'range': bkt.range,
            'rpt_type': bkt.rpt_type,
            'rpt_cndt': bkt.rpt_cndt,
            'lst_mod_dt': None if bkt.lst_mod_dt is None else bkt.lst_mod_dt.strftime("%Y-%m-%d %H:%M:%S"),
            'cvr_img_url': None if bkt.cvr_img_id is None else photos.url(File.query.filter_by(id=bkt.cvr_img_id).first().name)
        }

        return {'status':'success',
                'description':'Bucket posted successfully.',
                'data':data}, 201


api.add_resource(BucketAPI, '/api/bucket/<int:id>', endpoint='bucket')
api.add_resource(UserBucketAPI, '/api/buckets/user/<int:id>', endpoint='buckets')


##### PLAN ##################################################

plan_fields = {
    'id': fields.Integer,
    'date': fields.String,
    'bucket_id': fields.Integer,
    'user_id': fields.Integer,
    'title': fields.String,
    'status': fields.Integer,
    'private': fields.Integer,
    'deadline': fields.String,
    'scope': fields.String,
    'range': fields.String,
    'rpt_type': fields.String,
    'rpt_cndt': fields.String,
    'parent_id': fields.Integer,
}


class PlanListAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(PlanListAPI, self).__init__()

    def get(self,username):

        data = []
        u = User.query.filter_by(username = username).first()
        if u is None:
            return {'status':'error',
                    'description':'User does not Exists'}, 400

        for p, b in db.session.query(Plan, Bucket).filter(Plan.bucket_id == Bucket.id,Plan.user_id == g.user.id).order_by(Plan.date.desc(), Bucket.deadline.desc()).all():
            data.append({
                'id': p.id,
                'date': p.date,
                'bucket_id': p.bucket_id,
                'user_id': p.user_id,
                'title': b.title,
                'status': b.status,
                'private': b.private,
                'deadline': b.deadline,
                'scope': b.scope,
                'range': b.range,
                'rpt_type': b.rpt_type,
                'rpt_cndt': b.rpt_cndt,
                'parent_id': b.parent_id
            })

        return map(lambda t: marshal(t, plan_fields), data), 200


class PlanAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(PlanAPI, self).__init__()

    def put(self, id):
        if request.json:
            params = request.json
        elif request.form:
            params = request.form
        else:
            return {'status':'Request Failed!'}

        p = Plan.query.filter_by(id=id).first()
        if p.user_id != g.user.id:
            return {'status':'Unauthorized'}, 401

        try:
            for item in params:
                if item:
                    setattr(p, item, params.get(item))
            db.session.commit()
        except:
            return {'status':'failed'}, 401

        return {'status':'succeed'}, 200

api.add_resource(PlanListAPI, '/api/plans/<username>', endpoint='plans')
api.add_resource(PlanAPI, '/api/plan/<id>', endpoint='plan')


##### FILE UPLOADS ##############################################

class UploadFiles(Resource):
    decorators = [auth.login_required]
    def __init__(self):
        super(UploadFiles, self).__init__()

    def post(self):
        if 'photo' in request.files:
            upload_type = 'photo'

            upload_files = UploadSet('photos',IMAGES)
            configure_uploads(app, upload_files)

            filename = upload_files.save(request.files[upload_type])
            splits = []
            for item in filename.split('.'):
                splits.append(item)
            extension = filename.split('.')[len(splits) - 1]
        else:
            return {'status':'error',
                    'description':'No attached Files'}, 400

        f = File(filename=filename, user_id=g.user.id, extension=extension, type=upload_type)
        try:
            db.session.add(f)
            db.session.commit()
        except:
            return {'status':'error',
                    'description':'Something went wrong'}, 500

        return {'status':'success',
                'description':'Upload Succeeded',
                'data':{'id':f.id,
                        'url':upload_files.url(f.name)}}, 201


api.add_resource(UploadFiles, '/api/file', endpoint='uploadFiles')
