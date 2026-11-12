"""Repositorios separados por entidad (persistencia / GRASP)."""
from .lugares import LugarRepositorio
from .sectores import SectorRepositorio
from .clientes import ClienteRepositorio
from .eventos import EventoRepositorio
from .precios import PrecioRepositorio
from .entradas import EntradaRepositorio
from .ventas import VentaRepositorio

__all__ = ["LugarRepositorio", "SectorRepositorio", "ClienteRepositorio", "EventoRepositorio",
           "PrecioRepositorio", "EntradaRepositorio", "VentaRepositorio"]
