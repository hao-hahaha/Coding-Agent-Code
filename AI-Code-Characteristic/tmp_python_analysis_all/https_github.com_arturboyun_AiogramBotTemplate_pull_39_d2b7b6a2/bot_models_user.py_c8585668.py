from sqlalchemy.orm import Mapped, mapped_column
from bot.models.base import Base
from bot.models.fields import uuid_pk, chat_id_bigint


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid_pk]
    chat_id: Mapped[chat_id_bigint]
    username: Mapped[str | None] = mapped_column(nullable=True, unique=True)
    first_name: Mapped[str]
    last_name: Mapped[str | None]
    blocked: Mapped[bool] = mapped_column(default=False, server_default="false")
