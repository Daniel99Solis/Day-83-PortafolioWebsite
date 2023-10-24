# Imported classes
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import os

# Created classes
from forms import ContactForm, EditForm, CreateForm, LoginForm
from send_email import EmailSender

app = Flask(__name__, static_url_path='/static')

app.config['SECRET_KEY'] = os.environ["APP_KEY"]

# Adding Bootstrap
Bootstrap5(app)

# Adding Special CKEditor field to forms
ckeditor = CKEditor(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
db = SQLAlchemy()
db.init_app(app)

# Variable to check if the person is a visitor or the administrator
current_user = "visitor"


# Creation of the tables of the Data Base
class User(db.Model):
    __tablename__ = "users_data"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    # This will act like a List of Project objects attached to each User.
    # The "user" refers to the user property in the Project class.
    projects = relationship("Project", back_populates="user")


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.String(100))
    img_logo = db.Column(db.String(100))
    img_bg = db.Column(db.String(100))
    # This will act like a List of Project objects attached to each User.
    # The "user" refers to the user property in the Project class.
    projects = relationship("Project", back_populates="category")


class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)

    # Relationship with User Table
    # Create Foreign Key, "user.id"
    user_id = db.Column(db.Integer, db.ForeignKey("users_data.id"))
    # Create reference to the User object, the "python_posts" refers to the python_posts property in the User class.
    user = relationship("User", back_populates="projects")

    # Relationship with Category Table
    # Create Foreign Key, "category.id"
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    # Create reference to the User object, the "python_posts" refers to the python_posts property in the User class.
    category = relationship("Category", back_populates="projects")

    title = db.Column(db.String(250), unique=True, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


def create_categories():
    python = Category(
        name="Python",
        description="Python projects in some fields like webdesign, scrapping, scripts, etc.",
        img_logo="assets/img/python-logo.png",
        img_bg="assets/img/python-bg.png",
    )
    db.session.add(python)
    db.session.commit()
    frontend = Category(
        name="FrontEnd",
        description="FrontEnd projects where I just take care of the interface the user see.",
        img_logo="assets/img/frontend-icon.png",
        img_bg="assets/img/frontend-bg.jpg",
    )
    db.session.add(frontend)
    db.session.commit()
    fullstack = Category(
        name="FullStack",
        description="FullStack projects where I take care of the FrontEnd and also to stored the data generated.",
        img_logo="assets/img/fullstack-icon.png",
        img_bg="assets/img/fullstack-bg.jpg",
    )
    db.session.add(fullstack)
    db.session.commit()
    robotics = Category(
        name="Robotics",
        description="Robotics projects where I apply Cinematic and Dynamic",
        img_logo="assets/img/robotics-icon.png",
        img_bg="assets/img/robotics-bg.jpg",
    )
    db.session.add(robotics)
    db.session.commit()


def create_admin():
    secure_password = generate_password_hash(os.environ["ADMIN_PASSWORD"], method="pbkdf2", salt_length=8)
    admin = User(
        email=os.environ["ADMIN_EMAIL"],
        password=secure_password,
        name="Daniel Solis"
    )
    db.session.add(admin)
    db.session.commit()


def random_projects(categories):
    projects = []
    for category in categories:
        projects_by_category = db.session.execute(db.select(Project).where(Project.category_id == category.id)).scalars().all()
        if len(projects_by_category) == 0:
            print("No projects in this category")
        elif len(projects_by_category) == 1:
            print(projects_by_category[0])
            projects.append(projects_by_category[0])
        else:
            print(projects_by_category)
            for i in range(0, 2):
                projects.append(projects_by_category[i])
    return projects


@app.route('/')
def home():
    categories_data = db.session.execute(db.select(Category))
    categories = categories_data.scalars().all()
    overview_projects = random_projects(categories)  # Function that returns an overview of the projects
    user_data = db.session.execute(db.select(User))
    user = user_data.scalars().all()
    if not categories:
        create_categories()
        categories_data = db.session.execute(db.select(Category))
        categories = categories_data.scalars().all()
    if not user:
        create_admin()
    return render_template("index.html", user=current_user, projects=overview_projects, categories=categories)


# --------------------------------- Show Projects ---------------------------------- #
@app.route('/projects/<name>/<category_id>')
def show_projects(name, category_id):
    global current_user
    projects_by_category = db.session.execute(db.select(Project).where(Project.category_id == category_id))
    projects = projects_by_category.scalars().all()
    category = db.get_or_404(Category, category_id)
    categories_data = db.session.execute(db.select(Category))
    categories = categories_data.scalars().all()

    return render_template("projects_template.html", projects=projects, category=category, user=current_user, categories=categories)


@app.route("/project/<category>/<int:project_id>")
def show_project(category, project_id):
    global current_user
    project_to_show = db.get_or_404(Project, project_id)
    category_data = db.session.execute(db.select(Category).where(Category.name == category))
    category_info = category_data.scalar()
    categories_data = db.session.execute(db.select(Category))
    categories = categories_data.scalars().all()
    return render_template("project_template.html", project=project_to_show, user=current_user, category=category_info, categories=categories)


@app.route('/create-project/<category>/<int:c_id>', methods=["GET", "POST"])
def create_project(category, c_id):
    create_form = CreateForm()
    action = "Create"
    categories_data = db.session.execute(db.select(Category))
    categories = categories_data.scalars().all()
    if create_form.validate_on_submit():
        new_project = Project(
            user=db.get_or_404(User, 1),
            category=db.get_or_404(Category, c_id),
            title=create_form.title.data,
            description=create_form.description.data,
            body=create_form.body.data,
            date=date.today().strftime("%B %d, %Y"),
            img_url=create_form.img_url.data
        )
        db.session.add(new_project)
        db.session.commit()
        new_add_python = db.session.execute(db.select(Project).where(Project.title == create_form.title.data)).scalar()
        return redirect(url_for("show_project", category=category, project_id=new_add_python.id))
    return render_template("create_edit_project.html", form=create_form, action=action, user=current_user, categories=categories, cat_name=category)


@app.route("/edit-project/<category>/<int:project_id>", methods=["GET", "POST"])
def edit_project(category, project_id):
    post_to_edit = db.get_or_404(Project, project_id)
    categories_data = db.session.execute(db.select(Category))
    categories = categories_data.scalars().all()
    edit_form = EditForm(
        title=post_to_edit.title,
        description=post_to_edit.description,
        img_url=post_to_edit.img_url,
        body=post_to_edit.body
    )
    action = "Edit"
    if edit_form.validate_on_submit():
        post_to_edit.title = edit_form.title.data
        post_to_edit.description = edit_form.description.data
        post_to_edit.img_url = edit_form.img_url.data
        post_to_edit.user = db.get_or_404(User, 1)
        post_to_edit.body = edit_form.body.data
        post_to_edit.date = date.today().strftime("%B %d, %Y")
        db.session.commit()
        return redirect(url_for("show_project", category=category, project_id=post_to_edit.id))
    return render_template("create_edit_project.html", form=edit_form, action=action, user=current_user, categories=categories, cat_name=category)


@app.route("/delete-project/<category>/<int:project_id>")
def delete_project(category, project_id):
    project_to_delete = db.get_or_404(Project, project_id)
    db.session.delete(project_to_delete)
    db.session.commit()
    category_info = db.session.execute(db.select(Category).where(Category.name == category)).scalar()
    category_name = category_info.name
    category_id = category_info.id
    return redirect(url_for("show_projects", name=category_name, category_id=category_id))


# ------------------------ Hobbies -------------------------------------------------- #
@app.route('/hobbies')
def hobbies():
    categories_data = db.session.execute(db.select(Category))
    categories = categories_data.scalars().all()
    return render_template("hobbies.html", categories=categories, user=current_user)


@app.route('/contact', methods=["GET", "POST"])
def contact():
    global current_user
    contact_form = ContactForm()
    categories_data = db.session.execute(db.select(Category))
    categories = categories_data.scalars().all()
    if request.method == "POST":
        if contact_form.validate_on_submit():
            sender = EmailSender()
            msm_data = {"name": contact_form.name.data, "email": contact_form.email.data,
                        "phone": contact_form.phone.data, "message": contact_form.message.data}
            sender.send_mail(msm_data)
            return render_template("contact.html", form=contact_form, method=request.method, user=current_user, categories=categories)
    return render_template("contact.html", form=contact_form, method=request.method, user=current_user, categories=categories)


@app.route('/admin', methods=["GET", "POST"])
def administrator():
    login_form = LoginForm()
    categories_data = db.session.execute(db.select(Category))
    categories = categories_data.scalars().all()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        # Find user by email entered.
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()

        # Check if the email is correct
        if user is None:
            flash("The email is not correct, check if it has any typo please.")
            return redirect(url_for("administrator"))
        # Check stored password hash against entered password hashed.
        elif check_password_hash(user.password, password):
            global current_user
            current_user = "admin"
            return redirect(url_for('home'))
        else:
            flash("Sorry, The password is wrong, try again please.")
            return redirect(url_for("administrator"))
    return render_template("login_admin.html", form=login_form, categories=categories)


@app.route('/logout_admin', methods=["GET", "POST"])
def logout_admin():
    global current_user
    current_user = "visitor"
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True, port=5002)
