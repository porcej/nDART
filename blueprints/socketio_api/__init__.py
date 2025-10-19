#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SocketIO API Blueprint for nDART Application

This blueprint handles SocketIO events for the /api namespace.
"""

from .routes import socketio_api_bp

__all__ = ['socketio_api_bp']
