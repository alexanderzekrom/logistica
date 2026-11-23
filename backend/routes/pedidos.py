from typing import List, Optional, Dict, Set
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from config.database import get_db
from models.database_models import PedidoModel, ClienteModel, ConductorModel, VehiculoModel, RolEnum, EstadoPedidoEnum
from models.schemas import PedidoCreate, PedidoUpdateState, PedidoResponse
from routes.auth import get_current_user_optional

# Reglas de transición de estado por rol
TRANSICIONES_PERMITIDAS: Dict[str, Set[str]] = {
    EstadoPedidoEnum.PENDIENTE: {
        EstadoPedidoEnum.ASIGNADO,
        EstadoPedidoEnum.CANCELADO,
    },
    EstadoPedidoEnum.ASIGNADO: {
        EstadoPedidoEnum.EN_CAMINO,
        EstadoPedidoEnum.INCIDENCIA,
        EstadoPedidoEnum.CANCELADO,
    },
    EstadoPedidoEnum.EN_CAMINO: {
        EstadoPedidoEnum.ENTREGADO,
        EstadoPedidoEnum.INCIDENCIA,
    },
    EstadoPedidoEnum.ENTREGADO: set(),  # Estado final
    EstadoPedidoEnum.INCIDENCIA: {
        EstadoPedidoEnum.ASIGNADO,
        EstadoPedidoEnum.CANCELADO,
    },
    EstadoPedidoEnum.CANCELADO: set(),  # Estado final
}

# Roles que pueden realizar cada transición
TRANSICIONES_POR_ROL: Dict[str, Set[str]] = {
    EstadoPedidoEnum.PENDIENTE: {RolEnum.ADMIN, RolEnum.CLIENTE},
    EstadoPedidoEnum.ASIGNADO: {RolEnum.ADMIN, RolEnum.CONDUCTOR},
    EstadoPedidoEnum.EN_CAMINO: {RolEnum.ADMIN, RolEnum.CONDUCTOR},
    EstadoPedidoEnum.ENTREGADO: {RolEnum.ADMIN, RolEnum.CONDUCTOR},
    EstadoPedidoEnum.INCIDENCIA: {RolEnum.ADMIN, RolEnum.CONDUCTOR},
    EstadoPedidoEnum.CANCELADO: {RolEnum.ADMIN, RolEnum.CLIENTE},
}

def get_pedidos(db: Session = Depends(get_db)) -> List[PedidoResponse]:
    return db.query(PedidoModel).all()

def listar_pedidos_filtrados(
    db: Session = Depends(get_db), 
    token: Optional[str] = None
) -> List[PedidoResponse]:
    current_user = get_current_user_optional(token, db)
    if current_user:
        if current_user.rol == RolEnum.CONDUCTOR:
            return db.query(PedidoModel).filter(PedidoModel.id_conductor == current_user.conductor_id).all()
        elif current_user.rol == RolEnum.CLIENTE:
            return db.query(PedidoModel).filter(PedidoModel.id_cliente == current_user.cliente_id).all()
    return db.query(PedidoModel).all()

def crear_pedido(
    pedido_in: PedidoCreate,
    db: Session = Depends(get_db),
    token: Optional[str] = None
) -> PedidoResponse:
    current_user = get_current_user_optional(token, db)

    if current_user and current_user.rol == RolEnum.CLIENTE and pedido_in.id_cliente != current_user.cliente_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para crear pedidos a nombre de otro cliente",
        )

    cliente = db.query(ClienteModel).filter(ClienteModel.id_cliente == pedido_in.id_cliente).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El cliente con ID {pedido_in.id_cliente} no existe",
        )

    if pedido_in.id_conductor:
        conductor = db.query(ConductorModel).filter(ConductorModel.id_conductor == pedido_in.id_conductor).first()
        if not conductor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El conductor con ID {pedido_in.id_conductor} no existe",
            )

    if pedido_in.id_vehiculo:
        vehiculo = db.query(VehiculoModel).filter(VehiculoModel.id_vehiculo == pedido_in.id_vehiculo).first()
        if not vehiculo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El vehículo con ID {pedido_in.id_vehiculo} no existe",
            )

    estado_inicial = pedido_in.estado if pedido_in.estado else (
        EstadoPedidoEnum.ASIGNADO
        if pedido_in.id_conductor and pedido_in.id_vehiculo
        else EstadoPedidoEnum.PENDIENTE
    )

    nuevo_pedido = PedidoModel(
        id_cliente=pedido_in.id_cliente,
        id_conductor=pedido_in.id_conductor,
        id_vehiculo=pedido_in.id_vehiculo,
        direccion=pedido_in.direccion,
        latitud=pedido_in.latitud,
        longitud=pedido_in.longitud,
        estado=estado_inicial,
    )

    db.add(nuevo_pedido)
    db.commit()
    db.refresh(nuevo_pedido)
    return nuevo_pedido

def actualizar_pedido_completo(
    id_pedido: int,
    pedido_in: PedidoCreate,
    db: Session = Depends(get_db)
) -> PedidoResponse:
    pedido = db.query(PedidoModel).filter(PedidoModel.id_pedido == id_pedido).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    for field, value in pedido_in.dict(exclude_unset=True).items():
        setattr(pedido, field, value)
        
    db.commit()
    db.refresh(pedido)
    return pedido

def actualizar_estado_pedido(
    id_pedido: int,
    estado_in: PedidoUpdateState,
    db: Session = Depends(get_db),
    token: Optional[str] = None
) -> PedidoResponse:
    current_user = get_current_user_optional(token, db)
    pedido = db.query(PedidoModel).filter(PedidoModel.id_pedido == id_pedido).first()

    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El pedido con ID {id_pedido} no existe",
        )

    # Validar permisos por rol
    if current_user:
        if current_user.rol == RolEnum.CONDUCTOR and pedido.id_conductor != current_user.conductor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para modificar un pedido asignado a otro conductor",
            )
        if current_user.rol == RolEnum.CLIENTE and pedido.id_cliente != current_user.cliente_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para modificar pedidos de otro cliente",
            )

    # Validar que la transición sea permitida
    estado_actual = pedido.estado.value
    nuevo_estado = estado_in.estado.value

    transiciones_desde_actual = TRANSICIONES_PERMITIDAS.get(estado_actual, set())
    if nuevo_estado not in transiciones_desde_actual:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transición no permitida: no se puede cambiar de {estado_actual} a {nuevo_estado}. Estados permitidos desde {estado_actual}: {', '.join(transiciones_desde_actual) if transiciones_desde_actual else 'ninguno (estado final)'}",
        )

    # Validar que el rol tenga permiso para realizar esta transición
    if current_user and current_user.rol.value not in TRANSICIONES_POR_ROL.get(nuevo_estado, set()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"El rol {current_user.rol.value} no tiene permiso para cambiar el estado a {nuevo_estado}",
        )

    # Validaciones especiales por estado
    if nuevo_estado == EstadoPedidoEnum.EN_CAMINO:
        if not pedido.id_conductor or not pedido.id_vehiculo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para cambiar a EN_CAMINO, el pedido debe tener conductor y vehículo asignados",
            )

    if nuevo_estado == EstadoPedidoEnum.ASIGNADO:
        if not pedido.id_conductor or not pedido.id_vehiculo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para cambiar a ASIGNADO, el pedido debe tener conductor y vehículo asignados",
            )

    pedido.estado = estado_in.estado
    db.commit()
    db.refresh(pedido)
    return pedido

def eliminar_pedido(id_pedido: int, db: Session = Depends(get_db)):
    pedido = db.query(PedidoModel).filter(PedidoModel.id_pedido == id_pedido).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    db.delete(pedido)
    db.commit()
