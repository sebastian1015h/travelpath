class TravelPathException(Exception):
    """Base para todas las excepciones de dominio."""

class FechaPasadaException(TravelPathException): pass
class FechaInvalidaException(TravelPathException): pass
class OrigenIgualDestinoException(TravelPathException): pass
class SuperposicionDeViajesException(TravelPathException): pass
class UsuarioNoEncontradoException(TravelPathException): pass
class CredencialesInvalidasException(TravelPathException): pass
class ItinerarioNoEncontradoException(TravelPathException): pass
class ItinerarioPasadoException(TravelPathException): pass
class EmailYaRegistradoException(TravelPathException): pass
class AeropuertoNoEncontradoException(TravelPathException): pass
