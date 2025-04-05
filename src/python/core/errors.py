# -*- coding: utf-8 -*-

from fastapi import HTTPException, status, logger
import mongoengine


def handle_api_exceptions(exception):
    logger.logger.error(exception)
    if isinstance(exception, mongoengine.errors.DoesNotExist):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
        )
    elif isinstance(exception, HTTPException):
        raise HTTPException(
            status_code=exception.status_code,
            detail=exception.detail,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
 