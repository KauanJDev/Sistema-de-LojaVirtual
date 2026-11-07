from enum import Enum
class StatusPedido(str, Enum):
    AGUARDANDO_CONFIRMACAO = "AGUARDANDO_CONFIRMACAO"
    CONFIRMADO = "CONFIRMADO"
    ENVIADO = "ENVIADO"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"

class TipoMovimentacao(str, Enum):
    ENTRADA = "ENTRADA"
    SAIDA_VENDA = "SAIDA_VENDA"
    ESTORNO_CANCELAMENTO = "ESTORNO_CANCELAMENTO"
    AJUSTE = "AJUSTE"

STATUS_VENDA_EFETIVADA = (
    StatusPedido.CONFIRMADO,
    StatusPedido.ENVIADO,
    StatusPedido.ENTREGUE,
)

TRANSICOES_PERMITIDAS = {
    StatusPedido.AGUARDANDO_CONFIRMACAO: {StatusPedido.CONFIRMADO, StatusPedido.CANCELADO},
    StatusPedido.CONFIRMADO: {StatusPedido.ENVIADO, StatusPedido.CANCELADO},
    StatusPedido.ENVIADO: {StatusPedido.ENTREGUE},
    StatusPedido.ENTREGUE: set(),
    StatusPedido.CANCELADO: set(),
}