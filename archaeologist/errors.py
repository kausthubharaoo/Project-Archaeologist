class ArchaeologistError(Exception):
    """Base exception for Project Archaeologist."""
    pass


class ProjectNotFoundError(ArchaeologistError):
    """Raised when the project path does not exist."""
    pass


class InvalidProjectError(ArchaeologistError):
    """Raised when the supplied path is not a directory."""
    pass


class GitRepositoryError(ArchaeologistError):
    """Raised when Git analysis cannot be performed."""
    pass