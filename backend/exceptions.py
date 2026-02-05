"""Custom exceptions for Antariks Clipper"""


class AntariksException(Exception):
    """Base exception for Antariks Clipper"""
    pass


class LicenseException(AntariksException):
    """License-related exceptions"""
    pass


class JobException(AntariksException):
    """Job-related exceptions"""
    pass


class ClipException(AntariksException):
    """Clip-related exceptions"""
    pass


class RenderException(AntariksException):
    """Render-related exceptions"""
    pass


class VideoException(AntariksException):
    """Video processing exceptions"""
    pass
