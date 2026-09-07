from pydantic import BaseModel, EmailStr, field_validator


def validate_password(value: str) -> str:
    # bcrypt only hashes the first 72 bytes, so reject longer inputs explicitly.
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must be 72 bytes or fewer.")
    return value


class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        return validate_password(value)


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        return validate_password(value)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"