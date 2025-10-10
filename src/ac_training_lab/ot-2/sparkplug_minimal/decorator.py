"""Minimal Sparkplug B decorator for auto-registering device tasks."""

_task_registry = {}


def sparkplug_task(func):
    """Register a function as a Sparkplug B metric that can be called remotely."""
    _task_registry[func.__name__] = func
    return func


def get_registered_tasks():
    """Get all registered tasks for publishing in Birth certificate."""
    return _task_registry
