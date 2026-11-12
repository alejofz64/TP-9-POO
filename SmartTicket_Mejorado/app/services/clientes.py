from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import Cliente
from app.domain.exceptions import NoEncontrado, ConflictoEstado
from app.repositories import ClienteRepositorio
from app.schemas import ClienteCrear


class ClienteServicio:
    def __init__(self, db: Session, repo: ClienteRepositorio):
        self.db, self.repo = db, repo

    def crear(self, datos: ClienteCrear):
        email = datos.email.strip().lower()
        if not email:
            raise ConflictoEstado("El correo es obligatorio")
        if self.repo.por_email(email):
            raise ConflictoEstado("Ya existe un cliente con ese correo")
        cliente = Cliente(nombre=datos.nombre.strip(), email=email)
        self.repo.agregar(cliente)
        try:
            self.db.commit()
        except IntegrityError as err:
            self.db.rollback()
            raise ConflictoEstado("Ya existe un cliente con ese correo") from err
        self.db.refresh(cliente)
        return cliente

    def listar(self):
        return self.repo.listar()

    def obtener(self, id: int):
        cliente = self.repo.obtener(id)
        if cliente is None:
            raise NoEncontrado("Cliente no encontrado")
        return cliente
