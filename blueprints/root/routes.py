#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Root Routes for nDART Application

This module contains the root route and other main application routes.
"""

from flask import Blueprint, redirect, url_for
from flask_login import login_required

# Create the root blueprint
root_bp = Blueprint('root', __name__)


@root_bp.route('/')
@login_required
def index():
    """Root route - redirects to dashboard after login."""
    return redirect(url_for('main_bp.dashboard'))
