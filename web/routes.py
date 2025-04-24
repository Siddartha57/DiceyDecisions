from flask import render_template, redirect, flash, url_for, session, request
from flask_login import login_user, logout_user,login_required, current_user
from web import app, db
from web.models import User, DecisionRoom, Participant, Option, Vote
from web.forms import Register, Login, CreateRoomForm, JoinRoomForm, SubmitOptionForm, VoteForm
from .auth import hash, verify
import string, random
from datetime import datetime


@app.route('/')
def landing():
    return render_template("landing.html", current_year=datetime.now().year)


@app.route('/base')
def base():
    return render_template('base.html')

@app.route('/dashboard')
@login_required
def dashboard():
    active_rooms = DecisionRoom.query.filter_by(creator_id=current_user.id, is_open=True).all()

    return render_template('dashboard.html', active_rooms=active_rooms)



@app.route('/register',methods=['GET','POST'])
def register_page():
    form =Register()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first() or User.query.filter_by(email=form.email.data).first():
            flash('username or email already exist','danger')
            return redirect(url_for('register_page'))
        else:    
            hashed_password = hash(form.password.data)
            new_user = User(username=form.username.data,email=form.email.data,password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
        flash('Registerd Successfully','success')     
        return login_page()
    return render_template('register.html',form=form)


@app.route('/login',methods=['GET','POST'])
def login_page():
    form = Login()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and verify(user.password,form.password.data):
            db.session.refresh(user)
            login_user(user)
            flash(f'Logged in as {user.username} ','success')
            return redirect(url_for('dashboard'))
        flash('Invalid details','danger')
    return render_template('login.html',form=form) 

@app.route('/logout')
def logout():
    session.clear()
    logout_user()
    flash('logged out','info')
    return redirect(url_for('landing'))

def generate_room_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@app.route('/create-room', methods=['GET', 'POST'])
@login_required
def create_room():
    form = CreateRoomForm()
    if form.validate_on_submit():
        room_code = generate_room_code()
        while DecisionRoom.query.filter_by(room_code=room_code).first():
            room_code = generate_room_code()

        room = DecisionRoom(
            title=form.title.data,
            description=form.description.data,
            room_code=room_code,
            creator_id=current_user.id
        )
        db.session.add(room)
        db.session.commit()
        flash('Room created successfully!', 'success')
        return redirect(url_for('room_detail', room_code=room_code))
    return render_template('create_room.html', form=form)

@app.route('/join-room', methods=['GET', 'POST'])
@login_required
def join_room():
    form = JoinRoomForm()
    if form.validate_on_submit():
        room = DecisionRoom.query.filter_by(room_code=form.room_code.data.upper()).first()
        if not room:
            flash("Room not found!", "danger")
            return redirect(url_for('join_room'))

        existing = Participant.query.filter_by(user_id=current_user.id, room_id=room.id).first()
        if not existing:
            new_participant = Participant(user_id=current_user.id, room_id=room.id)
            db.session.add(new_participant)
            db.session.commit()

        return redirect(url_for('room_detail', room_code=room.room_code))

    return render_template('join_room.html', form=form)


@app.route('/room/<room_code>', methods=['GET', 'POST'])
@login_required
def room_detail(room_code):
    room = DecisionRoom.query.filter_by(room_code=room_code).first_or_404()

    is_creator = (room.creator_id == current_user.id)
    participant = Participant.query.filter_by(user_id=current_user.id, room_id=room.id).first()
    if not participant and not is_creator:
        flash("You are not part of this room!", "danger")
        return redirect(url_for('base'))

    if request.method == 'POST' and 'close_room' in request.form and is_creator:
        room.is_open = False
        db.session.commit()
        flash("Room closed for voting.", "warning")
        return redirect(url_for('room_detail', room_code=room_code))

    form = SubmitOptionForm()
    if is_creator and form.validate_on_submit() and room.is_open:
        new_option = Option(
            text=form.text.data,
            room_id=room.id,
            submitted_by=current_user.id
        )
        db.session.add(new_option)
        db.session.commit()
        flash("Option added successfully!", "success")
        return redirect(url_for('room_detail', room_code=room_code))

    vote_form = VoteForm()
    options = Option.query.filter_by(room_id=room.id).all()
    vote_form.selected_option.choices = [(opt.id, opt.text) for opt in options]

    existing_vote = Vote.query.join(Option).filter(
        Vote.voter_id == current_user.id,
        Option.room_id == room.id
    ).first()

    if vote_form.validate_on_submit() and not is_creator and not existing_vote and room.is_open:
        vote = Vote(
            voter_id=current_user.id,
            option_id=vote_form.selected_option.data
        )
        db.session.add(vote)
        db.session.commit()
        flash("Vote submitted successfully!", "success")
        return redirect(url_for('room_detail', room_code=room_code))

    tied_options = None 
    winning_option = None  
    if not room.is_open:
        vote_counts = {option.id: len(option.votes) for option in options}

        max_votes = max(vote_counts.values())

        tied_options = [option for option in options if len(option.votes) == max_votes]

        if len(tied_options) > 1 and is_creator: 
            if request.method == 'POST' and 'choose_random' in request.form:

                winning_option = random.choice(tied_options)
                flash(f"Randomly selected: {winning_option.text}", "success")
                room.is_open = False
                db.session.commit()
                random_vote = Vote(
                    voter_id=current_user.id, 
                    option_id=winning_option.id
                )
                db.session.add(random_vote)
                db.session.commit()

        else:
            winning_option = options[0] if vote_counts.get(options[0].id, 0) == max_votes else None
            for option in options:
                if len(option.votes) == max_votes:
                    winning_option = option

    return render_template(
        'room_detail.html',
        room=room,
        form=form,
        vote_form=vote_form,
        options=options,
        is_creator=is_creator,
        existing_vote=existing_vote,
        tied_options=tied_options,
        winning_option=winning_option 
    )

