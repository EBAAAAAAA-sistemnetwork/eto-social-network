import sys, os
sys.path.insert(0, '/home/THIS26/eto-social-network/backend')

from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import jwt, uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, select, or_, func, desc, and_
from sqlalchemy.orm import Session, sessionmaker

SECRET_KEY = 'eto-social-secret-key-change-me'
ALGORITHM = 'HS256'
TOKEN_EXPIRE = 60 * 24 * 7
FRONTEND_DIR = '/home/THIS26/eto-social-network/frontend/dist'

engine = create_engine('sqlite:////home/THIS26/eto-social-network/social.db')
SessionLocal = sessionmaker(bind=engine)

# Init database tables
from app.models.models import Base
Base.metadata.create_all(bind=engine)

app = Flask(__name__)


def get_user_from_token():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    try:
        payload = jwt.decode(auth[7:], SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get('sub')
    except Exception:
        return None


# --- API AUTH ---

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json(force=True)
    from app.models.models import User
    db = SessionLocal()
    try:
        user = User(
            id=str(uuid.uuid4()),
            username=data['username'],
            display_name=data['display_name'],
            email=data.get('email'),
            phone=data.get('phone'),
            hashed_password=generate_password_hash(data['password']),
        )
        db.add(user)
        db.commit()
        return jsonify({
            'id': user.id, 'username': user.username, 'display_name': user.display_name,
            'avatar_url': user.avatar_url, 'bio': user.bio, 'status': user.status,
            'is_online': user.is_online,
            'last_seen': user.last_seen.isoformat() if user.last_seen else None,
            'created_at': user.created_at.isoformat() if user.created_at else None,
        })
    except Exception as e:
        db.rollback()
        return jsonify({'detail': str(e)}), 400
    finally:
        db.close()


@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json(force=True)
    from app.models.models import User
    db = SessionLocal()
    try:
        result = db.execute(
            select(User).where(
                or_(User.username == data['login'], User.email == data['login'], User.phone == data['login'])
            )
        )
        user = result.scalar_one_or_none()
        if not user or not check_password_hash(user.hashed_password, data['password']):
            return jsonify({'detail': 'Неверный логин или пароль'}), 401
        token = jwt.encode({'sub': user.id, 'exp': datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE)}, SECRET_KEY, algorithm=ALGORITHM)
        return jsonify({
            'access_token': token, 'token_type': 'bearer',
            'user': {'id': user.id, 'username': user.username, 'display_name': user.display_name, 'avatar_url': user.avatar_url}
        })
    finally:
        db.close()


@app.route('/api/auth/me')
def api_me():
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'detail': 'Не авторизован'}), 401
    from app.models.models import User
    db = SessionLocal()
    try:
        result = db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return jsonify({'detail': 'Пользователь не найден'}), 404
        return jsonify({
            'id': user.id, 'username': user.username, 'display_name': user.display_name,
            'avatar_url': user.avatar_url, 'bio': user.bio, 'status': user.status,
            'is_online': user.is_online,
            'last_seen': user.last_seen.isoformat() if user.last_seen else None,
            'created_at': user.created_at.isoformat() if user.created_at else None,
        })
    finally:
        db.close()


# --- API POSTS ---

@app.route('/api/posts/feed')
def api_feed():
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'detail': 'Не авторизован'}), 401
    from app.models.models import Post, User, friends_table, Like, Comment
    db = SessionLocal()
    try:
        friend_ids = [row[0] for row in db.execute(select(friends_table.c.friend_id).where(friends_table.c.user_id == user_id)).all()]
        friend_ids.append(user_id)
        posts_query = db.execute(select(Post).where(Post.author_id.in_(friend_ids)).order_by(desc(Post.created_at)).limit(20))
        posts = posts_query.scalars().all()
        result = []
        for p in posts:
            author = db.execute(select(User).where(User.id == p.author_id)).scalar_one_or_none()
            likes = db.execute(select(func.count()).where(Like.post_id == p.id)).scalar() or 0
            comments = db.execute(select(func.count()).where(Comment.post_id == p.id)).scalar() or 0
            liked = db.execute(select(Like).where(and_(Like.post_id == p.id, Like.user_id == user_id))).first()
            result.append({
                'id': p.id, 'author_id': p.author_id, 'content': p.content,
                'image_url': p.image_url, 'video_url': p.video_url,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'updated_at': p.updated_at.isoformat() if p.updated_at else None,
                'author_name': author.display_name if author else '',
                'author_avatar': author.avatar_url if author else None,
                'likes_count': likes, 'comments_count': comments,
                'liked_by_me': liked is not None,
            })
        return jsonify(result)
    finally:
        db.close()


@app.route('/api/posts/', methods=['POST'])
def api_create_post():
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'detail': 'Не авторизован'}), 401
    from app.models.models import Post, User
    data = request.get_json(force=True)
    db = SessionLocal()
    try:
        post = Post(id=str(uuid.uuid4()), author_id=user_id, content=data.get('content'), image_url=data.get('image_url'))
        db.add(post)
        db.commit()
        author = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        return jsonify({
            'id': post.id, 'author_id': post.author_id, 'content': post.content,
            'image_url': post.image_url, 'video_url': post.video_url,
            'created_at': post.created_at.isoformat() if post.created_at else None,
            'updated_at': post.updated_at.isoformat() if post.updated_at else None,
            'author_name': author.display_name if author else '',
            'author_avatar': author.avatar_url if author else None,
            'likes_count': 0, 'comments_count': 0, 'liked_by_me': False,
        })
    finally:
        db.close()


@app.route('/api/posts/<post_id>/like', methods=['POST'])
def api_like(post_id):
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'detail': 'Не авторизован'}), 401
    from app.models.models import Like
    db = SessionLocal()
    try:
        existing = db.execute(select(Like).where(and_(Like.post_id == post_id, Like.user_id == user_id))).scalar_one_or_none()
        if existing:
            db.delete(existing)
            db.commit()
            return jsonify({'status': 'unliked'})
        like = Like(id=str(uuid.uuid4()), post_id=post_id, user_id=user_id)
        db.add(like)
        db.commit()
        return jsonify({'status': 'liked'})
    finally:
        db.close()


@app.route('/api/posts/<post_id>/comments', methods=['GET'])
def api_comments(post_id):
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'detail': 'Не авторизован'}), 401
    from app.models.models import Comment, User
    db = SessionLocal()
    try:
        comments_query = db.execute(select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at))
        comments = comments_query.scalars().all()
        result = []
        for c in comments:
            author = db.execute(select(User).where(User.id == c.author_id)).scalar_one_or_none()
            result.append({
                'id': c.id, 'post_id': c.post_id, 'author_id': c.author_id,
                'content': c.content,
                'created_at': c.created_at.isoformat() if c.created_at else None,
                'author_name': author.display_name if author else '',
            })
        return jsonify(result)
    finally:
        db.close()


@app.route('/api/posts/<post_id>/comments', methods=['POST'])
def api_add_comment(post_id):
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'detail': 'Не авторизован'}), 401
    from app.models.models import Comment
    data = request.get_json(force=True)
    db = SessionLocal()
    try:
        comment = Comment(id=str(uuid.uuid4()), post_id=post_id, author_id=user_id, content=data['content'])
        db.add(comment)
        db.commit()
        return jsonify({
            'id': comment.id, 'post_id': comment.post_id, 'author_id': comment.author_id,
            'content': comment.content,
            'created_at': comment.created_at.isoformat() if comment.created_at else None,
            'author_name': '',
        })
    finally:
        db.close()


@app.route('/api/posts/<post_id>', methods=['DELETE'])
def api_delete_post(post_id):
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'detail': 'Не авторизован'}), 401
    from app.models.models import Post
    db = SessionLocal()
    try:
        post = db.execute(select(Post).where(Post.id == post_id)).scalar_one_or_none()
        if not post:
            return jsonify({'detail': 'Пост не найден'}), 404
        if post.author_id != user_id:
            return jsonify({'detail': 'Нет прав'}), 403
        db.delete(post)
        db.commit()
        return jsonify({'status': 'deleted'})
    finally:
        db.close()


# --- API USERS ---

@app.route('/api/users/search')
def api_search():
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'detail': 'Не авторизован'}), 401
    q = request.args.get('q', '')
    from app.models.models import User
    db = SessionLocal()
    try:
        result = db.execute(
            select(User).where(or_(User.username.ilike(f'%{q}%'), User.display_name.ilike(f'%{q}%'))).limit(20)
        )
        users = result.scalars().all()
        return jsonify([{'id': u.id, 'username': u.username, 'display_name': u.display_name, 'avatar_url': u.avatar_url} for u in users])
    finally:
        db.close()


@app.route('/api/users/<target_id>')
def api_get_user(target_id):
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'detail': 'Не авторизован'}), 401
    from app.models.models import User, Post, friends_table
    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.id == target_id)).scalar_one_or_none()
        if not user:
            return jsonify({'detail': 'Пользователь не найден'}), 404
        friends_count = db.execute(select(func.count()).where(friends_table.c.user_id == target_id)).scalar() or 0
        posts_count = db.execute(select(func.count()).where(Post.author_id == target_id)).scalar() or 0
        return jsonify({
            'id': user.id, 'username': user.username, 'display_name': user.display_name,
            'email': user.email, 'phone': user.phone, 'avatar_url': user.avatar_url,
            'bio': user.bio, 'status': user.status, 'is_online': user.is_online,
            'last_seen': user.last_seen.isoformat() if user.last_seen else None,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'friends_count': friends_count, 'posts_count': posts_count,
        })
    finally:
        db.close()


@app.route('/api/users/<target_id>/friend', methods=['POST'])
def api_toggle_friend(target_id):
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'detail': 'Не авторизован'}), 401
    if user_id == target_id:
        return jsonify({'detail': 'Нельзя добавить самого себя'}), 400
    from app.models.models import friends_table, User
    db = SessionLocal()
    try:
        existing = db.execute(
            select(friends_table).where(and_(friends_table.c.user_id == user_id, friends_table.c.friend_id == target_id))
        ).first()
        if existing:
            db.execute(friends_table.delete().where(
                or_(
                    and_(friends_table.c.user_id == user_id, friends_table.c.friend_id == target_id),
                    and_(friends_table.c.user_id == target_id, friends_table.c.friend_id == user_id)
                )
            ))
            db.commit()
            return jsonify({'status': 'removed'})
        db.execute(friends_table.insert().values(user_id=user_id, friend_id=target_id))
        db.execute(friends_table.insert().values(user_id=target_id, friend_id=user_id))
        db.commit()
        return jsonify({'status': 'added'})
    finally:
        db.close()


@app.route('/api/users/<target_id>/friends')
def api_get_friends(target_id):
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'detail': 'Не авторизован'}), 401
    from app.models.models import User, friends_table
    db = SessionLocal()
    try:
        result = db.execute(
            select(User).join(friends_table, User.id == friends_table.c.friend_id)
            .where(friends_table.c.user_id == target_id)
        )
        friends = result.scalars().all()
        return jsonify([{'id': u.id, 'username': u.username, 'display_name': u.display_name, 'avatar_url': u.avatar_url, 'is_online': u.is_online} for u in friends])
    finally:
        db.close()


@app.route('/api/users/<target_id>/posts')
def api_get_user_posts(target_id):
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'detail': 'Не авторизован'}), 401
    from app.models.models import Post, User, Like
    db = SessionLocal()
    try:
        posts = db.execute(select(Post).where(Post.author_id == target_id).order_by(desc(Post.created_at)).limit(20)).scalars().all()
        result = []
        for p in posts:
            author = db.execute(select(User).where(User.id == p.author_id)).scalar_one_or_none()
            likes = db.execute(select(func.count()).where(Like.post_id == p.id)).scalar() or 0
            liked = db.execute(select(Like).where(and_(Like.post_id == p.id, Like.user_id == user_id))).first()
            result.append({
                'id': p.id, 'author_id': p.author_id, 'content': p.content,
                'image_url': p.image_url, 'video_url': p.video_url,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'updated_at': p.updated_at.isoformat() if p.updated_at else None,
                'author_name': author.display_name if author else '',
                'author_avatar': author.avatar_url if author else None,
                'likes_count': likes, 'comments_count': 0, 'liked_by_me': liked is not None,
            })
        return jsonify(result)
    finally:
        db.close()


# --- API HEALTH ---

@app.route('/api/health')
def api_health():
    return jsonify({'status': 'ok', 'app': 'ЭТО'})


# --- FRONTEND ---

@app.route('/assets/<path:path>')
def serve_assets(path):
    safe = path.replace('..', '')
    return send_from_directory(os.path.join(FRONTEND_DIR, 'assets'), safe)


@app.route('/')
@app.route('/<path:path>')
def serve_frontend(path='index.html'):
    if path.startswith('api/'):
        return jsonify({'detail': 'not found'}), 404
    safe = path.replace('..', '')
    filepath = os.path.join(FRONTEND_DIR, safe) if safe else os.path.join(FRONTEND_DIR, 'index.html')
    if os.path.isfile(filepath) and safe:
        return send_from_directory(FRONTEND_DIR, safe)
    return send_from_directory(FRONTEND_DIR, 'index.html')
