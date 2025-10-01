from enum import Enum

from app.errors.errors import GenericError
from http import HTTPStatus


class BaseEnum(Enum):
    @classmethod
    def get_by_char(cls, db_char):
        for action in cls:
            if action.value[0] == db_char:
                return action
        raise GenericError(
            HTTPStatus.BAD_REQUEST,
            HTTPStatus.BAD_REQUEST.phrase,
            f"Error..Caracter de accion no valido {db_char}"
        )

    def get_descripcion(self):
        return self.value[1]

    def get_caracter(self):
        return self.value[0]


class Sesion(BaseEnum):

    LOGIN = ('I',"INICIO DE SESION")
    LOGOUT = ('C',"CIERRE DE SESION")
    REGISTRO_DE_USUARIO = ('R',"REGISTRO DE USUARIO")
    ACTUALIZACION_PASSWORD = ('P',"ACTUALIZACION DE PASSWORD")
    ACTUALIZACION_PERFIL = ('K',"ACTUALIZACION DE IMAGEN DE PERFIL")
    ACTUALIZACION_DATA = ('U',"ACTUALIZACION DE DATOS")
    DELETE_ACCOUNT = ('D',"ELIMINACION DE CUENTA")
    BLOCK_ACCOUNT = ('B',"BLOCKEO DE CUENTA")
    
class Estado(BaseEnum):
    DISPONIBLE = ('D',"DISPONIBLE")
    NO_DISPONIBLE = ('N',"NO DISPONIBLE")
    PENDIENTE = ('P','PENDIENTE')
    PAGADO = ('G','PAGADO')