from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log in")


class RegisterForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=64)],
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters."),
            # regex checks for at least one upper, lower and number
            Regexp(
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$",
                message="Password must contain uppercase, lowercase, and a digit.",
            ),
        ],
    )
    confirm = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")


# MFA forms - only admins need these

class MFAVerifyForm(FlaskForm):
    token = StringField(
        "Authenticator code",
        validators=[
            DataRequired(),
            Length(min=6, max=6, message="Code must be exactly 6 digits."),
            Regexp(r"^\d{6}$", message="Code must be 6 digits."),
        ],
    )
    submit = SubmitField("Verify")


class MFASetupForm(FlaskForm):
    # shown once during setup so we can check the authenticator app is working
    token = StringField(
        "Enter the 6-digit code from your authenticator app",
        validators=[
            DataRequired(),
            Length(min=6, max=6),
            Regexp(r"^\d{6}$", message="Code must be 6 digits."),
        ],
    )
    submit = SubmitField("Enable MFA")
