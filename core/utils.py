from rest_framework import status
from rest_framework.response import Response as DRFResponse


class Response(DRFResponse):
    """
    Custom Response class for consistent API responses across all endpoints.

    Usage:
        return Response(
            status=status.HTTP_200_OK,
            message="Success",
            data={"key": "value"}
        )

        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            message="Validation failed",
            error_details={"field": ["This field is required"]}
        )
    """

    def __init__(
        self,
        status=status.HTTP_200_OK,
        message="Success",
        data=None,
        error_details=None,
        additional_info=None,
        status_code=None,
        *args,
        **kwargs,
    ):
        content = {
            "status": status,
            "message": message,
            "data": data if data is not None else {},
        }

        if error_details is not None:
            content["error_details"] = error_details

        if additional_info is not None:
            content["additional_info"] = additional_info

        if status_code is not None:
            content["status_code"] = status_code

        super().__init__(content, status=status, *args, **kwargs)
