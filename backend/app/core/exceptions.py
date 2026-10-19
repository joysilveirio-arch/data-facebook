from fastapi import HTTPException, status

class AppError(HTTPException):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=message)

class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)

class ValidationError(AppError):
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)

class ModelNotTrainedError(AppError):
    def __init__(self, message: str = "Model belum dilatih"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)

class ImportError_(AppError):
    def __init__(self, message: str = "Import gagal"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)